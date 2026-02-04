"""
Parse baby tracking CSV exports into time-bucketed data for visualization.

This module converts raw sleep/feed/meds data into 5-minute time buckets,
making it suitable for heatmap visualization.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(config_path: Path) -> dict:
    """Load data source configuration from YAML file."""
    if not HAS_YAML:
        print("Warning: PyYAML not installed, using default configuration")
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_day_boundary(ts: datetime, day_start_hour: int = 7) -> datetime:
    """
    Get the day boundary for a given timestamp.
    
    If before the day start hour, belongs to previous day's boundary.
    Returns the datetime that starts this 'day'.
    
    Args:
        ts: Timestamp to find boundary for
        day_start_hour: Hour that starts each "day" (default: 7, meaning 7:00 AM)
    
    Returns:
        datetime representing the start of the "day" this timestamp belongs to
    """
    if ts.hour < day_start_hour:
        return datetime(ts.year, ts.month, ts.day, day_start_hour) - timedelta(days=1)
    else:
        return datetime(ts.year, ts.month, ts.day, day_start_hour)


def get_minute_of_day(ts: datetime, day_start_hour: int = 7) -> int:
    """
    Get minute of day relative to day boundary.
    
    Args:
        ts: Timestamp to convert
        day_start_hour: Hour that starts each "day"
    
    Returns:
        Minutes since day boundary (0 = day_start_hour:00)
    """
    boundary = get_day_boundary(ts, day_start_hour)
    delta = ts - boundary
    return int(delta.total_seconds() // 60)


def normalize_med_name(name: str, known_meds: list[str]) -> str:
    """Normalize medication names to known types or 'Other'."""
    if pd.isna(name):
        return 'Other'
    name = str(name).strip()
    
    # Handle common variations
    name_lower = name.lower()
    if 'tylenol' in name_lower:
        return 'Tylenol'
    if 'ibuprofen' in name_lower or 'motrin' in name_lower:
        return 'Motrin'
    
    if name in known_meds:
        return name
    return 'Other'


def parse_data(
    input_path: Path,
    output_path: Path,
    config: dict,
    day_start_hour: int = 7,
    bucket_minutes: int = 5
) -> pd.DataFrame:
    """
    Parse baby tracking CSV and convert to time-bucketed format.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path for output CSV file
        config: Data source configuration dict
        day_start_hour: Hour that starts each "day" (default: 7am)
        bucket_minutes: Size of time buckets in minutes (default: 5)
    
    Returns:
        DataFrame with bucketed data
    """
    # Load column mappings from config
    columns = config.get('columns', {})
    type_col = columns.get('type', 'Type')
    start_col = columns.get('start', 'Start')
    end_col = columns.get('end', 'End')
    
    event_types = config.get('event_types', {})
    sleep_type = event_types.get('sleep', 'sleep')
    feed_type = event_types.get('feed', 'feed')
    meds_type = event_types.get('meds', 'meds')
    
    med_name_col = config.get('med_name_column', 'Start Location')
    known_meds = config.get('medication_types', [
        'Tylenol', 'Pepcid', 'Gas Relief Drops', 'Gripe Water', 
        'Vitamin D', 'Probiotics', 'Motrin'
    ])
    
    # Load the CSV
    df = pd.read_csv(input_path)
    
    # --- SLEEP: intervals with Start and End ---
    sleep_df = df[(df[type_col] == sleep_type) & (df[end_col].notna() & (df[end_col] != ''))].copy()
    sleep_df[start_col] = pd.to_datetime(sleep_df[start_col])
    sleep_df[end_col] = pd.to_datetime(sleep_df[end_col])
    sleep_df = sleep_df.dropna(subset=[start_col, end_col])
    print(f"Found {len(sleep_df)} valid sleep records")
    
    # --- MEDS: point-in-time events with medication type ---
    meds_df = df[df[type_col] == meds_type].copy()
    meds_df[start_col] = pd.to_datetime(meds_df[start_col])
    meds_df = meds_df.dropna(subset=[start_col])
    meds_df['med_name'] = meds_df[med_name_col].str.strip().str.replace('"', '')
    meds_df['med_type'] = meds_df['med_name'].apply(lambda x: normalize_med_name(x, known_meds))
    print(f"Found {len(meds_df)} meds records")
    if len(meds_df) > 0:
        print(f"Medication types: {meds_df['med_type'].value_counts().to_dict()}")
    
    # --- FEED: point-in-time events ---
    feed_df = df[df[type_col] == feed_type].copy()
    feed_df[start_col] = pd.to_datetime(feed_df[start_col])
    feed_df = feed_df.dropna(subset=[start_col])
    print(f"Found {len(feed_df)} feed records")
    
    # Find date range
    all_starts = pd.concat([sleep_df[start_col], meds_df[start_col], feed_df[start_col]])
    all_boundaries = all_starts.apply(lambda x: get_day_boundary(x, day_start_hour))
    day_zero = all_boundaries.min()
    print(f"Day 0 starts at: {day_zero}")
    
    all_ends = pd.concat([sleep_df[end_col], meds_df[start_col], feed_df[start_col]])
    latest_end_boundaries = all_ends.apply(lambda x: get_day_boundary(x, day_start_hour))
    last_day_boundary = latest_end_boundaries.max()
    total_days = (last_day_boundary - day_zero).days + 1
    print(f"Total days to cover: {total_days}")
    
    # Create all possible buckets
    all_buckets = []
    for day in range(total_days):
        for minute in range(0, 24 * 60, bucket_minutes):
            bucket = {
                'day': day,
                'minute_of_day': minute,
                'asleep': 0,
                'feed': 0,
            }
            for med_type in known_meds:
                bucket[f'med_{med_type}'] = 0
            bucket['med_Other'] = 0
            all_buckets.append(bucket)
    
    buckets_df = pd.DataFrame(all_buckets)
    print(f"Created {len(buckets_df)} total buckets")
    
    # Create sets to track marked buckets
    asleep_buckets = set()
    feed_buckets = set()
    med_buckets = {med_type: set() for med_type in known_meds + ['Other']}
    
    # Process sleep intervals
    for _, row in sleep_df.iterrows():
        start = row[start_col]
        end = row[end_col]
        
        # Round to bucket boundaries
        start_bucket = start.replace(second=0, microsecond=0)
        start_bucket = start_bucket - timedelta(minutes=start_bucket.minute % bucket_minutes)
        
        end_bucket = end.replace(second=0, microsecond=0)
        if end.second > 0 or end.microsecond > 0 or end.minute % bucket_minutes != 0:
            end_bucket = end_bucket + timedelta(minutes=bucket_minutes - (end_bucket.minute % bucket_minutes))
        
        current = start_bucket
        while current < end:
            boundary = get_day_boundary(current, day_start_hour)
            day_num = (boundary - day_zero).days
            minute_of_day = get_minute_of_day(current, day_start_hour)
            minute_of_day = (minute_of_day // bucket_minutes) * bucket_minutes
            
            if 0 <= day_num < total_days:
                asleep_buckets.add((day_num, minute_of_day))
            
            current += timedelta(minutes=bucket_minutes)
    
    print(f"Marked {len(asleep_buckets)} buckets as asleep")
    
    # Process meds events
    for _, row in meds_df.iterrows():
        ts = row[start_col]
        med_type = row['med_type']
        boundary = get_day_boundary(ts, day_start_hour)
        day_num = (boundary - day_zero).days
        minute_of_day = get_minute_of_day(ts, day_start_hour)
        minute_of_day = (minute_of_day // bucket_minutes) * bucket_minutes
        
        if 0 <= day_num < total_days:
            med_buckets[med_type].add((day_num, minute_of_day))
    
    for med_type in known_meds + ['Other']:
        if len(med_buckets[med_type]) > 0:
            print(f"Marked {len(med_buckets[med_type])} buckets with {med_type}")
    
    # Process feed events
    for _, row in feed_df.iterrows():
        ts = row[start_col]
        boundary = get_day_boundary(ts, day_start_hour)
        day_num = (boundary - day_zero).days
        minute_of_day = get_minute_of_day(ts, day_start_hour)
        minute_of_day = (minute_of_day // bucket_minutes) * bucket_minutes
        
        if 0 <= day_num < total_days:
            feed_buckets.add((day_num, minute_of_day))
    
    print(f"Marked {len(feed_buckets)} buckets with feed")
    
    # Update DataFrame
    buckets_df['asleep'] = buckets_df.apply(
        lambda row: 1 if (row['day'], row['minute_of_day']) in asleep_buckets else 0, axis=1
    )
    buckets_df['feed'] = buckets_df.apply(
        lambda row: 1 if (row['day'], row['minute_of_day']) in feed_buckets else 0, axis=1
    )
    
    for med_type in known_meds + ['Other']:
        col_name = f'med_{med_type}'
        buckets_df[col_name] = buckets_df.apply(
            lambda row, mt=med_type: 1 if (row['day'], row['minute_of_day']) in med_buckets[mt] else 0, axis=1
        )
    
    # Sort and save
    buckets_df = buckets_df.sort_values(['day', 'minute_of_day']).reset_index(drop=True)
    buckets_df.to_csv(output_path, index=False)
    
    print(f"\nSaved to {output_path}")
    print(f"Shape: {buckets_df.shape}")
    
    # Summary stats
    total_asleep = buckets_df['asleep'].sum()
    total_feed = buckets_df['feed'].sum()
    total_buckets = len(buckets_df)
    print(f"\nSummary:")
    print(f"Total buckets: {total_buckets}")
    print(f"Asleep buckets: {total_asleep} ({100 * total_asleep / total_buckets:.2f}%)")
    print(f"Feed buckets: {total_feed}")
    print(f"Average sleep per day: {total_asleep * bucket_minutes / total_days:.1f} minutes ({total_asleep * bucket_minutes / total_days / 60:.1f} hours)")
    print(f"Average feeds per day: {total_feed / total_days:.2f}")
    
    return buckets_df
