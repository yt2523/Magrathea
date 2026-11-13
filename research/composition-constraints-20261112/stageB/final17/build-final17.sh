#!/bin/bash
set -euo pipefail
cd /mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/stageB/source
out=/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/stageB
/usr/bin/timeout 180 make -B -j2 >"$out/final17-build.stdout.log" 2>"$out/final17-build.stderr.log"
objs=()
for object in src/*.o; do if [ "$object" != src/main.o ]; then objs+=("$object"); fi; done
for pair in native_hhe_control_audit:native_audit native_water_audit:native_water_audit; do
 src=${pair%%:*}; dst=${pair##*:}
 /usr/bin/timeout 90 g++ -std=c++11 -O3 -Wall -I. -Isrc "tests/$src.cpp" "${objs[@]}" -lgsl -lgslcblas -lm -o "$dst" >"$out/final17-$dst-build.stdout.log" 2>"$out/final17-$dst-build.stderr.log"
done
printf 'PASS final17 fresh build and two scientific audit tools\n'
