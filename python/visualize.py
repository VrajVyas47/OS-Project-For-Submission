"""
visualize.py – Matplotlib Gantt chart and metrics panel.
"""

import json
import matplotlib.pyplot as plt

COLORS = [
    "#4C9BE8", "#E8834C", "#4CE87A", "#E84C4C", "#9B4CE8",
    "#E8D44C", "#4CE8D4", "#E84CA3", "#84E84C", "#4C6BE8",
]


def get_figure(json_path: str) -> tuple:
    """Return (fig, (ax_gantt, ax_metrics)) ready to embed or show."""
    with open(json_path) as f:
        data = json.load(f)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 7),
        gridspec_kw={"height_ratios": [3, 1]}
    )
    _draw_gantt(ax1, data)
    _draw_metrics(ax2, data)
    fig.tight_layout()
    return fig, (ax1, ax2)


def show_gantt(json_path: str) -> None:
    """Open a standalone matplotlib window."""
    get_figure(json_path)
    plt.show()


# ── Internal helpers ──────────────────────────────────────────────

def _draw_gantt(ax, data: dict) -> None:
    ax.clear()
    gantt = data.get("gantt", [])
    if not gantt:
        ax.set_title("No data")
        return

    pids     = sorted({b["pid"] for b in gantt if b["pid"] != -1})
    pid_to_y = {pid: i for i, pid in enumerate(pids)}
    labels   = [f"P{pid}" for pid in pids]

    if any(b["pid"] == -1 for b in gantt):
        pid_to_y[-1] = len(pids)
        labels.append("IDLE")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Time")

    quantum_str = ""
    if data.get("time_quantum") is not None:
        quantum_str = f"  (quantum = {data['time_quantum']})"
    ax.set_title(f"{data['algorithm']}{quantum_str} — Gantt Chart")

    max_time = 0
    for block in gantt:
        pid      = block["pid"]
        start    = block["start"]
        end      = block["end"]
        duration = end - start
        max_time = max(max_time, end)
        y        = pid_to_y[pid]

        if pid == -1:
            color, hatch, txt_color = "#CCCCCC", "////", "black"
            label = "IDLE"
        else:
            color, hatch, txt_color = COLORS[pid % len(COLORS)], "", "white"
            label = f"P{pid} ({duration})"

        ax.barh(y, duration, left=start, color=color,
                hatch=hatch, edgecolor="black", height=0.6)
        ax.text(start + duration / 2, y, label,
                ha="center", va="center",
                color=txt_color, fontweight="bold", fontsize=8)

    ax.set_xlim(0, max_time)
    ax.set_xticks(range(max_time + 1))
    ax.grid(axis="x", linestyle="--", alpha=0.5)


def _draw_metrics(ax, data: dict) -> None:
    ax.clear()
    labels = ["Avg Waiting Time", "Avg Turnaround Time"]
    values = [data["avg_waiting"], data["avg_turnaround"]]

    bars = ax.barh(labels, values, color=["#E8834C", "#4C9BE8"], height=0.4)
    ax.set_xlim(0, max(values) * 1.25 if max(values) > 0 else 1)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + max(values) * 0.02 + 0.05,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}", ha="left", va="center", fontweight="bold")

    info = (f"CPU Utilization: {data['cpu_utilization']:.1f}%\n"
            f"Context Switches: {data['context_switches']}")
    ax.text(0.99, 0.5, info, transform=ax.transAxes,
            ha="right", va="center",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="gray"))
