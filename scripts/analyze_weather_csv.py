#!/usr/bin/env python3
"""
Analyzes the weather CSV file to compute:
1. Probability of rain on any given day per month (April-September)
2. Average amount of rain for rainy days per month (April-September)
3. Average evapotranspiration per month (April-September)
"""

import csv
from collections import defaultdict


def analyze_weather_csv(csv_path):
    """
    Read weather CSV and compute rain statistics for April through September.

    Returns:
        dict: Monthly statistics with keys as month numbers (4-9)
    """

    # Month names for reference
    month_names = {
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September"
    }

    # Initialize data structures
    month_stats = defaultdict(lambda: {
        "total_days": 0,
        "rainy_days": 0,
        "total_rain": 0.0,  # in mm
        "total_evapotranspiration": 0.0,  # in mm
        "years": set()
    })

    # Read CSV file
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            month_num = int(row['Month number'])

            # Only process April through September
            if month_num not in range(4, 10):
                continue

            # Extract date to get year
            date_str = row['YYYYMMDD']
            year = int(date_str[:4])

            # Track rain data
            rain_flag = int(row['Rain'])  # 1 = rain, 0 = no rain
            rain_amount_0_1mm = int(row['Rain (0.1mm)'])
            rain_amount_mm = rain_amount_0_1mm * 0.1  # Convert to mm

            # Track evapotranspiration
            evapotranspiration_0_1mm = int(row['Evapotranspiration (0.1mm)'])
            evapotranspiration_mm = evapotranspiration_0_1mm * 0.1  # Convert to mm

            # Update stats
            month_stats[month_num]['total_days'] += 1
            month_stats[month_num]['years'].add(year)
            month_stats[month_num]['total_evapotranspiration'] += evapotranspiration_mm

            if rain_flag == 1:
                month_stats[month_num]['rainy_days'] += 1
                month_stats[month_num]['total_rain'] += rain_amount_mm

    # Calculate probabilities and averages
    results = {}
    for month_num in sorted(month_stats.keys()):
        stats = month_stats[month_num]
        total_days = stats['total_days']
        rainy_days = stats['rainy_days']
        total_rain = stats['total_rain']
        total_evapotranspiration = stats['total_evapotranspiration']

        rain_probability = rainy_days / total_days if total_days > 0 else 0
        avg_rain_on_rainy_days = total_rain / rainy_days if rainy_days > 0 else 0
        avg_evapotranspiration = total_evapotranspiration / \
            total_days if total_days > 0 else 0

        results[month_num] = {
            'month_name': month_names[month_num],
            'total_days': total_days,
            'rainy_days': rainy_days,
            'rain_probability': rain_probability,
            'avg_rain_on_rainy_days': avg_rain_on_rainy_days,
            'avg_evapotranspiration': avg_evapotranspiration,
            'years': stats['years']
        }

    return results


def print_results(results):
    """Pretty-print the analysis results."""
    print("\n" + "="*80)
    print("WEATHER ANALYSIS: April - September")
    print("="*80)
    print()

    avg_probability = 0.0
    avg_rain = 0.0
    avg_evapotranspiration = 0.0

    for month_num in sorted(results.keys()):
        r = results[month_num]
        years_str = f"{min(r['years'])}-{max(r['years'])}"

        print(f"{r['month_name'].upper()}")
        print("-" * 40)
        print(f"  Years analyzed: {years_str}")
        print(f"  Total days:     {r['total_days']}")
        print(f"  Rainy days:     {r['rainy_days']}")
        print(f"  Rain probability: {r['rain_probability']:.1%}")
        print(f"  Avg rain (rainy days): {r['avg_rain_on_rainy_days']:.2f} mm")
        print(
            f"  Avg evapotranspiration: {r['avg_evapotranspiration']:.2f} mm")
        print()

        avg_probability += r['rain_probability']
        avg_rain += r['avg_rain_on_rainy_days']
        avg_evapotranspiration += r['avg_evapotranspiration']

    avg_probability /= len(results.keys())
    avg_rain /= len(results.keys())
    avg_evapotranspiration /= len(results.keys())
    print("Growth season (april - September)")
    print("-" * 40)
    print(f"  Rain probability: {avg_probability:.1%}")
    print(f"  Avg rain (rainy days): {avg_rain:.2f} mm")
    print(f"  Avg evapotranspiration: {avg_evapotranspiration:.2f} mm")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_weather_csv.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    results = analyze_weather_csv(csv_file)
    print_results(results)
