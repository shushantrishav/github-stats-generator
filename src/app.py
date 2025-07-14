# app.py
import os
import asyncio
from datetime import date

from fastapi import FastAPI, HTTPException, status, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import json

# Import your existing classes
from src.github_stats import GitHubStatsAggregator
from src.cache.cache_manager import CacheManager
from src.config.config import get_cache_file
from src.models.models import GitHubProfileStats
from src.svg_util.svg_util import GitHubSVGUtil
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="GitHub Stats API",
    description="Fetches and caches comprehensive GitHub user statistics.",
    version="1.0.0",
)

# Configure CORS middleware
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables once when the app starts
load_dotenv()
env = Environment(loader=FileSystemLoader("templates"))

# Define SVG cache directory
SVG_CACHE_DIR = "cache/svg/"

@app.on_event("startup")
async def startup_event():
    """Event handler that runs when the application starts."""
    # Ensure SVG cache directory exists on startup
    os.makedirs(SVG_CACHE_DIR, exist_ok=True)
    logger.info(f"Ensured SVG cache directory exists: {SVG_CACHE_DIR}")

# New Helper Function for fetching and caching stats
async def _fetch_and_cache_github_stats(username: str, token: str, cache_manager: CacheManager) -> GitHubProfileStats:
    """
    Helper function to fetch fresh GitHub stats and save them to cache.
    Raises HTTPException if fetching fails.
    """
    logger.info(f" Fetching fresh GitHub stats for {username}...")
    try:
        aggregator = GitHubStatsAggregator(username, token)
        stats = await asyncio.to_thread(aggregator.get_all_stats)
        # Use .dict() for Pydantic v1 compatibility
        await asyncio.to_thread(cache_manager.save_stats_to_cache, stats.dict())
        logger.info(f" Successfully fetched and cached stats for {username}.")
        return stats
    except Exception as e:
        logger.error(f" Failed to fetch stats for {username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GitHub stats for {username}: {e}"
        )

@app.get("/stats/{username}", response_class=JSONResponse)
async def get_github_stats(username: str):
    """
    Fetches comprehensive GitHub statistics for a given username.
    Stats are cached to reduce API calls.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub token not configured. Please set GITHUB_TOKEN environment variable."
        )

    CACHE_FILE = get_cache_file(username)
    cache_manager = CacheManager(CACHE_FILE)

    stats = await asyncio.to_thread(cache_manager.load_cached_stats)

    if stats:
        logger.info(f"Using cached stats for {username}.")
        # Validate cached stats against the Pydantic model schema
        try:
            # Ensure the loaded stats are converted back into a Pydantic model
            stats = GitHubProfileStats(**stats)
        except Exception as e:
            logger.warning(f" Cached stats for {username} do not match schema: {e}. Refetching fresh stats.", exc_info=True)
            stats = None # Force refetch
    else:
        # JSON cache is expired or not present, force refetch
        logger.info(f" JSON cache expired or not present for {username}. Forcing fresh fetch.")
        stats = None

    # If stats are not available (JSON cache expired/missing, or schema mismatch), fetch fresh
    if stats is None:
        stats = await _fetch_and_cache_github_stats(username, github_token, cache_manager)

    # Use .dict() for Pydantic v1 compatibility
    return JSONResponse(content=stats.dict())


@app.get("/stats/{username}/svg", response_class=Response)
async def get_github_stats_svg(username: str):
    """
    Generates an SVG image displaying GitHub statistics for a given username.
    The SVG is cached to reduce regeneration time.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub token not configured. Please set GITHUB_TOKEN environment variable."
        )

    CACHE_FILE = get_cache_file(username)
    SVG_FILE_PATH = os.path.join(SVG_CACHE_DIR, f"cache_{username}.svg")
    cache_manager = CacheManager(CACHE_FILE)

    stats = None # Initialize stats to None

    # Step 1: Try to load from JSON cache first
    cached_json_stats = await asyncio.to_thread(cache_manager.load_cached_stats)

    if cached_json_stats:
        try:
            # Validate JSON cache schema
            stats = GitHubProfileStats(**cached_json_stats) # Convert to Pydantic model for internal consistency
            logger.info(f"Using valid JSON cache for {username}.")

            # Step 2: If JSON cache is valid, check if SVG cache exists and serve it
            if os.path.exists(SVG_FILE_PATH):
                with open(SVG_FILE_PATH, "r") as f:
                    svg_content = f.read()
                logger.info(f"Serving cached SVG for {username}.")
                return Response(content=svg_content, media_type="image/svg+xml")
            else:
                logger.info(f"SVG cache not found for {username}, but valid JSON cache exists. Generating new SVG from cache.")
                # `stats` is already populated from `cached_json_stats`, so we proceed to generation
        except Exception as e:
            logger.warning(f" Cached JSON for {username} do not match schema: {e}. Forcing fresh fetch.", exc_info=True)
            stats = None # Force refetch as JSON cache is invalid/corrupt
    else:
        logger.info(f"JSON cache expired or not present for {username}. Forcing fresh fetch.")
        stats = None # Force refetch as JSON cache is not available or expired

    # Step 3: If `stats` is still None (i.e., no valid JSON cache was found/used), fetch fresh data
    if stats is None:
        stats = await _fetch_and_cache_github_stats(username, github_token, cache_manager)

    # Step 4: Now that we have valid `stats` (either from fresh fetch or valid JSON cache), generate and serve SVG
    try:
        # GitHubSVGUtil.load_stats_from_json expects a path to a JSON file.
        # Since `_fetch_and_cache_github_stats` and `cache_manager.load_cached_stats`
        # both ensure the CACHE_FILE is up-to-date, we can reliably use it here.
        template_data = await asyncio.to_thread(GitHubSVGUtil.load_stats_from_json, CACHE_FILE)
        template = env.get_template("template.svg")
        svg_content = template.render(**template_data)

        # Save the generated SVG to file
        await asyncio.to_thread(lambda: os.makedirs(SVG_CACHE_DIR, exist_ok=True))
        await asyncio.to_thread(lambda: open(SVG_FILE_PATH, "w").write(svg_content))
        logger.info(f"Saved new SVG to cache: {SVG_FILE_PATH}")

        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        logger.error(f" Error generating or saving SVG for {username}: {e}", exc_info=True)
        return HTMLResponse(f"<h3>Error generating or saving SVG: {e}</h3>", status_code=500)


@app.get("/")
async def read_root():
    """
    Root endpoint for the API.
    """
    return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GitHub Stats API</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f4f7f6;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 30px auto;
                    background: #fff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 25px;
                }
                h2 {
                    color: #34495e;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }
                p {
                    margin-bottom: 15px;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    background-color: #ecf0f1;
                    margin-bottom: 10px;
                    padding: 12px 15px;
                    border-left: 4px solid #3498db;
                    border-radius: 4px;
                }
                li strong {
                    color: #2980b9;
                }
                code {
                    background-color: #e0e0e0;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>GitHub Stats API</h1>
                <p>Welcome to the GitHub Stats API! This service allows you to fetch comprehensive statistics for any public GitHub user and even generate an SVG image of their stats.</p>

                <h2>Available Endpoints:</h2>
                <ul>
                    <li>
                        <strong>Get JSON Stats:</strong> <code>/stats/{username}</code>
                        <p>Fetches detailed GitHub profile statistics in JSON format. Replace <code>{username}</code> with the desired GitHub username (e.g., <a href="/stats/octocat">/stats/octocat</a>).</p>
                        <p>This endpoint provides data such as total stars, commits, contributions, repository counts, and contribution streaks.</p>
                    </li>
                    <li>
                        <strong>Get SVG Stats Image:</strong> <code>/stats/{username}/svg</code>
                        <p>Generates a dynamic SVG image displaying the GitHub statistics. Replace <code>{username}</code> with the desired GitHub username (e.g., <a href="/stats/octocat/svg">/stats/octocat/svg</a>).</p>
                        <p>This image can be embedded directly into web pages, READMEs, or other platforms to visually represent a user's GitHub activity.</p>
                    </li>
                </ul>

                <h2>How it Works:</h2>
                <p>The API fetches data from GitHub, aggregates it, and caches the results to optimize performance and reduce API rate limit issues. SVG images are also cached for faster delivery.</p>

                <h2>Note:</h2>
                <p>A <code>GITHUB_TOKEN</code> environment variable is required for the API to function correctly. Without it, requests may fail due to GitHub API rate limits or authentication requirements.</p>
            </div>
        </body>
        </html>
    """)