import sqlite3
import sys
import math
import random
from datetime import datetime
from collections import Counter

def get_actual_data(db_path):
    """Fetches real gap data from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT dateTime, sum FROM archive_day_rain ORDER BY dateTime ASC")
    rows = cursor.fetchall()
    conn.close()

    gap_lengths = []
    current_gap = 0
    for timestamp, rain_sum in rows:
        dt = datetime.fromtimestamp(timestamp)
        if 4 <= dt.month <= 9:
            if rain_sum > 0:
                gap_lengths.append(current_gap)
                current_gap = 0
            else:
                current_gap += 1
    return gap_lengths

def generate_random_dry_spell(p):
    """Samples a dry spell length from the Geometric distribution."""
    if p >= 1.0: return 0
    u = random.random()
    # Inverse CDF: k = floor(ln(1-u) / ln(1-p))
    return math.floor(math.log(1 - u) / math.log(1 - p))

def verify_fit(actual_gaps, p, iterations=10000):
    """Compares the database average to a simulated average."""
    simulated_gaps = [generate_random_dry_spell(p) for _ in range(iterations)]
    
    actual_avg = sum(actual_gaps) / len(actual_gaps)
    sim_avg = sum(simulated_gaps) / len(simulated_gaps)
    
    print(f"--- Verification (N={iterations}) ---")
    print(f"Actual Average Dry Spell:    {actual_avg:.2f} days")
    print(f"Simulated Average Dry Spell: {sim_avg:.2f} days")
    print(f"Accuracy:                   {100 - abs(actual_avg - sim_avg)/actual_avg * 100:.2f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <database_file>")
    else:
        path = sys.argv[1]
        real_data = get_actual_data(path)
        
        if real_data:
            # Fit the parameter p
            avg_gap = sum(real_data) / len(real_data)
            p_fit = 1 / (avg_gap + 1)
            
            print(f"Fitted p (Rain Probability): {p_fit:.4f}\n")
            verify_fit(real_data, p_fit)