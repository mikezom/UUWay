#!/usr/bin/env bash
set -Eeuo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
stage="$repo_dir/build/native-presenter"
mkdir -p "$stage"
cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC $(pkg-config --cflags json-c) \
  -c "$repo_dir/src/native_display_client.c" -o "$stage/native_display_client.o"
"${UURB_WINE_BIN:-/opt/wine-stable/bin}/winegcc" -m64 -shared -std=c11 -O2 -Wall -Wextra -Werror \
  -I "${UURB_WINE_HEADERS:-$repo_dir/build/gpu-relay/wine-dev/usr/include/wine}" \
  -I "${UURB_WINE_HEADERS:-$repo_dir/build/gpu-relay/wine-dev/usr/include/wine}/windows" \
  -o "$stage/uurb-native-display.dll" "$repo_dir/src/uu_native_display.spec" \
  "$repo_dir/src/uu_native_display.c" "$stage/native_display_client.o" $(pkg-config --libs json-c)
x86_64-w64-mingw32-gcc -std=c11 -O2 -Wall -Wextra -Werror -shared \
  -o "$stage/uurb-native-display-loader.dll" "$repo_dir/src/uu_native_display_loader.c"
