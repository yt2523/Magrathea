import os, sys, json, hashlib, shutil, subprocess, time, difflib

def hashfile(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def jsonwrite(p, d):
    with open(p, 'w') as f:
        json.dump(d, f, indent=2, sort_keys=True)

def copytree_ignore_o(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.o'))

def prepare(args):
    repo, old, out = args.repo, args.old, args.out
    if os.path.exists(out):
        print('out exists'); sys.exit(1)
    os.makedirs(out)
    src = os.path.join(out, 'source')
    os.makedirs(src)
    copytree_ignore_o(os.path.join(old, 'src'), os.path.join(src, 'src'))
    shutil.copy2(os.path.join(old, 'Makefile'), os.path.join(src, 'Makefile'))
    os.symlink(os.path.abspath(os.path.join(old, 'tabulated')), os.path.join(src, 'tabulated'))
    staged = os.path.join(src, 'src')
    shutil.copy2(os.path.join(repo, 'src', 'hydro.cpp'), os.path.join(staged, 'hydro.cpp'))
    shutil.copy2(os.path.join(repo, 'src', 'radius_bracket.h'), os.path.join(staged, 'radius_bracket.h'))
    old_hydro = os.path.join(old, 'src', 'hydro.cpp')
    new_hydro = os.path.join(staged, 'hydro.cpp')
    with open(old_hydro) as f: old_text = f.read()
    with open(new_hydro) as f: new_text = f.read()
    start_marker = 'hydro* Rloop('
    end_marker = 'int fitting_error'
    old_start = old_text.index(start_marker)
    old_end = old_text.index(end_marker, old_start)
    new_start = new_text.index(start_marker)
    new_end = new_text.index(end_marker, new_start)
    old_outside = old_text[:old_start] + old_text[old_end:]
    new_prefix = new_text[:new_start]
    new_prefix = new_prefix.replace('#include "radius_bracket.h"\n', '')
    new_outside = new_prefix + new_text[new_end:]
    if old_outside != new_outside:
        raise RuntimeError("Outside text differs")
    diff = difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile='old/hydro.cpp', tofile='new/hydro.cpp')
    with open(os.path.join(out, 'hydro.diff'), 'w') as f:
        f.write('\n'.join(diff))
    old_src = os.path.join(old, 'src')
    old_files = {}
    for root, dirs, files in os.walk(old_src):
        for fn in files:
            if fn.endswith('.o'): continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, old_src)
            old_files[rel] = hashfile(p)
    staged_files = {}
    for root, dirs, files in os.walk(staged):
        for fn in files:
            if fn.endswith('.o'): continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, staged)
            staged_files[rel] = hashfile(p)
    for rel, h in old_files.items():
        if rel == 'hydro.cpp': continue
        if rel not in staged_files or staged_files[rel] != h:
            print(f'mismatch {rel}'); sys.exit(1)
    extra = set(staged_files) - set(old_files) - {'hydro.cpp', 'radius_bracket.h'}
    if extra:
        print(f'extra {extra}'); sys.exit(1)
    tab_hashes = {}
    tab_dir = os.path.join(old, 'tabulated')
    for root, dirs, files in os.walk(tab_dir):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, tab_dir)
            tab_hashes[rel] = hashfile(p)
    profile = os.path.join(old, 'inputs', 'profile.csv')
    profile_hash = hashfile(profile)
    manifest = {
        'old_src_hashes': old_files,
        'staged_src_hashes': staged_files,
        'tabulated_hashes': tab_hashes,
        'profile_hash': profile_hash,
        'hydro_diff': 'hydro.diff'
    }
    jsonwrite(os.path.join(out, 'manifest.json'), manifest)
    log_out = os.path.join(out, 'build_stdout.log')
    log_err = os.path.join(out, 'build_stderr.log')
    with open(log_out, 'w') as fo, open(log_err, 'w') as fe:
        r = subprocess.run(['make', '-B', '-j2'], cwd=src, stdout=fo, stderr=fe, timeout=180)
    if r.returncode != 0:
        print('build failed'); sys.exit(1)
    with open(os.path.join(out, 'PREPARED'), 'w') as f:
        f.write('ok')

def run(args):
    repo, old, out = args.repo, args.old, args.out
    if not os.path.exists(os.path.join(out, 'PREPARED')):
        print('not prepared'); sys.exit(1)
    cases_dir = os.path.join(out, 'cases')
    if os.path.exists(cases_dir):
        print('cases exist'); sys.exit(1)
    os.makedirs(cases_dir)
    src = os.path.join(out, 'source')
    staged = os.path.join(src, 'src')
    manifest = json.load(open(os.path.join(out, 'manifest.json')))
    staged_hashes = {}
    for root, dirs, files in os.walk(staged):
        for fn in files:
            if fn.endswith('.o'): continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, staged)
            staged_hashes[rel] = hashfile(p)
    if staged_hashes != manifest['staged_src_hashes']:
        print('staged hash mismatch'); sys.exit(1)
    tab_dir = os.path.join(old, 'tabulated')
    tab_hashes = {}
    for root, dirs, files in os.walk(tab_dir):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, tab_dir)
            tab_hashes[rel] = hashfile(p)
    if tab_hashes != manifest['tabulated_hashes']:
        print('tab hash mismatch'); sys.exit(1)
    profile = os.path.join(old, 'inputs', 'profile.csv')
    if hashfile(profile) != manifest['profile_hash']:
        print('profile hash mismatch'); sys.exit(1)
    hist_dir = os.path.join(repo, 'experiments', 'pure-fe-pilot-20261106', 'data', 'run02')
    cases = ['grid-' + str(i) for i in range(17, 25)] + ['grid-14', 'grid-20-tight']
    for c in cases:
        cfg_path = os.path.join(hist_dir, 'grid-20' if c == 'grid-20-tight' else c, 'run.cfg')
        if not os.path.exists(cfg_path):
            print(f'missing config {c}'); sys.exit(1)
    base_tight = 'grid-20'
    binary = os.path.join(src, 'planet')
    binary_sha = hashfile(binary)
    source_hash = manifest['staged_src_hashes'].get('hydro.cpp', '')
    tp_sha = manifest['profile_hash']
    attempts = []
    for c in cases:
        cfg_src = os.path.join(hist_dir, 'grid-20' if c == 'grid-20-tight' else c, 'run.cfg')
        case_dir = os.path.join(cases_dir, c)
        os.makedirs(case_dir)
        cfg_dst = os.path.join(case_dir, 'config')
        with open(cfg_src) as f:
            lines = f.readlines()
        out_lines = []
        replaced = set()
        for line in lines:
            line = line.rstrip('\n')
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                if k == 'output_file':
                    line = f'output_file="{os.path.abspath(os.path.join(case_dir, "model.dat"))}"'
                    replaced.add(k)
                elif k == 'tp_profile_file':
                    line = f'tp_profile_file="{os.path.abspath(profile)}"'
                    replaced.add(k)
                elif c == 'grid-20-tight':
                    if k == 'ode_eps_rel0':
                        line = 'ode_eps_rel0=1e-8'; replaced.add(k)
                    elif k == 'ode_eps_rel1':
                        line = 'ode_eps_rel1=1e-11'; replaced.add(k)
                    elif k == 'ode_eps_rel2':
                        line = 'ode_eps_rel2=1e-11'; replaced.add(k)
                    elif k == 'R_eps_rel':
                        line = 'R_eps_rel=2e-6'; replaced.add(k)
                    elif k == 'fit_eps_rel':
                        line = 'fit_eps_rel=1e-7'; replaced.add(k)
            out_lines.append(line)
        required = {'output_file', 'tp_profile_file'}
        if c == 'grid-20-tight':
            required.update(['ode_eps_rel0', 'ode_eps_rel1', 'ode_eps_rel2', 'R_eps_rel', 'fit_eps_rel'])
        if not required.issubset(replaced):
            print(f'missing keys for {c}'); sys.exit(1)
        with open(cfg_dst, 'w') as f:
            f.write('\n'.join(out_lines) + '\n')
        attempt = {
            'state': 'STARTED',
            'config_sha': hashfile(cfg_dst),
            'binary_sha': binary_sha,
            'source_hash': source_hash,
            'TP_sha': tp_sha
        }
        jsonwrite(os.path.join(case_dir, 'attempt.json'), attempt)
        attempts.append((c, case_dir, cfg_dst))
    for case_name, case_dir, config_path in attempts:
        with open(os.path.join(case_dir, 'stdout.log'), 'w') as fo, open(os.path.join(case_dir, 'stderr.log'), 'w') as fe:
            start = time.monotonic()
            try:
                proc = subprocess.run([binary, config_path], cwd=src, stdout=fo, stderr=fe, timeout=180)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                exit_code = 124
            elapsed = time.monotonic() - start
        attempt_path = os.path.join(case_dir, 'attempt.json')
        with open(attempt_path, 'r') as f:
            data = json.load(f)
        data['state'] = 'FINISHED'
        data['exit'] = exit_code
        data['elapsed'] = elapsed
        jsonwrite(attempt_path, data)
        print(case_name, exit_code, elapsed, flush=True)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'run'])
    p.add_argument('--repo', required=True)
    p.add_argument('--old', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    if args.action == 'prepare':
        prepare(args)
    else:
        run(args)