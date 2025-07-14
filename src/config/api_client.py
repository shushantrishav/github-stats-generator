# src/config/api_client.py
import requests
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GitHubAPIClient:
    """
    A low-level client for interacting with the GitHub API (REST and GraphQL).
    Handles authentication and basic error checking.
    """
    def __init__(self, username: str, token: str | None = None):
        self.username = username
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if token:
            self.headers['Authorization'] = f'token {token}'
        else:
            logger.warning("No GitHub token provided. Rate limits might be hit sooner, and some GraphQL queries may not work.")

    def _make_request(self, method: str, url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        Helper method to make a generic REST API request.
        """
        try:
            response = requests.request(method, url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"REST API request failed for {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"    Response status: {e.response.status_code}")
                logger.error(f"    Response content: {e.response.text}")
            # Corrected syntax here: removed escaped quotes from within the dict literal
            return {"errors": [{"message": str(e)}]}

    def get_user_repos(self, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetches a list of public repositories for the user."""
        url = f"https://api.github.com/users/{self.username}/repos"
        result = self._make_request("GET", url, params={'page': page, 'per_page': per_page})
        if isinstance(result, list):
            return result
        logger.error(f"get_user_repos received non-list result or error for {self.username}: {result}")
        return []

    def get_repo_languages(self, owner: str, repo_name: str) -> Dict[str, int]:
        """
        Fetches language breakdown (bytes) for a specific repository.
        """
        url = f"https://api.github.com/repos/{owner}/{repo_name}/languages"
        result = self._make_request("GET", url)
        if isinstance(result, dict) and "error" not in result: # Check for 'error' key to ensure it's not an error dict
            return result
        logger.error(f"get_repo_languages failed for {owner}/{repo_name}: {result}")
        return {}

    def execute_graphql_query(self, query: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Executes a GraphQL query against the GitHub API.
        """
        url = "https://api.github.com/graphql"
        payload = {'query': query, 'variables': variables}
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"    Response status: {e.response.status_code}")
                logger.error(f"    Response content: {e.response.text}")
            # Corrected syntax here: removed escaped quotes from within the dict literal
            return {"errors": [{"message": str(e)}]}