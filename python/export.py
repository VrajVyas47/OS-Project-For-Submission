"""
export.py – Export scheduler results to CSV or a full JSON report.
"""

import json
import csv
import datetime

from runner import OUTPUT_JSON


def export_csv(out: str = "output/results.csv",
               json_path: str = OUTPUT_JSON) -> str:
    """Write process table to CSV.  Returns the output path."""
    with open(json_path) as f:
        data = json.load(f)

    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["PID", "Arrival", "Burst", "Priority",
                         "Completion", "Waiting", "Turnaround", "Response"])
        for p in data.get("processes", []):
            writer.writerow([
                p["pid"],       p["arrival"],    p["burst"],
                p.get("priority", 0),
                p["completion"], p["waiting"],   p["turnaround"], p["response"],
            ])
    return out


def export_report(out: str = "output/report.json",
                  json_path: str = OUTPUT_JSON) -> str:
    """Wrap raw output with a timestamp + summary.  Returns the output path."""
    with open(json_path) as f:
        data = json.load(f)

    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": {
            "algorithm":        data.get("algorithm"),
            "time_quantum":     data.get("time_quantum"),
            "avg_waiting":      data.get("avg_waiting"),
            "avg_turnaround":   data.get("avg_turnaround"),
            "context_switches": data.get("context_switches"),
            "cpu_utilization":  data.get("cpu_utilization"),
        },
        "details": data,
    }

    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    return out
