import subprocess
import sys
import os
import argparse
from visualize import show_gantt
from table import show_table

def build_c():
    """Compile scheduler.c using gcc. Exit on failure."""
    os.makedirs('output', exist_ok=True)
    r = subprocess.run(
        ['gcc', '-Wall', '-O2', 'c_code/scheduler.c', '-o', 'c_code/scheduler'],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print('Build failed:\n', r.stderr, file=sys.stderr)
        sys.exit(1)

def run_scheduler(algo, n, processes, quantum=None):
    """Build the argument list and call the C binary."""
    args = ['./c_code/scheduler', '--algo', algo, '--n', str(n)]
    for p in processes:
        args += ['--pid', str(p['pid']), '--at', str(p['at']),
                 '--bt', str(p['bt']), '--priority', str(p.get('priority', 0))]
    if quantum: 
        args += ['--quantum', str(quantum)]
    subprocess.run(args, check=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--algo', type=str, required=True)
    parser.add_argument('--file', type=str)
    parser.add_argument('--quantum', type=int)
    args, unknown = parser.parse_known_args()
    
    build_c()
    
    if args.file:
        cmd = ['./c_code/scheduler', '--file', args.file, '--algo', args.algo]
        if args.quantum:
            cmd += ['--quantum', str(args.quantum)]
        subprocess.run(cmd, check=True)
    else:
        # Parse processes from unknown args if needed, but usually we run via GUI
        pass
        
    show_table()
    show_gantt()
