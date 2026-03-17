# CPU Scheduling Simulator

A desktop application that simulates and visualises classic CPU scheduling algorithms.
Enter your own processes directly in the table, pick an algorithm, and instantly see a
colour-coded Gantt chart, a detailed metrics table, and a side-by-side comparison of
every algorithm on your exact workload.

The simulation engine is written in **C** for speed and correctness.
The interface is built with **Python · Tkinter · Matplotlib** for a clean,
interactive experience that works on Windows, Linux, and macOS.

---

## What the Project Does

When a computer runs multiple programs at the same time, the operating system must
decide which program gets access to the CPU at any given moment. This decision is made
by a **CPU scheduler**, and the rule it follows is called a **scheduling algorithm**.

Different algorithms optimise for different goals:

- **Throughput** — finishing as many processes as possible per unit of time
- **Fairness** — making sure no process waits too long
- **Response time** — how quickly a process first gets a turn on the CPU
- **Turnaround time** — total time from a process arriving to it finishing

This simulator lets you define your own set of processes (or generate random ones),
run any of 6 classic algorithms on that data, and immediately see the results — so
you can understand *why* one algorithm outperforms another on a specific workload.

---

## Features at a Glance

| Feature | Detail |
|---------|--------|
| **Live editable process table** | Double-click any cell to edit values directly in the UI — no files needed |
| **Add / Remove / Clear rows** | Manage processes with toolbar buttons |
| **Random data generator** | Fills the table with random processes in one click |
| **Load from file** | Import a `.txt` process file into the table |
| **Save to file** | Export the current table to a `.txt` file for reuse |
| **6 scheduling algorithms** | FCFS, SJF, SRTF, Priority NP, Priority P, Round Robin |
| **Gantt chart** | Colour-coded execution timeline with zoom, pan, and PNG save |
| **Process metrics table** | Sortable columns: WT, TAT, RT, CT, Priority |
| **Compare All** | Runs all 6 algorithms and plots grouped bar charts side by side |
| **Export CSV** | Save the metrics table for Excel / Google Sheets |
| **Export JSON report** | Timestamped full report including raw Gantt data |
| **Status bar** | Shows compile status, run time, and progress |

---

## Using the Interface

### The Process Table

The table at the top of the window is where you define the processes you want to simulate.
You can enter or change data in several ways — you never need to edit a file manually.

#### Editing cells directly

Double-click any cell in the **Arrival Time**, **Burst Time**, or **Priority** columns.
A text entry box appears over the cell. Type the new value and press **Enter** or **Tab**
to confirm, or **Escape** to cancel. Only whole numbers are accepted.

> **PID** is read-only — it is assigned automatically and stays stable.

#### Toolbar buttons

| Button | What it does |
|--------|--------------|
| **＋ Add** | Appends a new row at the bottom (PID auto-increments) |
| **－ Remove** | Deletes the selected row, or the last row if nothing is selected |
| **✕ Clear** | Removes all rows after asking you to confirm |
| **⚄ Random** | Replaces the table with randomly generated processes — the count spinner controls how many |
| **📂 Load…** | Opens a file dialog to load processes from a `.txt` file |
| **💾 Save…** | Opens a file dialog to save the current table to a `.txt` file |

#### Validation rules

- **Burst Time** must be ≥ 1 (a process needs at least 1 unit of CPU time)
- **Arrival Time** must be ≥ 0
- **Priority** can be any integer — lower number means higher priority
- All fields must be whole numbers

The simulator shows a clear error message if any value is invalid before running.

---

### Running a Simulation

1. Enter your processes in the table (or use Load / Random)
2. Select an algorithm from the **Algorithm** dropdown in the Controls bar
3. If you selected **RR (Round Robin)**, set the **Time Quantum** in the spinner
   that activates next to the dropdown
4. Click **▶ Run**

The status bar shows progress and how long the run took.

Results appear in two tabs:

**📊 Gantt Chart tab**
A horizontal bar chart showing the execution timeline for every process.
Each process has its own colour. Idle CPU time (when no process is running)
is shown as a hatched grey bar. The x-axis shows time units.
Use the matplotlib toolbar at the bottom of the chart to zoom, pan, or save as PNG.

**📋 Process Table tab**
One row per process showing all computed metrics.
Click any column header to sort by that column (click again to reverse).

---

### Comparing All Algorithms

Click **⇄ Compare All** in the controls bar.
The simulator uses the exact same processes currently in the table and runs all 6
algorithms back-to-back, then shows two charts on the **Compare All** tab:

- **Left chart** — Grouped bars showing average waiting time and average turnaround time
  for each algorithm so you can directly compare their efficiency
- **Right chart** — CPU utilisation percentage per algorithm, colour-coded
  green (≥ 90%) / yellow (≥ 70%) / red (< 70%)

The Time Quantum spinner value is used for the Round Robin run in the comparison.

---

### Exporting Results

After running a simulation, go to the **📋 Process Table** tab.
Two export buttons appear at the bottom:

- **Export CSV** — saves the process metrics as a `.csv` file you can open in Excel or Google Sheets
- **Export JSON Report** — saves a timestamped `.json` file with summary statistics,
  per-process details, and the full Gantt data

Both buttons open a Save dialog so you choose exactly where the file is written.

---

## Algorithms

### 1 · FCFS — First Come, First Served

The simplest possible scheduler. Processes are executed strictly in the order they
arrive in the ready queue. No interruptions, no priority checks — whoever arrives
first, runs first.

```
Processes:  P1(AT=0, BT=4)  P2(AT=1, BT=3)  P3(AT=2, BT=5)

Timeline:  [----P1----][---P2---][-----P3-----]
            0          4         7            12
```

- **Type:** Non-preemptive
- **Pros:** Simple, predictable, no starvation
- **Cons:** The *convoy effect* — one long process blocks every short process
  behind it, causing high average waiting times
- **Real-world use:** Batch systems, print queues

---

### 2 · SJF — Shortest Job First

Among all processes that have already arrived, the one with the **shortest burst time**
is chosen next. Once it starts running it is not interrupted.

```
At t=0 only P1 has arrived → runs P1(BT=8).
At t=8 both P2(BT=4) and P3(BT=2) have arrived → picks P3 (shortest) first.

Timeline:  [--------P1--------][--P3--][----P2----]
            0                   8     10          14
```

- **Type:** Non-preemptive
- **Pros:** Provably minimises average waiting time among all non-preemptive algorithms
- **Cons:** Starvation — long processes can wait indefinitely if short ones keep
  arriving. Requires burst time estimates in practice.
- **Real-world use:** Batch processing, job schedulers

---

### 3 · SRTF — Shortest Remaining Time First

The preemptive version of SJF. Every time a new process arrives, the scheduler
checks whether its burst time is shorter than the *remaining* burst time of the
currently running process. If so, it preempts immediately.

```
P1 starts at t=0 (BT=8, remaining=8).
P2 arrives at t=1 (BT=4).  remaining_P1=7 > BT_P2=4  →  preempt, run P2.
P3 arrives at t=2 (BT=2).  remaining_P2=3 > BT_P3=2  →  preempt, run P3.
```

- **Type:** Preemptive
- **Pros:** Optimal average waiting time of all preemptive schedulers
- **Cons:** High context-switch count; long processes can starve; burst estimates needed
- **Real-world use:** Interactive systems where minimising average wait is critical

---

### 4 · Priority (Non-Preemptive)

Every process is assigned a **priority number** (lower = more important).
The ready process with the lowest priority number gets the CPU next.
Once it starts, it runs to completion without interruption even if a
higher-priority process arrives while it is running.

- **Type:** Non-preemptive
- **Tie-breaking:** Earlier arrival first, then lower PID
- **Pros:** Important tasks complete sooner
- **Cons:** Low-priority processes can starve indefinitely
- **Real-world use:** OS kernel threads vs user processes, medical monitoring systems

---

### 5 · Priority (Preemptive)

Same as Priority NP, but if a newly arrived process has a **higher priority**
(lower number) than the currently running one, it immediately preempts it.

- **Type:** Preemptive
- **Tie-breaking:** Running process is kept when priorities are equal — avoids
  needless context switches
- **Pros:** High-priority tasks get the CPU almost instantly after arrival
- **Cons:** More context switches than the NP version; starvation still possible
- **Real-world use:** Real-time operating systems, interrupt handling

---

### 6 · RR — Round Robin

Each process is given a fixed CPU slice called the **time quantum** (you set this
in the UI). After the slice expires the process goes to the back of the ready queue.
If a process finishes before its quantum is up, the next process starts immediately.

```
Processes: P1(BT=6)  P2(BT=4)  P3(BT=5)    Quantum = 2

Timeline:  [P1][P2][P3][P1][P2][P3][P1][P3]
            0   2   4   6   8  10  12  14  15
```

**Quantum size matters:**

| Quantum | Effect |
|---------|--------|
| Too small | Lots of context switches, high overhead |
| Too large | Behaves like FCFS |
| Just right | Slightly larger than the typical CPU burst gives the best balance |

- **Type:** Preemptive
- **Pros:** Fair, no starvation, good interactive response time
- **Cons:** Higher average turnaround time than SJF/SRTF
- **Real-world use:** The foundation of virtually all modern OS time-sharing schedulers

---

## Key Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Arrival Time (AT)** | — | When the process enters the ready queue |
| **Burst Time (BT)** | — | Total CPU time the process requires |
| **Completion Time (CT)** | — | When the process finishes executing |
| **Turnaround Time (TAT)** | CT − AT | Total time from arrival to completion |
| **Waiting Time (WT)** | TAT − BT | Time spent idle in the ready queue |
| **Response Time (RT)** | First CPU time − AT | Time until the process first gets the CPU |
| **CPU Utilisation** | Active time / Total time × 100% | How busy the CPU was (100% = never idle) |
| **Context Switches** | — | How many times the CPU switched between processes |

> **Priority convention:** A **lower number = higher priority** throughout this project.
> Priority 1 always runs before priority 5.

---

## Input File Format

If you prefer to write process data in a text file and load it with the **📂 Load** button:

```
<number of processes>
<pid>  <arrival_time>  <burst_time>  <priority>
<pid>  <arrival_time>  <burst_time>  <priority>
...
```

Example (`input/input.txt`):
```
5
1 0 8 2
2 1 4 1
3 2 9 3
4 3 5 2
5 4 2 4
```

- Fields are separated by spaces
- For algorithms that do not use priority (FCFS, SJF, SRTF, RR) you can set
  the priority column to 0 — it is ignored
- The **💾 Save** button writes the current UI table in exactly this format,
  so you can round-trip data between the UI and files freely

---

## Project Structure

```
project/
├── c_code/
│   ├── scheduler.h       ← shared structs and all function declarations
│   ├── common.c          ← utilities, JSON writer, argument parser, main()
│   ├── fcfs.c            ← FCFS only  — only open this file to fix FCFS bugs
│   ├── sjf.c             ← SJF  only
│   ├── srtf.c            ← SRTF only
│   ├── priority_np.c     ← Priority Non-Preemptive only
│   ├── priority_p.c      ← Priority Preemptive only
│   ├── round_robin.c     ← Round Robin only
│   └── Makefile
├── python/
│   ├── gui.py            ← main window — run this to launch the app
│   ├── runner.py         ← compiles the C binary with gcc (no make needed on Windows)
│   ├── visualize.py      ← Gantt chart and metrics panel (Matplotlib)
│   ├── table.py          ← process results table helpers
│   ├── compare.py        ← runs all algorithms and plots comparison charts
│   └── export.py         ← CSV and timestamped JSON report export
├── input/
│   └── input.txt         ← sample process file (5 processes)
├── output/               ← output.json is written here at runtime
└── README.md
```

### Why one C file per algorithm?

The original code had all 6 algorithms in a single large file.
A bug in Round Robin meant scrolling through hundreds of lines of unrelated code.
The new structure isolates each algorithm completely:

- A bug in SRTF → only open `srtf.c`, nothing else changes
- Adding a new algorithm → create one new `.c` file, no other files need editing
- The Makefile compiles each file to its own `.o` object, so only changed files
  are recompiled on each build

---

## Quick Start

### Step 0 — Install gcc

The GUI compiles the C code automatically on first launch — you just need `gcc` on your PATH.

| Platform | How to install gcc |
|----------|--------------------|
| **Windows** | Download **MinGW-w64** from https://winlibs.com → extract the zip → add the `bin\` folder to your **PATH** environment variable → restart your terminal |
| **Ubuntu / Debian** | `sudo apt install gcc` |
| **Fedora / RHEL** | `sudo dnf install gcc` |
| **macOS** | `xcode-select --install`  or  `brew install gcc` |

> No `make` required — `runner.py` calls `gcc` directly and works on every platform.

### Step 1 — Install Python packages

```bash
pip install matplotlib numpy tabulate
```

### Step 2 — Launch

```bash
cd python
python gui.py
```

The status bar shows `Scheduler binary ready.` once compilation succeeds.
After that, enter your process data and click **▶ Run**.

---

## CLI Usage (without the GUI)

The compiled binary can be driven directly from a terminal for scripting or testing.

```bash
# Build first (Linux / macOS — Windows users can run: gcc -O2 c_code\*.c -o c_code\scheduler.exe)
cd c_code && make

# FCFS using a file
./scheduler --file ../input/input.txt --algo FCFS

# SJF with inline process data
./scheduler --algo SJF \
  --pid 1 --at 0 --bt 8 --priority 0 \
  --pid 2 --at 1 --bt 4 --priority 0

# Round Robin with quantum = 3
./scheduler --algo RR --quantum 3 \
  --pid 1 --at 0 --bt 8 --priority 0 \
  --pid 2 --at 2 --bt 5 --priority 0

# Priority (Preemptive)
./scheduler --algo Priority_P \
  --pid 1 --at 0 --bt 6 --priority 3 \
  --pid 2 --at 1 --bt 4 --priority 1

# All available algorithm names:
#   FCFS   SJF   SRTF   Priority_NP   Priority_P   RR
```

Output is always written to `output/output.json`.

---

## Adding a New Algorithm

1. Create `c_code/my_algo.c` with one function:
   ```c
   void my_algo(Process p[], int n, Result *r) { /* your logic */ }
   ```
2. Add the declaration to `scheduler.h`
3. Add `my_algo.c` to the `SRCS` line in the `Makefile`
4. Add an `else if` branch in the dispatch block inside `main()` in `common.c`
5. Add the name string to the `ALGOS` list in `ControlBar` in `python/gui.py`

The Gantt chart, process table, comparison, and export all pick it up automatically —
no other files need to change.
