#include "native_capture_timing.h"
#include <assert.h>
#include <math.h>
#include <limits.h>

int main(void)
{
    struct uurb_capture_timing s = {0};
    assert(uurb_capture_timing_fresh(&s, 0));
    assert(!uurb_capture_timing_fresh(&s, -1));
    assert(uurb_capture_timing_fps(&s) == 0);
    uurb_capture_timing_add(&s, 0);
    assert(uurb_capture_timing_fps(&s) == 0);
    for (int i = 1; i <= 60; i++) uurb_capture_timing_add(&s, (int64_t)i * 1000000000 / 60);
    assert(fabs(uurb_capture_timing_fps(&s) - 60.0) < 0.001);
    assert(s.samples == 61 && s.gaps[1] == 60);
    assert(!uurb_capture_timing_fresh(&s, s.last_ns));
    assert(!uurb_capture_timing_fresh(&s, s.last_ns - 1));
    assert(uurb_capture_timing_fresh(&s, s.last_ns + 1));
    uurb_capture_timing_add(&s, s.last_ns);
    uurb_capture_timing_add(&s, INT64_MIN);
    assert(s.invalid == 2 && s.samples == 61 && uurb_capture_timing_fps(&s) == 0);
    s = (struct uurb_capture_timing){0};
    uurb_capture_timing_add(&s, INT64_MAX - 1000000000);
    uurb_capture_timing_add(&s, INT64_MAX);
    assert(uurb_capture_timing_fps(&s) == 1 && s.maximum_gap_ns == 1000000000);
    s = (struct uurb_capture_timing){0};
    for (int i = 0; i <= 40; i++) uurb_capture_timing_add(&s, (int64_t)(i / 2) * 50000000 + (i % 2) * 16666666);
    assert(uurb_capture_timing_fps(&s) == 40);
    assert(s.gaps[1] == 20 && s.gaps[2] == 20);
    s = (struct uurb_capture_timing){0};
    const int64_t kwin_pts[] = {100, 100, 90, 120, 110, 140};
    for (unsigned i = 0; i < sizeof(kwin_pts) / sizeof(kwin_pts[0]); i++)
        if (uurb_capture_timing_fresh(&s, kwin_pts[i])) uurb_capture_timing_add(&s, kwin_pts[i]);
    assert(s.samples == 3 && s.invalid == 0 && s.last_ns == 140);
    return 0;
}
