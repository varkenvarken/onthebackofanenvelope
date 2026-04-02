# rain_simulator.py (c) 2026 Michel Anders
# Attribution-NonCommercial-NoDerivatives 4.0 Internationa

from pathlib import Path
import sqlite3
import sys
import math
import random
from datetime import datetime


def get_weather_parameters(db_path):
    """Extracts both p (rain probability) and beta (rain intensity) from DB."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT dateTime, sum FROM archive_day_rain ORDER BY dateTime ASC")
        rows = cursor.fetchall()
        conn.close()

        gap_lengths = []
        rain_amounts = []
        current_gap = 0

        for timestamp, rain_sum in rows:
            dt = datetime.fromtimestamp(timestamp)
            if 4 <= dt.month <= 9:
                if rain_sum > 0:
                    gap_lengths.append(current_gap)
                    # convert from inches to mm
                    rain_amounts.append(rain_sum * 25.4)
                    current_gap = 0
                else:
                    current_gap += 1

        if not gap_lengths or not rain_amounts:
            return None, None

        # p = probability of rain occurring on any given day
        p = 1 / ((sum(gap_lengths) / len(gap_lengths)) + 1)
        # beta = average amount of rain on a wet day
        beta = sum(rain_amounts) / len(rain_amounts)

        return p, beta
    except Exception as e:
        print(f"Error: {e}")
        return None, None


def simulate_month(p, beta, days=30):
    """Generates a synthetic month of rainfall data."""
    print(f"{'Day':<5} | {'Status':<10} | {'Rain (mm)':<10}")
    print("-" * 30)

    total_rain = 0
    rainy_days = 0

    for day in range(1, days + 1):
        # Determine IF it rains using the Geometric/Bernoulli logic
        if random.random() < p:
            # Determine HOW MUCH it rains using Exponential logic
            amount = -beta * math.log(1 - random.random())
            status = "RAIN 🌧️"
            total_rain += amount
            rainy_days += 1
        else:
            amount = 0.0
            status = "Dry ☀️"

        print(f"{day:<5} | {status:<10} | {amount:>8.2f} mm")

    print("-" * 30)
    print(f"Total Monthly Rainfall: {total_rain:.2f} mm")
    print(f"Number of Rainy Days:   {rainy_days}")


STORAGE_CAPACITY = 2000  # volume of our two IBC containers
IRRIGATION_AREA = 100  # combined size of borders we will be watering
CAPTURE_AREA = 40  # effective roof area
MAX_DEFICIT = 5  # water deficit at which we start to irrigate
DOSE = 5  # home much we water the border if we do decide to water

def evaporation(day):
    """
    This is a crude approximation based on the average daily evapotranspiration as recorded in Volkel, the Netherlands, between 2018 and 2025.

    Day should be between 1 - 180 
    """
    month = ( day - 1 )// 30

    return [2.33, 3.17, 3.76, 3.45, 3.04, 2.07][month]
    # if day <= 120:
    #     return 1 + day/30  # 1 - 5
    # return 5 - (day - 120)/30


def simulate_season(p, beta, days=180, do_print=True):
    """Generates a synthetic growth season (April - September) of rainfall data.
    
    p: float    probability of rain occurring on any given day
    beta: float average amount of rain on a wet day
    """

    if do_print:
        print(
            f"{'Day':<5} | {'Status':<10} | {'Rain (mm)':<10} | Deficit | Irrigation | Storage")
        print("-" * 30)

    total_rain = 0
    rainy_days = 0

    deficit = 0
    irrigation = 0

    storage_limit = STORAGE_CAPACITY
    storage = storage_limit  # initial storage is full

    water_saved = 0
    wasted = 0

    days_watered = 0

    for day in range(1, days + 1):
        # Determine IF it rains using the Geometric/Bernoulli logic
        if random.random() < p:
            # Determine HOW MUCH it rains using Exponential logic
            amount = -beta * math.log(1 - random.random())
            status = "RAIN 🌧️"
            total_rain += amount
            rainy_days += 1

            # amount is in mm
            potential_storage = storage + CAPTURE_AREA * amount
            storage = min(storage_limit, potential_storage)
            wasted += potential_storage - storage  # overflow
        else:
            amount = 0.0
            status = "Dry ☀️"

        # deficit is in mm
        deficit = deficit + evaporation(day) - amount

        if deficit > MAX_DEFICIT:
            # what can we get from storage?
            water_needed = DOSE * IRRIGATION_AREA
            water_from_storage = min(water_needed, storage)
            # we always water what we need (rest comes from tap water)
            deficit -= DOSE
            irrigation += water_needed  # we keep a running total of the amount of water used
            storage -= water_from_storage
            water_saved += water_from_storage
            days_watered += 1
        if do_print:
            print(
                f"{day:<5} | {status:<10} | {amount:>8.2f} mm | {deficit:>8.2f} | {irrigation:>8.2f} | {storage:>8.2f}")

    if do_print:
        print("-" * 30)
        print(f"Total Seasonal Rainfall: {total_rain:.2f} mm")
        print(f"Number of Rainy Days:   {rainy_days} / 180")
        print(
            f"Volume irrigated:   {irrigation / 1000:.1f} m³ ")
        print(
            f"Volume saved:   {water_saved / 1000:.1f} m³ ")

    return total_rain, rainy_days, irrigation / 1000, water_saved / 1000, wasted / 1000, days_watered


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <database_file>")
    else:
        p, beta = get_weather_parameters(sys.argv[1])

        print(f"{p=:.1%} {beta=:.2f}mm")

        # create a folder for images if it doesn´t exist yet
        images = Path("images")
        images.mkdir(exist_ok=True)

        import numpy as np
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D

        # 1. Define the ranges
        irrigation_range = np.arange(25, 201, 25)
        storage_range = np.arange(250, 4001, 250)
        area_range = np.arange(10, 81, 10)

        # 2. Create grids for the X and Y coordinates
        X, Y = np.meshgrid(storage_range, area_range)

        # 3. Loop over different sizes of irrigation area
        for a, IRRIGATION_AREA in enumerate(irrigation_range):

            # 4. Initialize empty grids for the Z-axis values (Results)
            Z_saved = np.zeros(X.shape)
            Z_wasted = np.zeros(X.shape)

            # 5. Run the simulation
            # We use enumerate to map the loop values back to grid indices
            for i, CAPTURE_AREA in enumerate(area_range):
                for j, STORAGE_CAPACITY in enumerate(storage_range):
                    water_saved_total = 0
                    wasted_total = 0
                    n = 1000

                    for _ in range(n):
                        t, r, ir, w, ww, dw = simulate_season(
                            p, beta, do_print=False)
                        water_saved_total += w
                        wasted_total += ww

                    # Assign the averages to the result grids
                    Z_saved[i, j] = water_saved_total / n
                    Z_wasted[i, j] = wasted_total / n

            # 6. Plotting
            fig1 = plt.figure(figsize=(10, 7))
            ax1 = fig1.add_subplot(111, projection='3d')
            surf1 = ax1.plot_surface(X, Y, Z_saved, cmap='viridis')
            ax1.set_title(
                f'Average Water Saved (Irrigation area {IRRIGATION_AREA}m²)')
            ax1.set_xlabel('Storage Capacity')
            ax1.set_ylabel('Capture Area')
            ax1.set_zlabel('Volume')
            fig1.colorbar(surf1, shrink=0.5, aspect=5)

            fig2 = plt.figure(figsize=(10, 7))
            ax2 = fig2.add_subplot(111, projection='3d')
            surf2 = ax2.plot_surface(X, Y, Z_wasted, cmap='plasma')
            ax2.set_title(
                f'Average Water Wasted (Irrigation area {IRRIGATION_AREA}m²)')
            ax2.set_xlabel('Storage Capacity')
            ax2.set_ylabel('Capture Area')
            ax2.set_zlabel('Volume')
            fig2.colorbar(surf2, shrink=0.5, aspect=5)

            # Plot 3: 2D Line Plot - Saved vs Capacity at Area = 40
            fig3, ax3 = plt.subplots(figsize=(8, 5))

            # Find the index where Capture Area is 40
            area_idx_40 = np.where(area_range == 40)[0][0]
            saved_at_40 = Z_saved[area_idx_40, :]

            ax3.plot(storage_range, saved_at_40, marker='o',
                     linestyle='-', color='tab:blue')
            ax3.set_title(
                f'Water Saved vs Storage Capacity (at Capture Area = 40m² and Irrigation area = {IRRIGATION_AREA}m²)')
            ax3.set_xlabel('Storage Capacity')
            ax3.set_ylabel('Average Water Saved')
            ax3.grid(True, linestyle='--', alpha=0.7)

            # Plot 3: 2D Line Plot - Saved vs Capacity at Area = 80
            fig4, ax4 = plt.subplots(figsize=(8, 5))

            # Find the index where Capture Area is 80
            area_idx_80 = np.where(area_range == 80)[0][0]
            saved_at_80 = Z_saved[area_idx_80, :]

            ax4.plot(storage_range, saved_at_80, marker='o',
                     linestyle='-', color='tab:blue')
            ax4.set_title(
                f'Water Saved vs Storage Capacity (at Capture Area = 80m² and Irrigation area = {IRRIGATION_AREA}m²)')
            ax4.set_xlabel('Storage Capacity')
            ax4.set_ylabel('Average Water Saved')
            ax4.grid(True, linestyle='--', alpha=0.7)

            # plot.show()

            print(
                f"saving results for irrigation area {IRRIGATION_AREA}m²")

            # Save plots to PNG with names reflecting the current irrigation range
            fig1.savefig(images /
                         f'water_saved_irrigation_{IRRIGATION_AREA}m2.png', dpi=150, bbox_inches='tight')
            fig2.savefig(images /
                         f'water_wasted_irrigation_{IRRIGATION_AREA}m2.png', dpi=150, bbox_inches='tight')
            fig3.savefig(images /
                         f'water_saved_vs_capacity_area40_irrigation_{IRRIGATION_AREA}m2.png', dpi=150, bbox_inches='tight')
            fig4.savefig(images /
                         f'water_saved_vs_capacity_area80_irrigation_{IRRIGATION_AREA}m2.png', dpi=150, bbox_inches='tight')

            # Close figures to free memory when looping
            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)
            plt.close(fig4)
