"""Tests for parse_data module."""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add src to path for testing without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from babysleepviz.parse_data import get_day_boundary, get_minute_of_day, normalize_med_name


class TestGetDayBoundary:
    """Tests for get_day_boundary function."""
    
    def test_morning_after_boundary(self):
        """Time after day start hour stays on same day."""
        ts = datetime(2024, 1, 15, 9, 30, 0)  # 9:30 AM
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2024, 1, 15, 7, 0, 0)
    
    def test_morning_before_boundary(self):
        """Time before day start hour goes to previous day."""
        ts = datetime(2024, 1, 15, 5, 30, 0)  # 5:30 AM
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2024, 1, 14, 7, 0, 0)
    
    def test_exactly_at_boundary(self):
        """Time exactly at day start hour stays on same day."""
        ts = datetime(2024, 1, 15, 7, 0, 0)  # 7:00 AM
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2024, 1, 15, 7, 0, 0)
    
    def test_midnight(self):
        """Midnight goes to previous day's boundary."""
        ts = datetime(2024, 1, 15, 0, 0, 0)  # midnight
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2024, 1, 14, 7, 0, 0)
    
    def test_late_evening(self):
        """Late evening stays on same day."""
        ts = datetime(2024, 1, 15, 23, 59, 0)  # 11:59 PM
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2024, 1, 15, 7, 0, 0)
    
    def test_custom_day_start(self):
        """Custom day start hour works correctly."""
        ts = datetime(2024, 1, 15, 8, 30, 0)  # 8:30 AM
        result = get_day_boundary(ts, day_start_hour=9)
        # 8:30 AM is before 9 AM, so goes to previous day
        assert result == datetime(2024, 1, 14, 9, 0, 0)
    
    def test_year_boundary(self):
        """Works correctly across year boundary."""
        ts = datetime(2024, 1, 1, 3, 0, 0)  # 3 AM on Jan 1
        result = get_day_boundary(ts, day_start_hour=7)
        assert result == datetime(2023, 12, 31, 7, 0, 0)


class TestGetMinuteOfDay:
    """Tests for get_minute_of_day function."""
    
    def test_at_boundary(self):
        """Time at boundary returns 0."""
        ts = datetime(2024, 1, 15, 7, 0, 0)  # 7:00 AM
        result = get_minute_of_day(ts, day_start_hour=7)
        assert result == 0
    
    def test_one_hour_after(self):
        """One hour after boundary returns 60."""
        ts = datetime(2024, 1, 15, 8, 0, 0)  # 8:00 AM
        result = get_minute_of_day(ts, day_start_hour=7)
        assert result == 60
    
    def test_midnight(self):
        """Midnight is 17 hours (1020 minutes) after 7 AM."""
        ts = datetime(2024, 1, 15, 0, 0, 0)  # midnight
        result = get_minute_of_day(ts, day_start_hour=7)
        assert result == 17 * 60  # 1020
    
    def test_just_before_boundary(self):
        """Just before boundary is end of day (1435 minutes for 5-min buckets)."""
        ts = datetime(2024, 1, 15, 6, 55, 0)  # 6:55 AM
        result = get_minute_of_day(ts, day_start_hour=7)
        # 6:55 AM is 23 hours and 55 minutes after 7 AM (previous day)
        assert result == 23 * 60 + 55  # 1435
    
    def test_with_minutes(self):
        """Partial hours work correctly."""
        ts = datetime(2024, 1, 15, 9, 30, 0)  # 9:30 AM
        result = get_minute_of_day(ts, day_start_hour=7)
        assert result == 2 * 60 + 30  # 150


class TestNormalizeMedName:
    """Tests for normalize_med_name function."""
    
    def test_known_med(self):
        """Known medication names are returned as-is."""
        known_meds = ['Tylenol', 'Motrin', 'Vitamin D']
        assert normalize_med_name('Tylenol', known_meds) == 'Tylenol'
        assert normalize_med_name('Vitamin D', known_meds) == 'Vitamin D'
    
    def test_unknown_med(self):
        """Unknown medications return 'Other'."""
        known_meds = ['Tylenol', 'Motrin']
        assert normalize_med_name('SomethingElse', known_meds) == 'Other'
    
    def test_tylenol_variations(self):
        """Tylenol variations are normalized."""
        known_meds = ['Tylenol', 'Motrin']
        assert normalize_med_name('tylenol', known_meds) == 'Tylenol'
        assert normalize_med_name('Tylenol 5ml', known_meds) == 'Tylenol'
    
    def test_motrin_variations(self):
        """Motrin/ibuprofen variations are normalized."""
        known_meds = ['Tylenol', 'Motrin']
        assert normalize_med_name('motrin', known_meds) == 'Motrin'
        assert normalize_med_name('ibuprofen', known_meds) == 'Motrin'
        assert normalize_med_name('Ibuprofen 100mg', known_meds) == 'Motrin'
    
    def test_none_value(self):
        """None values return 'Other'."""
        known_meds = ['Tylenol', 'Motrin']
        assert normalize_med_name(None, known_meds) == 'Other'
    
    def test_whitespace(self):
        """Whitespace is stripped."""
        known_meds = ['Tylenol', 'Motrin']
        assert normalize_med_name('  Tylenol  ', known_meds) == 'Tylenol'


class TestIntegration:
    """Integration tests using sample data."""
    
    @pytest.fixture
    def sample_data_path(self):
        """Path to sample data file."""
        return Path(__file__).parent.parent / "local" / "sample_huckleberry.csv"
    
    def test_sample_data_exists(self, sample_data_path):
        """Sample data file should exist."""
        assert sample_data_path.exists(), f"Sample data not found at {sample_data_path}"
    
    def test_sample_data_has_required_columns(self, sample_data_path):
        """Sample data should have required columns."""
        import pandas as pd
        
        if not sample_data_path.exists():
            pytest.skip("Sample data not available")
        
        df = pd.read_csv(sample_data_path)
        required_columns = ['Type', 'Start', 'End']
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
    
    def test_sample_data_has_records(self, sample_data_path):
        """Sample data should have sleep, feed, and meds records."""
        import pandas as pd
        
        if not sample_data_path.exists():
            pytest.skip("Sample data not available")
        
        df = pd.read_csv(sample_data_path)
        types = df['Type'].unique()
        
        assert 'sleep' in types, "Sample data should have sleep records"
        assert 'feed' in types, "Sample data should have feed records"
        assert 'meds' in types, "Sample data should have meds records"
