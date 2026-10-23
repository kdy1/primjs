#!/usr/bin/env bash
set -eo pipefail
cd "$1"
source tools/envsetup.sh
hab sync . -f
gn gen out/gungraun --args='is_debug=false target_cpu="x64" target_os="linux" symbol_level=2 enable_primjs_snapshot=false enable_compatible_mm=false enable_tracing_gc=false'
ninja -C out/gungraun qjs_exe
# The normal executable is stripped by the Linux GN toolchain, even with
# symbol_level=2. Measure the matching unstripped executable so Callgrind can
# attribute costs to internal functions and source lines.
binary=out/gungraun/exe.unstripped/qjs
test -s "$binary"
readelf --sections "$binary" | grep '\.debug_info' > /dev/null
cp "$binary" "$2"
