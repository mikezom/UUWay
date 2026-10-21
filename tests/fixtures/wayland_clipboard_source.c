#define _GNU_SOURCE
#include <wayland-client.h>
#include "ext-data-control-v1-client.h"
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static struct wl_seat *seat;
static struct ext_data_control_manager_v1 *manager;
static int count;
static char **formats;

static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version)
{
    (void)data;
    (void)version;
    if (strcmp(interface, "wl_seat") == 0 && seat == NULL)
        seat = wl_registry_bind(registry, name, &wl_seat_interface, 1);
    if (strcmp(interface, "ext_data_control_manager_v1") == 0)
        manager = wl_registry_bind(registry, name, &ext_data_control_manager_v1_interface, 1);
}

static void removed(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {.global = global, .global_remove = removed};

static void send_data(void *data, struct ext_data_control_source_v1 *source, const char *mime, int fd)
{
    (void)data;
    (void)source;
    for (int index = 0; index < count; index += 2) {
        if (strcmp(formats[index], mime) != 0)
            continue;
        /* Keep the source event loop responsive while a slow reader waits. */
        if (fork() == 0) {
            int input = open(formats[index + 1], O_RDONLY);
            char buffer[16384];
            ssize_t size;
            const char *delay = getenv("UURB_TEST_SEND_DELAY_MS");

            if (delay != NULL)
                usleep((unsigned int)atoi(delay) * 1000);
            while (input >= 0 && (size = read(input, buffer, sizeof(buffer))) > 0) {
                ssize_t written = 0;
                while (written < size) {
                    ssize_t result = write(fd, buffer + written, (size_t)(size - written));
                    if (result < 0 && errno == EINTR)
                        continue;
                    if (result <= 0)
                        _exit(0);
                    written += result;
                }
            }
            _exit(0);
        }
        break;
    }
    close(fd);
}

static void cancelled(void *data, struct ext_data_control_source_v1 *source)
{
    (void)data;
    ext_data_control_source_v1_destroy(source);
}

static const struct ext_data_control_source_v1_listener source_listener = {
    .send = send_data, .cancelled = cancelled,
};

static void offered_mime(void *data, struct ext_data_control_offer_v1 *offer, const char *mime)
{
    (void)data;
    (void)offer;
    (void)mime;
}

static const struct ext_data_control_offer_v1_listener offer_listener = {.offer = offered_mime};

static void data_offer(void *data, struct ext_data_control_device_v1 *device,
                       struct ext_data_control_offer_v1 *offer)
{
    (void)data;
    (void)device;
    ext_data_control_offer_v1_add_listener(offer, &offer_listener, NULL);
}

static void selection(void *data, struct ext_data_control_device_v1 *device,
                      struct ext_data_control_offer_v1 *offer)
{
    (void)data;
    (void)device;
    if (offer != NULL)
        ext_data_control_offer_v1_destroy(offer);
}

static void finished(void *data, struct ext_data_control_device_v1 *device)
{
    (void)data;
    (void)device;
}

static const struct ext_data_control_device_v1_listener device_listener = {
    .data_offer = data_offer, .selection = selection, .finished = finished,
    .primary_selection = selection,
};

int main(int argc, char **argv)
{
    struct wl_display *display = wl_display_connect(NULL);
    struct wl_registry *registry;
    struct ext_data_control_device_v1 *device;
    struct ext_data_control_source_v1 *source;

    if (display == NULL || argc < 3 || argc % 2 != 1)
        return 2;
    signal(SIGCHLD, SIG_IGN);
    signal(SIGPIPE, SIG_IGN);
    count = argc - 1;
    formats = argv + 1;
    registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    if (wl_display_roundtrip(display) < 0 || manager == NULL || seat == NULL)
        return 3;
    device = ext_data_control_manager_v1_get_data_device(manager, seat);
    ext_data_control_device_v1_add_listener(device, &device_listener, NULL);
    source = ext_data_control_manager_v1_create_data_source(manager);
    ext_data_control_source_v1_add_listener(source, &source_listener, NULL);
    for (int index = 0; index < count; index += 2)
        ext_data_control_source_v1_offer(source, formats[index]);
    ext_data_control_device_v1_set_selection(device, source);
    if (wl_display_roundtrip(display) < 0)
        return 4;
    puts("ready");
    fflush(stdout);
    while (wl_display_dispatch(display) >= 0) {}
    return 0;
}
