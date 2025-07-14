# src/services/language_service.py
from typing import Dict, Any, List
from collections import defaultdict
from src.config.api_client import GitHubAPIClient
import os
import json
# Removed: import logging

# Setup logger
# Removed: logging.basicConfig(
# Removed:     level=logging.INFO,
# Removed:     format="%(asctime)s | %(levelname)s | %(message)s"
# Removed: )
from src.utils.logger import get_logger # Import the new logger utility
logger = get_logger(__name__) # Initialize logger for this module


# Constants
BACKEND_LANGUAGES = {
    "Python", "Go", "Java", "JavaScript",
    "Solidity", "C++", "Jupyter Notebook"
}

AVG_BYTES_PER_LINE = {
    "Python": 60, "Go": 20, "Java": 30, "JavaScript": 20,
    "Solidity": 25, "C++": 10, "Jupyter Notebook": 550
}

class GitHubLanguageService:
    """
    Service for estimating lines of code and usage percentages of backend languages.
    """

    def __init__(self, api_client: GitHubAPIClient):
        self.api_client = api_client
        self.username = api_client.username

    def _get_all_user_repos(self) -> List[Dict[str, Any]]:
        """Fetch all public, non-fork repos owned by the user."""
        all_repos = []
        page = 1

        while True:
            try:
                repos = self.api_client.get_user_repos(page=page, per_page=100)
                if not repos:
                    break

                for repo in repos:
                    # Only include owned, non-fork repositories
                    if repo.get("owner", {}).get("login") == self.username and not repo.get("fork"):
                        all_repos.append(repo)
                page += 1
            except Exception as e:
                logger.error(f"Error fetching user repositories for {self.username} (page {page}): {e}", exc_info=True)
                break
        return all_repos

    def get_backend_language_loc(self) -> Dict[str, Any]:
        """
        Estimates lines of code for specified backend languages across all owned, non-fork repos.
        Caches the result.
        """
        language_loc = defaultdict(int)
        all_repos = self._get_all_user_repos()

        for repo in all_repos:
            repo_name = repo.get("name")
            owner_name = repo.get("owner", {}).get("login")
            if not repo_name or not owner_name:
                logger.warning(f"Skipping malformed repository data: {repo}")
                continue

            try:
                lang_data = self.api_client.get_repo_languages(owner_name, repo_name)
            except Exception as e:
                logger.error(f"Error fetching languages for {owner_name}/{repo_name}: {e}", exc_info=True)
                continue

            for lang, bytes_count in lang_data.items():
                if lang in BACKEND_LANGUAGES:
                    est_loc = int(bytes_count // AVG_BYTES_PER_LINE.get(lang, 60))
                    if lang == "Jupyter Notebook":
                        language_loc["Python"] += est_loc
                    else:
                        language_loc[lang] += est_loc

        # Clean and compute total
        language_loc = {lang: loc for lang, loc in language_loc.items() if loc > 0}
        total_loc = sum(language_loc.values())
        logger.info(f"Total estimated LOC: {total_loc}")

        language_report = {}
        for lang, loc in language_loc.items():
            percent = (loc / total_loc * 100) if total_loc else 0
            language_report[lang] = {
                "approx_lines_of_code": loc,
                "percentage": round(percent, 2)
            }

        sorted_language_report = dict(
            sorted(
                language_report.items(),
                key=lambda item: item[1]["percentage"],
                reverse=True
            )
        )

        # Optional: Save to cache (mimicking original script)
        os.makedirs("cache", exist_ok=True)
        try:
            with open("cache/approx_backend_language_loc_cache.json", "w") as f:
                json.dump(sorted_language_report, f, indent=4)
            logger.info(" LOC and percentage report saved to cache/approx_backend_language_loc_cache.json")
        except IOError as e:
            logger.error(f"Error saving language LOC cache: {e}", exc_info=True)


        return sorted_language_report