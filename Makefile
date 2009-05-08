LDFLAGS := -lnl
CFLAGS := -g3 -O2 -Wall

all: mib-tc-stats

clean:
	rm -f mib-tc-stats
