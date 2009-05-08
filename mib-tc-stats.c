#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <libgen.h>
#include <netlink/route/class.h>
#include <netlink/route/link.h>

static const char *mib_prefix = ".1.3.6.1.4.1.27934.2.2";
static char *prog;
static int found;

static struct mib {
    char *mib_suffix;
    char *name;
    char *id;
} mibv[] = {
    { "1", "default", "01:02" },
    { "2", "orion", "01:03" },
    { "3", "campus", "01:04" },
};

static int mibc = sizeof(mibv)/sizeof(*mibv);

static int mib_match(const char *arg, const char *mib_suffix) {
    if (strlen(arg) < strlen(mib_prefix) + 1)
        return 0;
    if (strncmp(arg, mib_prefix, strlen(mib_prefix)))
        return 0;
    return !strcmp(arg + strlen(mib_prefix) + 1, mib_suffix);
}

static int mib_find(const char *arg) {
    int i;
    for (i = 0; i < mibc; i++) {
        if (mib_match(arg, mibv[i].mib_suffix))
                return i;
    }
    return -1;
}

static struct nl_handle *nl_handle;

static void dump_class_stats(struct nl_object *obj, void *arg)
{
    struct mib *mib = arg;
    struct rtnl_class *class = (struct rtnl_class *)obj;
    uint32_t handle = rtnl_class_get_handle(class);
//    uint64_t rate = rtnl_class_get_stat(class, RTNL_TC_RATE_BPS);
    uint64_t bytes = rtnl_class_get_stat(class, RTNL_TC_BYTES);
    char id[32];

    rtnl_tc_handle2str(handle, id, sizeof(id));

    if (strcmp(id, mib->id))
        return;

    fprintf(stdout, "%s.%s\ncounter\n%ld\n", mib_prefix, mib->mib_suffix, bytes);
    found = 1;
}

void die(const char *message) {
    fprintf(stderr, "fatal: %s\n", message);
    exit(1);
}

static void usage(void) {
    fprintf(stderr, "usage: %s [-g | -n] %s[.X]\n", prog, mib_prefix);
    exit(2);
}

int main(int argc, char *argv[]) {
    struct nl_cache *link_cache, *class_cache;
    struct rtnl_link *eth;
    int ifindex, mibindex;

    prog = basename(argv[0]);

    if (argc < 2)
        usage();

    mibindex = mib_find(argv[2]);

    if (!strcmp(argv[1], "-n")) {
        if (mibindex < 0) {
            if (!strcmp(argv[2], mib_prefix))
                mibindex = 0;
        } else if (mibindex == mibc - 1) {
            exit(0);
        } else {
            mibindex++;
        }
    } else if (strcmp(argv[1], "-g")) {
        usage();
    }

    if (mibindex < 0 || mibindex >= mibc)
        die("invalid mib");

    nl_handle = nl_handle_alloc();
    if (!nl_handle)
        die("unable to allocate handle");

    if (nl_connect(nl_handle, NETLINK_ROUTE) < 0)
        die("unable to connect to netlink");

    link_cache = rtnl_link_alloc_cache(nl_handle);
    if (!link_cache)
        die("unable to allocate link cache");
//    nl_cache_mgmt_provide(link_cache);

    eth = rtnl_link_get_by_name(link_cache, "eth0");
    if (!eth)
        die("unable to acquire eth0");
    ifindex = rtnl_link_get_ifindex(eth);

    class_cache = rtnl_class_alloc_cache(nl_handle, ifindex);
    if (!class_cache)
        die("unable to allocate class cache");

    nl_cache_foreach(class_cache, dump_class_stats, &mibv[mibindex]);

    if (!found)
        die("class not found");

    rtnl_link_put(eth);
    nl_cache_free(class_cache);
    nl_cache_free(link_cache);
    nl_close(nl_handle);
    nl_handle_destroy(nl_handle);
    return 0;
}
