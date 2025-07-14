# src/services/streak_calculator.py
from datetime import datetime, timedelta
from collections import namedtuple
from typing import Dict, Any, List

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
                            or None if no streak exists.
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

        return {
            "longest_streak": longest_streak_obj, # Removed ._asdict() as it's already a dict or None
            "current_streak": current_streak_obj  # Removed ._asdict() as it's already a dict or None
        }

    def _calculate_longest_streak(self, days_processed: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        """
        Calculates the longest contribution streak.
        """
        if not days_processed:
            return None

        max_streak = 0
        current_streak = 0
        longest_start_date = None
        longest_end_date = None
        current_start_date = None

        for i, day_data in enumerate(days_processed):
            day_date = day_data['date']
            day_count = day_data['count']

            if day_count > 0:
                if current_streak == 0:
                    current_start_date = day_date
                    current_streak = 1
                elif day_date == days_processed[i-1]['date'] + timedelta(days=1):
                    current_streak += 1
                else: # Gap in streak
                    current_start_date = day_date
                    current_streak = 1
            else: # Day has 0 contributions
                if current_streak > max_streak:
                    max_streak = current_streak
                    longest_start_date = current_start_date
                    longest_end_date = days_processed[i-1]['date'] # Previous day was end of streak
                current_streak = 0
                current_start_date = None

        # After loop, check if the last streak was the longest
        if current_streak > max_streak:
            max_streak = current_streak
            longest_start_date = current_start_date
            longest_end_date = days_processed[-1]['date']

        longest_streak_obj = None
        if max_streak > 0 and longest_start_date and longest_end_date:
            longest_streak_obj = self.Streak(longest_start_date, longest_end_date, max_streak)
        
        return longest_streak_obj._asdict() if longest_streak_obj else None


    def _calculate_current_streak(self, days_processed: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        """
        Calculates the current contribution streak ending today or yesterday.
        Considers contributions up to the most recent day.
        """
        if not days_processed:
            return None

        today = datetime.now().date()
        current_streak_length = 0
        current_streak_start_date = None
        current_streak_end_date = None # Initialize end date

        # Filter days to include only those up to today (or yesterday if today has no contribution)
        recent_days = [d for d in days_processed if d['date'] <= today]
        recent_days.sort(key=lambda x: x['date'], reverse=True) # Process from most recent backward

        current_day_ptr = 0
        
        while current_day_ptr < len(recent_days):
            day_data = recent_days[current_day_ptr]
            day_date = day_data['date']

            # Check for current day contribution or yesterday's if today has none
            if current_streak_length == 0:
                # If today has contributions
                if day_date == today and day_data['count'] > 0:
                    current_streak_length = 1
                    current_streak_start_date = day_date
                    current_streak_end_date = day_date
                # If yesterday has contributions and today doesn't (or it's the first check and today has no activity)
                elif day_date == today - timedelta(days=1) and day_data['count'] > 0 and (today not in [d['date'] for d in recent_days if d['count'] > 0]):
                    current_streak_length = 1
                    current_streak_start_date = day_date
                    current_streak_end_date = day_date
                elif day_date < today - timedelta(days=1): # We've gone too far back without finding a recent contribution
                    break
            else: # We are already in a streak, check if the previous day was consecutive
                is_consecutive = False
                if current_streak_start_date:
                    # For the first day after identifying the streak start, check if it's today or yesterday
                    if current_streak_length == 1: # This is the first day of the potential streak
                        if (day_date == today or day_date == today - timedelta(days=1)) and day_data['count'] > 0:
                            is_consecutive = True
                            current_streak_end_date = day_date # Set end date to the most recent contribution day
                    else: # Subsequent days in the streak must be exactly one day before the previous
                        if day_date == current_streak_start_date - timedelta(days=1) and day_data['count'] > 0:
                            is_consecutive = True
                    
                    if is_consecutive:
                        current_streak_length += 1
                        current_streak_start_date = day_date # Update start date as we go backward
                    elif current_streak_length > 0: # Streak broken, or no more consecutive days
                        break
                    elif day_date < today - timedelta(days=1) and day_data['count'] == 0:
                        # If we've passed yesterday and there was no contribution, there's no current streak
                        break
                    
                    current_day_ptr += 1

        current_streak_obj = None
        if current_streak_length > 0 and current_streak_start_date and current_streak_end_date:
            current_streak_obj = self.Streak(current_streak_start_date, current_streak_end_date, current_streak_length)

        return current_streak_obj._asdict() if current_streak_obj else None