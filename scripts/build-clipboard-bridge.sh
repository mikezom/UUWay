#!/usr/bin/env bash
set -Eeuo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-$repo_dir/build/helpers}"
mkdir -p "$output_dir"
generated_dir="$repo_dir/build/clipboard-protocol"
mkdir -p "$generated_dir"
protocol="$repo_dir/protocols/ext-data-control-v1.xml"
wayland-scanner client-header "$protocol" "$generated_dir/ext-data-control-v1-client.h"
wayland-scanner private-code "$protocol" "$generated_dir/ext-data-control-v1.c"
cc -std=c11 -O2 -Wall -Wextra -Werror -I "$generated_dir" \
    -o "$output_dir/uu-clipboard-bridge" \
    "$repo_dir/src/uu_clipboard_bridge.c" "$generated_dir/ext-data-control-v1.c" \
    -lX11 -lXfixes $(pkg-config --cflags --libs wayland-client)
