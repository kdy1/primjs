#!/usr/bin/env bash
set -eo pipefail
cd "$1"
source tools/envsetup.sh
hab sync . -f
gn gen out/gungraun --args='is_debug=false target_cpu="x64" target_os="linux" symbol_level=2 enable_primjs_snapshot=false enable_compatible_mm=false enable_tracing_gc=false'
ninja -C out/gungraun qjs_exe
cp out/gungraun/qjs "$2"
