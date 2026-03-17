CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11
TARGET  = scheduler

SRCS = common.c fcfs.c sjf.c srtf.c priority_np.c priority_p.c round_robin.c
OBJS = $(SRCS:.c=.o)

.PHONY: all clean rebuild

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c scheduler.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

rebuild: clean all
