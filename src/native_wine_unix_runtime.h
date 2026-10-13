#ifndef UURB_NATIVE_WINE_UNIX_RUNTIME_H
#define UURB_NATIVE_WINE_UNIX_RUNTIME_H
#include <dlfcn.h>
#include <link.h>
#include <string.h>

struct uurb_wine_runtime_location {
    const char *path;
    unsigned matches;
};

static int uurb_find_wine_runtime(struct dl_phdr_info *info, size_t size, void *opaque)
{
    (void)size;
    struct uurb_wine_runtime_location *location = opaque;
    const char suffix[] = "/x86_64-unix/ntdll.so";
    size_t length = strlen(info->dlpi_name);
    if (length >= sizeof(suffix) - 1 &&
        !strcmp(info->dlpi_name + length - (sizeof(suffix) - 1), suffix)) {
        location->path = info->dlpi_name;
        location->matches++;
    }
    return 0;
}

static void *uurb_loaded_wine_runtime(void)
{
    struct uurb_wine_runtime_location location = {0};
    dl_iterate_phdr(uurb_find_wine_runtime, &location);
    /* The supervisor pins Wine 11.0. Resolve that process's existing Unix
     * runtime, including a relocated installation; never load another one. */
    return location.matches == 1 ? dlopen(location.path, RTLD_NOW | RTLD_NOLOAD) : NULL;
}
#endif
