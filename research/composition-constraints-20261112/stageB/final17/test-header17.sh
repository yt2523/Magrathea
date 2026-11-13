#!/bin/bash
set -euo pipefail
cd /mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/stageB/source
out=/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/stageB
for item in base edge barrier; do
 case "$item" in
 base) src=fixed-test-radius-bracket.cpp; flag=-DUSE_DOMAIN_BRACKET;;
 edge) src=fixed-test-radius-extra.cpp; flag=;;
 barrier) src=fixed-test-radius-barrier.cpp; flag=;;
 esac
 /usr/bin/timeout 60 g++ -std=c++11 -Isrc $flag "$out/$src" -o "$out/header17-$item" 2>"$out/header17-$item-build.stderr.log"
 /usr/bin/timeout 5 "$out/header17-$item" >"$out/header17-$item.stdout.log" 2>"$out/header17-$item.stderr.log"
 printf 'PASS header17-%s\n' "$item"
done
/usr/bin/timeout 5 "$out/header17-barrier" --tiny >"$out/header17-tiny.stdout.log" 2>"$out/header17-tiny.stderr.log"
printf 'PASS header17 tiny interval terminates\n'
