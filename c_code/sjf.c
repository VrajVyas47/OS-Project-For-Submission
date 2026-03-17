/*
 * sjf.c – Shortest-Job-First (non-preemptive)
 *
 * Tie-breaking: shorter arrival time first, then lower PID.
 */

#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void sjf(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);

    int time      = 0;
    int completed = 0;
    int done[MAX_PROCESSES] = {0};
    r->gantt_len  = 0;

    while (completed < n) {
        int idx     = -1;
        int min_bt  = INT_MAX;

        for (int i = 0; i < n; i++) {
            if (done[i] || p[i].at > time) continue;
            if (p[i].bt < min_bt ||
               (p[i].bt == min_bt && p[i].at < p[idx].at) ||
               (p[i].bt == min_bt && p[i].at == p[idx].at && p[i].pid < p[idx].pid)) {
                min_bt = p[i].bt;
                idx    = i;
            }
        }

        if (idx == -1) {
            /* No process ready – jump to next arrival */
            int next = INT_MAX;
            for (int i = 0; i < n; i++)
                if (!done[i] && p[i].at < next) next = p[i].at;
            add_gantt(r, -1, time, next);
            time = next;
            continue;
        }

        p[idx].first_start = time;
        add_gantt(r, p[idx].pid, time, time + p[idx].bt);
        time         += p[idx].bt;
        p[idx].ct    = time;
        p[idx].tat   = p[idx].ct  - p[idx].at;
        p[idx].wt    = p[idx].tat - p[idx].bt;
        p[idx].rt    = p[idx].first_start - p[idx].at;
        done[idx]    = 1;
        completed++;
    }

    memcpy(r->processes, p, n * sizeof(Process));
    r->n            = n;
    r->time_quantum = -1;
    strcpy(r->algorithm, "SJF");
    calculate_metrics(r);
}
