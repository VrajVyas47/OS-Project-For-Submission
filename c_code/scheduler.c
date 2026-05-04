#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "scheduler.h"

int compare_at_pid(const void *a, const void *b) {
    Process *p1 = (Process *)a;
    Process *p2 = (Process *)b;
    if (p1->at != p2->at) return p1->at - p2->at;
    return p1->pid - p2->pid;
}

void calculate_metrics(Result *r) {
    int total_wt = 0;
    int total_tat = 0;
    int total_bt = 0;
    int total_time = 0;
    if (r->gantt_len > 0) {
        total_time = r->gantt[r->gantt_len - 1].end - r->gantt[0].start;
    }
    
    for (int i = 0; i < r->n; i++) {
        total_wt += r->processes[i].wt;
        total_tat += r->processes[i].tat;
        total_bt += r->processes[i].bt;
    }
    
    r->avg_waiting = (double)total_wt / r->n;
    r->avg_turnaround = (double)total_tat / r->n;
    
    int active_time = 0;
    r->context_switches = 0;
    for (int i = 0; i < r->gantt_len; i++) {
        if (r->gantt[i].pid != -1) {
            active_time += (r->gantt[i].end - r->gantt[i].start);
        }
        if (i > 0 && r->gantt[i].pid != r->gantt[i-1].pid) {
            r->context_switches++;
        }
    }
    
    if (total_time > 0) {
        r->cpu_utilization = ((double)active_time / total_time) * 100.0;
    } else {
        r->cpu_utilization = 0.0;
    }
}

void add_gantt(Result *r, int pid, int start, int end) {
    if (start == end) return;
    if (r->gantt_len > 0 && r->gantt[r->gantt_len - 1].pid == pid && r->gantt[r->gantt_len - 1].end == start) {
        r->gantt[r->gantt_len - 1].end = end;
    } else {
        if (r->gantt_len >= MAX_GANTT) {
            fprintf(stderr, "Warning: Maximum Gantt chart length exceeded.\n");
            return;
        }
        r->gantt[r->gantt_len].pid = pid;
        r->gantt[r->gantt_len].start = start;
        r->gantt[r->gantt_len].end = end;
        r->gantt_len++;
    }
}

void write_json(Result *r) {
    FILE *f = fopen(OUTPUT_PATH, "w");
    if (!f) {
        fprintf(stderr, "Error opening %s for writing\n", OUTPUT_PATH);
        return;
    }
    
    fprintf(f, "{\n");
    fprintf(f, "  \"algorithm\": \"%s\",\n", r->algorithm);
    if (r->time_quantum == -1) {
        fprintf(f, "  \"time_quantum\": null,\n");
    } else {
        fprintf(f, "  \"time_quantum\": %d,\n", r->time_quantum);
    }
    fprintf(f, "  \"context_switches\": %d,\n", r->context_switches);
    fprintf(f, "  \"cpu_utilization\": %.2f,\n", r->cpu_utilization);
    fprintf(f, "  \"avg_waiting\": %.2f,\n", r->avg_waiting);
    fprintf(f, "  \"avg_turnaround\": %.2f,\n", r->avg_turnaround);
    
    fprintf(f, "  \"processes\": [\n");
    for (int i = 0; i < r->n; i++) {
        fprintf(f, "    {\"pid\":%d,\"arrival\":%d,\"burst\":%d,\"completion\":%d,\"waiting\":%d,\"turnaround\":%d,\"response\":%d}",
                r->processes[i].pid, r->processes[i].at, r->processes[i].bt,
                r->processes[i].ct, r->processes[i].wt, r->processes[i].tat, r->processes[i].rt);
        if (i < r->n - 1) fprintf(f, ",\n");
        else fprintf(f, "\n");
    }
    fprintf(f, "  ],\n");
    
    fprintf(f, "  \"gantt\": [\n");
    for (int i = 0; i < r->gantt_len; i++) {
        fprintf(f, "    {\"pid\":%d, \"start\":%d, \"end\":%d}",
                r->gantt[i].pid, r->gantt[i].start, r->gantt[i].end);
        if (i < r->gantt_len - 1) fprintf(f, ",\n");
        else fprintf(f, "\n");
    }
    fprintf(f, "  ]\n");
    fprintf(f, "}\n");
    
    fclose(f);
}

void parse_args(int argc, char *argv[], char *algo, int *n, Process p[], int *quantum) {
    int p_count = 0;
    *quantum = -1;
    strcpy(algo, "FCFS");
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--algo") == 0 && i + 1 < argc) {
            strcpy(algo, argv[++i]);
        } else if (strcmp(argv[i], "--n") == 0 && i + 1 < argc) {
            // we will determine n from p_count, but we can consume the arg
            i++;
        } else if (strcmp(argv[i], "--quantum") == 0 && i + 1 < argc) {
            *quantum = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--pid") == 0 && i + 1 < argc) {
            p[p_count].pid = atoi(argv[++i]);
            p[p_count].priority = 0; // default
            
            while (i + 1 < argc && strncmp(argv[i+1], "--", 2) == 0) {
                if (strcmp(argv[i+1], "--at") == 0 && i + 2 < argc) {
                    p[p_count].at = atoi(argv[i+2]);
                    i += 2;
                } else if (strcmp(argv[i+1], "--bt") == 0 && i + 2 < argc) {
                    p[p_count].bt = atoi(argv[i+2]);
                    i += 2;
                } else if (strcmp(argv[i+1], "--priority") == 0 && i + 2 < argc) {
                    p[p_count].priority = atoi(argv[i+2]);
                    i += 2;
                } else {
                    break;
                }
            }
            p_count++;
        }
    }
    *n = p_count;
}

void read_input_file(const char *path, int *n, Process p[]) {
    FILE *f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "Error opening %s\n", path);
        exit(1);
    }
    if (fscanf(f, "%d", n) != 1) {
        fprintf(stderr, "Error reading n\n");
        exit(1);
    }
    for (int i = 0; i < *n; i++) {
        if (fscanf(f, "%d %d %d %d", &p[i].pid, &p[i].at, &p[i].bt, &p[i].priority) != 4) {
            fprintf(stderr, "Error reading process %d\n", i);
            exit(1);
        }
    }
    fclose(f);
}

int main(int argc, char *argv[]) {
    char algo[64];
    int n = 0;
    Process p[MAX_PROCESSES];
    int quantum = -1;
    
    int use_file = 0;
    char file_path[256];
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--file") == 0 && i + 1 < argc) {
            use_file = 1;
            strcpy(file_path, argv[++i]);
        }
    }
    
    if (use_file) {
        read_input_file(file_path, &n, p);
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "--algo") == 0 && i + 1 < argc) {
                strcpy(algo, argv[++i]);
            } else if (strcmp(argv[i], "--quantum") == 0 && i + 1 < argc) {
                quantum = atoi(argv[++i]);
            }
        }
    } else {
        int temp_n = 0;
        parse_args(argc, argv, algo, &temp_n, p, &quantum);
        n = temp_n;
    }
    
    Process p_copy[MAX_PROCESSES];
    memcpy(p_copy, p, n * sizeof(Process));
    
    for (int i = 0; i < n; i++) {
        if (p_copy[i].bt <= 0) {
            fprintf(stderr, "Error: Burst time must be greater than 0 for all processes.\n");
            exit(1);
        }
    }
    
    Result r;
    
    if (strcmp(algo, "FCFS") == 0) {
        fcfs(p_copy, n, &r);
    } else if (strcmp(algo, "SJF") == 0) {
        sjf(p_copy, n, &r);
    } else if (strcmp(algo, "SRTF") == 0) {
        srtf(p_copy, n, &r);
    } else if (strcmp(algo, "Priority_NP") == 0) {
        priority_np(p_copy, n, &r);
    } else if (strcmp(algo, "Priority_P") == 0) {
        priority_p(p_copy, n, &r);
    } else if (strcmp(algo, "RR") == 0) {
        if (quantum <= 0) {
            fprintf(stderr, "Error: Round Robin requires quantum > 0\n");
            exit(1);
        }
        round_robin(p_copy, n, quantum, &r);
    } else if (strcmp(algo, "HRRN") == 0) {
        hrrn(p_copy, n, &r);
    } else if (strcmp(algo, "LJF") == 0) {
        ljf(p_copy, n, &r);
    } else if (strcmp(algo, "LRTF") == 0) {
        lrtf(p_copy, n, &r);
    } else {
        fprintf(stderr, "Unknown algorithm: %s\n", algo);
        exit(1);
    }
    
    write_json(&r);
    printf("Done\n");
    
    return 0;
}
