import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import os
import time

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from main import build_c, run_scheduler
from visualize import get_figure
from table import get_table_data
from export import export_csv, export_report
from compare import compare_all, plot_comparison

class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.build_input_panel()
        self.build_controls()
        self.build_results_notebook()
        
    def build_input_panel(self):
        frame = ttk.LabelFrame(self.root, text="Input Panel")
        frame.pack(fill='x', padx=10, pady=5)
        
        top_ctrl = ttk.Frame(frame)
        top_ctrl.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(top_ctrl, text="Number of Processes:").pack(side='left')
        self.n_var = tk.IntVar(value=5)
        self.n_spin = ttk.Spinbox(top_ctrl, from_=1, to=20, textvariable=self.n_var, width=5, command=self.update_table_rows)
        self.n_spin.pack(side='left', padx=5)
        
        ttk.Button(top_ctrl, text="Add Row", command=self.add_row).pack(side='left', padx=5)
        ttk.Button(top_ctrl, text="Remove Row", command=self.remove_row).pack(side='left', padx=5)
        
        columns = ('PID', 'Arrival Time', 'Burst Time', 'Priority')
        self.tree_input = ttk.Treeview(frame, columns=columns, show='headings', height=6)
        for col in columns:
            self.tree_input.heading(col, text=col)
            self.tree_input.column(col, width=100, anchor='center')
        self.tree_input.pack(fill='x', padx=5, pady=5)
        
        self.tree_input.bind('<Double-1>', self.on_double_click)
        
        # Default data
        default_data = [
            (1, 0, 8, 2),
            (2, 1, 4, 1),
            (3, 2, 9, 3),
            (4, 3, 5, 2),
            (5, 4, 2, 4)
        ]
        for row in default_data:
            self.tree_input.insert('', 'end', values=row)
            
    def update_table_rows(self):
        n = self.n_var.get()
        items = self.tree_input.get_children()
        if len(items) < n:
            for i in range(len(items) + 1, n + 1):
                self.tree_input.insert('', 'end', values=(i, 0, 1, 0))
        elif len(items) > n:
            for item in items[n:]:
                self.tree_input.delete(item)

    def add_row(self):
        self.n_var.set(self.n_var.get() + 1)
        self.update_table_rows()

    def remove_row(self):
        if self.n_var.get() > 1:
            self.n_var.set(self.n_var.get() - 1)
            self.update_table_rows()

    def on_double_click(self, event):
        item = self.tree_input.selection()[0]
        column = self.tree_input.identify_column(event.x)
        col_idx = int(column.replace('#', '')) - 1
        if col_idx == 0: return # PID auto
        
        x, y, width, height = self.tree_input.bbox(item, column)
        value = self.tree_input.item(item, 'values')[col_idx]
        
        entry = ttk.Entry(self.tree_input)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, value)
        entry.focus()
        
        def save_edit(event):
            new_val = entry.get()
            values = list(self.tree_input.item(item, 'values'))
            values[col_idx] = new_val
            self.tree_input.item(item, values=values)
            entry.destroy()
            
        entry.bind('<Return>', save_edit)
        entry.bind('<FocusOut>', save_edit)

    def build_controls(self):
        frame = ttk.LabelFrame(self.root, text="Controls")
        frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(frame, text="Algorithm:").pack(side='left', padx=5)
        self.algo_var = tk.StringVar(value="FCFS")
        self.algo_cb = ttk.Combobox(frame, textvariable=self.algo_var, values=["FCFS", "SJF", "SRTF", "Priority_NP", "Priority_P", "RR"], state="readonly")
        self.algo_cb.pack(side='left', padx=5)
        self.algo_cb.bind('<<ComboboxSelected>>', self.on_algo_change)
        
        ttk.Label(frame, text="Time Quantum:").pack(side='left', padx=5)
        self.quantum_var = tk.IntVar(value=2)
        self.quantum_spin = ttk.Spinbox(frame, from_=1, to=100, textvariable=self.quantum_var, width=5, state='disabled')
        self.quantum_spin.pack(side='left', padx=5)
        
        self.run_btn = ttk.Button(frame, text="RUN", command=self.on_run)
        self.run_btn.pack(side='left', padx=20)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(frame, mode='determinate', variable=self.progress_var, maximum=100)
        self.progress.pack(side='left', fill='x', expand=True, padx=10)
        
        self.progress_label = ttk.Label(frame, text="", width=40)
        self.progress_label.pack(side='left', padx=5)

    def update_progress(self, current, total, start_time):
        percentage = (current / total) * 100
        self.progress_var.set(percentage)
        
        elapsed = time.time() - start_time
        if current > 0 and current < total:
            avg_time = elapsed / current
            time_left = avg_time * (total - current)
            self.progress_label.config(text=f"{percentage:.1f}% | Elapsed: {elapsed:.1f}s | Left: {time_left:.1f}s")
        elif current == total:
            self.progress_label.config(text=f"100% | Total time: {elapsed:.1f}s")
        else:
            self.progress_label.config(text=f"{percentage:.1f}%")

    def build_results_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Gantt Chart")
        self.canvas_widget = None
        
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Process Table")
        
        columns = ('PID', 'Arrival', 'Burst', 'Completion', 'Waiting', 'Turnaround', 'Response')
        self.tree_res = ttk.Treeview(self.tab2, columns=columns, show='headings')
        for col in columns:
            self.tree_res.heading(col, text=col)
            self.tree_res.column(col, width=100, anchor='center')
        self.tree_res.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(self.tab2)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Export CSV", command=lambda: self.export_data('csv')).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Export JSON Report", command=lambda: self.export_data('json')).pack(side='left', padx=5)
        
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Compare")
        ttk.Button(self.tab3, text="Run All Algorithms & Compare", command=self.run_compare).pack(pady=10)
        self.compare_canvas_widget = None

    def on_algo_change(self, event):
        if self.algo_var.get() == "RR":
            self.quantum_spin.config(state='normal')
        else:
            self.quantum_spin.config(state='disabled')

    def on_run(self):
        processes = []
        for item in self.tree_input.get_children():
            vals = self.tree_input.item(item, 'values')
            try:
                bt = int(vals[2])
                if bt <= 0:
                    messagebox.showerror("Input Error", "Burst time must be greater than 0.")
                    return
                processes.append({
                    'pid': int(vals[0]),
                    'at': int(vals[1]),
                    'bt': bt,
                    'priority': int(vals[3])
                })
            except ValueError:
                messagebox.showerror("Input Error", "All fields must be integers.")
                return
                
        if not processes:
            messagebox.showerror("Input Error", "Please add at least one process.")
            return
            
        algo = self.algo_var.get()
        quantum = self.quantum_var.get() if algo == "RR" else None
        
        if algo == "RR" and quantum <= 0:
            messagebox.showerror("Input Error", "Quantum must be greater than 0.")
            return
        
        self.progress_var.set(0)
        self.progress_label.config(text="Starting...")
        self.run_btn.config(state='disabled')
        
        def task():
            start_time = time.time()
            try:
                build_c()
                self.root.after(0, lambda: self.update_progress(1, 2, start_time))
                run_scheduler(algo, len(processes), processes, quantum)
                self.root.after(0, lambda: self.update_progress(2, 2, start_time))
                self.root.after(0, self.refresh_gantt)
                self.root.after(0, self.refresh_table)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.run_btn.config(state='normal'))
                
        threading.Thread(target=task).start()

    def refresh_gantt(self):
        if not os.path.exists('output/output.json'): return
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()
        fig, _ = get_figure('output/output.json')
        self.canvas_widget = FigureCanvasTkAgg(fig, master=self.tab1)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill='both', expand=True)

    def refresh_table(self):
        if not os.path.exists('output/output.json'): return
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
        _, rows = get_table_data('output/output.json')
        for row in rows:
            self.tree_res.insert('', 'end', values=row)

    def export_data(self, fmt):
        if not os.path.exists('output/output.json'):
            messagebox.showwarning("Warning", "No data to export. Run simulation first.")
            return
        try:
            if fmt == 'csv':
                export_csv()
                messagebox.showinfo("Success", "Exported to output/results.csv")
            else:
                export_report()
                messagebox.showinfo("Success", "Exported to output/report.json")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def run_compare(self):
        processes = []
        for item in self.tree_input.get_children():
            vals = self.tree_input.item(item, 'values')
            try:
                bt = int(vals[2])
                if bt <= 0:
                    messagebox.showerror("Input Error", "Burst time must be greater than 0.")
                    return
                processes.append({
                    'pid': int(vals[0]),
                    'at': int(vals[1]),
                    'bt': bt,
                    'priority': int(vals[3])
                })
            except ValueError:
                messagebox.showerror("Input Error", "All fields must be integers.")
                return
                
        if not processes:
            messagebox.showerror("Input Error", "Please add at least one process.")
            return
                
        quantum = self.quantum_var.get()
        
        if quantum <= 0:
            messagebox.showerror("Input Error", "Quantum must be greater than 0 for Round Robin.")
            return
        
        self.progress_var.set(0)
        self.progress_label.config(text="Starting comparison...")
        self.run_btn.config(state='disabled')
        
        def task():
            start_time = time.time()
            try:
                build_c()
                def progress_cb(current, total):
                    self.root.after(0, lambda c=current, t=total: self.update_progress(c, t, start_time))
                
                results = compare_all(processes, quantum, progress_callback=progress_cb)
                self.root.after(0, lambda: self.show_compare_chart(results))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.run_btn.config(state='normal'))
                
        threading.Thread(target=task).start()
        
    def show_compare_chart(self, results):
        if self.compare_canvas_widget:
            self.compare_canvas_widget.get_tk_widget().destroy()
        fig = plot_comparison(results)
        self.compare_canvas_widget = FigureCanvasTkAgg(fig, master=self.tab3)
        self.compare_canvas_widget.draw()
        self.compare_canvas_widget.get_tk_widget().pack(fill='both', expand=True)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('CPU Scheduling Simulator')
    root.geometry('1100x750')
    app = SchedulerGUI(root)
    root.mainloop()
