import json
import matplotlib.pyplot as plt
import numpy as np
from main import build_c, run_scheduler

ALGORITHMS = ['FCFS', 'SJF', 'SRTF', 'Priority_NP', 'Priority_P', 'RR']

def compare_all(processes, quantum=2, progress_callback=None):
    """Run all algorithms. Return dict: algo -> {avg_wt, avg_tat}."""
    results = {}
    total = len(ALGORITHMS)
    for i, algo in enumerate(ALGORITHMS):
        run_scheduler(algo, len(processes), processes, quantum if algo == 'RR' else None)
        with open('output/output.json') as f:
            data = json.load(f)
            results[algo] = {
                'avg_wt': data['avg_waiting'],
                'avg_tat': data['avg_turnaround']
            }
        if progress_callback:
            progress_callback(i + 1, total)
    return results

def plot_comparison(results):
    """Grouped bar chart: X = algorithms, bars = avg_wt and avg_tat."""
    labels = list(results.keys())
    avg_wt = [results[algo]['avg_wt'] for algo in labels]
    avg_tat = [results[algo]['avg_tat'] for algo in labels]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, avg_wt, width, label='Avg Waiting Time', color='#E8834C')
    rects2 = ax.bar(x + width/2, avg_tat, width, label='Avg Turnaround Time', color='#4C9BE8')

    ax.set_ylabel('Time')
    ax.set_title('Algorithm Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    ax.bar_label(rects1, padding=3, fmt='%.2f')
    ax.bar_label(rects2, padding=3, fmt='%.2f')

    fig.tight_layout()
    return fig
