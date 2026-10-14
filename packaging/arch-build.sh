#!/usr/bin/env bash
# Build the same runtime as the Ubuntu package with Arch toolchain inputs.
set -Eeuo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
export UURB_ARCH_BUILD=1
export UURB_WINE_BIN="${UURB_WINE_BIN:-/opt/uuway/wine-11.0/bin}"
export UURB_WINE_HEADERS="${UURB_WINE_HEADERS:-/usr/include/wine}"
export UURB_CUDA_INCLUDE="${UURB_CUDA_INCLUDE:-/opt/cuda/include}"
export UURB_PIPEWIRE_HEADERS=/usr/include
export UURB_GLSLANG="$(command -v glslangValidator)"
export LIBRARY_PATH="/opt/cuda/lib64/stubs${LIBRARY_PATH:+:$LIBRARY_PATH}"

[[ "$("$UURB_WINE_BIN/wine" --version)" == wine-11.0 ]] || {
    printf 'GPU server protocol 930 requires Wine 11.0; system Wine may be newer.\n' >&2
    exit 1
}
[[ -f "$UURB_CUDA_INCLUDE/cuda.h" && -f /opt/cuda/lib64/stubs/libcuda.so ]] || {
    printf 'Missing system CUDA headers and driver link stub in /opt/cuda.\n' >&2
    exit 1
}
for script in build-dxvk-capture build-dxgi-capture-probe build-uu-native-bootstrap \
              build-uu-native-input build-uu-native-display build-native-ime \
              build-helpers build-pipewire-probe; do
    printf '\n-- %s\n' "$script"
    bash "scripts/$script.sh"
done
