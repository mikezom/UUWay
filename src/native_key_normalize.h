#ifndef UURB_NATIVE_KEY_NORMALIZE_H
#define UURB_NATIVE_KEY_NORMALIZE_H
#include "x11_input_protocol.h"
/* Normalize layout-independent keypad/logo keys at the native boundary.
 * Wine/Xvfb can omit keypad digits or the E0 prefix on keypad Divide.
 * Explicit scan codes take precedence over virtual keys. */
static inline int uurb_native_key_normalize(uint32_t virtual_key, uint32_t *scan, uint32_t *flags)
{
    if (!(*flags & UURB_KEYEVENTF_SCANCODE)) {
        static const uint8_t keypad_digits[] = {
            0x52, 0x4f, 0x50, 0x51, 0x4b, 0x4c, 0x4d, 0x47, 0x48, 0x49
        };
        unsigned keypad_scan = 0;
        if (virtual_key >= 0x60 && virtual_key <= 0x69)
            keypad_scan = keypad_digits[virtual_key - 0x60];
        else switch (virtual_key) {
        case 0x6a: keypad_scan = 0x37; break; /* Multiply */
        case 0x6b: keypad_scan = 0x4e; break; /* Add */
        case 0x6d: keypad_scan = 0x4a; break; /* Subtract */
        case 0x6e: keypad_scan = 0x53; break; /* Decimal */
        case 0x6f: keypad_scan = 0xe035; break; /* Divide */
        case 0x90: keypad_scan = 0x45; break; /* Num Lock */
        }
        if (keypad_scan) {
            *scan = keypad_scan;
            *flags &= ~UURB_KEYEVENTF_EXTENDED;
        }
        if (virtual_key == 0x5b || virtual_key == 0x5c) {
            *scan = virtual_key; *flags |= UURB_KEYEVENTF_EXTENDED;
        }
    }
    if ((*scan & 0xff00u) == 0xe000u) {
        *scan &= 0xffu; *flags |= UURB_KEYEVENTF_EXTENDED;
    }
    /* Windows marks Num Lock E0-45; evdev uses the ordinary AT code 45. */
    if (*scan == 0x45) *flags &= ~UURB_KEYEVENTF_EXTENDED;
    if (*scan == 0x5b || *scan == 0x5c) *flags |= UURB_KEYEVENTF_EXTENDED;
    return *scan > 0 && *scan <= 0xff;
}
#endif
