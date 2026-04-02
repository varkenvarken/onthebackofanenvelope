import sqlite3
import sys
import math
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
        
        for timestamp, rain_sum in rows:
            dt = datetime.fromtimestamp(timestamp)
            if 4 <= dt.month <= 9: # April to September
                if rain_sum > 0:
                    gap_lengths.append(current_gap)
                    current_gap = 0
                else:
                    current_gap += 1
        
        if not gap_lengths:
            return None

        # Calculate the mean gap length (average dry spell)
        avg_gap = sum(gap_lengths) / len(gap_lengths)
        
        # The probability of 'success' (rain) on any day
        p = 1 / (avg_gap + 1)
        return p

    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_random_dry_spell(p):
    """
    Returns a random number of dry days (k) based on the 
    Geometric distribution parameter p.
    """
    if p >= 1.0: return 0
    if p <= 0.0: return float('inf')
    
    # We use the Inverse CDF method for a Geometric distribution
    # U is a uniform random variable [0, 1)
    u = random.random()
    
    # Formula for discrete geometric sampling:
    # k = floor(log(1-u) / log(1-p))
    return math.floor(math.log(1 - u) / math.log(1 - p))

# --- Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <database_file>")
    else:
        prob_rain = fit_geometric_distribution(sys.argv[1])
        
        if prob_rain:
            print(f"Fitted Daily Rain Probability (p): {prob_rain:.4f}")
            print("-" * 30)
            print("Simulating 10 random dry spell lengths:")
            
            for i in range(10):
                days = generate_random_dry_spell(prob_rain)
                print(f"Simulation {i+1}: {days} dry days")