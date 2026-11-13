#!/usr/bin/env python3
"""Generate native configuration files for planetary structure simulations."""
import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path


def build_cases(masses, compositions):
    """Build cases from masses and compositions with exact deduplication."""
    if not isinstance(masses, list) or not masses:
        raise ValueError("masses must be a non-empty list")
    if not isinstance(compositions, list) or not compositions:
        raise ValueError("compositions must be a non-empty list")

    validated_masses = []
    for m in masses:
        if isinstance(m, bool) or not isinstance(m, (int, float)):
            raise ValueError("mass must be a finite number, not bool")
        if not math.isfinite(m):
            raise ValueError("mass must be finite")
        if m <= 0:
            raise ValueError("mass must be positive")
        validated_masses.append(float(m))

    validated_comps = []
    seen_ids = set()
    for comp in compositions:
        if not isinstance(comp, dict):
            raise ValueError("composition must be a dict")
        required = {'id', 'family', 'fractions'}
        if not required.issubset(comp.keys()):
            raise ValueError("composition missing required keys")
        cid = comp['id']
        family = comp['family']
        fractions = comp['fractions']
        if not isinstance(cid, str) or not cid:
            raise ValueError("composition id must be non-empty string")
        if any(ord(ch) < 32 for ch in cid):
            raise ValueError("composition id contains control characters")
        if cid in seen_ids:
            raise ValueError(f"duplicate composition id: {cid}")
        seen_ids.add(cid)
        if not isinstance(family, str) or not family:
            raise ValueError("family must be non-empty string")
        if any(ord(ch) < 32 for ch in family):
            raise ValueError("family contains control characters")
        if not isinstance(fractions, list) or len(fractions) != 4:
            raise ValueError("fractions must be a list of 4 numbers")
        validated_fractions = []
        for f in fractions:
            if isinstance(f, bool) or not isinstance(f, (int, float)):
                raise ValueError("fraction must be a finite number, not bool")
            if not math.isfinite(f):
                raise ValueError("fraction must be finite")
            if f < 0:
                raise ValueError("fraction must be non-negative")
            validated_fractions.append(float(f))
        total = sum(validated_fractions)
        if abs(total - 1.0) > 1e-12:
            raise ValueError(f"fractions sum to {total}, expected 1.0 within 1e-12")
        validated_comps.append({
            'id': cid,
            'family': family,
            'fractions': validated_fractions
        })

    cases = []
    seen_physical = {}
    for m in validated_masses:
        for comp in validated_comps:
            fractions = comp['fractions']
            # Canonical key using float.hex for exact representation
            key_parts = [float(m).hex()]
            for f in fractions:
                key_parts.append(float(f).hex())
            physical_key = tuple(key_parts)
            if physical_key in seen_physical:
                # Merge aliases and families
                existing = seen_physical[physical_key]
                existing['aliases'].append(comp['id'])
                existing['families'].append(comp['family'])
            else:
                # Create new case
                case = {
                    'mass_earth': m,
                    'fractions': fractions,
                    'aliases': [comp['id']],
                    'families': [comp['family']]
                }
                # Compute stable SHA256 key from physical inputs
                key_str = json.dumps({
                    'mass_earth': m,
                    'fractions': fractions
                }, sort_keys=True, separators=(',', ':'), allow_nan=False)
                key_hash = hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:16]
                case['key'] = key_hash
                cases.append(case)
                seen_physical[physical_key] = case
    return cases


def configuration(template_text, case, output_native):
    """Generate configuration text for a case."""
    lines = template_text.splitlines()
    config = {}
    order = []
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            raise ValueError(f"Invalid line {line_no}: no '=' found")
        key, value = stripped.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key in config:
            raise ValueError(f"Duplicate key '{key}' on line {line_no}")
        config[key] = value
        order.append(key)

    required_keys = ['mass_of_core', 'mass_of_mantle', 'mass_of_hydro', 'mass_of_atm',
                      'output_file', 'input_mode', 'atm_phasedgm', 'hydro_phasedgm']
    for req in required_keys:
        if req not in config:
            raise ValueError(f"Missing required key: {req}")

    # Validate selectors (strip matching outer quotes for comparison)
    def strip_outer_quotes(s):
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            return s[1:-1]
        return s
    if strip_outer_quotes(config['input_mode']) != '0':
        raise ValueError("input_mode must be 0")
    if strip_outer_quotes(config['atm_phasedgm']) != 'gas_hhe_iso_adiabatic100':
        raise ValueError("atm_phasedgm must be gas_hhe_iso_adiabatic100")
    if strip_outer_quotes(config['hydro_phasedgm']) != 'water_tabulated':
        raise ValueError("hydro_phasedgm must be water_tabulated")
    if 'tp_profile_file' in config:
        raise ValueError("tp_profile_file must not be present")

    # Validate output_native path
    if not isinstance(output_native, str) or not output_native:
        raise ValueError("output_native must be a non-empty string")
    if '"' in output_native or '\n' in output_native or '\r' in output_native:
        raise ValueError("output_native contains invalid characters")
    if not output_native.startswith('/'):
        raise ValueError("output_native must be absolute path")

    # Replace mass keys
    mass_map = {
        'mass_of_core': case['fractions'][0],
        'mass_of_mantle': case['fractions'][1],
        'mass_of_hydro': case['fractions'][2],
        'mass_of_atm': case['fractions'][3]
    }
    for key, fraction in mass_map.items():
        actual_mass = fraction * case['mass_earth']
        if not math.isfinite(actual_mass):
            raise ValueError(f"Computed mass for {key} is not finite")
        if actual_mass == 0:
            config[key] = '0'
        else:
            config[key] = f"{actual_mass:.17g}"

    # Set output_file
    config['output_file'] = f'"{output_native}"'

    # Rebuild text preserving order and comments
    output_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            output_lines.append(line)
            continue
        if '=' not in stripped:
            # Should not happen as validated earlier
            output_lines.append(line)
            continue
        key, value = stripped.split('=', 1)
        key = key.strip()
        if key in config:
            output_lines.append(f"{key}={config[key]}")
        else:
            output_lines.append(line)
    return '\n'.join(output_lines) + '\n'


def native_path(path):
    """Convert path to native absolute path string."""
    p = Path(path).resolve()
    s = p.as_posix()
    if len(s) >= 3 and s[0].isalpha() and s[1] == ':' and s[2] == '/':
        # Windows drive letter like C:/... -> /mnt/c/...
        drive = s[0].lower()
        s = f"/mnt/{drive}{s[2:]}"
    if '"' in s or '\n' in s or '\r' in s:
        raise ValueError("Path contains invalid characters")
    return s


def generate(input_json_path, output_dir):
    """Main generation function."""
    input_json_path = Path(input_json_path).resolve()
    if not input_json_path.is_file():
        raise FileNotFoundError(f"Input JSON not found: {input_json_path}")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # Validate input structure
    if not isinstance(input_data, dict):
        raise ValueError("Input JSON must be a dict")
    if 'masses_earth' not in input_data or 'compositions' not in input_data or 'template_cfg' not in input_data:
        raise ValueError("Input JSON must contain masses_earth, compositions, template_cfg")

    masses = input_data['masses_earth']
    compositions = input_data['compositions']
    template_cfg_rel = input_data['template_cfg']
    if not isinstance(template_cfg_rel, str):
        raise ValueError("template_cfg must be a string path")
    template_cfg_path = (input_json_path.parent / template_cfg_rel).resolve()
    if not template_cfg_path.is_file():
        raise FileNotFoundError(f"Template config not found: {template_cfg_path}")
    with open(template_cfg_path, 'r', encoding='utf-8') as f:
        template_text = f.read()

    # Build cases (validates masses and compositions)
    cases = build_cases(masses, compositions)

    # Validate output directory
    output_dir_path = Path(output_dir).resolve()
    if output_dir_path.exists():
        raise FileExistsError(f"Output directory already exists: {output_dir_path}")

    # Pre-validate all configurations before creating anything
    configs = []
    for case in cases:
        case_dir = output_dir_path / case['key']
        output_native = native_path(str(case_dir / 'model.dat'))
        cfg_text = configuration(template_text, case, output_native)
        configs.append((case, cfg_text))

    # Now create directories and write files
    output_dir_path.mkdir(parents=True)
    manifest_cases = []
    for case, cfg_text in configs:
        case_dir = output_dir_path / case['key']
        case_dir.mkdir()
        cfg_path = case_dir / 'run.cfg'
        cfg_bytes = cfg_text.encode('utf-8')
        cfg_path.write_bytes(cfg_bytes)
        cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
        manifest_cases.append({
            'key': case['key'],
            'mass_earth': case['mass_earth'],
            'fractions': case['fractions'],
            'aliases': case['aliases'],
            'families': case['families'],
            'config_sha256': cfg_sha,
            'status': 'GENERATED_NOT_RUN'
        })

    # Compute SHAs
    with open(input_json_path, 'rb') as f:
        input_sha = hashlib.sha256(f.read()).hexdigest()
    with open(template_cfg_path, 'rb') as f:
        template_sha = hashlib.sha256(f.read()).hexdigest()

    manifest = {
        'cases': manifest_cases,
        'input_sha256': input_sha,
        'template_sha256': template_sha
    }
    manifest_path = output_dir_path / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Generate native configuration files for planetary structure simulations.')
    parser.add_argument('--generate', nargs=2, metavar=('INPUT_JSON', 'OUTPUT_DIR'),
                        help='Generate configurations from INPUT_JSON into OUTPUT_DIR')
    args = parser.parse_args()
    if args.generate:
        input_json, output_dir = args.generate
        try:
            generate(input_json, output_dir)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
