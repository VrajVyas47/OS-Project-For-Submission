/*
 * fcfs.c – First-Come, First-Served (non-preemptive)
 */

#include <stdlib.h>
#include <string.h>
#include "scheduler.h"

void fcfs(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);

    int time = 0;
    r->gantt_len = 0;

    for (int i = 0; i < n; i++) {
        if (time < p[i].at) {
            add_gantt(r, -1, time, p[i].at);   /* idle gap */
            time = p[i].at;
        }

        p[i].first_start = time;
        add_gantt(r, p[i].pid, time, time + p[i].bt);
        time       += p[i].bt;
        p[i].ct    = time;
        p[i].tat   = p[i].ct  - p[i].at;
        p[i].wt    = p[i].tat - p[i].bt;
        p[i].rt    = p[i].first_start - p[i].at;
    }

    memcpy(r->processes, p, n * sizeof(Process));
    r->n            = n;
    r->time_quantum = -1;
    strcpy(r->algorithm, "FCFS");
    calculate_metrics(r);
}
