"""
Command-line interface for BabySleepViz.

Provides CLI entrypoints for parsing and visualizing baby tracking data.

Commands:
    babysleepviz          Main workflow: CSV → PNG (parse + render in one step)
    babysleepviz-parse    Advanced: just parse CSV to bucketed data
    babysleepviz-render   Advanced: just render bucketed data to PNG
"""

import argparse
import tempfile
from datetime import datetime
from pathlib import Path

from .parse_data import load_config, parse_data
from .visualize import load_config as load_viz_config, create_visualization


def parse_cli():
    """Parse baby tracking CSV exports into time-bucketed data."""
    parser = argparse.ArgumentParser(
        description='Parse baby tracking CSV exports into time-bucketed data for visualization'
    )
    parser.add_argument(
        'input', type=str, nargs='?', default='local/export.csv',
        help='Input CSV file path (default: local/export.csv)'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='local/buckets.csv',
        help='Output CSV file path (default: local/buckets.csv)'
    )
    parser.add_argument(
        '-c', '--config', type=str, default='configs/huckleberry.yaml',
        help='Configuration file path (default: configs/huckleberry.yaml)'
    )
    parser.add_argument(
        '--day-start-hour', type=int, default=7,
        help='Hour that starts each "day" (default: 7, meaning 7:00 AM)'
    )
    parser.add_argument(
        '--bucket-minutes', type=int, default=5,
        help='Size of time buckets in minutes (default: 5)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    config_path = Path(args.config)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Put your export in local/ or use sample data: babysleepviz-parse local/sample_huckleberry.csv")
        return 1
    
    if config_path.exists():
        config = load_config(config_path)
        print(f"Loaded config: {config.get('name', 'unknown')}")
    else:
        print(f"Warning: Config not found at {config_path}, using defaults")
        config = {}
    
    parse_data(
        input_path=input_path,
        output_path=output_path,
        config=config,
        day_start_hour=args.day_start_hour,
        bucket_minutes=args.bucket_minutes
    )
    
    return 0


def render_cli():
    """Generate heatmap visualization from bucketed data."""
    parser = argparse.ArgumentParser(
        description='Render heatmap visualization from bucketed baby tracking data'
    )
    parser.add_argument(
        'input', type=str, nargs='?', default='local/buckets.csv',
        help='Input bucketed CSV file path (default: local/buckets.csv)'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='local/heatmap.png',
        help='Output PNG file path (default: local/heatmap.png)'
    )
    parser.add_argument(
        '-c', '--config', type=str, default='configs/huckleberry.yaml',
        help='Configuration file path (default: configs/huckleberry.yaml)'
    )
    parser.add_argument(
        '--day-zero', type=str, required=True,
        help='Start date for day 0 in YYYY-MM-DD format (e.g., 2024-01-01)'
    )
    parser.add_argument(
        '--birthday-day', type=int, default=1,
        help='Day of month for birthday (for month boundary alignment, default: 1)'
    )
    parser.add_argument(
        '--max-months', type=int, default=24,
        help='Maximum number of months to display (default: 24)'
    )
    parser.add_argument(
        '--day-start-hour', type=int, default=7,
        help='Hour that starts each "day" (default: 7, meaning 7:00 AM)'
    )
    parser.add_argument(
        '--bucket-minutes', type=int, default=5,
        help='Size of time buckets in minutes (default: 5)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    config_path = Path(args.config)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("First run: babysleepviz-parse <your_data.csv>")
        return 1
    
    if config_path.exists():
        config = load_viz_config(config_path)
        print(f"Loaded config: {config.get('name', 'unknown')}")
    else:
        print(f"Warning: Config not found at {config_path}, using defaults")
        config = {}
    
    day_zero = datetime.strptime(args.day_zero, '%Y-%m-%d').replace(hour=args.day_start_hour)
    
    create_visualization(
        input_path=input_path,
        output_path=output_path,
        config=config,
        day_zero=day_zero,
        birthday_day=args.birthday_day,
        max_months=args.max_months,
        day_start_hour=args.day_start_hour,
        bucket_minutes=args.bucket_minutes
    )
    
    return 0


def main_cli():
    """
    Main BabySleepViz workflow: parse CSV and generate visualization in one step.
    
    This is the recommended command for most users.
    """
    parser = argparse.ArgumentParser(
        description='Generate baby sleep visualization from tracking app CSV export',
        epilog='Example: babysleepviz data.csv --day-zero 2024-01-15 -o sleep_patterns.png'
    )
    parser.add_argument(
        'input', type=str,
        help='Input CSV file from baby tracking app (e.g., Huckleberry export)'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='local/heatmap.png',
        help='Output PNG file path (default: local/heatmap.png)'
    )
    parser.add_argument(
        '-c', '--config', type=str, default='configs/huckleberry.yaml',
        help='Configuration file path (default: configs/huckleberry.yaml)'
    )
    parser.add_argument(
        '--day-zero', type=str, required=True,
        help='Start date for visualization in YYYY-MM-DD format (usually baby\'s birthday)'
    )
    parser.add_argument(
        '--birthday-day', type=int, default=1,
        help='Day of month for birthday (for month boundary alignment, default: 1)'
    )
    parser.add_argument(
        '--max-months', type=int, default=24,
        help='Maximum number of months to display (default: 24)'
    )
    parser.add_argument(
        '--day-start-hour', type=int, default=7,
        help='Hour that starts each "day" (default: 7, meaning 7:00 AM)'
    )
    parser.add_argument(
        '--bucket-minutes', type=int, default=5,
        help='Size of time buckets in minutes (default: 5)'
    )
    parser.add_argument(
        '--save-buckets', type=str, default=None,
        help='Optional: save intermediate bucketed data to this CSV path'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    config_path = Path(args.config)
    
    # Validate input
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("\nTo get started:")
        print("  1. Export data from your baby tracking app (e.g., Huckleberry)")
        print("  2. Save the CSV file to your local/ folder")
        print("  3. Run: babysleepviz local/your_export.csv --day-zero YYYY-MM-DD")
        return 1
    
    # Load config
    if config_path.exists():
        config = load_config(config_path)
        print(f"Loaded config: {config.get('name', 'unknown')}")
    else:
        print(f"Warning: Config not found at {config_path}, using defaults")
        config = {}
    
    # Determine where to save bucketed data
    if args.save_buckets:
        buckets_path = Path(args.save_buckets)
        cleanup_buckets = False
    else:
        # Use a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        buckets_path = Path(temp_file.name)
        temp_file.close()
        cleanup_buckets = True
    
    try:
        # Step 1: Parse CSV to buckets
        print("=" * 60)
        print("Step 1: Parsing tracking data...")
        print("=" * 60)
        parse_data(
            input_path=input_path,
            output_path=buckets_path,
            config=config,
            day_start_hour=args.day_start_hour,
            bucket_minutes=args.bucket_minutes
        )
        
        # Step 2: Generate visualization
        print()
        print("=" * 60)
        print("Step 2: Generating visualization...")
        print("=" * 60)
        
        day_zero = datetime.strptime(args.day_zero, '%Y-%m-%d').replace(hour=args.day_start_hour)
        
        # Reload config for visualization (may have different settings)
        if config_path.exists():
            viz_config = load_viz_config(config_path)
        else:
            viz_config = {}
        
        create_visualization(
            input_path=buckets_path,
            output_path=output_path,
            config=viz_config,
            day_zero=day_zero,
            birthday_day=args.birthday_day,
            max_months=args.max_months,
            day_start_hour=args.day_start_hour,
            bucket_minutes=args.bucket_minutes
        )
        
        print()
        print("=" * 60)
        print(f"Done! Visualization saved to: {output_path}")
        if args.save_buckets:
            print(f"Bucketed data saved to: {buckets_path}")
        print("=" * 60)
        
    finally:
        # Clean up temporary file if we created one
        if cleanup_buckets and buckets_path.exists():
            buckets_path.unlink()
    
    return 0


def help_cli():
    """Show help information about available commands."""
    print("BabySleepViz - Baby Sleep Tracking Data Visualization")
    print()
    print("Transform baby tracking app exports into beautiful heatmap visualizations")
    print("showing sleep patterns, feeding schedules, and medication timing.")
    print()
    print("Commands:")
    print()
    print("  babysleepviz            Main command: CSV → PNG in one step (recommended)")
    print("                          Example: babysleepviz data.csv --day-zero 2024-01-15 -o output.png")
    print()
    print("  babysleepviz-parse      Advanced: parse CSV to intermediate bucketed format")
    print("                          Example: babysleepviz-parse data.csv -o buckets.csv")
    print()
    print("  babysleepviz-render     Advanced: render bucketed data to PNG")
    print("                          Example: babysleepviz-render buckets.csv --day-zero 2024-01-15")
    print()
    print("For help on each command, use --help (e.g., babysleepviz --help)")
    return 0


if __name__ == '__main__':
    exit(help_cli())
