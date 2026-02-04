"""Tests for visualize module."""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for testing without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from babysleepviz.visualize import get_age_label, hex_to_rgba


class TestHexToRgba:
    """Tests for hex_to_rgba function."""

    def test_basic_colors(self):
        """Basic color conversion works."""
        # Red
        result = hex_to_rgba("#FF0000")
        expected = np.array([1.0, 0.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

        # Green
        result = hex_to_rgba("#00FF00")
        expected = np.array([0.0, 1.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

        # Blue
        result = hex_to_rgba("#0000FF")
        expected = np.array([0.0, 0.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_with_alpha(self):
        """Alpha parameter works."""
        result = hex_to_rgba("#FF0000", alpha=0.5)
        expected = np.array([1.0, 0.0, 0.0, 0.5])
        np.testing.assert_array_almost_equal(result, expected)

    def test_without_hash(self):
        """Works without leading hash."""
        result = hex_to_rgba("FF0000")
        expected = np.array([1.0, 0.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_sleep_color(self):
        """Huckleberry sleep color converts correctly."""
        result = hex_to_rgba("#3DD2E6")
        assert 0.2 < result[0] < 0.3  # R
        assert 0.8 < result[1] < 0.9  # G
        assert 0.9 < result[2] < 1.0  # B
        assert result[3] == 1.0  # A

    def test_feed_color(self):
        """Huckleberry feed color converts correctly."""
        result = hex_to_rgba("#D5622F")
        assert 0.8 < result[0] < 0.9  # R (orange has high red)
        assert 0.3 < result[1] < 0.4  # G
        assert 0.1 < result[2] < 0.2  # B
        assert result[3] == 1.0  # A


class TestGetAgeLabel:
    """Tests for get_age_label function."""

    def test_zero_months(self):
        """Month 0 returns 'Born'."""
        assert get_age_label(0) == "Born"

    def test_single_month(self):
        """Single month displays correctly."""
        assert get_age_label(1) == "1 mo"
        assert get_age_label(6) == "6 mo"
        assert get_age_label(11) == "11 mo"

    def test_one_year(self):
        """12 months displays as 1 year."""
        assert get_age_label(12) == "1 yr"

    def test_year_and_months(self):
        """Combined years and months display correctly."""
        assert get_age_label(13) == "1 yr 1 mo"
        assert get_age_label(14) == "1 yr 2 mo"
        assert get_age_label(18) == "1 yr 6 mo"
        assert get_age_label(23) == "1 yr 11 mo"

    def test_two_years(self):
        """24 months displays as 2 years."""
        assert get_age_label(24) == "2 yr"

    def test_two_years_and_months(self):
        """Two years plus months display correctly."""
        assert get_age_label(25) == "2 yr 1 mo"
        assert get_age_label(30) == "2 yr 6 mo"


class TestVisualizationIntegration:
    """Integration tests for visualization."""

    @pytest.fixture
    def sample_buckets_path(self):
        """Path to sample bucketed data."""
        return Path(__file__).parent.parent / "local" / "sample_buckets.csv"

    def test_bucketed_data_has_required_columns(self, sample_buckets_path):
        """Bucketed data should have required columns for visualization."""
        import pandas as pd

        if not sample_buckets_path.exists():
            pytest.skip("Sample bucketed data not available")

        df = pd.read_csv(sample_buckets_path)
        required_columns = ["day", "minute_of_day", "asleep", "feed"]
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_bucketed_data_has_valid_values(self, sample_buckets_path):
        """Bucketed data should have valid binary values."""
        import pandas as pd

        if not sample_buckets_path.exists():
            pytest.skip("Sample bucketed data not available")

        df = pd.read_csv(sample_buckets_path)

        # asleep and feed should be 0 or 1
        assert df["asleep"].isin([0, 1]).all(), "asleep column should be binary"
        assert df["feed"].isin([0, 1]).all(), "feed column should be binary"

        # minute_of_day should be 0-1435 in 5-minute increments
        assert df["minute_of_day"].min() >= 0
        assert df["minute_of_day"].max() <= 1435
        assert (df["minute_of_day"] % 5 == 0).all(), "minute_of_day should be in 5-min increments"
