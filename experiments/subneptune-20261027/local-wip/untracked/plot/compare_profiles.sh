#!/usr/bin/env bash
# Ubuntu/WSL entry point; uses installed packages without downloading anything.
set -eu
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
if command -v python3 >/dev/null 2>&1 && python3 -c 'import numpy, matplotlib' >/dev/null 2>&1; then
    exec python3 "$script_dir/compare_profiles.py" "$@"
fi
# Existing Python on this computer; configurable for another machine.
windows_python="${MAGRATHEA_WINDOWS_PYTHON:-/mnt/c/Users/PC/AppData/Local/Programs/Python/Python312/python.exe}"
if [[ -x "$windows_python" ]] && command -v wslpath >/dev/null 2>&1; then
    exec "$windows_python" "$(wslpath -w "$script_dir/compare_profiles.py")" "$@"
fi
printf '%s\n' 'No existing Python with NumPy/Matplotlib found. Use a suitable Python to run plot/compare_profiles.py.' >&2
exit 1
