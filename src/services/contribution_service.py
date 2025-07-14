# src/services/contribution_service.py
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Tuple

from src.config.api_client import GitHubAPIClient
from src.services.streak_calculator import StreakCalculator # Import the new streak calculator
from src.utils.logger import get_logger # Import the new logger utility

logger = get_logger(__name__) # Initialize logger for this module

class GitHubContributionService:
    """
    Service responsible for fetching raw contribution-related data from GitHub.
    It utilizes StreakCalculator for streak calculations.
    """
    def __init__(self, api_client: GitHubAPIClient):
        self.api_client = api_client
        self.username = api_client.username
        self.streak_calculator = StreakCalculator() # Initialize StreakCalculator here

    def get_total_commits(self) -> int:
        """
        Fetches the total number of commit contributions using GraphQL.
        """
        query = f"""
        {{
          user(login: "{self.username}") {{
            contributionsCollection {{
              totalCommitContributions
            }}
          }}
        }}
        """
        data = self.api_client.execute_graphql_query(query)
        if 'errors' in data or 'data' not in data or data['data'] is None:
            logger.error(f" Error fetching total commits for {self.username}: {data.get('errors', 'Unknown GraphQL error')}") # Use logger.error
            return 0
        return data.get('data', {}).get('user', {}).get('contributionsCollection', {}).get('totalCommitContributions', 0)

    def _get_batched_year_ranges(self, start_year: int) -> List[Tuple[str, str]]:
        """
        Generates year ranges for batch fetching contributions to avoid API limits.
        """
        current_year = datetime.now().year
        year_ranges = []
        for year in range(start_year, current_year + 1):
            start_date = f"{year}-01-01T00:00:00Z"
            end_date = f"{year}-12-31T23:59:59Z"
            year_ranges.append((start_date, end_date))
        return year_ranges

    def get_total_contributions_all_time(self) -> int:
        """
        Fetches total contributions by year, then sums them up.
        This includes commits, issues, pull requests, and reviews.
        """
        total_contributions = 0
        # Determine the user's first contribution year or a reasonable starting point
        # For simplicity, let's assume a fixed start year or fetch it if possible.
        # In a real app, you might get the user's creation date.
        first_contribution_year = 2008 # GitHub started in 2008, so a safe lower bound

        year_ranges = self._get_batched_year_ranges(first_contribution_year)

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Map each year range to a call that fetches contributions for that period
            futures = [
                executor.submit(self._fetch_contributions_for_period, start_date, end_date)
                for start_date, end_date in year_ranges
            ]
            for future in futures:
                try:
                    total_contributions += future.result()
                except Exception as e:
                    logger.error(f"Error fetching contributions for a period: {e}", exc_info=True)

        return total_contributions

    def _fetch_contributions_for_period(self, from_date: str, to_date: str) -> int:
        """
        Fetches total contributions within a specific date range using GraphQL.
        """
        query = f"""
        query($username: String!, $from: DateTime!, $to: DateTime!) {{
          user(login: $username) {{
            contributionsCollection(from: $from, to: $to) {{
              contributionCalendar {{
                totalContributions
              }}
            }}
          }}
        }}
        """
        variables = {
            "username": self.username,
            "from": from_date,
            "to": to_date
        }
        data = self.api_client.execute_graphql_query(query, variables)

        if 'errors' in data or 'data' not in data or data['data'] is None:
            logger.error(f" Error fetching contributions for period {from_date} to {to_date}: {data.get('errors', 'Unknown GraphQL error')}") # Use logger.error
            return 0
        
        return data.get('data', {}).get('user', {}).get('contributionsCollection', {}).get('contributionCalendar', {}).get('totalContributions', 0)

    def get_contribution_days_data(self) -> List[Dict[str, Any]]:
        """
        Fetches all individual contribution days with their counts for streak calculation.
        """
        query = f"""
        {{
          user(login: "{self.username}") {{
            contributionsCollection {{
              contributionCalendar {{
                weeks {{
                  contributionDays {{
                    date
                    contributionCount
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        data = self.api_client.execute_graphql_query(query)
        if 'errors' in data or 'data' not in data or data['data'] is None:
            logger.error(f" Error fetching contribution calendar for streaks for {self.username}: {data.get('errors', 'Unknown GraphQL error')}") # Use logger.error
            return []

        days = [
            {
                'date': day['date'],
                'count': day['contributionCount']
            }
            for week in data.get('data', {}).get('user', {}).get('contributionsCollection', {}).get('contributionCalendar', {}).get('weeks', [])
            for day in week.get('contributionDays', [])
        ]
        return days

    def get_contribution_streaks(self) -> Dict[str, Any]:
        """
        Fetches raw contribution day data and then calculates the current and longest streaks.
        """
        contribution_days_data = self.get_contribution_days_data()
        return self.streak_calculator.calculate_streaks(contribution_days_data)