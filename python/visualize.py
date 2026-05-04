import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

COLORS = ['#4C9BE8','#E8834C','#4CE87A','#E84C4C','#9B4CE8',
          '#E8D44C','#4CE8D4','#E84CA3','#84E84C','#4C6BE8']

def get_figure(json_path='output/output.json'):
    with open(json_path) as f:
        data = json.load(f)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7),
                                    gridspec_kw={'height_ratios': [3, 1]})
    _draw_gantt(ax1, data)
    _draw_metrics(ax2, data)
    fig.tight_layout()
    return fig, (ax1, ax2)

def show_gantt(json_path='output/output.json'):
    fig, _ = get_figure(json_path)
    plt.show()

def _draw_gantt(ax, data):
    ax.clear()
    gantt = data.get('gantt', [])
    if not gantt:
        return
        
    pids = sorted(list(set(b['pid'] for b in gantt if b['pid'] != -1)))
    pid_to_y = {pid: i for i, pid in enumerate(pids)}
    y_labels = [f"P{pid}" for pid in pids]
    
    if any(b['pid'] == -1 for b in gantt):
        pid_to_y[-1] = len(pids)
        y_labels.append("IDLE")
        
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel('Time')
    ax.set_title(f"{data['algorithm']} — Gantt Chart")
    
    max_time = 0
    for block in gantt:
        pid = block['pid']
        start = block['start']
        end = block['end']
        duration = end - start
        max_time = max(max_time, end)
        
        y = pid_to_y[pid]
        if pid == -1:
            color = '#CCCCCC'
            hatch = '////'
            label_text = 'IDLE'
        else:
            color = COLORS[pid % len(COLORS)]
            hatch = ''
            label_text = f"P{pid} ({duration})"
            
        ax.barh(y, duration, left=start, color=color, hatch=hatch, edgecolor='black')
        ax.text(start + duration/2, y, label_text, ha='center', va='center', color='black' if pid==-1 else 'white', fontweight='bold')
        
    ax.set_xticks(range(max_time + 1))
    ax.grid(axis='x', linestyle='--', alpha=0.7)

def _draw_metrics(ax, data):
    ax.clear()
    metrics = ['Avg Waiting Time', 'Avg Turnaround Time']
    values = [data['avg_waiting'], data['avg_turnaround']]
    
    bars = ax.barh(metrics, values, color=['#E8834C', '#4C9BE8'])
    ax.set_xlim(0, max(values) * 1.2 if max(values) > 0 else 1)
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (max(values)*0.02 if max(values)>0 else 0.1), bar.get_y() + bar.get_height()/2, 
                f"{width:.2f}", ha='left', va='center', fontweight='bold')
                
    info_text = f"CPU Utilization: {data['cpu_utilization']:.2f}%\nContext Switches: {data['context_switches']}"
    ax.text(0.95, 0.5, info_text, transform=ax.transAxes, ha='right', va='center', 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'))
