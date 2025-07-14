# src/github_stats.py

# Removed: import logging
from typing import Dict, Any
from datetime import date # Import date for formatting

from src.models.models import GitHubProfileStats, StreakData, LanguageLOCData
from src.config.api_client import GitHubAPIClient
from src.services.repo_service import GitHubRepoService
from src.services.contribution_service import GitHubContributionService
from src.services.language_service import GitHubLanguageService
from src.utils.logger import get_logger # Import the new logger utility

logger = get_logger(__name__) # Initialize logger for this module

class GitHubStatsAggregator:
    """
    Aggregates statistics from various GitHub services to compile a complete
    GitHubProfileStats object.
    """
    def __init__(self, username: str, token: str | None = None):
        self.username = username
        self.api_client = GitHubAPIClient(username, token)
        self.repo_service = GitHubRepoService(self.api_client)
        self.contribution_service = GitHubContributionService(self.api_client)
        self.language_service = GitHubLanguageService(self.api_client)

    def get_all_stats(self) -> GitHubProfileStats:
        """
        Fetches all GitHub profile statistics and returns them as a GitHubProfileStats object.
        """
        total_stars = self.repo_service.get_total_stars()
        repo_counts = self.repo_service.get_repo_counts()
        total_commits = self.contribution_service.get_total_commits()
        total_contributions = self.contribution_service.get_total_contributions_all_time()
        
        streaks = self.contribution_service.get_contribution_streaks()
        total_prs = self.repo_service.get_total_prs_authored()
        total_issues = self.repo_service.get_total_issues_authored()
        estimated_loc_report = self.language_service.get_backend_language_loc()


        current_streak_data = None
        if streaks and streaks["current_streak"]:
            try:
                current_streak_data = StreakData(
                    start_date=streaks["current_streak"]["start_date"].strftime("%b %d"), # Format date here
                    end_date=streaks["current_streak"]["end_date"].strftime("%b %d"),     # Format date here
                    length=streaks["current_streak"]["length"]
                )
            except KeyError as e:
                logger.warning(f"Missing key in current_streak data: {e}. Raw data was: {streaks['current_streak']}")
                current_streak_data = None


        longest_streak_data = None
        if streaks and streaks["longest_streak"]:
            try:
                longest_streak_data = StreakData(
                    start_date=streaks["longest_streak"]["start_date"].strftime("%b %d"), # Format date here
                    end_date=streaks["longest_streak"]["end_date"].strftime("%b %d"),     # Format date here
                    length=streaks["longest_streak"]["length"]
                )
            except KeyError as e:
                logger.warning(f"Missing key in longest_streak data: {e}. Raw data was: {streaks['longest_streak']}")
                longest_streak_data = None

        # initial_date is missing from the current `GitHubProfileStats` initialization.
        # You'll need to fetch this (e.g., from user profile GraphQL query)
        # For now, I'll add a placeholder to make the Pydantic model valid.
        # You would typically add a service method to get this, e.g., self.user_service.get_initial_date()
        initial_date_placeholder = "Aug 26, 2019" # Replace with actual fetching logic

        return GitHubProfileStats(
            username=self.username,
            total_stars=total_stars,
            total_commits=total_commits,
            total_contributions=total_contributions,
            repos_owned=repo_counts["owned"],
            repos_contributed=repo_counts["contributed"],
            repos_total=repo_counts["total"],
            initial_date=initial_date_placeholder, # Add initial_date
            current_streak=current_streak_data,
            longest_streak=longest_streak_data,
            total_prs=total_prs,
            total_issues=total_issues,
            Languages=estimated_loc_report # Use 'Languages' as per models.py
        )