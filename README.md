# CPU Scheduling Simulator Visualizer

## Project Overview
This project is a detailed visualizer and simulator for 9 different CPU Scheduling Algorithms. The project divides responsibilities between two languages to harness performance and presentability:
- **C Language** acts as the engine handling the complex scheduling logic, time flow, accurate context switching, metric calculations, and JSON generation.
- **Python (Tkinter & Matplotlib)** acts as the frontend GUI handling table inputs, loading configurations, plotting process outcomes, drawing Gantt charts, and exporting results.
Communication between the simulation layer and GUI layer takes place securely via `output/output.json`.

## Features
- Interactive Tkinter Desktop Application.
- Compare multiple scheduling algorithms against a given workload instantly with bar charts.
- **New updates**:
  - Support for 3 new scheduling algorithms: HRRN, LJF, LRTF.
  - Direct execution of `.exe` builds to natively support Windows environments without `make`.
  - GUI utilities: Clear All grid rows, Load input directly from `.txt` config files.
  - Refactored C architecture with isolated algorithms into individual module `.c` files.
- Visualizations: Auto-rendered Gantt Chart plots and per-process metrics tables.
- Performance Details: Tracks Context Switches, CPU Utilization percentage, Turnaround Time, and Waiting Time.

## Implemented Algorithms
1. **FCFS (First Come First Serve)**: Non-preemptive, simple logical FIFO queue.
2. **SJF (Shortest Job First)**: Non-preemptive, prioritizes the process with the shortest absolute burst time.
3. **SRTF (Shortest Remaining Time First)**: Preemptive version of SJF. Preempts a running process if a newer process arrives with a shorter remaining burst time.
4. **Priority_NP (Priority Non-Preemptive)**: Executes the arriving process with the highest priority (lowest integer value).
5. **Priority_P (Priority Preemptive)**: Preempts executing processes instantaneously when an even higher priority process arrives.
6. **RR (Round Robin)**: Preemptive strategy using a standard cyclic queue scheduling processes for a fixed Time Quantum limit.
7. **HRRN (Highest Response Ratio Next)**: Non-preemptive, prioritizes based on the response ratio `((Wait_Time + Burst_Time) / Burst_Time)`. Naturally prevents process starvation.
8. **LJF (Longest Job First)**: Non-preemptive, purposefully selects the incoming process with the longest burst time.
9. **LRTF (Longest Remaining Time First)**: Preemptive version of LJF. Continues executing processes with maximum remaining burst times.

## Application Architecture

The system is split into two cleanly separated module spaces.

### C Engine (`c_code/`)
- `Makefile`: Script to build the `scheduler` executable linking all modular algorithms.
- `scheduler.h`: Standardizes definitions (Process, Result states), constant boundaries, and utility definitions.
- `scheduler.c`: Responsible for parsing command line arguments, generating exact Gantt snapshots, verifying context switches, rendering exact JSON states, and serving as the primary `main()` hook.
- `<algorithm>.c` (`fcfs.c`, `sjf.c`, `hrrn.c`, etc.): Modular implementations of logic specifically isolated to their individual algorithm rules.

### Python Frontend (`python/`)
- `gui.py`: Primary interactive application window constructed with `tkinter`. Hosts input grids, configures the algorithms, embeds `matplotlib` visualizers.
- `main.py`: Automation script utilized internally to trigger compilation via `gcc`/`make` and launch execution runs against the C binary via subprocess safely handling exceptions on varying platforms.
- `visualize.py`: Constructs real-time visual step-by-step plotted Gantt charts leveraging Python's `matplotlib`. 
- `table.py`: Structures tabular readouts mapping outcome characteristics (WT, TAT) for the processes using `tabulate`.
- `compare.py`: Executes the input task across every supported scheduling algorithm sequentially, capturing global metrics and evaluating the most optimal solution statistically using horizontal bar-charts.
- `export.py`: Module permitting users to persist current table snapshots and simulation statistics into `.csv` files or `.json` trees natively to disk.

## Prerequisites
- **C Compiler**: `gcc` installed and added to PATH. 
- **Python 3**.x environments.
- **Python Dependencies**:
  ```bash
  pip install matplotlib tabulate numpy
  ```

## How to Run

### Step 1: Run the Visualizer Tool (Recommended)
You can directly spin up the GUI. It will auto-compile the C binary in the background using `gcc`.
```bash
python python/gui.py
```
From the GUI, try loading an example dataset by clicking **Load File**, or configure jobs by double-clicking the grid cells and inserting numbers. Click **Run** to execute the visualization payload, or **Compare** to plot across all algorithms.

### Step 2: Command Line Run (Optional)
If you wish to use the tool without visual UI elements (only parsing outputs to terminals). Setup compilation first:
```bash
cd c_code
make
cd ..
```
Run simulation specifically for an algorithm:
```bash
python python/main.py --file input/input.txt --algo HRRN
```

## Input File Format Specification (`.txt`)
If you define custom inputs in a strictly text file:
```text
<number_of_processes>
<pid1> <arrival_time1> <burst_time1> <priority1>
<pid2> <arrival_time2> <burst_time2> <priority2>
```
*Note: Priority is standard lowest number = highest priority.*

### Sample `input.txt`
```text
5
1 0 8 2
2 1 4 1
3 2 9 3
4 3 5 2
5 4 2 4
```
