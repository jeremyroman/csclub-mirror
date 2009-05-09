#include "mib-tc-stats.h"

int main(int argc, char *argv[]) {
    mirror_stats_initialize();
    for (;;) {
        printf("%s %"PRIu64"\n", cogent_class.id, get_class_byte_count(&cogent_class));
        printf("%s %"PRIu64"\n", orion_class.id, get_class_byte_count(&orion_class));
        printf("%s %"PRIu64"\n", campus_class.id, get_class_byte_count(&campus_class));
        sleep(1);
        mirror_stats_refresh();
    }
}
