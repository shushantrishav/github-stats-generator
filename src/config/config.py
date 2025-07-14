# src/config/config.py
import os

# --- Configuration ---

CACHE_DURATION_HOURS = 12

def get_cache_file(username: str) -> str:
    """
    Constructs the path for the cache file.

    Args:
        username (str): The GitHub username.

    Returns:
        str: The full path to the cache file.
    """
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{username}_github_stats.json")