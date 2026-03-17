"""
visualize.py – Matplotlib Gantt chart and metrics panel.

Fixes applied
-------------
* constrained_layout replaces tight_layout (no more clipping in tkinter)
* Smart x-axis ticks via MaxNLocator – no more label pile-ups on long schedules
* Minor gridlines at every time unit for readability without tick crowding
* Dynamic figure height based on process count so bars are never squashed
* Metrics panel has enough vertical space for labels even when window is small
"""

import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

COLORS = [
    "#4C9BE8", "#E8834C", "#4CE87A", "#E84C4C", "#9B4CE8",
    "#E8D44C", "#4CE8D4", "#E84CA3", "#84E84C", "#4C6BE8",
]


def get_figure(json_path: str):
    """Return (fig, (ax_gantt, ax_metrics)) ready to embed or show."""
    with open(json_path) as f:
        data = json.load(f)

    gantt    = data.get("gantt", [])
    n_procs  = len({b["pid"] for b in gantt if b["pid"] != -1})
    has_idle = any(b["pid"] == -1 for b in gantt)
    n_rows   = n_procs + (1 if has_idle else 0)

    # Dynamic height: at least 5 inches, 0.55 per row + fixed base
    fig_h = max(5.5, n_rows * 0.55 + 3.2)

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(14, fig_h),
        gridspec_kw={"height_ratios": [max(3, n_rows), 1.6]},
        constrained_layout=True,   # replaces tight_layout – handles clipping
    )

    _draw_gantt(ax1, data)
    _draw_metrics(ax2, data)
    return fig, (ax1, ax2)


def show_gantt(json_path: str) -> None:
    """Open a standalone matplotlib window."""
    get_figure(json_path)
    plt.show()


# ── Internal helpers ──────────────────────────────────────────────

def _smart_xticks(ax, max_time: int) -> None:
    """
    Set x-axis ticks intelligently:
    - MaxNLocator keeps label count ≤ 20 so they never overlap
    - Minor ticks at every unit give a fine grid without crowding labels
    """
    ax.set_xlim(0, max_time)

    # Major ticks: at most 20 labels regardless of time span
    ax.xaxis.set_major_locator(
        mticker.MaxNLocator(nbins=20, integer=True, steps=[1,2,5,10])
    )
    # Minor ticks at every integer unit (for grid lines only)
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))

    ax.grid(axis="x", which="major", linestyle="--", linewidth=0.8,
            alpha=0.6, color="gray")
    ax.grid(axis="x", which="minor", linestyle=":",  linewidth=0.4,
            alpha=0.35, color="gray")


def _draw_gantt(ax, data: dict) -> None:
    ax.clear()
    gantt = data.get("gantt", [])
    if not gantt:
        ax.set_title("No data"); return

    pids     = sorted({b["pid"] for b in gantt if b["pid"] != -1})
    pid_to_y = {pid: i for i, pid in enumerate(pids)}
    labels   = [f"P{pid}" for pid in pids]

    if any(b["pid"] == -1 for b in gantt):
        pid_to_y[-1] = len(pids)
        labels.append("IDLE")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(-0.6, len(labels) - 0.4)
    ax.set_xlabel("Time", fontsize=9)

    quantum_str = ""
    if data.get("time_quantum") is not None:
        quantum_str = f"  (quantum = {data['time_quantum']})"
    ax.set_title(f"{data['algorithm']}{quantum_str} — Gantt Chart",
                 fontsize=11, pad=6)

    max_time = 0
    bar_h    = 0.6

    for block in gantt:
        pid      = block["pid"]
        start    = block["start"]
        end      = block["end"]
        duration = end - start
        max_time = max(max_time, end)
        y        = pid_to_y[pid]

        if pid == -1:
            color, hatch, txt_col = "#CCCCCC", "////", "black"
            label = "IDLE"
        else:
            color, hatch, txt_col = COLORS[pid % len(COLORS)], "", "white"
            label = f"P{pid}\n({duration})"

        ax.barh(y, duration, left=start, color=color,
                hatch=hatch, edgecolor="black",
                height=bar_h, linewidth=0.6)

        # Only draw label if bar is wide enough (estimated in data units).
        # Use figure width in inches × ~80 data-units per inch as a rough threshold.
        fig_w_inches = ax.get_figure().get_size_inches()[0]
        units_per_inch = max(max_time, 1) / (fig_w_inches * 0.75)
        min_units_for_label = units_per_inch * 0.22   # ~22% of an inch wide
        if duration > min_units_for_label:
            ax.text(start + duration / 2, y, label,
                    ha="center", va="center",
                    color=txt_col, fontweight="bold",
                    fontsize=7, linespacing=1.2)

    _smart_xticks(ax, max_time)


def _draw_metrics(ax, data: dict) -> None:
    ax.clear()
    metric_labels = ["Avg Waiting", "Avg Turnaround"]
    values        = [data["avg_waiting"], data["avg_turnaround"]]
    bar_colors    = ["#E8834C", "#4C9BE8"]

    bars = ax.barh(metric_labels, values, color=bar_colors,
                   height=0.45, edgecolor="black", linewidth=0.6)

    max_v = max(values) if max(values) > 0 else 1
    ax.set_xlim(0, max_v * 1.28)
    ax.set_xlabel("Time units", fontsize=8)
    ax.tick_params(axis="both", labelsize=8)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + max_v * 0.025, bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}", ha="left", va="center",
                fontsize=8, fontweight="bold")

    # Info box: utilization + context switches
    info = (
        f"CPU Utilization: {data['cpu_utilization']:.1f}%\n"
        f"Context Switches: {data['context_switches']}"
    )
    ax.text(0.99, 0.5, info, transform=ax.transAxes,
            ha="right", va="center", fontsize=8,
            bbox=dict(facecolor="white", alpha=0.85,
                      edgecolor="gray", boxstyle="round,pad=0.3"))
