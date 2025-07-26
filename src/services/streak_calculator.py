# src/services/streak_calculator.py
from datetime import datetime, timedelta
from collections import namedtuple
from typing import Dict, Any, List, Optional

class StreakCalculator:
    """
    Calculates current and longest contribution streaks from raw contribution day data.
    """
    def __init__(self):
        self.Streak = namedtuple('Streak', ['start_date', 'end_date', 'length'])

    def calculate_streaks(self, contribution_days: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates the current and longest contribution streaks from a list of
        contribution day dictionaries.

        Args:
            contribution_days (List[Dict[str, Any]]): A list of dictionaries,
                                                    each with 'date' (str) and 'count' (int).

        Returns:
            Dict[str, Any]: A dictionary containing 'longest_streak' and 'current_streak',
                            each being a dictionary with 'start_date', 'end_date', and 'length',
                            or a default dictionary for current_streak if none.
        """
        days_processed = []
        for day in contribution_days:
            try:
                date = datetime.strptime(day['date'], '%Y-%m-%d').date()
                count = day['count']
                days_processed.append({'date': date, 'count': count})
            except (ValueError, TypeError) as e:
                print(f" Skipping invalid contribution day data: {day} - {e}")
                continue

        # Sort days by date in ascending order
        days_processed.sort(key=lambda x: x['date'])

        # Calculate streaks
        longest_streak_obj = self._calculate_longest_streak(days_processed)
        current_streak_obj = self._calculate_current_streak(days_processed)

        # Convert namedtuple to dictionary for Pydantic compatibility
        # If current_streak_obj is None, provide default values as requested
        today = datetime.today().date()
        current_streak_output = current_streak_obj._asdict() if current_streak_obj else {
            "start_date": today,
            "end_date": today,
            "length": 0
        }

        return {
            "longest_streak": longest_streak_obj._asdict() if longest_streak_obj else None,
            "current_streak": current_streak_output
        }

    def _calculate_longest_streak(self, days: List[Dict[str, Any]]) -> Optional[Any]:
        """
        Calculates the longest streak of consecutive contribution days.
        """
        if not days:
            return None

        longest_length = 0
        longest_start_date = None
        longest_end_date = None

        current_length = 0
        current_start_date = None

        for i in range(len(days)):
            if days[i]['count'] > 0:
                if current_length == 0:
                    current_start_date = days[i]['date']
                current_length += 1
            else:
                if current_length > longest_length:
                    longest_length = current_length
                    longest_start_date = current_start_date
                    longest_end_date = days[i-1]['date'] if i > 0 else current_start_date
                current_length = 0
                current_start_date = None

        # Check after loop for the last streak
        if current_length > longest_length:
            longest_length = current_length
            longest_start_date = current_start_date
            longest_end_date = days[-1]['date']

        if longest_length > 0:
            return self.Streak(
                start_date=longest_start_date,
                end_date=longest_end_date,
                length=longest_length
            )
        return None

    def _calculate_current_streak(self, days: List[Dict[str, Any]]) -> Optional[Any]:
        """
        Calculates the current consecutive streak of contribution days ending today or yesterday.
        Returns a Streak namedtuple or None if no streak is found.
        """
        if not days:
            return None

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # Filter days to include only up to today/yesterday for current streak calculation
        relevant_days = [d for d in days if d['date'] <= today]
        relevant_days.sort(key=lambda x: x['date'], reverse=True) # Process from most recent

        current_length = 0
        current_end_date = None
        current_start_date = None
        
        expected_date = today

        for day_data in relevant_days:
            day_date = day_data['date']
            day_count = day_data['count']

            if day_date == expected_date:
                if day_count > 0:
                    if current_length == 0:
                        current_end_date = day_date
                    current_length += 1
                    current_start_date = day_date # Update start date as we go backward
                    expected_date -= timedelta(days=1)
                else:
                    # Contribution count is 0 for an expected day, streak breaks
                    break
            elif day_date < expected_date:
                # We've skipped a day with 0 contributions, so the streak is broken
                if expected_date == today and day_date == yesterday and day_count > 0:
                    # Edge case: today has no contribution, but yesterday does,
                    # and we are looking for a streak ending yesterday.
                    if current_length == 0:
                        current_end_date = day_date
                    current_length += 1
                    current_start_date = day_date
                    expected_date -= timedelta(days=1)
                else:
                    # If we found an older date with a gap, the streak is broken.
                    break
            else:
                # day_date > expected_date, this shouldn't happen with sorted and filtered data
                continue

        if current_length > 0 and current_end_date:
            return self.Streak(
                start_date=current_start_date,
                end_date=current_end_date,
                length=current_length
            )
        return None