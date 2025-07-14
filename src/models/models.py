# src/models/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import date # Keep import for internal use if converting from date objects

class StreakData(BaseModel):
    """
    Represents a GitHub contribution streak.
    """
    start_date: str = Field(..., description="The start date of the streak (Month DD).")
    end_date: str = Field(..., description="The end date of the streak (Month DD).")
    length: int = Field(..., description="The length of the streak in days.")

class LanguageLOCData(BaseModel):
    """
    Represents estimated lines of code and percentage for a single programming language.
    """
    approx_lines_of_code: int = Field(..., description="Estimated lines of code for this language.")
    percentage: float = Field(..., description="Percentage of total estimated lines of code for this language, rounded to 2 decimal places.")

class GitHubProfileStats(BaseModel):
    """
    A comprehensive data model for a GitHub user's profile statistics.
    """
    username: str = Field(..., description="The GitHub username.")
    total_stars: int = Field(0, description="Total stars received across all owned repositories.")
    total_commits: int = Field(0, description="Total commit contributions made by the user.")
    total_contributions: int = Field(0, description="Total contributions (commits, PRs, issues) across all time.")
    repos_owned: int = Field(0, description="Number of repositories owned by the user.")
    repos_contributed: int = Field(0, description="Number of repositories the user contributed to (excluding owned).")
    repos_total: int = Field(0, description="Total number of repositories (owned + contributed).")
    initial_date: str = Field(..., description="The GitHub account creation date.")
    # These now use the Pydantic StreakData model
    current_streak: Optional[StreakData] = Field(None, description="Details of the current contribution streak.")
    longest_streak: Optional[StreakData] = Field(None, description="Details of the longest contribution streak achieved.")

    total_prs: int = Field(0, description="Total Pull Requests authored by the user.")
    total_issues: int = Field(0, description="Total Issues authored by the user.")
    # This now uses the Pydantic LanguageLOCData model for structured validation
    Languages: Dict[str, LanguageLOCData] = Field({}, description="Estimated lines of code and percentage for specific backend languages.")