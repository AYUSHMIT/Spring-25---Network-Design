#!/usr/bin/env python3
"""
Author: Joseph Nguyen
Description: This script loads performance_data.csv, sums DataRetrans + ACKRetrans to get
the total number of retransmissions, groups by (Option, LossRate), averages across multiple runs,
and then plots the total retransmissions vs loss rate for each option.

Usage:
    python plot_retransmissions.py
"""

import pandas as pd
import matplotlib.pyplot as plt

def main():
    # Load CSV
    try:
        df = pd.read_csv("performance_data.csv")
    except FileNotFoundError:
        print("Error: performance_data.csv not found.")
        return

    # Expected columns in performance_data.csv:
    #   Option, LossRate, CompletionTime, Throughput, DataRetrans, ACKRetrans, ACKEfficiency
    # If your CSV uses different column names, adjust accordingly.

    # 1. Create a new column for total retransmissions
    df["TotalRetrans"] = df["DataRetrans"] + df["ACKRetrans"]

    # 2. Group by (Option, LossRate) and average (in case there are multiple runs per condition)
    df_avg = df.groupby(["Option", "LossRate"], as_index=False).mean()

    # 3. Sort for nicer plotting
    df_avg.sort_values(by=["Option", "LossRate"], inplace=True)

    # 4. Plot total retransmissions vs loss rate for each option
    options = sorted(df_avg["Option"].unique())
    plt.figure(figsize=(10, 6))
    for opt in options:
        subset = df_avg[df_avg["Option"] == opt]
        plt.plot(
            subset["LossRate"],
            subset["TotalRetrans"],
            marker="o",
            label=f"Option {opt}"
        )

    plt.xlabel("Loss Rate (%)")
    plt.ylabel("Average Total Retransmissions")
    plt.title("Retransmission Overhead vs Loss Rate for Sender-Driven RDT 3.0")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()