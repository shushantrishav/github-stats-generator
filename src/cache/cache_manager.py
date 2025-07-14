# src/cache/cache_manager.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from src.config.config import CACHE_DURATION_HOURS
from src.models.models import GitHubProfileStats # Import the dataclass
from src.utils.logger import get_logger # Import the new logger utility

logger = get_logger(__name__) # Initialize logger for this module

class CacheManager:
    """
    Manages caching of GitHub profile statistics to a JSON file.
    """
    def __init__(self, cache_file: str):
        self.cache_file = cache_file

    def load_cached_stats(self) -> Dict[str, Any] | None:
        """
        Loads cached GitHub stats if available and not expired.

        Returns:
            dict | None: The cached statistics as a dictionary if valid, otherwise None.
        """
        if not os.path.exists(self.cache_file):
            logger.info(f"Cache file not found at {self.cache_file}.")
            return None
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                last_updated = datetime.fromisoformat(data.get("last_updated"))
                if datetime.now() - last_updated < timedelta(hours=CACHE_DURATION_HOURS):
                    return data.get("stats")
                else:
                    logger.info(f"Cache file at {self.cache_file} has expired.")
        except Exception as e:
            logger.error(f" Failed to load cache from {self.cache_file}: {e}", exc_info=True) # Use logger.error
        return None

    def save_stats_to_cache(self, stats_dict: Dict[str, Any]):
        """
        Saves the given statistics to the cache file.

        Args:
            stats_dict (dict): The GitHub profile statistics as a dictionary.
        """
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "stats": stats_dict
                }, f, indent=2, default=str) # default=str to handle datetime objects if any
            logger.info(f"Stats successfully saved to cache: {self.cache_file}")
        except IOError as e:
            logger.error(f"Error saving stats to cache file {self.cache_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving cache to {self.cache_file}: {e}", exc_info=True)