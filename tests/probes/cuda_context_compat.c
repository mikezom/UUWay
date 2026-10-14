#include "native_cuda_compat.h"
#include <stdio.h>

int main(void)
{
    CUdevice device;
    CUcontext context, popped;
    if (cuInit(0) != CUDA_SUCCESS || cuDeviceGet(&device, 0) != CUDA_SUCCESS ||
        uurb_cu_ctx_create(&context, device) != CUDA_SUCCESS) {
        fputs("CUDA context creation failed\n", stderr);
        return 1;
    }
    if (cuCtxPopCurrent(&popped) != CUDA_SUCCESS || popped != context ||
        cuCtxDestroy(context) != CUDA_SUCCESS) {
        fputs("CUDA context cleanup failed\n", stderr);
        return 1;
    }
    puts("CUDA context API works");
    return 0;
}
