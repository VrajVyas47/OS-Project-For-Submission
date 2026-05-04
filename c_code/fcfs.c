#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void fcfs(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);
    int current_time = 0;
    r->gantt_len = 0;
    
    for (int i = 0; i < n; i++) {
        if (current_time < p[i].at) {
            add_gantt(r, -1, current_time, p[i].at);
            current_time = p[i].at;
        }
        p[i].first_start = current_time;
        add_gantt(r, p[i].pid, current_time, current_time + p[i].bt);
        current_time += p[i].bt;
        p[i].ct = current_time;
        p[i].tat = p[i].ct - p[i].at;
        p[i].wt = p[i].tat - p[i].bt;
        p[i].rt = p[i].first_start - p[i].at;
    }
    
    memcpy(r->processes, p, n * sizeof(Process));
    r->n = n;
    strcpy(r->algorithm, "FCFS");
    r->time_quantum = -1;
    calculate_metrics(r);
}
