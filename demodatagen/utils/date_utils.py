#!/usr/bin/env python3
"""
CarbonTally Data Generator - Date Utilities
Handles date generation and manipulation.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import random
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List, Union
from dateutil.relativedelta import relativedelta
import pytz


class DateUtils:
    """Utilities for generating and manipulating dates."""
    
    @staticmethod
    def random_date(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_time: bool = True
    ) -> datetime:
        """
        Generate a random date between two dates.
        
        Args:
            start_date: Start of range (default: 1 year ago)
            end_date: End of range (default: now)
            include_time: Include time component
            
        Returns:
            Random datetime.
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        delta = end_date - start_date
        random_days = random.randint(0, max(0, delta.days))
        random_seconds = random.randint(0, 86399) if include_time else 0
        
        result = start_date + timedelta(days=random_days, seconds=random_seconds)
        
        if not include_time:
            result = result.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return result
    
    @staticmethod
    def random_date_business(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_weekends: bool = False
    ) -> datetime:
        """
        Generate a random date, optionally excluding weekends.
        
        Args:
            start_date: Start of range
            end_date: End of range
            include_weekends: Include weekends in selection
            
        Returns:
            Random date (business days only if include_weekends=False).
        """
        date = DateUtils.random_date(start_date, end_date, include_time=False)
        
        if not include_weekends:
            while date.weekday() >= 5:  # Saturday=5, Sunday=6
                date = DateUtils.random_date(start_date, end_date, include_time=False)
        
        return date
    
    @staticmethod
    def random_date_range(
        min_days: int = 1,
        max_days: int = 365,
        start_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """
        Generate a random date range.
        
        Args:
            min_days: Minimum number of days in range
            max_days: Maximum number of days in range
            start_date: Start of range (default: random date in last year)
            
        Returns:
            Tuple of (start_date, end_date).
        """
        if start_date is None:
            start_date = DateUtils.random_date()
        
        range_days = random.randint(min_days, max_days)
        end_date = start_date + timedelta(days=range_days)
        
        return start_date, end_date
    
    @staticmethod
    def random_quarter_end(year: Optional[int] = None) -> datetime:
        """
        Generate a random quarter-end date.
        
        Args:
            year: Year (default: current or random)
            
        Returns:
            Quarter-end datetime.
        """
        if year is None:
            year = random.randint(2020, 2026)
        
        quarter = random.randint(1, 4)
        month = quarter * 3
        day = 30 if month in [3, 6, 9] else 31  # Q4 ends Dec 31
        
        return datetime(year, month, day)
    
    @staticmethod
    def random_financial_year_end(country: str = "UK") -> datetime:
        """Generate a financial year end date."""
        year = random.randint(2020, 2025)
        
        # Common FYE months by country
        months = {
            "UK": [3, 12],  # March or December
            "IE": [12, 6],  # December or June
            "DE": [12],      # December
            "FR": [12],      # December
            "NL": [12],      # December
            "BE": [12],      # December
            "FI": [12]       # December
        }
        
        month = random.choice(months.get(country, [12]))
        day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
        
        return datetime(year, month, day)
    
    @staticmethod
    def is_business_day(date_obj: Union[datetime, date]) -> bool:
        """Check if a date is a business day (Monday-Friday)."""
        return date_obj.weekday() < 5
    
    @staticmethod
    def is_holiday(date_obj: Union[datetime, date], country: str = "UK") -> bool:
        """Check if a date is a holiday in a given country."""
        # Simplified holiday checking
        holidays = {
            "UK": [
                (1, 1),  # New Year's Day
                (12, 25), # Christmas
                (12, 26)  # Boxing Day
            ],
            "IE": [
                (1, 1),   # New Year's Day
                (3, 17),  # St. Patrick's Day
                (12, 25)  # Christmas
            ]
        }
        
        month = date_obj.month
        day = date_obj.day
        
        for holiday_month, holiday_day in holidays.get(country, []):
            if month == holiday_month and day == holiday_day:
                return True
        
        return False
    
    @staticmethod
    def get_business_days_between(
        start_date: Union[datetime, date],
        end_date: Union[datetime, date],
        exclude_holidays: bool = True,
        country: str = "UK"
    ) -> int:
        """Count business days between two dates."""
        current = start_date
        count = 0
        
        while current <= end_date:
            if DateUtils.is_business_day(current):
                if exclude_holidays and DateUtils.is_holiday(current, country):
                    pass  # Skip holiday
                else:
                    count += 1
            current += timedelta(days=1)
        
        return count
    
    @staticmethod
    def add_business_days(
        start_date: Union[datetime, date],
        days: int,
        exclude_holidays: bool = True,
        country: str = "UK"
    ) -> datetime:
        """Add business days to a date."""
        current = start_date
        added = 0
        
        while added < days:
            current += timedelta(days=1)
            if DateUtils.is_business_day(current):
                if exclude_holidays and DateUtils.is_holiday(current, country):
                    pass  # Skip holiday
                else:
                    added += 1
        
        return current
    
    @staticmethod
    def format_date(
        date_obj: Union[datetime, date, str],
        format_str: str = "%Y-%m-%d %H:%M:%S%z"
    ) -> str:
        """Format a date for output."""
        if isinstance(date_obj, str):
            return date_obj
        if isinstance(date_obj, datetime):
            return date_obj.strftime(format_str)
        if isinstance(date_obj, date):
            return date_obj.strftime("%Y-%m-%d")
        return ""
    
    @staticmethod
    def ensure_timezone(
        dt: datetime,
        tz_name: str = "UTC"
    ) -> datetime:
        """Ensure a datetime has timezone info."""
        if dt.tzinfo is None:
            tz = pytz.timezone(tz_name)
            return tz.localize(dt)
        return dt
    
    @staticmethod
    def random_timestamp_in_range(
        start_date: datetime,
        end_date: datetime,
        business_hours_only: bool = False
    ) -> datetime:
        """Generate a random timestamp within a range."""
        if business_hours_only:
            # Generate during business hours (9 AM - 5 PM)
            dt = DateUtils.random_date(start_date, end_date)
            dt = dt.replace(hour=random.randint(9, 16), minute=random.randint(0, 59))
            
            # Ensure it's a business day
            while not DateUtils.is_business_day(dt):
                dt -= timedelta(days=1)
                dt = dt.replace(hour=random.randint(9, 16), minute=random.randint(0, 59))
            
            return dt
        
        return DateUtils.random_date(start_date, end_date)