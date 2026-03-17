/*
 * round_robin.c – Round-Robin Scheduling
 *
 * Uses a circular FIFO queue.  Newly arrived processes are enqueued
 * after the current time-slice completes (standard UNIX-style RR).
 */

#include <stdlib.h>
#include <string.h>
#include "scheduler.h"

void round_robin(Process p[], int n, int quantum, Result *r) {
    qsort(p, n, sizeof(Process), compare_at_pid);

    for (int i = 0; i < n; i++) {
        p[i].rem_bt      = p[i].bt;
        p[i].first_start = -1;
    }

    int time      = 0;
    int completed = 0;
    r->gantt_len  = 0;

    /* Circular queue */
    int queue[MAX_PROCESSES * 2];
    int head = 0, tail = 0, count = 0;
    int in_queue[MAX_PROCESSES] = {0};

    /* Enqueue all processes that arrive at time 0 */
    int next_idx = 0;
    while (next_idx < n && p[next_idx].at <= time) {
        queue[tail++ % (MAX_PROCESSES * 2)] = next_idx;
        in_queue[next_idx] = 1;
        count++;
        next_idx++;
    }

    while (completed < n) {
        if (count == 0) {
            /* CPU idle – jump to next arrival */
            if (next_idx < n) {
                add_gantt(r, -1, time, p[next_idx].at);
                time = p[next_idx].at;
                while (next_idx < n && p[next_idx].at <= time) {
                    queue[tail++ % (MAX_PROCESSES * 2)] = next_idx;
                    in_queue[next_idx] = 1;
                    count++;
                    next_idx++;
                }
            } else {
                break; /* safeguard */
            }
            continue;
        }

        int idx = queue[head++ % (MAX_PROCESSES * 2)];
        count--;

        if (p[idx].first_start == -1) p[idx].first_start = time;

        int run = (p[idx].rem_bt > quantum) ? quantum : p[idx].rem_bt;
        add_gantt(r, p[idx].pid, time, time + run);
        time          += run;
        p[idx].rem_bt -= run;

        /* Enqueue newly arrived processes before re-queueing current */
        while (next_idx < n && p[next_idx].at <= time) {
            if (!in_queue[next_idx]) {
                queue[tail++ % (MAX_PROCESSES * 2)] = next_idx;
                in_queue[next_idx] = 1;
                count++;
            }
            next_idx++;
        }

        if (p[idx].rem_bt == 0) {
            p[idx].ct  = time;
            p[idx].tat = p[idx].ct  - p[idx].at;
            p[idx].wt  = p[idx].tat - p[idx].bt;
            p[idx].rt  = p[idx].first_start - p[idx].at;
            completed++;
        } else {
            queue[tail++ % (MAX_PROCESSES * 2)] = idx;
            count++;
        }
    }

    memcpy(r->processes, p, n * sizeof(Process));
    r->n            = n;
    r->time_quantum = quantum;
    strcpy(r->algorithm, "RR");
    calculate_metrics(r);
}
