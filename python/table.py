"""
table.py – Parse output JSON into tabular rows.
"""

import json

HEADERS = ["PID", "Arrival", "Burst", "Priority",
           "Completion", "Waiting", "Turnaround", "Response"]


def get_table_data(json_path: str) -> tuple[list, list]:
    """Return (HEADERS, rows) from a scheduler output JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    rows = []
    for p in data.get("processes", []):
        rows.append([
            p["pid"],        p["arrival"],    p["burst"],
            p.get("priority", "-"),
            p["completion"], p["waiting"],    p["turnaround"], p["response"],
        ])
    return HEADERS, rows


def show_table(json_path: str) -> None:
    """Print a nicely formatted table to the terminal."""
    try:
        from tabulate import tabulate
        headers, rows = get_table_data(json_path)
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        headers, rows = get_table_data(json_path)
        print("\t".join(headers))
        for row in rows:
            print("\t".join(str(v) for v in row))
