/*
 * srtf.c – Shortest-Remaining-Time-First (preemptive SJF)
 *
 * Tie-breaking on equal remaining burst: keep the running process
 * (no unnecessary preemption).  Among newly arrived ties use lower PID.
 */

#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

void srtf(Process p[], int n, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);

    for (int i = 0; i < n; i++) {
        p[i].rem_bt      = p[i].bt;
        p[i].first_start = -1;
    }

    int time      = 0;
    int completed = 0;
    int prev      = -1;
    r->gantt_len  = 0;

    while (completed < n) {
        int idx     = -1;
        int min_rem = INT_MAX;

        for (int i = 0; i < n; i++) {
            if (p[i].at > time || p[i].rem_bt == 0) continue;
            if (p[i].rem_bt < min_rem) {
                min_rem = p[i].rem_bt;
                idx     = i;
            } else if (p[i].rem_bt == min_rem) {
                /* Prefer currently running to avoid pointless switches */
                if (prev == i) { idx = i; }
                else if (prev != idx && p[i].pid < p[idx].pid) { idx = i; }
            }
        }

        if (idx == -1) {
            int next = INT_MAX;
            for (int i = 0; i < n; i++)
                if (p[i].rem_bt > 0 && p[i].at < next) next = p[i].at;
            add_gantt(r, -1, time, next);
            time = next;
            prev = -1;
            continue;
        }

        if (p[idx].first_start == -1) p[idx].first_start = time;

        /* Run until the next arrival or completion, whichever is sooner */
        int next_arr = INT_MAX;
        for (int i = 0; i < n; i++)
            if (p[i].at > time && p[i].at < next_arr) next_arr = p[i].at;

        int run = p[idx].rem_bt;
        if (next_arr != INT_MAX && (next_arr - time) < run)
            run = next_arr - time;

        add_gantt(r, p[idx].pid, time, time + run);
        p[idx].rem_bt -= run;
        time          += run;

        if (p[idx].rem_bt == 0) {
            p[idx].ct  = time;
            p[idx].tat = p[idx].ct  - p[idx].at;
            p[idx].wt  = p[idx].tat - p[idx].bt;
            p[idx].rt  = p[idx].first_start - p[idx].at;
            completed++;
        }
        prev = idx;
    }

    memcpy(r->processes, p, n * sizeof(Process));
    r->n            = n;
    r->time_quantum = -1;
    strcpy(r->algorithm, "SRTF");
    calculate_metrics(r);
}
