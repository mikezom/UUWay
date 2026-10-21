#include "native_key_normalize.h"
#include "uu_native_input_translate.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    static const struct { unsigned vk, scan, key; } keypad[] = {
        {0x60, 0x52, KEY_KP0}, {0x61, 0x4f, KEY_KP1},
        {0x62, 0x50, KEY_KP2}, {0x63, 0x51, KEY_KP3},
        {0x64, 0x4b, KEY_KP4}, {0x65, 0x4c, KEY_KP5},
        {0x66, 0x4d, KEY_KP6}, {0x67, 0x47, KEY_KP7},
        {0x68, 0x48, KEY_KP8}, {0x69, 0x49, KEY_KP9},
        {0x6a, 0x37, KEY_KPASTERISK}, {0x6b, 0x4e, KEY_KPPLUS},
        {0x6d, 0x4a, KEY_KPMINUS}, {0x6e, 0x53, KEY_KPDOT},
        {0x6f, 0x35, KEY_KPSLASH}, {0x90, 0x45, KEY_NUMLOCK},
    };
    for (unsigned i = 0; i < sizeof(keypad) / sizeof(keypad[0]); ++i)
        for (unsigned up = 0; up < 2; ++up)
            for (unsigned mapped = 0; mapped < 3; ++mapped) {
                uint32_t scan = mapped == 0 ? 0 : mapped == 1 ? keypad[i].scan : 0xe000 | keypad[i].scan;
                uint32_t flags = (up ? UURB_KEYEVENTF_KEYUP : 0) | UURB_KEYEVENTF_EXTENDED;
                assert(uurb_native_key_normalize(keypad[i].vk, &scan, &flags));
                assert(scan == keypad[i].scan);
                assert(!!(flags & UURB_KEYEVENTF_EXTENDED) == (keypad[i].vk == 0x6f));
                uurb_x11_input_event in = {.type = UURB_X11_INPUT_KEYBOARD,
                    .virtual_key = keypad[i].vk, .scan_code = scan, .flags = flags};
                struct uurb_native_events out;
                assert(uurb_native_translate(&in, &out));
                assert(out.keyboard && out.count == 2);
                assert(out.events[0].code == keypad[i].key && out.events[0].value == !up);
            }
    for (unsigned up = 0; up < 2; ++up) {
        uint32_t scan = 0x1e, flags = UURB_KEYEVENTF_SCANCODE | (up ? UURB_KEYEVENTF_KEYUP : 0);
        assert(uurb_native_key_normalize(0x61, &scan, &flags));
        assert(scan == 0x1e && flags == (UURB_KEYEVENTF_SCANCODE | (up ? UURB_KEYEVENTF_KEYUP : 0)));
        scan = 0xe01c;
        assert(uurb_native_key_normalize(0, &scan, &flags));
        assert(scan == 0x1c && (flags & UURB_KEYEVENTF_EXTENDED));
        scan = 0xe045;
        assert(uurb_native_key_normalize(0, &scan, &flags));
        assert(scan == 0x45 && !(flags & UURB_KEYEVENTF_EXTENDED));
        for (unsigned side = 0; side < 2; ++side) {
            scan = 0; flags = up ? UURB_KEYEVENTF_KEYUP : 0;
            assert(uurb_native_key_normalize(0x5b + side, &scan, &flags));
            assert(scan == 0x5b + side && (flags & UURB_KEYEVENTF_EXTENDED));
        }
    }
    uint32_t scan = 0, flags = 0;
    assert(!uurb_native_key_normalize(0xff, &scan, &flags));
    scan = 0x1e;
    assert(uurb_native_key_normalize('A', &scan, &flags) && scan == 0x1e && flags == 0);
    puts("native keypad normalization checks passed");
    return 0;
}
