"""
Generate heatmap visualizations of baby sleep, feeding, and medication data.

This module reads time-bucketed data and creates a layered visualization
showing patterns over time.
"""

from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(config_path: Path) -> dict:
    """Load visualization configuration from YAML file."""
    if not HAS_YAML:
        print("Warning: PyYAML not installed, using default configuration")
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f)


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> np.ndarray:
    """Convert hex color to RGBA numpy array."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return np.array([r, g, b, alpha])


def get_age_label(month_num: int) -> str:
    """Convert month number to age label like 'Born', '1 mo', '1 yr 2 mo', etc."""
    if month_num == 0:
        return "Born"
    years = month_num // 12
    months = month_num % 12
    if years == 0:
        return f"{months} mo"
    elif months == 0:
        return f"{years} yr"
    else:
        return f"{years} yr {months} mo"


# Default medication colors
DEFAULT_MED_COLORS = {
    'Tylenol': '#FF0080',
    'Motrin': '#FF3333',
    'Pepcid': '#CCFF00',
    'Gas Relief Drops': '#9900FF',
    'Gripe Water': '#FFFF66',
    'Vitamin D': '#FFD700',
    'Probiotics': '#FF66B2',
    'Other': '#FFFFFF',
}


def create_visualization(
    input_path: Path,
    output_path: Path,
    config: dict,
    day_zero: datetime,
    birthday_day: int = 8,
    max_months: int = 24,
    day_start_hour: int = 7,
    bucket_minutes: int = 5
) -> None:
    """
    Create heatmap visualization from bucketed data.
    
    Args:
        input_path: Path to bucketed CSV file
        output_path: Path for output PNG file
        config: Visualization configuration dict
        day_zero: The start date for day 0
        birthday_day: Day of month for birthday (for month boundary alignment)
        max_months: Maximum months to display
        day_start_hour: Hour that starts each "day"
        bucket_minutes: Size of time buckets in minutes
    """
    # Load config colors
    viz_config = config.get('visualization', {})
    colors_config = viz_config.get('colors', {})
    med_colors_config = colors_config.get('medications', {})
    
    # Default colors
    SLEEP_COLOR = hex_to_rgba(colors_config.get('sleep', '#3DD2E6'))
    FEED_COLOR = hex_to_rgba(colors_config.get('feed', '#D5622F'))
    BG_COLOR = np.array([0.0, 0.0, 0.0, 0.0])
    SEPARATOR_COLOR = hex_to_rgba(colors_config.get('separator', '#9B59B6'))
    
    MED_TYPES = config.get('medication_types', [
        'Tylenol', 'Pepcid', 'Gas Relief Drops', 'Gripe Water', 
        'Vitamin D', 'Probiotics', 'Motrin', 'Other'
    ])
    if 'Other' not in MED_TYPES:
        MED_TYPES = MED_TYPES + ['Other']
    
    MED_COLORS = {}
    for med_type in MED_TYPES:
        hex_color = med_colors_config.get(med_type, DEFAULT_MED_COLORS.get(med_type, '#FFFFFF'))
        MED_COLORS[med_type] = hex_to_rgba(hex_color)
    
    # Read the data
    df = pd.read_csv(input_path)
    
    # Get dimensions
    num_days = df['day'].nunique()
    minutes_per_day = df['minute_of_day'].nunique()
    
    print(f"Number of days: {num_days}")
    print(f"Expected rows per day (buckets): {minutes_per_day}")
    
    # Pivot to get matrices
    asleep_matrix = df.pivot(index='minute_of_day', columns='day', values='asleep').values
    feed_matrix = df.pivot(index='minute_of_day', columns='day', values='feed').values
    
    # Individual medication matrices
    med_matrices = {}
    for med_type in MED_TYPES:
        col_name = f'med_{med_type}'
        if col_name in df.columns:
            med_matrices[med_type] = df.pivot(index='minute_of_day', columns='day', values=col_name).values
        else:
            med_matrices[med_type] = np.zeros((minutes_per_day, num_days))
    
    # Calculate month boundaries based on birthday
    # Skip day 0 since we already have "Born" label there
    month_boundaries = []
    current_boundary = None
    for day_idx in range(num_days):
        day_date = day_zero + timedelta(days=day_idx)
        if day_date.day == birthday_day:
            month_key = (day_date.year, day_date.month)
            if current_boundary != month_key:
                if day_idx > 0:  # Skip day 0 - "Born" is already there
                    month_boundaries.append(day_idx)
                current_boundary = month_key
    
    print(f"Number of month boundaries (birthday-aligned): {len(month_boundaries)}")
    
    # Limit to max months
    if len(month_boundaries) > max_months:
        max_day = month_boundaries[max_months] if max_months < len(month_boundaries) else num_days
        month_boundaries = month_boundaries[:max_months]
    else:
        max_day = num_days
    
    num_days = min(num_days, max_day)
    asleep_matrix = asleep_matrix[:, :num_days]
    feed_matrix = feed_matrix[:, :num_days]
    for med_type in MED_TYPES:
        med_matrices[med_type] = med_matrices[med_type][:, :num_days]
    
    print(f"Limited to {max_months} months ({num_days} days)")
    
    # Layout settings
    num_separators = len(month_boundaries)
    day_width = 6
    day_padding = 2
    separator_padding = 4
    separator_line_width = 2
    separator_width = separator_padding + separator_line_width + separator_padding
    
    total_cols = (num_days * day_width) + ((num_days - 1) * day_padding) + (num_separators * (separator_width - day_padding))
    rows = minutes_per_day
    
    print(f"Total columns (with separators): {total_cols}")
    
    # Initialize image
    image = np.zeros((rows, total_cols, 4), dtype=np.float32)
    image[:, :] = BG_COLOR
    
    def get_col_offset(day_idx):
        """Get the starting column for a given day."""
        separators_before = sum(1 for b in month_boundaries if b <= day_idx)
        base_col = day_idx * (day_width + day_padding)
        extra_from_separators = separators_before * (separator_width - day_padding)
        return base_col + extra_from_separators
    
    # Time markers (relative to day start hour)
    hours_to_9am = (9 - day_start_hour) % 24
    hours_to_5pm = (17 - day_start_hour) % 24
    hours_to_midnight = (24 - day_start_hour) % 24
    
    WORK_HOURS_START_ROW = (hours_to_9am * 60) // bucket_minutes
    WORK_HOURS_END_ROW = (hours_to_5pm * 60) // bucket_minutes
    MIDNIGHT_ROW = (hours_to_midnight * 60) // bucket_minutes
    
    WORK_HOURS_COLOR = hex_to_rgba(colors_config.get('work_hours', '#9B59B6'), 0.15)
    
    # Apply work hours background
    for row in range(WORK_HOURS_START_ROW, WORK_HOURS_END_ROW):
        for col in range(total_cols):
            image[row, col] = WORK_HOURS_COLOR
    
    print(f"Highlighted 9am-5pm (rows {WORK_HOURS_START_ROW} to {WORK_HOURS_END_ROW})")
    
    # Draw separators
    row_start_sep = int(rows * 0.25)
    row_end_sep = int(rows * 0.75)
    
    for boundary_day in month_boundaries:
        day_col = get_col_offset(boundary_day)
        line_col = day_col - separator_width // 2
        if 0 <= line_col < total_cols:
            for row in range(row_start_sep, row_end_sep):
                image[row, line_col] = SEPARATOR_COLOR
                if line_col + 1 < total_cols:
                    image[row, line_col + 1] = SEPARATOR_COLOR
    
    # Fill data lanes
    for day_idx in range(num_days):
        col_offset = get_col_offset(day_idx)
        col_start = col_offset
        col_end = col_offset + day_width
        
        # Layer 1: Sleep
        for row_idx in range(rows):
            if asleep_matrix[row_idx, day_idx] == 1:
                for c in range(col_start, min(col_end, total_cols)):
                    image[row_idx, c] = SLEEP_COLOR
        
        # Layer 2: Feed
        for row_idx in range(rows):
            if feed_matrix[row_idx, day_idx] == 1:
                for c in range(col_start, min(col_end, total_cols)):
                    image[row_idx, c] = FEED_COLOR
        
        # Layer 3: Medications (checkerboard pattern)
        for med_type in MED_TYPES:
            med_matrix = med_matrices[med_type]
            med_color = MED_COLORS[med_type]
            for row_idx in range(rows):
                if med_matrix[row_idx, day_idx] == 1:
                    for c in range(col_start, min(col_end, total_cols)):
                        if (row_idx + c) % 2 == 0:
                            image[row_idx, c] = med_color
    
    # Midnight highlight overlay
    MIDNIGHT_OVERLAY_COLOR = np.array([1.0, 1.0, 1.0, 0.35])
    
    for row in range(MIDNIGHT_ROW - 1, MIDNIGHT_ROW + 2):
        if 0 <= row < rows:
            for col in range(total_cols):
                base = image[row, col]
                alpha = MIDNIGHT_OVERLAY_COLOR[3]
                blended_rgb = base[:3] * (1 - alpha) + MIDNIGHT_OVERLAY_COLOR[:3] * alpha
                image[row, col, :3] = blended_rgb
    
    print(f"Highlighted midnight (row {MIDNIGHT_ROW}) on top of data")
    print(f"Final image shape: {image.shape} (rows, cols, RGBA)")
    
    # Generate section labels
    section_info = [(get_col_offset(0), get_age_label(0))]
    for i, boundary_day in enumerate(month_boundaries):
        separator_col = get_col_offset(boundary_day) - separator_width // 2
        section_info.append((separator_col, get_age_label(i + 1)))
    
    print(f"Generated {len(section_info)} section labels")
    
    # Create figure
    left_margin = 60
    fig_width = (total_cols + left_margin) / 100
    fig_height = (rows + 30) / 100
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
    fig.patch.set_alpha(0)
    ax.set_facecolor('none')
    
    ax.imshow(image, aspect='auto', interpolation='nearest', extent=[left_margin, total_cols + left_margin, rows, 0])
    
    # Month labels
    for label_col, label in section_info:
        ax.text(label_col + left_margin, -8, label, 
                ha='left', va='bottom',
                fontsize=7, color='white', fontweight='bold',
                fontfamily='sans-serif')
    
    # Y-axis labels
    label_x = left_margin - 5
    label_fontsize = 5
    
    ax.text(label_x, 0, f'{day_start_hour} am', ha='right', va='top',
            fontsize=label_fontsize, color='white', fontweight='bold',
            fontfamily='sans-serif')
    
    work_hours_center = (WORK_HOURS_START_ROW + WORK_HOURS_END_ROW) / 2
    ax.text(label_x, work_hours_center, '9 - 5', ha='right', va='center',
            fontsize=label_fontsize, color='#9B59B6', fontweight='bold',
            fontfamily='sans-serif')
    
    ax.text(label_x, MIDNIGHT_ROW, 'midnight', ha='right', va='center',
            fontsize=label_fontsize, color='white', fontweight='bold',
            fontfamily='sans-serif')
    
    ax.text(label_x, rows, f'{day_start_hour} am', ha='right', va='bottom',
            fontsize=label_fontsize, color='white', fontweight='bold',
            fontfamily='sans-serif')
    
    # Legend
    legend_x = left_margin
    legend_fontsize = 5
    legend_row_height = 12
    square_size = 8
    
    legend_items = [
        (colors_config.get('sleep', '#3DD2E6'), 'Sleep'),
        (colors_config.get('feed', '#D5622F'), 'Feeding'),
    ]
    
    # Add medications that have data
    for med_type in MED_TYPES:
        if med_type != 'Other' and med_matrices[med_type].sum() > 0:
            hex_color = med_colors_config.get(med_type, DEFAULT_MED_COLORS.get(med_type, '#FFFFFF'))
            legend_items.append((hex_color, med_type))
    
    legend_start_y = rows + 10
    
    for i, (color, label) in enumerate(legend_items):
        y_pos = legend_start_y + (i * legend_row_height)
        ax.add_patch(plt.Rectangle((legend_x, y_pos - 4), square_size, square_size, 
                                     facecolor=color, edgecolor='none'))
        ax.text(legend_x + square_size + 3, y_pos, label,
                ha='left', va='center',
                fontsize=legend_fontsize, color='white', fontweight='bold',
                fontfamily='sans-serif')
    
    legend_height = len(legend_items) * legend_row_height + 15
    
    ax.set_xlim(0, total_cols + left_margin)
    ax.set_ylim(rows + legend_height, -25)
    
    ax.axis('off')
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.02, transparent=True)
    plt.close()
    
    print(f"\nSaved to: {output_path}")
    print(f"\nMonth boundaries at days: {month_boundaries[:12]}... (showing first 12)")
