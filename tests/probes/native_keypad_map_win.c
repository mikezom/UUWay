#define UURB_NATIVE_INPUT_ONLY
#define wWinMain uurb_fixture_unused_main
#include "../../src/uu_input_broker.c"
#undef wWinMain
#include <assert.h>

int wmain(void)
{
    static const struct { WORD vk, scan; DWORD extended; } keys[] = {
        {VK_NUMPAD0, 0x52, 0}, {VK_NUMPAD1, 0x4f, 0}, {VK_NUMPAD2, 0x50, 0},
        {VK_NUMPAD3, 0x51, 0}, {VK_NUMPAD4, 0x4b, 0}, {VK_NUMPAD5, 0x4c, 0},
        {VK_NUMPAD6, 0x4d, 0}, {VK_NUMPAD7, 0x47, 0}, {VK_NUMPAD8, 0x48, 0},
        {VK_NUMPAD9, 0x49, 0}, {VK_MULTIPLY, 0x37, 0}, {VK_ADD, 0x4e, 0},
        {VK_SUBTRACT, 0x4a, 0}, {VK_DECIMAL, 0x53, 0},
        {VK_DIVIDE, 0x35, KEYEVENTF_EXTENDEDKEY}, {VK_NUMLOCK, 0x45, 0},
    };
    native_only = TRUE;
    for (unsigned i = 0; i < ARRAYSIZE(keys); ++i)
        for (unsigned up = 0; up < 2; ++up) {
            INPUT input = {.type = INPUT_KEYBOARD,
                .ki = {.wVk = keys[i].vk, .dwFlags = up ? KEYEVENTF_KEYUP : 0}};
            uurb_x11_input_event event;
            assert(input_to_x11_event(&input, &event));
            assert(event.scan_code == keys[i].scan && event.virtual_key == keys[i].vk);
            assert(event.flags == (keys[i].extended | input.ki.dwFlags));
        }
    INPUT input = {.type = INPUT_KEYBOARD, .ki = {.wVk = VK_NUMPAD1,
        .wScan = 0x1e, .dwFlags = KEYEVENTF_SCANCODE}};
    uurb_x11_input_event event;
    assert(input_to_x11_event(&input, &event) && event.scan_code == 0x1e);
    input.ki = (KEYBDINPUT){.wScan = 0xe01c, .dwFlags = KEYEVENTF_SCANCODE};
    assert(input_to_x11_event(&input, &event) && event.scan_code == 0x1c &&
           (event.flags & KEYEVENTF_EXTENDEDKEY));
    input.ki = (KEYBDINPUT){.wVk = 0xff};
    assert(!input_to_x11_event(&input, &event));
    printf("UURB_KEYPAD_MAP_PASS cases=32 wine_numpad0_map=%u input_events_sent=0\n",
           MapVirtualKeyW(VK_NUMPAD0, MAPVK_VK_TO_VSC_EX));
    return 0;
}
