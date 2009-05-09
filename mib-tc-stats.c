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
#include "mib-tc-stats.h"

static struct nl_cache *link_cache, *class_cache;
static struct rtnl_link *eth;
static int ifindex;

struct class_info cogent_class = { "cogent", "01:02", };
struct class_info orion_class  = { "orion",  "01:03", };
struct class_info campus_class = { "campus", "01:04", };

static struct nl_handle *nl_handle;

void die(const char *message) {
    fprintf(stderr, "fatal: %s\n", message);
    exit(1);
}

static void match_obj(struct nl_object *obj, void *arg) {
    struct nl_object *needle = *(struct nl_object **)arg;
    struct nl_object **ret = (struct nl_object **)arg + 1;

    if (!*ret && nl_object_identical(obj, needle)) {
        nl_object_get(obj);
        *ret = obj;
    }
}

static struct rtnl_class *get_class_by_id(char *id, int ifindex) {
    uint32_t handle;
    struct rtnl_class *needle;
    struct nl_object *magic[2];

    if (rtnl_tc_str2handle(id, &handle))
        die("invalid id");

    needle = rtnl_class_alloc();
    rtnl_class_set_ifindex(needle, ifindex);
    rtnl_class_set_handle(needle, handle);

    magic[0] = (struct nl_object *)needle;
    magic[1] = (struct nl_object *)NULL;

    nl_cache_foreach(class_cache, match_obj, magic);

    rtnl_class_put(needle);
    return (struct rtnl_class *)magic[1];
}

uint64_t get_class_byte_count(struct class_info *info) {
    struct rtnl_class *class = get_class_by_id(info->id, ifindex);
    uint64_t bytes;
    if (!class)
        die("class not found");
    bytes = rtnl_class_get_stat(class, RTNL_TC_BYTES);
    rtnl_class_put(class);
    return bytes;
}

void mirror_stats_refresh(void) {
    nl_cache_refill(nl_handle, class_cache);
}

void mirror_stats_initialize(void) {
    nl_handle = nl_handle_alloc();
    if (!nl_handle)
        die("unable to allocate handle");

    if (nl_connect(nl_handle, NETLINK_ROUTE) < 0)
        die("unable to connect to netlink");

    link_cache = rtnl_link_alloc_cache(nl_handle);
    if (!link_cache)
        die("unable to allocate link cache");

    eth = rtnl_link_get_by_name(link_cache, "eth0");
    if (!eth)
        die("unable to acquire eth0");
    ifindex = rtnl_link_get_ifindex(eth);

    class_cache = rtnl_class_alloc_cache(nl_handle, ifindex);
    if (!class_cache)
        die("unable to allocate class cache");
}

void mirror_stats_cleanup(void) {
    rtnl_link_put(eth);
    nl_cache_free(class_cache);
    nl_cache_free(link_cache);
    nl_close(nl_handle);
    nl_handle_destroy(nl_handle);
}

