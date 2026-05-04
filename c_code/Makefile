all: scheduler

OBJS = scheduler.o fcfs.o sjf.o srtf.o priority_np.o priority_p.o round_robin.o hrrn.o ljf.o lrtf.o

scheduler: $(OBJS)
	gcc -Wall -O2 -o scheduler $(OBJS)

%.o: %.c scheduler.h
	gcc -Wall -O2 -c $< -o $@

clean:
	rm -f scheduler *.o
