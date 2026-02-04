#!/usr/bin/env python3
"""
Generate synthetic baby sleep/feed/meds data in Huckleberry CSV format.

This creates realistic but completely synthetic data for demonstration purposes.
Sleep patterns mimic newborn-to-toddler progression over the specified duration.
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_sleep_patterns(start_date: datetime, num_days: int, seed: int = 42) -> list[dict]:
    """
    Generate realistic baby sleep patterns that evolve over time.
    
    Newborns (0-3 months): Many short naps, frequent night wakings
    Infants (3-6 months): Consolidating to 3-4 naps, longer night stretches
    Older infants (6-12 months): 2-3 naps, mostly sleeping through night
    Toddlers (12+ months): 1-2 naps, consistent night sleep
    """
    random.seed(seed)
    records = []
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        age_months = day_offset / 30  # Approximate age in months
        
        # Determine sleep pattern based on age
        if age_months < 3:
            # Newborn: 4-6 naps, short night stretches
            num_naps = random.randint(4, 6)
            night_wakings = random.randint(2, 4)
            nap_duration_range = (30, 120)  # 30min to 2hrs
            night_stretch_range = (90, 180)  # 1.5 to 3 hours
        elif age_months < 6:
            # 3-6 months: 3-4 naps, longer night stretches
            num_naps = random.randint(3, 4)
            night_wakings = random.randint(1, 3)
            nap_duration_range = (45, 150)
            night_stretch_range = (180, 300)
        elif age_months < 12:
            # 6-12 months: 2-3 naps, mostly through the night
            num_naps = random.randint(2, 3)
            night_wakings = random.randint(0, 2)
            nap_duration_range = (60, 180)
            night_stretch_range = (300, 480)
        else:
            # 12+ months: 1-2 naps, sleeping through
            num_naps = random.randint(1, 2)
            night_wakings = random.randint(0, 1)
            nap_duration_range = (60, 150)
            night_stretch_range = (480, 660)
        
        # Generate daytime naps
        nap_starts = sorted([
            random.randint(8, 17) * 60 + random.randint(0, 59)  # Minutes from midnight
            for _ in range(num_naps)
        ])
        
        for nap_start_minutes in nap_starts:
            nap_duration = random.randint(*nap_duration_range)
            start_time = current_date.replace(hour=0, minute=0, second=0) + timedelta(minutes=nap_start_minutes)
            end_time = start_time + timedelta(minutes=nap_duration)
            
            duration_str = f"{nap_duration // 60}:{nap_duration % 60:02d}"
            records.append({
                'Type': 'sleep',
                'Start': start_time.strftime('%Y-%m-%d %H:%M'),
                'End': end_time.strftime('%Y-%m-%d %H:%M'),
                'Duration': duration_str,
                'Start Conditions': '',
                'Start Location': '',
                'End Conditions': '',
                'Notes': ''
            })
        
        # Generate night sleep (evening of this day into next morning)
        bedtime_hour = random.randint(18, 20)
        bedtime_minute = random.randint(0, 59)
        bedtime = current_date.replace(hour=bedtime_hour, minute=bedtime_minute, second=0)
        
        wake_hour = random.randint(6, 8)
        wake_minute = random.randint(0, 59)
        final_wake = (current_date + timedelta(days=1)).replace(hour=wake_hour, minute=wake_minute, second=0)
        
        # Generate night sleep segments based on wakings
        current_sleep_start = bedtime
        for i in range(night_wakings + 1):
            if i < night_wakings:
                # Calculate wake time
                remaining_night = (final_wake - current_sleep_start).total_seconds() / 60
                stretch_duration = min(
                    random.randint(*night_stretch_range),
                    int(remaining_night * 0.8)  # Don't use more than 80% of remaining time
                )
                sleep_end = current_sleep_start + timedelta(minutes=stretch_duration)
                
                # Brief wake period (10-30 min)
                wake_duration = random.randint(10, 30)
                next_sleep_start = sleep_end + timedelta(minutes=wake_duration)
            else:
                # Final stretch to morning
                sleep_end = final_wake
            
            duration_minutes = int((sleep_end - current_sleep_start).total_seconds() / 60)
            if duration_minutes > 0:
                duration_str = f"{duration_minutes // 60}:{duration_minutes % 60:02d}"
                records.append({
                    'Type': 'sleep',
                    'Start': current_sleep_start.strftime('%Y-%m-%d %H:%M'),
                    'End': sleep_end.strftime('%Y-%m-%d %H:%M'),
                    'Duration': duration_str,
                    'Start Conditions': '',
                    'Start Location': '',
                    'End Conditions': '',
                    'Notes': ''
                })
            
            if i < night_wakings:
                current_sleep_start = next_sleep_start
    
    return records


def generate_feed_patterns(start_date: datetime, num_days: int, seed: int = 42) -> list[dict]:
    """Generate feeding events that decrease in frequency as baby ages."""
    random.seed(seed + 1)  # Different seed from sleep
    records = []
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        age_months = day_offset / 30
        
        # Feeding frequency decreases with age
        if age_months < 3:
            num_feeds = random.randint(8, 12)
        elif age_months < 6:
            num_feeds = random.randint(6, 8)
        elif age_months < 12:
            num_feeds = random.randint(5, 7)
        else:
            num_feeds = random.randint(4, 6)
        
        # Distribute feeds throughout the day
        feed_times = sorted([
            random.randint(0, 23) * 60 + random.randint(0, 59)
            for _ in range(num_feeds)
        ])
        
        feed_types = ['Breast', 'Formula', 'Bottle']
        amounts = ['2oz', '3oz', '4oz', '5oz', '6oz', '8oz']
        
        for feed_minutes in feed_times:
            feed_time = current_date.replace(hour=0, minute=0, second=0) + timedelta(minutes=feed_minutes)
            
            # Older babies get more formula/solids
            if age_months > 6:
                feed_type = random.choice(['Formula', 'Bottle', 'Solids'])
            else:
                feed_type = random.choice(feed_types)
            
            amount = random.choice(amounts) if feed_type != 'Breast' else ''
            
            records.append({
                'Type': 'feed',
                'Start': feed_time.strftime('%Y-%m-%d %H:%M'),
                'End': '',
                'Duration': '',
                'Start Conditions': feed_type,
                'Start Location': 'bottle' if feed_type in ['Formula', 'Bottle'] else '',
                'End Conditions': amount,
                'Notes': ''
            })
    
    return records


def generate_meds_patterns(start_date: datetime, num_days: int, seed: int = 42) -> list[dict]:
    """Generate occasional medication events."""
    random.seed(seed + 2)
    records = []
    
    med_types = ['Tylenol', 'Vitamin D', 'Gas Relief Drops', 'Gripe Water', 'Probiotics']
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Daily vitamins
        if random.random() < 0.9:  # 90% chance of vitamin D
            vitamin_time = current_date.replace(hour=random.randint(8, 10), minute=random.randint(0, 59))
            records.append({
                'Type': 'meds',
                'Start': vitamin_time.strftime('%Y-%m-%d %H:%M'),
                'End': vitamin_time.strftime('%Y-%m-%d %H:%M'),
                'Duration': '',
                'Start Conditions': '1ml',
                'Start Location': 'Vitamin D',
                'End Conditions': '',
                'Notes': ''
            })
        
        # Occasional other meds (5% chance per day for each)
        for med in ['Tylenol', 'Gas Relief Drops', 'Gripe Water']:
            if random.random() < 0.05:
                med_time = current_date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
                dosage = '5ml' if med == 'Tylenol' else '2.5ml'
                records.append({
                    'Type': 'meds',
                    'Start': med_time.strftime('%Y-%m-%d %H:%M'),
                    'End': med_time.strftime('%Y-%m-%d %H:%M'),
                    'Duration': '',
                    'Start Conditions': dosage,
                    'Start Location': med,
                    'End Conditions': '',
                    'Notes': ''
                })
    
    return records


def write_csv(records: list[dict], output_path: Path) -> None:
    """Write records to CSV in Huckleberry format."""
    headers = ['Type', 'Start', 'End', 'Duration', 'Start Conditions', 'Start Location', 'End Conditions', 'Notes']
    
    # Sort by start time descending (newest first, like Huckleberry export)
    records.sort(key=lambda r: r['Start'], reverse=True)
    
    with open(output_path, 'w') as f:
        f.write(','.join(headers) + '\n')
        for record in records:
            row = [f'"{record.get(h, "")}"' if ',' in str(record.get(h, '')) else str(record.get(h, '')) 
                   for h in headers]
            f.write(','.join(row) + '\n')
    
    print(f"Generated {len(records)} records -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic baby sleep/feed/meds data in Huckleberry format'
    )
    parser.add_argument(
        '--days', type=int, default=90,
        help='Number of days of data to generate (default: 90)'
    )
    parser.add_argument(
        '--start-date', type=str, default='2024-01-01',
        help='Start date in YYYY-MM-DD format (default: 2024-01-01)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output', '-o', type=str, default='local/sample_huckleberry.csv',
        help='Output file path (default: local/sample_huckleberry.csv)'
    )
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.days} days of synthetic data starting from {args.start_date}")
    
    # Generate all record types
    records = []
    records.extend(generate_sleep_patterns(start_date, args.days, args.seed))
    records.extend(generate_feed_patterns(start_date, args.days, args.seed))
    records.extend(generate_meds_patterns(start_date, args.days, args.seed))
    
    write_csv(records, output_path)
    
    # Print summary
    sleep_count = sum(1 for r in records if r['Type'] == 'sleep')
    feed_count = sum(1 for r in records if r['Type'] == 'feed')
    meds_count = sum(1 for r in records if r['Type'] == 'meds')
    print(f"  Sleep records: {sleep_count}")
    print(f"  Feed records: {feed_count}")
    print(f"  Meds records: {meds_count}")


if __name__ == '__main__':
    main()
