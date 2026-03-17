/*
 * common.c – shared utilities, JSON output, argument parsing, and main().
 *
 * Each scheduler algorithm lives in its own file (fcfs.c, sjf.c, …).
 * Only touch this file for I/O, metrics, or the dispatch table.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

/* ── Sorting helper ──────────────────────────────────────────────── */

int compare_at_pid(const void *a, const void *b) {
    const Process *p1 = (const Process *)a;
    const Process *p2 = (const Process *)b;
    if (p1->at != p2->at) return p1->at - p2->at;
    return p1->pid - p2->pid;
}

/* ── Gantt chart helper ──────────────────────────────────────────── */

void add_gantt(Result *r, int pid, int start, int end) {
    if (start == end) return;

    /* Merge consecutive blocks with the same PID */
    if (r->gantt_len > 0 &&
        r->gantt[r->gantt_len - 1].pid == pid &&
        r->gantt[r->gantt_len - 1].end == start) {
        r->gantt[r->gantt_len - 1].end = end;
        return;
    }

    if (r->gantt_len >= MAX_GANTT) {
        fprintf(stderr, "Warning: Gantt chart limit (%d) exceeded.\n", MAX_GANTT);
        return;
    }

    r->gantt[r->gantt_len].pid   = pid;
    r->gantt[r->gantt_len].start = start;
    r->gantt[r->gantt_len].end   = end;
    r->gantt_len++;
}

/* ── Metrics calculation ─────────────────────────────────────────── */

void calculate_metrics(Result *r) {
    int total_wt  = 0;
    int total_tat = 0;
    int active    = 0;
    int total_time = 0;

    if (r->gantt_len > 0)
        total_time = r->gantt[r->gantt_len - 1].end - r->gantt[0].start;

    for (int i = 0; i < r->n; i++) {
        total_wt  += r->processes[i].wt;
        total_tat += r->processes[i].tat;
    }

    r->avg_waiting    = (double)total_wt  / r->n;
    r->avg_turnaround = (double)total_tat / r->n;

    r->context_switches = 0;
    for (int i = 0; i < r->gantt_len; i++) {
        if (r->gantt[i].pid != -1)
            active += r->gantt[i].end - r->gantt[i].start;
        if (i > 0 && r->gantt[i].pid != r->gantt[i - 1].pid)
            r->context_switches++;
    }

    r->cpu_utilization = (total_time > 0)
                         ? ((double)active / total_time) * 100.0
                         : 0.0;
}

/* ── JSON output ─────────────────────────────────────────────────── */

void write_json(Result *r) {
    FILE *f = fopen(OUTPUT_PATH, "w");
    if (!f) {
        fprintf(stderr, "Error: cannot open %s for writing\n", OUTPUT_PATH);
        return;
    }

    fprintf(f, "{\n");
    fprintf(f, "  \"algorithm\": \"%s\",\n", r->algorithm);

    if (r->time_quantum == -1)
        fprintf(f, "  \"time_quantum\": null,\n");
    else
        fprintf(f, "  \"time_quantum\": %d,\n", r->time_quantum);

    fprintf(f, "  \"context_switches\": %d,\n",  r->context_switches);
    fprintf(f, "  \"cpu_utilization\": %.2f,\n",  r->cpu_utilization);
    fprintf(f, "  \"avg_waiting\": %.2f,\n",       r->avg_waiting);
    fprintf(f, "  \"avg_turnaround\": %.2f,\n",    r->avg_turnaround);

    fprintf(f, "  \"processes\": [\n");
    for (int i = 0; i < r->n; i++) {
        fprintf(f,
            "    {\"pid\":%d,\"arrival\":%d,\"burst\":%d,"
            "\"priority\":%d,\"completion\":%d,\"waiting\":%d,"
            "\"turnaround\":%d,\"response\":%d}",
            r->processes[i].pid,  r->processes[i].at,  r->processes[i].bt,
            r->processes[i].priority,
            r->processes[i].ct,   r->processes[i].wt,
            r->processes[i].tat,  r->processes[i].rt);
        fprintf(f, (i < r->n - 1) ? ",\n" : "\n");
    }
    fprintf(f, "  ],\n");

    fprintf(f, "  \"gantt\": [\n");
    for (int i = 0; i < r->gantt_len; i++) {
        fprintf(f, "    {\"pid\":%d,\"start\":%d,\"end\":%d}",
                r->gantt[i].pid, r->gantt[i].start, r->gantt[i].end);
        fprintf(f, (i < r->gantt_len - 1) ? ",\n" : "\n");
    }
    fprintf(f, "  ]\n");
    fprintf(f, "}\n");

    fclose(f);
}

/* ── Input: command-line arguments ──────────────────────────────── */

void parse_args(int argc, char *argv[],
                char *algo, int *n, Process p[], int *quantum) {
    *n      = 0;
    *quantum = -1;
    strcpy(algo, "FCFS");

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--algo") == 0 && i + 1 < argc) {
            strcpy(algo, argv[++i]);
        } else if (strcmp(argv[i], "--quantum") == 0 && i + 1 < argc) {
            *quantum = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--pid") == 0 && i + 1 < argc) {
            int idx = *n;
            p[idx].pid      = atoi(argv[++i]);
            p[idx].priority = 0;

            while (i + 1 < argc && strncmp(argv[i + 1], "--", 2) == 0) {
                if (strcmp(argv[i + 1], "--at") == 0 && i + 2 < argc) {
                    p[idx].at = atoi(argv[i + 2]); i += 2;
                } else if (strcmp(argv[i + 1], "--bt") == 0 && i + 2 < argc) {
                    p[idx].bt = atoi(argv[i + 2]); i += 2;
                } else if (strcmp(argv[i + 1], "--priority") == 0 && i + 2 < argc) {
                    p[idx].priority = atoi(argv[i + 2]); i += 2;
                } else {
                    break;
                }
            }
            (*n)++;
        }
    }
}

/* ── Input: text file ────────────────────────────────────────────── */
/*
 * File format (same as before):
 *   <n>
 *   <pid> <arrival> <burst> <priority>
 *   ...
 */
void read_input_file(const char *path, int *n, Process p[]) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "Error: cannot open %s\n", path); exit(1); }

    if (fscanf(f, "%d", n) != 1) {
        fprintf(stderr, "Error: bad process count in %s\n", path); exit(1);
    }

    for (int i = 0; i < *n; i++) {
        if (fscanf(f, "%d %d %d %d",
                   &p[i].pid, &p[i].at, &p[i].bt, &p[i].priority) != 4) {
            fprintf(stderr, "Error: bad data for process %d\n", i); exit(1);
        }
    }
    fclose(f);
}

/* ── main ────────────────────────────────────────────────────────── */

int main(int argc, char *argv[]) {
    char    algo[64];
    int     n = 0, quantum = -1;
    Process p[MAX_PROCESSES];
    char    file_path[256] = "";

    /* Check for --file flag first */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--file") == 0 && i + 1 < argc) {
            strncpy(file_path, argv[++i], sizeof(file_path) - 1);
        }
    }

    if (file_path[0] != '\0') {
        read_input_file(file_path, &n, p);
        /* Still allow --algo and --quantum from CLI */
        strcpy(algo, "FCFS");
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "--algo") == 0 && i + 1 < argc)
                strcpy(algo, argv[++i]);
            else if (strcmp(argv[i], "--quantum") == 0 && i + 1 < argc)
                quantum = atoi(argv[++i]);
        }
    } else {
        parse_args(argc, argv, algo, &n, p, &quantum);
    }

    if (n <= 0) {
        fprintf(stderr,
            "Usage: scheduler --algo <ALGO> [--quantum <Q>] "
            "--pid <id> --at <t> --bt <t> [--priority <p>] ...\n"
            "    or: scheduler --file <path> --algo <ALGO> [--quantum <Q>]\n");
        return 1;
    }

    /* Validate burst times */
    for (int i = 0; i < n; i++) {
        if (p[i].bt <= 0) {
            fprintf(stderr,
                "Error: process %d has burst time <= 0\n", p[i].pid);
            return 1;
        }
    }

    /* Work on a copy so callers can reuse the original array */
    Process pc[MAX_PROCESSES];
    memcpy(pc, p, n * sizeof(Process));

    Result r;
    memset(&r, 0, sizeof(r));

    if      (strcmp(algo, "FCFS")        == 0) fcfs(pc, n, &r);
    else if (strcmp(algo, "SJF")         == 0) sjf(pc, n, &r);
    else if (strcmp(algo, "SRTF")        == 0) srtf(pc, n, &r);
    else if (strcmp(algo, "Priority_NP") == 0) priority_np(pc, n, &r);
    else if (strcmp(algo, "Priority_P")  == 0) priority_p(pc, n, &r);
    else if (strcmp(algo, "RR")          == 0) {
        if (quantum <= 0) {
            fprintf(stderr, "Error: Round Robin requires --quantum > 0\n");
            return 1;
        }
        round_robin(pc, n, quantum, &r);
    } else {
        fprintf(stderr, "Error: unknown algorithm '%s'\n", algo);
        return 1;
    }

    write_json(&r);
    printf("Done\n");
    return 0;
}
