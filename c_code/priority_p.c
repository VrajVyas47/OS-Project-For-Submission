#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void priority_p(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);
    for (int i = 0; i < n; i++) {
        p[i].rem_bt = p[i].bt;
        p[i].first_start = -1;
    }
    
    int current_time = 0;
    int completed = 0;
    r->gantt_len = 0;
    int prev_idx = -1;
    
    while (completed < n) {
        int idx = -1;
        int min_priority = INT_MAX;
        for (int i = 0; i < n; i++) {
            if (p[i].at <= current_time && p[i].rem_bt > 0) {
                if (p[i].priority < min_priority) {
                    min_priority = p[i].priority;
                    idx = i;
                } else if (p[i].priority == min_priority) {
                    if (idx == -1) idx = i;
                    else if (prev_idx == i) idx = i; // Do not preempt if equal
                    else if (prev_idx != idx && p[i].at < p[idx].at) idx = i;
                    else if (prev_idx != idx && p[i].at == p[idx].at && p[i].pid < p[idx].pid) idx = i;
                }
            }
        }
        
        if (idx != -1) {
            if (p[idx].first_start == -1) {
                p[idx].first_start = current_time;
            }
            
            int next_arrival = INT_MAX;
            for (int i = 0; i < n; i++) {
                if (p[i].at > current_time && p[i].at < next_arrival) {
                    next_arrival = p[i].at;
                }
            }
            
            int run_time = p[idx].rem_bt;
            if (next_arrival != INT_MAX && (next_arrival - current_time) < run_time) {
                run_time = next_arrival - current_time;
            }
            
            add_gantt(r, p[idx].pid, current_time, current_time + run_time);
            p[idx].rem_bt -= run_time;
            current_time += run_time;
            
            if (p[idx].rem_bt == 0) {
                p[idx].ct = current_time;
                p[idx].tat = p[idx].ct - p[idx].at;
                p[idx].wt = p[idx].tat - p[idx].bt;
                p[idx].rt = p[idx].first_start - p[idx].at;
                completed++;
            }
            prev_idx = idx;
        } else {
            int next_at = INT_MAX;
            for (int i = 0; i < n; i++) {
                if (p[i].rem_bt > 0 && p[i].at < next_at) {
                    next_at = p[i].at;
                }
            }
            add_gantt(r, -1, current_time, next_at);
            current_time = next_at;
            prev_idx = -1;
        }
    }
    
    memcpy(r->processes, p, n * sizeof(Process));
    r->n = n;
    strcpy(r->algorithm, "Priority_P");
    r->time_quantum = -1;
    calculate_metrics(r);
}
