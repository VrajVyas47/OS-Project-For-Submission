"""
gui.py – CPU Scheduling Simulator GUI
======================================
Run directly:  python gui.py
               python gui.py  (from the python/ directory)

Features
--------
* Editable process table (double-click any cell to edit)
* Add / Remove / Clear / Random-generate process rows
* Load processes from a .txt file  (same format as input/input.txt)
* Save current process table to a .txt file
* Algorithm selector with Time Quantum spinbox (auto-enabled for RR)
* Run single algorithm  →  Gantt Chart + Process Table tabs
* Compare All algorithms  →  grouped bar charts
* Export results as CSV or JSON report
* Status bar with timing information
"""

import os
import sys
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── Resolve paths so the GUI can be launched from any cwd ────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
os.chdir(_ROOT)

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from runner    import build_c, run_scheduler, OUTPUT_JSON
from visualize import get_figure
from table     import get_table_data, HEADERS
from export    import export_csv, export_report
from compare   import compare_all, plot_comparison

# ── DPI awareness (Windows) ──────────────────────────────────────
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════════
class ProcessInputFrame(ttk.LabelFrame):
    """Editable treeview for entering process data."""

    COLS = ("PID", "Arrival Time", "Burst Time", "Priority")

    def __init__(self, parent, **kw):
        super().__init__(parent, text="Process Input", **kw)
        self._build_toolbar()
        self._build_tree()
        self._build_edit_overlay()
        self._populate_defaults()

    # ── Toolbar ───────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=(6, 2))

        ttk.Label(bar, text="Processes:").pack(side="left")
        self._n_var = tk.IntVar(value=5)
        self._n_spin = ttk.Spinbox(bar, from_=1, to=100,
                                   textvariable=self._n_var, width=5)
        self._n_spin.pack(side="left", padx=4)

        buttons = [
            ("＋ Add",    self.add_row),
            ("－ Remove", self.remove_row),
            ("✕ Clear",  self.clear_rows),
            ("⚄ Random", self.generate_random),
            ("📂 Load…",  self.load_from_file),
            ("💾 Save…",  self.save_to_file),
        ]
        for label, cmd in buttons:
            ttk.Button(bar, text=label, command=cmd, width=10).pack(
                side="left", padx=2)

        ttk.Label(bar,
                  text="  ✎ Double-click a cell to edit",
                  foreground="gray").pack(side="right", padx=6)

    # ── Treeview ──────────────────────────────────────────────────
    def _build_tree(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._tree = ttk.Treeview(frame, columns=self.COLS,
                                  show="headings", height=7,
                                  selectmode="browse")
        widths = {"PID": 60, "Arrival Time": 110,
                  "Burst Time": 100, "Priority": 90}
        for col in self.COLS:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=widths[col], anchor="center",
                              stretch=False)

        sb = ttk.Scrollbar(frame, orient="vertical",
                           command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", self._on_double_click)

    # ── Inline edit overlay ───────────────────────────────────────
    def _build_edit_overlay(self):
        """A hidden Entry widget floated over the clicked cell."""
        self._edit_entry = ttk.Entry(self._tree)
        self._edit_item  = None
        self._edit_col   = None

    def _on_double_click(self, event):
        region = self._tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item   = self._tree.identify_row(event.y)
        column = self._tree.identify_column(event.x)
        col_idx = int(column.replace("#", "")) - 1

        # PID is read-only
        if col_idx == 0:
            return

        bbox = self._tree.bbox(item, column)
        if not bbox:
            return
        x, y, w, h = bbox

        self._edit_item = item
        self._edit_col  = col_idx

        value = self._tree.item(item, "values")[col_idx]
        e = self._edit_entry
        e.delete(0, "end")
        e.insert(0, value)
        e.place(x=x, y=y, width=w, height=h)
        e.focus_set()
        e.select_range(0, "end")

        e.bind("<Return>",    self._save_edit)
        e.bind("<Tab>",       self._save_edit)
        e.bind("<FocusOut>",  self._save_edit)
        e.bind("<Escape>",    lambda _: e.place_forget())

    def _save_edit(self, event=None):
        if self._edit_item is None:
            return
        new_val = self._edit_entry.get().strip()
        if new_val == "":
            self._edit_entry.place_forget()
            return
        try:
            int(new_val)
        except ValueError:
            messagebox.showerror("Input Error",
                                 "All fields must be whole numbers.")
            self._edit_entry.focus_set()
            return

        vals = list(self._tree.item(self._edit_item, "values"))
        vals[self._edit_col] = new_val
        self._tree.item(self._edit_item, values=vals)
        self._edit_entry.place_forget()
        self._edit_item = None

    # ── Row helpers ───────────────────────────────────────────────
    def _next_pid(self) -> int:
        items = self._tree.get_children()
        if not items:
            return 1
        last = self._tree.item(items[-1], "values")
        return int(last[0]) + 1

    def add_row(self):
        pid = self._next_pid()
        self._tree.insert("", "end", values=(pid, 0, 1, 0))
        self._n_var.set(len(self._tree.get_children()))

    def remove_row(self):
        sel = self._tree.selection()
        if sel:
            self._tree.delete(sel[0])
        else:
            items = self._tree.get_children()
            if items:
                self._tree.delete(items[-1])
        self._n_var.set(len(self._tree.get_children()))

    def clear_rows(self):
        if messagebox.askyesno("Clear", "Remove all processes?"):
            for item in self._tree.get_children():
                self._tree.delete(item)
            self._n_var.set(0)

    def generate_random(self):
        """Replace the table with n randomly generated processes."""
        n = self._n_var.get()
        if n < 1:
            n = 5
            self._n_var.set(5)
        for item in self._tree.get_children():
            self._tree.delete(item)
        for pid in range(1, n + 1):
            at  = random.randint(0, 10)
            bt  = random.randint(1, 10)
            pri = random.randint(1, 5)
            self._tree.insert("", "end", values=(pid, at, bt, pri))

    # ── File I/O ──────────────────────────────────────────────────
    def load_from_file(self):
        """Load processes from a text file (n then pid at bt priority per line)."""
        path = filedialog.askopenfilename(
            title="Open process file",
            initialdir=os.path.join(_ROOT, "input"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path) as f:
                lines = [l.strip() for l in f if l.strip()]
            n = int(lines[0])
            rows = []
            for i in range(1, n + 1):
                parts = lines[i].split()
                if len(parts) < 4:
                    raise ValueError(f"Line {i+1} needs 4 values")
                rows.append(tuple(int(x) for x in parts[:4]))

            for item in self._tree.get_children():
                self._tree.delete(item)
            for row in rows:
                self._tree.insert("", "end", values=row)
            self._n_var.set(n)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def save_to_file(self):
        """Save current table to a text file in the same format."""
        procs = self.get_processes()
        if not procs:
            messagebox.showwarning("Nothing to save", "Add some processes first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save process file",
            initialdir=os.path.join(_ROOT, "input"),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                f.write(f"{len(procs)}\n")
                for p in procs:
                    f.write(f"{p['pid']} {p['at']} {p['bt']} {p['priority']}\n")
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ── Default data ──────────────────────────────────────────────
    def _populate_defaults(self):
        defaults = [
            (1, 0, 8, 2), (2, 1, 4, 1),
            (3, 2, 9, 3), (4, 3, 5, 2), (5, 4, 2, 4),
        ]
        for row in defaults:
            self._tree.insert("", "end", values=row)

    # ── Public API ────────────────────────────────────────────────
    def get_processes(self) -> list[dict]:
        """Return list of process dicts; raise ValueError on bad data."""
        procs = []
        for item in self._tree.get_children():
            vals = self._tree.item(item, "values")
            try:
                pid = int(vals[0])
                at  = int(vals[1])
                bt  = int(vals[2])
                pri = int(vals[3])
            except (ValueError, IndexError):
                raise ValueError("All fields must be whole numbers.")
            if bt <= 0:
                raise ValueError(f"P{pid}: Burst time must be > 0.")
            if at < 0:
                raise ValueError(f"P{pid}: Arrival time cannot be negative.")
            procs.append({"pid": pid, "at": at, "bt": bt, "priority": pri})
        return procs


# ═══════════════════════════════════════════════════════════════════
class ControlBar(ttk.LabelFrame):
    """Algorithm selector, quantum spinbox, and Run button."""

    ALGOS = ["FCFS", "SJF", "SRTF", "Priority_NP", "Priority_P", "RR"]

    def __init__(self, parent, on_run, on_compare, **kw):
        super().__init__(parent, text="Controls", **kw)
        self._on_run     = on_run
        self._on_compare = on_compare
        self._build()

    def _build(self):
        self._algo_var    = tk.StringVar(value="FCFS")
        self._quantum_var = tk.IntVar(value=2)

        ttk.Label(self, text="Algorithm:").pack(side="left", padx=(8, 2))
        cb = ttk.Combobox(self, textvariable=self._algo_var,
                          values=self.ALGOS, state="readonly", width=14)
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        ttk.Label(self, text="Time Quantum:").pack(side="left", padx=(12, 2))
        self._q_spin = ttk.Spinbox(self, from_=1, to=100,
                                   textvariable=self._quantum_var,
                                   width=5, state="disabled")
        self._q_spin.pack(side="left", padx=4)

        self._run_btn = ttk.Button(self, text="▶  Run",
                                   command=self._on_run, width=10)
        self._run_btn.pack(side="left", padx=16)

        ttk.Button(self, text="⇄  Compare All",
                   command=self._on_compare, width=14).pack(side="left", padx=4)

        # Progress bar
        self._progress_var = tk.DoubleVar()
        self._progress = ttk.Progressbar(self, mode="determinate",
                                         variable=self._progress_var,
                                         maximum=100, length=180)
        self._progress.pack(side="right", padx=(4, 8))

    def _on_algo_change(self, _event=None):
        state = "normal" if self._algo_var.get() == "RR" else "disabled"
        self._q_spin.configure(state=state)

    # ── Public ────────────────────────────────────────────────────
    @property
    def algo(self) -> str:
        return self._algo_var.get()

    @property
    def quantum(self) -> int:
        return self._quantum_var.get()

    def set_running(self, running: bool):
        self._run_btn.configure(state="disabled" if running else "normal")

    def set_progress(self, pct: float):
        self._progress_var.set(pct)


# ═══════════════════════════════════════════════════════════════════
class EmbeddedChart(ttk.Frame):
    """Matplotlib canvas with navigation toolbar that resizes with the window."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._canvas   = None
        self._toolbar  = None
        self._fig      = None
        self._resize_id = None
        self.bind("<Configure>", self._on_resize)

    def show_figure(self, fig):
        """Replace the current figure with a new one."""
        if self._canvas:
            self._toolbar.destroy()
            self._canvas.get_tk_widget().destroy()
        self._fig     = fig
        self._canvas  = FigureCanvasTkAgg(fig, master=self)
        self._toolbar = NavigationToolbar2Tk(self._canvas, self)
        self._toolbar.pack(side="bottom", fill="x")
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas.draw_idle()

    def _on_resize(self, event):
        """Debounced resize: update the figure size to match the widget."""
        if self._fig is None or self._canvas is None:
            return
        # Debounce – only act 120 ms after the last resize event
        if self._resize_id:
            self.after_cancel(self._resize_id)
        self._resize_id = self.after(120, self._do_resize, event.width, event.height)

    def _do_resize(self, w_px, h_px):
        self._resize_id = None
        if self._fig is None or w_px < 50 or h_px < 50:
            return
        dpi   = self._fig.get_dpi()
        new_w = w_px / dpi
        new_h = (h_px - 32) / dpi   # subtract toolbar height (~32 px)
        # Keep the figure's original height if the widget is taller
        orig_w, orig_h = self._fig.get_size_inches()
        # Don't shrink below the figure's natural height
        new_h = max(new_h, orig_h * 0.6)
        self._fig.set_size_inches(new_w, orig_h, forward=False)
        self._canvas.draw_idle()


# ═══════════════════════════════════════════════════════════════════
class ResultsTable(ttk.Frame):
    """Process results treeview + export buttons."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._build()

    def _build(self):
        cols = HEADERS
        self._tree = ttk.Treeview(self, columns=cols,
                                  show="headings", selectmode="none")
        for col in cols:
            self._tree.heading(col, text=col,
                               command=lambda c=col: self._sort(c, False))
            self._tree.column(col, width=100, anchor="center")

        vsb = ttk.Scrollbar(self, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill="x", padx=6, pady=4)
        ttk.Button(btn_bar, text="Export CSV",
                   command=self._export_csv).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Export JSON Report",
                   command=self._export_json).pack(side="left", padx=4)

    def _sort(self, col, reverse):
        items = [(self._tree.set(k, col), k)
                 for k in self._tree.get_children("")]
        try:
            items.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            items.sort(reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)
        self._tree.heading(col,
                           command=lambda: self._sort(col, not reverse))

    def refresh(self):
        if not os.path.exists(OUTPUT_JSON):
            return
        for item in self._tree.get_children():
            self._tree.delete(item)
        _, rows = get_table_data(OUTPUT_JSON)
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", values=row, tags=(tag,))
        self._tree.tag_configure("even", background="#f5f5f5")
        self._tree.tag_configure("odd",  background="#ffffff")

    def _export_csv(self):
        if not os.path.exists(OUTPUT_JSON):
            messagebox.showwarning("No Data", "Run a simulation first."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialdir=os.path.join(_ROOT, "output"),
            initialfile="results.csv")
        if path:
            try:
                export_csv(out=path)
                messagebox.showinfo("Exported", f"Saved to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def _export_json(self):
        if not os.path.exists(OUTPUT_JSON):
            messagebox.showwarning("No Data", "Run a simulation first."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=os.path.join(_ROOT, "output"),
            initialfile="report.json")
        if path:
            try:
                export_report(out=path)
                messagebox.showinfo("Exported", f"Saved to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))


# ═══════════════════════════════════════════════════════════════════
class StatusBar(ttk.Frame):
    """Single-line status message at the bottom of the window."""

    def __init__(self, parent, **kw):
        super().__init__(parent, relief="sunken", **kw)
        self._var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self._var,
                  anchor="w").pack(fill="x", padx=6)

    def set(self, msg: str):
        self._var.set(msg)


# ═══════════════════════════════════════════════════════════════════
class SchedulerGUI:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CPU Scheduling Simulator")
        root.geometry("1200x820")
        root.minsize(900, 600)
        self._build()
        self._try_build_c_on_startup()

    def _build(self):
        # Input panel
        self._input = ProcessInputFrame(self.root)
        self._input.pack(fill="x", padx=10, pady=(8, 4))

        # Controls
        self._ctrl = ControlBar(self.root,
                                on_run=self._on_run,
                                on_compare=self._on_compare)
        self._ctrl.pack(fill="x", padx=10, pady=4)

        # Results notebook
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=4)

        # Tab 1 – Gantt chart
        self._gantt_frame = EmbeddedChart(nb)
        nb.add(self._gantt_frame, text="  📊 Gantt Chart  ")

        # Tab 2 – Process table
        self._table = ResultsTable(nb)
        nb.add(self._table, text="  📋 Process Table  ")

        # Tab 3 – Comparison
        self._compare_frame = EmbeddedChart(nb)
        nb.add(self._compare_frame, text="  ⇄ Compare All  ")

        # Status bar
        self._status = StatusBar(self.root)
        self._status.pack(fill="x", side="bottom")

    # ── Startup build ─────────────────────────────────────────────
    def _try_build_c_on_startup(self):
        def _task():
            try:
                build_c()
                self.root.after(0, lambda: self._status.set(
                    "Scheduler binary ready."))
            except FileNotFoundError:
                msg = (
                    "gcc not found on PATH.\n\n"
                    "Windows: install MinGW-w64 from https://winlibs.com\n"
                    "  → extract zip → add its bin\\ folder to your PATH\n"
                    "  → restart this application.\n\n"
                    "Linux/macOS:  sudo apt install gcc   or   brew install gcc"
                )
                self.root.after(0, lambda: messagebox.showerror("gcc not found", msg))
                self.root.after(0, lambda: self._status.set(
                    "⚠ gcc not found — install MinGW-w64 and add to PATH."))
            except RuntimeError as e:
                self.root.after(0, lambda: messagebox.showerror("Build Error", str(e)))
                self.root.after(0, lambda: self._status.set(
                    "⚠ Build failed — see error dialog."))
        threading.Thread(target=_task, daemon=True).start()

    # ── Run single algorithm ──────────────────────────────────────
    def _on_run(self):
        try:
            procs = self._input.get_processes()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
        if not procs:
            messagebox.showerror("Input Error", "Add at least one process.")
            return

        algo    = self._ctrl.algo
        quantum = self._ctrl.quantum if algo == "RR" else None

        if algo == "RR" and (quantum is None or quantum <= 0):
            messagebox.showerror("Input Error",
                                 "Time Quantum must be > 0 for Round Robin.")
            return

        self._ctrl.set_running(True)
        self._ctrl.set_progress(0)
        self._status.set(f"Running {algo}…")

        def _task():
            t0 = time.time()
            try:
                build_c()
                run_scheduler(algo, procs, quantum)
                elapsed = time.time() - t0
                self.root.after(0, lambda: self._ctrl.set_progress(100))
                self.root.after(0, lambda: self._gantt_frame.show_figure(
                    get_figure(OUTPUT_JSON)[0]))
                self.root.after(0, self._table.refresh)
                self.root.after(0, lambda: self._status.set(
                    f"✓ {algo} completed in {elapsed:.2f}s"))
            except FileNotFoundError:
                self.root.after(0, lambda: messagebox.showerror(
                    "gcc not found",
                    "gcc was not found on PATH.\n\n"
                    "Windows: install MinGW-w64 from https://winlibs.com\n"
                    "and add its bin\\ folder to PATH, then restart."))
                self.root.after(0, lambda: self._status.set("⚠ gcc not found."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self._status.set("Error – see dialog."))
            finally:
                self.root.after(0, lambda: self._ctrl.set_running(False))

        threading.Thread(target=_task, daemon=True).start()

    # ── Compare all algorithms ────────────────────────────────────
    def _on_compare(self):
        try:
            procs = self._input.get_processes()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
        if not procs:
            messagebox.showerror("Input Error", "Add at least one process.")
            return

        quantum = self._ctrl.quantum
        if quantum <= 0:
            messagebox.showerror("Input Error",
                                 "Time Quantum must be > 0 (used for RR in comparison).")
            return

        self._ctrl.set_running(True)
        self._ctrl.set_progress(0)
        self._status.set("Comparing all algorithms…")

        def _task():
            t0 = time.time()
            try:
                build_c()
                total = 6  # number of algorithms

                def _cb(current, _total):
                    pct = (current / _total) * 100
                    self.root.after(0, lambda p=pct: self._ctrl.set_progress(p))
                    self.root.after(0, lambda c=current: self._status.set(
                        f"Ran {c}/{_total} algorithms…"))

                results = compare_all(procs, quantum, progress_callback=_cb)
                fig     = plot_comparison(results)
                elapsed = time.time() - t0
                self.root.after(0, lambda: self._compare_frame.show_figure(fig))
                self.root.after(0, lambda: self._status.set(
                    f"✓ Comparison done in {elapsed:.2f}s"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self._status.set("Error – see dialog."))
            finally:
                self.root.after(0, lambda: self._ctrl.set_running(False))

        threading.Thread(target=_task, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = SchedulerGUI(root)
    root.mainloop()
