#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <libgen.h>
#include <netlink/route/class.h>
#include <netlink/route/link.h>
#include <netlink/cache-api.h>
#include <netlink/object.h>

struct class_info {
    char *name;
    char *id;
};

extern struct class_info cogent_class;
extern struct class_info orion_class;
extern struct class_info campus_class;

void mirror_stats_refresh(void);
void mirror_stats_initialize(void);
void mirror_stats_cleanup(void);
void die(const char *);
uint64_t get_class_byte_count(struct class_info *);
