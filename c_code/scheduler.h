#ifndef SCHEDULER_H
#define SCHEDULER_H

#define MAX_PROCESSES  100
#define MAX_GANTT     2000   // max Gantt segments (preemptive algos fragment heavily)
#define OUTPUT_PATH   "output/output.json"

typedef struct {
    int pid;
    int at;          // Arrival Time
    int bt;          // Burst Time  (original, never modified)
    int priority;    // Lower number = higher priority
    int ct;          // Completion Time
    int tat;         // Turnaround Time = ct - at
    int wt;          // Waiting Time    = tat - bt
    int rt;          // Response Time   = first_start - at
    int rem_bt;      // Remaining Burst (used by SRTF, Priority-P, Round Robin)
    int first_start; // Time process first got CPU (-1 until scheduled)
} Process;

typedef struct {
    int pid;     // Process ID (-1 means CPU is IDLE)
    int start;
    int end;
} GanttBlock;

typedef struct {
    char algorithm[64];
    int  time_quantum;          // -1 if not Round Robin
    Process   processes[MAX_PROCESSES];
    int       n;
    GanttBlock gantt[MAX_GANTT];
    int       gantt_len;
    double    avg_waiting;
    double    avg_turnaround;
    int       context_switches;
    double    cpu_utilization;  // percentage
} Result;

void fcfs(Process p[], int n, Result *r);
void sjf(Process p[], int n, Result *r);
void srtf(Process p[], int n, Result *r);
void priority_np(Process p[], int n, Result *r);
void priority_p(Process p[], int n, Result *r);
void round_robin(Process p[], int n, int quantum, Result *r);
void write_json(Result *r);
void parse_args(int argc, char *argv[], char *algo, int *n,
                Process p[], int *quantum);
void read_input_file(const char *path, int *n, Process p[]);

#endif
