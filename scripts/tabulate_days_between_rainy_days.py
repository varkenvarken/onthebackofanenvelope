import sqlite3
import sys
from datetime import datetime
from collections import Counter
import math
import random

def analyze_rain_gaps(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Select dateTime and rain sum, ordered by time
        # We filter for April (4) through September (9)
        query = """
        SELECT dateTime, sum 
        FROM archive_day_rain 
        ORDER BY dateTime ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No data found in the database.")
            return

        gap_counts = []
        current_gap = 0

        for timestamp, rain_sum in rows:
            # Convert Unix epoch to datetime object
            dt = datetime.fromtimestamp(timestamp)
            
            # Filter for months April (4) through September (9)
            if 4 <= dt.month <= 9:
                if rain_sum > 0:
                    # It rained! Record the gap and reset
                    gap_counts.append(current_gap)
                    current_gap = 0
                else:
                    # Dry day, increment the gap
                    current_gap += 1

        # Tabulate the results
        histogram = Counter(gap_counts)
        
        print(f"{'days':>5} | {'count':>5}")
        print("-" * 15)
        for days in sorted(histogram.keys()):
            print(f"{days:5} | {histogram[days]:5}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_poisson_lambda(db_path):
    """
    Fits a Poisson distribution by calculating the mean (lambda).
    In a Poisson distribution, the MLE for lambda is simply the sample mean.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # We need the total count of days and the count of rainy days
        query = "SELECT sum FROM archive_day_rain"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        rainy_days = 0
        total_days = 0

        for (rain_sum,) in rows:
            total_days += 1
            if rain_sum > 0:
                rainy_days += 1

        # Lambda is the average number of 'rain events' per day
        # In this context, it's (Total Rainy Days / Total Days)
        return rainy_days / total_days

    except Exception as e:
        print(f"Error: {e}")
        return None

def does_it_rain_today(poisson_lambda):
    """
    Returns True or False based on the Poisson probability.
    P(k > 0) = 1 - P(0)
    P(0) = e^(-lambda)
    """
    # Probability of at least one rain event today
    prob_rain = 1 - math.exp(-poisson_lambda)
    
    # Generate a random number between 0 and 1
    return random.random() < prob_rain

import sqlite3
import sys
import random
from datetime import datetime

def fit_geometric_distribution(db_path):
    """
    Fits a Geometric distribution to the 'dry spell' data.
    Returns 'p' (the probability of rain on any given day).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dateTime, sum FROM archive_day_rain ORDER BY dateTime ASC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        gap_lengths = []
        current_gap = 0
        
        days = growth_season_days = 0

        for timestamp, rain_sum in rows:
            days += 1
            dt = datetime.fromtimestamp(timestamp)
            if 4 <= dt.month <= 9: # April to September
                growth_season_days += 1
                if rain_sum > 0:
                    gap_lengths.append(current_gap)
                    current_gap = 0
                else:
                    current_gap += 1
        
        if not gap_lengths:
            return None, days, growth_season_days

        # Calculate the mean gap length (average dry spell)
        avg_gap = sum(gap_lengths) / len(gap_lengths)
        
        # The probability of 'success' (rain) on any day
        p = 1 / (avg_gap + 1)
        return p, days, growth_season_days

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <database_file>")
    else:
        analyze_rain_gaps(sys.argv[1])

    lam = get_poisson_lambda(sys.argv[1])
    if lam is not None:
        print(f"Fitted Poisson Lambda (λ): {lam:.4f}")
        
        # Test the prediction
        result = does_it_rain_today(lam)
        print(f"Does it rain today? {'Yes 🌧️' if result else 'No ☀️'}")


    prob_rain, days, growth_season_days = fit_geometric_distribution(sys.argv[1])
    if prob_rain:
        print(f"Days in dataset: {days} ({growth_season_days} in growth season)")
        print(f"Fitted Daily Rain Probability (p): {prob_rain:.4f}")
        print(f"Average Dry Spell: { (1/prob_rain) - 1:.2f} days")
        
        result = random.random() < prob_rain
        print(f"Prediction for today: {'Rain 🌧️' if result else 'Dry ☀️'}")
