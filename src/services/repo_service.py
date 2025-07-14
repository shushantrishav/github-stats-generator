# src/services/repo_service.py
from typing import Dict, Any, List

from src.config.api_client import GitHubAPIClient # Import the new API client
from src.utils.logger import get_logger # Import the new logger utility

logger = get_logger(__name__) # Initialize logger for this module

class GitHubRepoService:
    """
    Service responsible for fetching repository-related statistics.
    Now also includes total PRs and Issues authored by the user.
    """
    def __init__(self, api_client: GitHubAPIClient):
        self.api_client = api_client
        self.username = api_client.username # Get username from API client

    def get_total_stars(self) -> int:
        """
        Fetches the total number of stars across all public repositories owned by the user.
        """
        total_stars = 0
        page = 1
        while True:
            repos = self.api_client.get_user_repos(page=page)
            if not repos or not isinstance(repos, list) or "error" in repos:
                # Handle API errors or no more repos
                if "error" in repos:
                    logger.error(f"Error fetching user repos for total stars: {repos['error']}")
                break
            for repo in repos:
                total_stars += repo.get('stargazers_count', 0)
            page += 1
        return total_stars

    def get_repo_counts(self) -> Dict[str, int]:
        """
        Fetches the count of owned, contributed, and total repositories using GraphQL.
        """
        query = f"""
        {{
          user(login: "{self.username}") {{
            repositories(first: 1, ownerAffiliations: OWNER) {{
              totalCount
            }}
            repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE], first: 1) {{
              totalCount
            }}
          }}
        }}
        """
        data = self.api_client.execute_graphql_query(query)
        if 'errors' in data or 'data' not in data or data['data'] is None:
            logger.error(f" Error fetching repo counts for {self.username}: {data.get('errors', 'Unknown GraphQL error')}") # Use logger.error
            return {"owned": 0, "contributed": 0, "total": 0}

        user = data.get('data', {}).get('user', {})
        owned = user.get('repositories', {}).get('totalCount', 0)
        contributed = user.get('repositoriesContributedTo', {}).get('totalCount', 0)
        return {
            'owned': owned,
            'contributed': contributed,
            'total': owned + contributed
        }

    def get_total_prs_authored(self) -> int:
        """
        Fetches the total number of Pull Requests authored by the user using the Search API.
        """
        url = "https://api.github.com/search/issues"
        query_params = {'q': f'type:pr author:{self.username}'}
        
        data = self.api_client._make_request("GET", url, params=query_params)
        
        if "error" in data:
            logger.error(f" Error fetching total PRs for {self.username}: {data.get('error')}") # Use logger.error
            return 0
        return data.get('total_count', 0)

    def get_total_issues_authored(self) -> int:
        """
        Fetches the total number of Issues authored by the user using the Search API.
        """
        url = "https://api.github.com/search/issues"
        query_params = {'q': f'type:issue author:{self.username}'}
        
        data = self.api_client._make_request("GET", url, params=query_params)
        
        if "error" in data:
            logger.error(f" Error fetching total Issues for {self.username}: {data.get('error')}") # Use logger.error
            return 0
        return data.get('total_count', 0)