from tabulate import tabulate
import json

HEADERS = ['PID', 'Arrival', 'Burst', 'Completion', 'Waiting', 'Turnaround', 'Response']

def get_table_data(json_path='output/output.json'):
    """Return (headers, rows) for GUI and CLI use."""
    with open(json_path) as f:
        data = json.load(f)
    
    rows = []
    for p in data.get('processes', []):
        rows.append([
            p['pid'], p['arrival'], p['burst'], 
            p['completion'], p['waiting'], p['turnaround'], p['response']
        ])
    return HEADERS, rows

def show_table(json_path='output/output.json'):
    """Print table to terminal using tabulate with 'grid' format."""
    headers, rows = get_table_data(json_path)
    print(tabulate(rows, headers=headers, tablefmt='grid'))
