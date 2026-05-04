import subprocess
import sys
import os
import argparse
from visualize import show_gantt
from table import show_table

def build_c():
    """Compile using gcc to support Windows without make. Exit on failure."""
    os.makedirs('output', exist_ok=True)
    import glob
    c_files = glob.glob('c_code/*.c')
    
    # On Windows, we append .exe to the output file to be safe, but gcc usually does it.
    exe_name = 'c_code/scheduler.exe' if os.name == 'nt' else 'c_code/scheduler'
    
    cmd = ['gcc', '-Wall', '-O2'] + c_files + ['-o', exe_name]
    
    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print('Build failed:\n', r.stderr, file=sys.stderr)
            raise Exception(f"Build failed:\n{r.stderr}")
    except FileNotFoundError:
        raise Exception("gcc compiler not found. Please ensure gcc is installed and in your system PATH.")

def run_scheduler(algo, n, processes, quantum=None):
    """Build the argument list and call the C binary."""
    exe_name = './c_code/scheduler.exe' if os.name == 'nt' else './c_code/scheduler'
    args = [exe_name, '--algo', algo, '--n', str(n)]
    for p in processes:
        args += ['--pid', str(p['pid']), '--at', str(p['at']),
                 '--bt', str(p['bt']), '--priority', str(p.get('priority', 0))]
    if quantum: 
        args += ['--quantum', str(quantum)]
    
    # Capture output to give helpful error messages
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise Exception(f"Scheduler execution failed!\nCommand: {' '.join(args)}\nError: {r.stderr}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--algo', type=str, required=True)
    parser.add_argument('--file', type=str)
    parser.add_argument('--quantum', type=int)
    args, unknown = parser.parse_known_args()
    
    build_c()
    
    if args.file:
        exe_name = './c_code/scheduler.exe' if os.name == 'nt' else './c_code/scheduler'
        cmd = [exe_name, '--file', args.file, '--algo', args.algo]
        if args.quantum:
            cmd += ['--quantum', str(args.quantum)]
        subprocess.run(cmd, check=True)
    else:
        # Parse processes from unknown args if needed, but usually we run via GUI
        pass
        
    show_table()
    show_gantt()
