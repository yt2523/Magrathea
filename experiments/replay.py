"""Portable replay of an archived configuration using the unchanged current solver."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'huang2022-fig4'))
from reproduce import diagnostic_build, run_case

parser = argparse.ArgumentParser()
parser.add_argument('suite', choices=['capstone', 'literature-cases'])
parser.add_argument('--case', help='One config stem; omit to replay all configurations')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
assert not output.exists(), 'Use a new output directory to prevent append/overwrite'
configs = Path(__file__).resolve().parent / 'archive/20261018' / args.suite / 'configs'
paths = sorted(configs.glob('*.cfg')) if args.case is None else [configs / (args.case + '.cfg')]
assert paths and all(p.is_file() for p in paths), 'Unknown configuration'
for directory in ['configs', 'profiles', 'logs']:
    (output / directory).mkdir(parents=True)
binary = diagnostic_build(output)
runs = []
for path in paths:
    # Only the output path is rewritten. Historical files remain byte-for-byte intact.
    result = run_case(binary, path.read_text(), output, path.stem, {})
    runs.append(result)
    (output / 'results.json').write_text(json.dumps({'suite': args.suite, 'runs': runs}, indent=2))
    assert result['status'] == 0, result
print('Replay complete. Status 0 does not establish physical validity; read the archive warnings.')
