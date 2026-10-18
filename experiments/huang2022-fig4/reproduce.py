"""Run from Ubuntu/WSL: python3 experiments/huang2022-fig4/reproduce.py --output NEW_DIRECTORY."""
from pathlib import Path
import argparse
import csv
import difflib
import hashlib
import json
import platform
import re
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = '4c560f36d2734f6b63ae5118d4074e0c255b59f0'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, output, name, timeout=240):
    start = time.perf_counter()
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    (output / 'logs' / (name + '.log')).write_text(proc.stdout + proc.stderr)
    assert proc.returncode == 0, (name, proc.returncode, 'see logs')
    return proc.stdout, time.perf_counter() - start


def diagnostic_build(output):
    # The repository Makefile does not track header or compiler-flag dependencies.
    command(['make', '-B', '-j4'], output, 'build')
    command(['./planet', '--test'], output, 'builtin-tests')
    build = output / '.build'
    build.mkdir()
    original = (REPO / 'src/main.cpp').read_text()
    needle = '      planet->print(outputfile, false);'
    assert original.count(needle) == 1
    extra = '''      cout << std::setprecision(17);
      cout << "REPRO_STATUS " << planet->getstatus() << endl;
      cout << "REPRO_R_RE " << planet->getRs().back() << endl;
      cout << "REPRO_PC_GPA " << planet->getP(0)/1E10 << endl;
      cout << "REPRO_TC_K " << planet->getT(0) << endl;
      cout << "REPRO_INTERFACES_RE";
      for (double radius : planet->getRs()) cout << ' ' << radius;
      cout << endl;
'''
    modified = original.replace(needle, extra + needle)
    (build / 'main-diagnostic.cpp').write_text(modified)
    (output / 'diagnostic-logging.patch').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), modified.splitlines(True),
        fromfile='original/src/main.cpp', tofile='temporary/main-diagnostic.cpp')))
    command(['g++', '-std=c++0x', '-O3', '-Wall', '-I' + str(REPO / 'src'), '-c',
             str(build / 'main-diagnostic.cpp'), '-o', str(build / 'main-diagnostic.o')],
            output, 'diagnostic-compile')
    objects = sorted(p for p in (REPO / 'src').glob('*.o') if p.name != 'main.o')
    assert len(objects) == 7, objects
    binary = build / 'planet-diagnostic'
    command(['g++', str(build / 'main-diagnostic.o'), *map(str, objects),
             '-lgsl', '-lgslcblas', '-lm', '-o', str(binary)], output, 'diagnostic-link')
    return binary


def config(template, changes):
    for key, value in changes.items():
        template, count = re.subn(r'^' + re.escape(key) + '=.*$',
                                  lambda _: key + '=' + str(value), template, flags=re.M)
        assert count == 1, (key, count)
    return template


def run_case(binary, template, output, name, changes):
    profile = output / 'profiles' / (name + '.txt')
    assert not profile.exists(), 'hydro::print appends: use a fresh output directory'
    cfg = output / 'configs' / (name + '.cfg')
    cfg.write_text(config(template, {'output_file': '"' + str(profile) + '"', **changes}))
    stdout, elapsed = command(['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s',
                               '150s', str(binary), str(cfg)], output, name, timeout=170)
    def field(key):
        match = re.search(r'^REPRO_' + key + r' (.+)$', stdout, re.M)
        assert match, (name, key, 'no result returned')
        return match.group(1)
    result = {'id': name, 'status': int(field('STATUS')), 'radius_RE': float(field('R_RE')),
              'Pc_GPa': float(field('PC_GPA')), 'Tc_K': float(field('TC_K')),
              'interfaces_RE': list(map(float, field('INTERFACES_RE').split())),
              'wall_seconds': elapsed, 'profile': 'profiles/' + profile.name,
              'profile_sha256': digest(profile), 'config_sha256': digest(cfg)}
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory, preferably on D: under /mnt/d; never overwrites prior results')
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists(), 'Output already exists; choose a new directory'
    for subdir in ['logs', 'profiles', 'configs']:
        (output / subdir).mkdir(parents=True)
    plan = {'paper': 'Huang, Rice & Steffen (2022), MNRAS 513, 5256, Fig.4 default',
            'doi': '10.1093/mnras/stac1133', 'reference_radius_RE': 0.9668,
            'reference_rounding_half_width_RE': 0.00005,
            'criterion': 'Within printed 4-decimal rounding interval; no fitting of inputs',
            'source_commit': SOURCE_COMMIT, 'mass_ME': 1, 'core_mass_ME': 0.33,
            'mantle_mass_ME': 0.67, 'T_surface_K': 300, 'P_surface_bar': 0.1,
            'Tgap_K': [0, 0, 0], 'mantle_phasedgm': 'Si_simple',
            'source_version_note': 'Current solver with existing paper-compatible Brg/PPv phase option; not an exact historical build.'}
    (output / 'plan.json').write_text(json.dumps(plan, indent=2))
    binary = diagnostic_build(output)
    template = config((REPO / 'run/mode0.cfg').read_text(), {
        'mass_of_core': 0.33, 'mass_of_mantle': 0.67, 'mass_of_hydro': 0,
        'mass_of_atm': 0, 'surface_temp': 300, 'P_surface': '1E5',
        'temp_jump_1': 0, 'temp_jump_2': 0, 'temp_jump_3': 0,
        'mantle_phasedgm': '"Si_simple"', 'verbose': 'true'})
    original_path = output / 'profiles/paper_original.txt'
    original_cfg = output / 'configs/paper_original.cfg'
    original_cfg.write_text(config(template, {'output_file': '"' + str(original_path) + '"'}))
    command(['./planet', str(original_cfg)], output, 'paper_original')
    cases = [('paper_baseline', {}), ('paper_repeat', {}),
             ('paper_tighter', {'ode_eps_rel1': '1E-11', 'fit_eps_rel': '1E-5'}),
             ('current_default_control', {'mantle_phasedgm': '"Si_default"'})]
    runs = []
    for name, changes in cases:
        runs.append(run_case(binary, template, output, name, changes))
    metadata = {'plan': plan, 'runs': runs, 'environment': platform.platform(),
                'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                'source_sha256': {str(p.relative_to(REPO)): digest(p) for p in
                                  sorted((REPO / 'src').glob('*')) if p.suffix in {'.cpp', '.h'}},
                'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                'gsl': subprocess.check_output(['gsl-config', '--version'], text=True).strip()}
    (output / 'results.json').write_text(json.dumps(metadata, indent=2))
    with (output / 'comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['case', 'radius_RE', 'paper_RE', 'delta_RE', 'delta_percent', 'status'])
        for r in runs:
            delta = r['radius_RE'] - plan['reference_radius_RE']
            writer.writerow([r['id'], r['radius_RE'], 0.9668, delta, 100 * delta / 0.9668, r['status']])
    # The report records disagreement even when verification fails.
    from verify import verify
    verify(output)


if __name__ == '__main__':
    main()
