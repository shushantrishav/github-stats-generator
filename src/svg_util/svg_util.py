# src/svg_util/svg_util.py
import json
from src.config.config import get_cache_file
from src.utils.logger import get_logger # Import the new logger utility

logger = get_logger(__name__) # Initialize logger for this module

# Constants
SVG_WIDTH = 570
MAX_LANGUAGES = 6
LANG_BAR_COLORS = ["#FF5F1F", "#FFA500", "#F4BB44", "#FFD580", "#FFDEAD", "#FBCEB1", "#FBD5BC"]
LANG_TEXT_X = [5, 135, 245, 330, 400, 480]

class GitHubSVGUtil:
    def load_stats_from_json(json_path):
        try:
            with open(json_path, "r") as f:
                raw = json.load(f)
            stats = raw["stats"]
        except FileNotFoundError:
            logger.error(f"SVGUtil: JSON cache file not found at {json_path}")
            return {} # Or raise an error, depending on desired behavior
        except json.JSONDecodeError as e:
            logger.error(f"SVGUtil: Error decoding JSON from {json_path}: {e}")
            return {}
        except KeyError as e:
            logger.error(f"SVGUtil: Missing expected key in JSON data: {e}")
            return {}
        except Exception as e:
            logger.error(f"SVGUtil: An unexpected error occurred loading JSON: {e}")
            return {}

        # Extract data
        username = stats.get("username", "Unknown User")
        user_name = username.replace("-", " ").title()
        total_stars = f"{stats.get('total_stars', 0):,}34"
        total_commits = f"{stats.get('total_commits', 0):,}"
        total_prs = stats.get("total_prs", 0)
        total_issues = stats.get("total_issues", 0)
        contributed_repos = stats.get("repos_total", 0)
        total_contributions = f"{stats.get('total_contributions', 0):,}"
        contribution_period = f"{stats.get('initial_date', 'N/A')} - Present"

        # Handle streaks, providing default empty dicts if None
        current_streak_data = stats.get('current_streak', {}) or {}
        longest_streak_data = stats.get('longest_streak', {}) or {}

        current_streak = current_streak_data.get('length', 0)
        current_streak_start_date = current_streak_data.get('start_date', 'N/A')
        current_streak_end_date = current_streak_data.get('end_date', 'N/A')
        current_streak_dates = f"{current_streak_start_date} - {current_streak_end_date}"

        longest_streak = longest_streak_data.get('length', 0)
        longest_streak_start_date = longest_streak_data.get('start_date', 'N/A')
        longest_streak_end_date = longest_streak_data.get('end_date', 'N/A')
        longest_streak_dates = f"{longest_streak_start_date} - {longest_streak_end_date}"


        # Placeholder for user rating calculation
        # This would ideally be a more complex logic
        user_rating = "B-"


        # Prepare language bar data
        lang_report = stats.get("Languages", {})
        sorted_langs = sorted(lang_report.items(), key=lambda x: -x[1].get("percentage", 0))[:MAX_LANGUAGES]

        x_cursor = 0
        languages = []
        for i, (lang, details) in enumerate(sorted_langs):
            percent = round(details.get("percentage", 0), 1)
            width = round((percent / 100) * SVG_WIDTH, 2)
            lang_data = {
                "name": lang,
                "percent": percent,
                "width": width,
                "rect_x": x_cursor,
                "text_x": LANG_TEXT_X[i % len(LANG_TEXT_X)], # Use modulo for safety
                "fill": LANG_BAR_COLORS[i % len(LANG_BAR_COLORS)],
            }
            x_cursor += width
            languages.append(lang_data)

        return {
            "user_name": str.upper(user_name),
            "total_stars": total_stars,
            "total_commits": total_commits,
            "total_prs": total_prs,
            "total_issues": total_issues,
            "contributed_repos": contributed_repos,
            "user_rating": user_rating,
            "total_contributions": total_contributions,
            "contribution_period": contribution_period,
            "current_streak": current_streak,
            "current_streak_dates": current_streak_dates,
            "longest_streak": longest_streak,
            "longest_streak_dates": longest_streak_dates,
            "languages": languages,
            "total_language_percent": sum(lang['percent'] for lang in languages) # Sum of displayed language percentages
        }