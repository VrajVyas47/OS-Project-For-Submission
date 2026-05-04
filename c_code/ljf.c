#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void ljf(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);
    int current_time = 0;
    int completed = 0;
    int is_completed[MAX_PROCESSES] = {0};
    r->gantt_len = 0;
    
    while (completed < n) {
        int idx = -1;
        int max_bt = -1;
        for (int i = 0; i < n; i++) {
            if (p[i].at <= current_time && !is_completed[i]) {
                if (p[i].bt > max_bt) {
                    max_bt = p[i].bt;
                    idx = i;
                } else if (p[i].bt == max_bt) {
                    if (p[i].at < p[idx].at) {
                        idx = i;
                    } else if (p[i].at == p[idx].at && p[i].pid < p[idx].pid) {
                        idx = i;
                    }
                }
            }
        }
        
        if (idx != -1) {
            p[idx].first_start = current_time;
            add_gantt(r, p[idx].pid, current_time, current_time + p[idx].bt);
            current_time += p[idx].bt;
            p[idx].ct = current_time;
            p[idx].tat = p[idx].ct - p[idx].at;
            p[idx].wt = p[idx].tat - p[idx].bt;
            p[idx].rt = p[idx].first_start - p[idx].at;
            is_completed[idx] = 1;
            completed++;
        } else {
            int next_at = INT_MAX;
            for (int i = 0; i < n; i++) {
                if (!is_completed[i] && p[i].at < next_at) {
                    next_at = p[i].at;
                }
            }
            add_gantt(r, -1, current_time, next_at);
            current_time = next_at;
        }
    }
    
    memcpy(r->processes, p, n * sizeof(Process));
    r->n = n;
    strcpy(r->algorithm, "LJF");
    r->time_quantum = -1;
    calculate_metrics(r);
}
