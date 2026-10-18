"""Independent physical and published-radius checks; Python standard library only."""
from pathlib import Path
import hashlib
import json
import math
import sys


def check_profile(path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        parts = line.split(maxsplit=6)
        if len(parts) == 7:
            rows.append([float(x) for x in parts[:6]])
    assert len(rows) > 50, (path, 'missing profile')
    assert all(math.isfinite(x) for row in rows for x in row)
    assert rows[0][1] == 0 and rows[0][3] == 0
    assert all(row[2] > 0 and row[4] > 0 and row[5] > 0 for row in rows)
    assert all(b[1] >= a[1] - 1e-10 and b[3] >= a[3] - 1e-10
               and b[2] <= a[2] + 1e-5 for a, b in zip(rows, rows[1:]))
    assert abs(rows[-1][3] - 1) < 1e-7
    assert abs(rows[-1][2] - 1e-5) < 1e-9  # 0.1 bar = 1e-5 GPa
    assert abs(rows[-1][5] - 300) < 1e-5
    return rows


def verify(output):
    data = json.loads((output / 'results.json').read_text())
    runs = {r['id']: r for r in data['runs']}
    for run in runs.values():
        assert run['status'] == 0, run
        path = output / run['profile']
        rows = check_profile(path)
        assert abs(rows[-1][1] - run['radius_RE']) < 1e-7
        assert hashlib.sha256(path.read_bytes()).hexdigest() == run['profile_sha256']
        cfg = output / 'configs' / (run['id'] + '.cfg')
        assert hashlib.sha256(cfg.read_bytes()).hexdigest() == run['config_sha256']
        if run['id'].startswith('paper_'):
            phases = {line.split(maxsplit=6)[6] for line in path.read_text().splitlines()[1:]
                      if line.strip()}
            assert phases == {'Fe hcp (Smith)', 'Brg (Oganov)', 'Si PPv (Sakai)'}, phases
    base = runs['paper_baseline']['radius_RE']
    assert abs(base - 0.9668) <= 0.00005, ('outside paper rounding interval', base)
    assert abs(base - runs['paper_repeat']['radius_RE']) < 1e-12
    assert (output / runs['paper_baseline']['profile']).read_bytes() == (
        output / runs['paper_repeat']['profile']).read_bytes()
    assert abs(base - runs['paper_tighter']['radius_RE']) / base < 1e-5
    assert runs['current_default_control']['radius_RE'] > base
    assert (output / 'profiles/paper_original.txt').read_bytes() == (
        output / 'profiles/paper_baseline.txt').read_bytes(), 'diagnostic changed output'
    print(f'PASS: {len(runs)} profiles, boundary/monotonicity/hash/status checks; '
          f'paper rounding interval; repeat; tighter tolerances; original equality. R={base:.12f}')


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / 'results')
