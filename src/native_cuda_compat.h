#ifndef UURB_NATIVE_CUDA_COMPAT_H
#define UURB_NATIVE_CUDA_COMPAT_H
#include <cuda.h>

static inline CUresult uurb_cu_ctx_create(CUcontext *context, CUdevice device)
{
#if CUDA_VERSION >= 13030
    return cuCtxCreate(context, NULL, 0, device);
#else
    return cuCtxCreate(context, 0, device);
#endif
}

#endif
