#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void round_robin(Process p[], int n, int quantum, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);
    for (int i = 0; i < n; i++) {
        p[i].rem_bt = p[i].bt;
        p[i].first_start = -1;
    }
    
    int current_time = 0;
    int completed = 0;
    r->gantt_len = 0;
    
    int queue[MAX_PROCESSES];
    int head = 0, tail = 0, count = 0;
    int in_queue[MAX_PROCESSES] = {0};
    
    int p_idx = 0;
    while (p_idx < n && p[p_idx].at <= current_time) {
        queue[tail] = p_idx;
        tail = (tail + 1) % MAX_PROCESSES;
        count++;
        in_queue[p_idx] = 1;
        p_idx++;
    }
    
    while (completed < n) {
        if (count > 0) {
            int idx = queue[head];
            head = (head + 1) % MAX_PROCESSES;
            count--;
            
            if (p[idx].first_start == -1) {
                p[idx].first_start = current_time;
            }
            
            int run_time = (p[idx].rem_bt > quantum) ? quantum : p[idx].rem_bt;
            add_gantt(r, p[idx].pid, current_time, current_time + run_time);
            current_time += run_time;
            p[idx].rem_bt -= run_time;
            
            while (p_idx < n && p[p_idx].at <= current_time) {
                if (!in_queue[p_idx]) {
                    queue[tail] = p_idx;
                    tail = (tail + 1) % MAX_PROCESSES;
                    count++;
                    in_queue[p_idx] = 1;
                }
                p_idx++;
            }
            
            if (p[idx].rem_bt == 0) {
                p[idx].ct = current_time;
                p[idx].tat = p[idx].ct - p[idx].at;
                p[idx].wt = p[idx].tat - p[idx].bt;
                p[idx].rt = p[idx].first_start - p[idx].at;
                completed++;
            } else {
                queue[tail] = idx;
                tail = (tail + 1) % MAX_PROCESSES;
                count++;
            }
        } else {
            if (p_idx < n) {
                add_gantt(r, -1, current_time, p[p_idx].at);
                current_time = p[p_idx].at;
                while (p_idx < n && p[p_idx].at <= current_time) {
                    if (!in_queue[p_idx]) {
                        queue[tail] = p_idx;
                        tail = (tail + 1) % MAX_PROCESSES;
                        count++;
                        in_queue[p_idx] = 1;
                    }
                    p_idx++;
                }
            } else {
                // Failsafe to prevent infinite loop if a process is lost
                break;
            }
        }
    }
    
    memcpy(r->processes, p, n * sizeof(Process));
    r->n = n;
    strcpy(r->algorithm, "RR");
    r->time_quantum = quantum;
    calculate_metrics(r);
}
