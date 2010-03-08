LDFLAGS := -lnl $(shell net-snmp-config --base-agent-libs)
CFLAGS := -g3 -O2 -Wall

all: mirror-stats csc-snmp-subagent

mirror-stats: mirror-stats.o mirror-nl-glue.o

csc-snmp-subagent: csc-snmp-subagent.o mirror-mib.o mirror-nl-glue.o

clean:
	rm -f *.o mirror-stats csc-snmp-subagent
