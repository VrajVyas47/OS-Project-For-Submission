import json
import csv
import datetime
import os

def export_csv(json_path='output/output.json', out='output/results.csv'):
    """Write CSV with headers: PID,Arrival,Burst,CT,WT,TAT,RT"""
    with open(json_path) as f:
        data = json.load(f)
        
    with open(out, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PID', 'Arrival', 'Burst', 'CT', 'WT', 'TAT', 'RT'])
        for p in data.get('processes', []):
            writer.writerow([
                p['pid'], p['arrival'], p['burst'],
                p['completion'], p['waiting'], p['turnaround'], p['response']
            ])

def export_report(json_path='output/output.json', out='output/report.json'):
    """Add timestamp + summary to JSON and save as report."""
    with open(json_path) as f:
        data = json.load(f)
        
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": {
            "algorithm": data.get("algorithm"),
            "time_quantum": data.get("time_quantum"),
            "avg_waiting": data.get("avg_waiting"),
            "avg_turnaround": data.get("avg_turnaround"),
            "context_switches": data.get("context_switches"),
            "cpu_utilization": data.get("cpu_utilization")
        },
        "details": data
    }
    
    with open(out, 'w') as f:
        json.dump(report, f, indent=2)
