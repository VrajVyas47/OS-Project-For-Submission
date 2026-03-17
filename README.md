# CPU Scheduling Simulator

A GUI-based CPU scheduling simulator written in C (algorithms) and Python (GUI / visualisation).

---

## Project Structure

```
project/
├── c_code/
│   ├── scheduler.h      ← shared structs & declarations
│   ├── common.c         ← utilities, JSON writer, arg parser, main()
│   ├── fcfs.c           ← FCFS algorithm
│   ├── sjf.c            ← SJF  algorithm
│   ├── srtf.c           ← SRTF algorithm
│   ├── priority_np.c    ← Priority Non-Preemptive
│   ├── priority_p.c     ← Priority Preemptive
│   ├── round_robin.c    ← Round Robin
│   └── Makefile
├── python/
│   ├── gui.py           ← Main GUI  (run this)
│   ├── runner.py        ← Build + invoke the C binary
│   ├── visualize.py     ← Matplotlib Gantt chart
│   ├── table.py         ← Process results table
│   ├── compare.py       ← Multi-algorithm comparison
│   └── export.py        ← CSV / JSON report export
├── input/
│   └── input.txt        ← Sample process file
└── output/              ← Generated at runtime
```

---

## Quick Start

### 0 – Prerequisites: gcc

| OS | How to get gcc |
|----|---------------|
| **Windows** | Install **MinGW-w64** from https://winlibs.com → download the zip → extract → add the `bin\` folder to your **PATH** environment variable |
| **Linux** | `sudo apt install gcc` (Debian/Ubuntu) or `sudo dnf install gcc` (Fedora) |
| **macOS** | `xcode-select --install` or `brew install gcc` |

> The GUI calls `gcc` directly — no `make` is required on any platform.

### 1 – Install Python dependencies
```bash
pip install matplotlib numpy tabulate
```

### 2 – Launch the GUI
```bash
cd python
python gui.py
```

The GUI automatically compiles the C code on first launch (requires `gcc` and `make`).

---

## Input File Format

```
<number of processes>
<pid> <arrival_time> <burst_time> <priority>
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

Lower priority number = higher priority.

---

## GUI Features

| Feature | How to use |
|---------|-----------|
| Edit a cell | Double-click it |
| Add a row | Click **＋ Add** |
| Remove a row | Select a row then click **－ Remove** |
| Random data | Click **⚄ Random** (respects the process count spinner) |
| Load from file | Click **📂 Load…** and pick a `.txt` file |
| Save to file | Click **💾 Save…** |
| Run algorithm | Choose algo → click **▶ Run** |
| Time Quantum | Auto-enabled when **RR** is selected |
| Compare all | Click **⇄ Compare All** |
| Export results | Process Table tab → **Export CSV** / **Export JSON Report** |

---

## Adding a New Algorithm

1. Create `c_code/my_algo.c` with a single function: `void my_algo(Process p[], int n, Result *r)`
2. Declare it in `scheduler.h`
3. Add `my_algo.c` to `SRCS` in the `Makefile`
4. Add an `else if` branch in `common.c` → `main()`
5. Add the algo name to `ControlBar.ALGOS` in `python/gui.py`

Everything else (JSON output, Gantt chart, table) works automatically.

---

## CLI Usage (without GUI)

```bash
# Build
cd c_code && make

# Run FCFS on the sample file
./scheduler --file ../input/input.txt --algo FCFS

# Run SJF with inline data
./scheduler --algo SJF \
  --pid 1 --at 0 --bt 8 --priority 2 \
  --pid 2 --at 1 --bt 4 --priority 1

# Round Robin (quantum = 3)
./scheduler --algo RR --quantum 3 \
  --pid 1 --at 0 --bt 8 --priority 0 \
  --pid 2 --at 2 --bt 5 --priority 0
```

Output is written to `output/output.json`.
