import os
import re

c_code_dir = 'c_code'
scheduler_c = os.path.join(c_code_dir, 'scheduler.c')

with open(scheduler_c, 'r') as f:
    content = f.read()

# We will extract functions using regex.

def extract_function(name, text):
    # This is a bit tricky, let's just find the start and end by matching braces.
    pattern = r'(void\s+' + name + r'\s*\([^)]*\)\s*\{)'
    match = re.search(pattern, text)
    if not match:
         return ""
    start = match.start()
    
    brace_count = 0
    in_string = False
    in_char = False
    i = match.end() - 1
    
    while i < len(text):
        if text[i] == '"' and not in_char and (i == 0 or text[i-1] != '\\'):
            in_string = not in_string
        elif text[i] == "'" and not in_string and (i == 0 or text[i-1] != '\\'):
            in_char = not in_char
        
        if not in_string and not in_char:
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i+1]
        i += 1
    return ""

algos = ['fcfs', 'sjf', 'srtf', 'priority_np', 'priority_p', 'round_robin']

for algo in algos:
    func_code = extract_function(algo, content)
    with open(os.path.join(c_code_dir, f'{algo}.c'), 'w') as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <limits.h>\n#include "scheduler.h"\n\n')
        f.write(func_code)
        f.write('\n')

utils = ['calculate_metrics', 'add_gantt', 'write_json', 'parse_args', 'read_input_file']
with open(os.path.join(c_code_dir, 'utils.c'), 'w') as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <limits.h>\n#include "scheduler.h"\n\n')
        
        # also copy compare_at_pid
        cmppid = re.search(r'int compare_at_pid\([^)]*\)\s*\{[\s\S]*?\}', content).group(0)
        f.write(cmppid + '\n\n')
        
        for u in utils:
            func_code = extract_function(u, content)
            f.write(func_code + '\n\n')

# Now main.c
main_code = re.search(r'int main\([^)]*\)\s*\{[\s\S]*', content).group(0)
with open(os.path.join(c_code_dir, 'main.c'), 'w') as f:
    f.write('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <limits.h>\n#include "scheduler.h"\n\n')
    f.write(main_code)
    
os.remove(scheduler_c)

# Update Makefile
makefile = """all: scheduler

scheduler: main.c utils.c fcfs.c sjf.c srtf.c priority_np.c priority_p.c round_robin.c hrrn.c ljf.c lrtf.c
\tgcc -Wall -O2 -o scheduler main.c utils.c fcfs.c sjf.c srtf.c priority_np.c priority_p.c round_robin.c hrrn.c ljf.c lrtf.c

clean:
\trm -f scheduler
"""
with open(os.path.join(c_code_dir, 'Makefile'), 'w') as f:
    f.write(makefile)

