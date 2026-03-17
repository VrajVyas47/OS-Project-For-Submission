"""
compare.py – Run every algorithm on the same process set and chart the results.
"""

import json
import matplotlib.pyplot as plt
import numpy as np

from runner import run_scheduler, OUTPUT_JSON

ALGORITHMS = ["FCFS", "SJF", "SRTF", "Priority_NP", "Priority_P", "RR"]


def compare_all(processes: list[dict], quantum: int = 2,
                progress_callback=None) -> dict:
    """
    Run all algorithms.  Return dict:  algo -> {avg_wt, avg_tat, cpu_util, ctx}.

    *progress_callback*, if provided, is called as ``cb(current, total)``.
    """
    results = {}
    total   = len(ALGORITHMS)

    for i, algo in enumerate(ALGORITHMS):
        run_scheduler(algo, processes,
                      quantum=quantum if algo == "RR" else None)
        with open(OUTPUT_JSON) as f:
            data = json.load(f)
        results[algo] = {
            "avg_wt":   data["avg_waiting"],
            "avg_tat":  data["avg_turnaround"],
            "cpu_util": data["cpu_utilization"],
            "ctx":      data["context_switches"],
        }
        if progress_callback:
            progress_callback(i + 1, total)

    return results


def plot_comparison(results: dict):
    """Return a matplotlib Figure with grouped bar charts."""
    labels  = list(results.keys())
    avg_wt  = [results[a]["avg_wt"]   for a in labels]
    avg_tat = [results[a]["avg_tat"]  for a in labels]
    cpu     = [results[a]["cpu_util"] for a in labels]

    x     = np.arange(len(labels))
    width = 0.3

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # ── Waiting & Turnaround
    r1 = ax1.bar(x - width / 2, avg_wt,  width, label="Avg Waiting",     color="#E8834C")
    r2 = ax1.bar(x + width / 2, avg_tat, width, label="Avg Turnaround",  color="#4C9BE8")
    ax1.set_title("Average Times by Algorithm")
    ax1.set_ylabel("Time units")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=15, ha="right")
    ax1.legend()
    ax1.bar_label(r1, fmt="%.1f", padding=2, fontsize=8)
    ax1.bar_label(r2, fmt="%.1f", padding=2, fontsize=8)

    # ── CPU Utilization
    colors = ["#4CE87A" if v >= 90 else "#E8D44C" if v >= 70 else "#E84C4C"
              for v in cpu]
    bars = ax2.bar(labels, cpu, color=colors, edgecolor="black")
    ax2.set_title("CPU Utilization (%)")
    ax2.set_ylabel("%")
    ax2.set_ylim(0, 110)
    ax2.set_xticklabels(labels, rotation=15, ha="right")
    ax2.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=8)

    fig.tight_layout()
    return fig
