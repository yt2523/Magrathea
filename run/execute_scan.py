#!/usr/bin/env python3
"""Serial scientific computation executor."""

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_quoted_path(s: str) -> str:
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def rel_error(a: float, b: float) -> float:
    if b == 0:
        return abs(a)
    return abs(a - b) / abs(b)


def validate_case(case: Dict[str, Any], campaign_dir: Path,
                  build_cases_func, configuration_func) -> Tuple[bool, str]:
    """Validate a single case from manifest."""
    key = case.get('key')
    if not isinstance(key, str) or len(key) != 16:
        return False, f"Invalid key: {key!r}"
    try:
        int(key, 16)
    except ValueError:
        return False, f"Key not hex: {key!r}"

    mass_earth = case.get('mass_earth')
    if not is_finite_number(mass_earth) or mass_earth <= 0:
        return False, f"Invalid mass_earth: {mass_earth!r}"

    fractions = case.get('fractions')
    if not isinstance(fractions, list) or len(fractions) != 4:
        return False, f"Invalid fractions: {fractions!r}"
    for f in fractions:
        if not is_finite_number(f) or f < 0 or f > 1:
            return False, f"Invalid fraction: {f!r}"
    if abs(sum(fractions) - 1.0) > 1e-12:
        return False, f"Fractions sum != 1: {fractions}"

    try:
        rebuilt = build_cases_func([mass_earth],
                                   [{'id': key, 'family': 'test',
                                     'fractions': fractions}])
    except Exception as e:
        return False, f"build_cases failed: {e}"
    if not rebuilt or len(rebuilt) != 1:
        return False, "build_cases did not return one case"
    rebuilt_case = rebuilt[0]
    if rebuilt_case.get('key') != key:
        return False, "Rebuilt key mismatch"
    if abs(rebuilt_case.get('mass_earth', 0) - mass_earth) > 1e-12:
        return False, "Rebuilt mass mismatch"
    rebuilt_fractions = rebuilt_case.get('fractions')
    if not rebuilt_fractions or len(rebuilt_fractions) != 4:
        return False, "Rebuilt fractions invalid"
    for i in range(4):
        if abs(rebuilt_fractions[i] - fractions[i]) > 1e-12:
            return False, f"Rebuilt fraction {i} mismatch"

    case_dir = campaign_dir / key
    cfg_path = case_dir / 'run.cfg'
    if not cfg_path.is_file():
        return False, f"Missing run.cfg in {case_dir}"
    cfg_bytes = cfg_path.read_bytes()
    if sha256_bytes(cfg_bytes) != case.get('config_sha256'):
        return False, "Config SHA mismatch"

    cfg_text = cfg_bytes.decode('utf-8')
    try:
        output_native = case_dir / 'model.dat'
        configuration_func(cfg_text, case, str(output_native))
    except Exception as e:
        return False, f"configuration validation failed: {e}"

    # Additional config checks
    lines = cfg_text.splitlines()
    config = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            return False, f"Invalid line: {stripped}"
        key, value = stripped.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key in config:
            return False, f"Duplicate key: {key}"
        config[key] = value

    if 'input_mode' not in config:
        return False, "Missing input_mode"
    if parse_quoted_path(config['input_mode']) != '0':
        return False, "input_mode must be 0"
    if 'atm_phasedgm' not in config or parse_quoted_path(config['atm_phasedgm']) != 'gas_hhe_iso_adiabatic100':
        return False, "atm_phasedgm must be gas_hhe_iso_adiabatic100"
    if 'hydro_phasedgm' not in config or parse_quoted_path(config['hydro_phasedgm']) != 'water_tabulated':
        return False, "hydro_phasedgm must be water_tabulated"
    if 'tp_profile_file' in config:
        return False, "tp_profile_file must not be present"

    if 'output_file' not in config:
        return False, "Missing output_file"
    output_val = parse_quoted_path(config['output_file'])
    expected_output = str(case_dir / 'model.dat')
    if output_val != expected_output:
        return False, f"output_file mismatch: {output_val} != {expected_output}"

    if 'P_surface' not in config:
        return False, "Missing P_surface"
    try:
        p_surface = float(config['P_surface'])
    except ValueError:
        return False, "Invalid P_surface"
    if not is_finite_number(p_surface) or p_surface <= 0:
        return False, f"Invalid P_surface: {p_surface}"

    if 'surface_temp' not in config:
        return False, "Missing surface_temp"
    try:
        temp_surface = float(config['surface_temp'])
    except ValueError:
        return False, "Invalid surface_temp"
    if not is_finite_number(temp_surface) or temp_surface <= 0:
        return False, f"Invalid surface_temp: {temp_surface}"

    mass_keys = ['mass_of_core', 'mass_of_mantle', 'mass_of_hydro', 'mass_of_atm']
    for mk in mass_keys:
        if mk not in config:
            return False, f"Missing {mk}"
        try:
            actual_mass = float(config[mk])
        except ValueError:
            return False, f"Invalid {mk}"
        if not is_finite_number(actual_mass) or actual_mass < 0:
            return False, f"Invalid {mk}: {actual_mass}"
        expected_mass = fractions[mass_keys.index(mk)] * mass_earth
        if fractions[mass_keys.index(mk)] == 0:
            if actual_mass != 0:
                return False, f"{mk} should be 0 but is {actual_mass}"
        else:
            if rel_error(actual_mass, expected_mass) > 1e-12:
                return False, f"{mk} mismatch: {actual_mass} vs {expected_mass}"

    return True, ""


def validate_runtime(runtime: Dict[str, Any]) -> Tuple[bool, str]:
    if runtime.get('cli_exit_code') != 0:
        return False, f"solver exit code {runtime.get('cli_exit_code')}"
    if runtime.get('strict_table_audit') is not True:
        return False, "strict_table_audit not true"
    if runtime.get('rejected_table_queries') != 0:
        return False, f"rejected_table_queries {runtime.get('rejected_table_queries')}"
    density_counts = runtime.get('density_audit_counts', {})
    if not isinstance(density_counts, dict):
        return False, "density_audit_counts not dict"
    for key in ['Gas', 'Gas_iso']:
        if density_counts.get(key, 0) != 0:
            return False, f"density_audit_counts has {key}"
    return True, ""


def validate_model(model_path: Path, case: Dict[str, Any],
                   cfg_text: str) -> Tuple[bool, str, Optional[float]]:
    if not model_path.is_file():
        return False, "model.dat missing", None
    if model_path.stat().st_size == 0:
        return False, "model.dat empty", None

    with open(model_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return False, "model.dat empty", None

    # Find first non-empty line
    first_nonempty_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_nonempty_idx = i
            break
    if first_nonempty_idx is None:
        return False, "no non-empty lines", None

    # Parse header from first non-empty line
    header_line = lines[first_nonempty_idx].strip()
    if not header_line.startswith('Index'):
        return False, f"header does not start with Index: {header_line}", None


    # Process data lines: all non-empty lines after header
    data_lines = []
    for line in lines[first_nonempty_idx+1:]:
        if line.strip():
            data_lines.append(line)
    if not data_lines:
        return False, "no data lines", None

    # Parse all data lines
    parsed_rows = []
    for line_num, line in enumerate(data_lines, start=first_nonempty_idx+2):
        parts = line.split(maxsplit=6)
        if len(parts) != 7:
            return False, f"line {line_num}: expected 7 fields, got {len(parts)}", None
        try:
            index = int(parts[0])
            r_re = float(parts[1])
            p_gpa = float(parts[2])
            m_me = float(parts[3])
            rho = float(parts[4])
            t_k = float(parts[5])
            phase = parts[6].strip()
        except Exception as e:
            return False, f"line {line_num}: parse error: {e}", None

        # Validate numbers
        if not all(is_finite_number(x) for x in [r_re, p_gpa, m_me, rho, t_k]):
            return False, f"line {line_num}: non-finite numbers", None
        if r_re < 0 or p_gpa <= 0 or m_me < 0 or rho <= 0 or t_k <= 0:
            return False, f"line {line_num}: invalid values (R/M non-negative, P/T/rho positive)", None

        parsed_rows.append((index, r_re, p_gpa, m_me, rho, t_k, phase))

    # Check index sequence: non-negative
    for row in parsed_rows:
        if row[0] < 0:
            return False, f"index sequence invalid: {row[0]}", None

    # Last row checks
    last_row = parsed_rows[-1]
    last_r_re = last_row[1]
    last_p_gpa = last_row[2]
    last_m_me = last_row[3]
    last_t_k = last_row[5]

    if last_r_re <= 0:
        return False, "last row R_RE must be > 0", None

    mass_earth = case['mass_earth']
    if rel_error(last_m_me, mass_earth) > 1e-7:
        return False, f"mass mismatch: {last_m_me} vs {mass_earth}", None

    # Parse config for P_surface and surface_temp
    p_surface = None
    temp_surface = None
    for line in cfg_text.splitlines():
        line = line.strip()
        if line.startswith('P_surface'):
            try:
                p_surface = float(line.split('=')[1].strip())
            except Exception:
                pass
        elif line.startswith('surface_temp'):
            try:
                temp_surface = float(line.split('=')[1].strip())
            except Exception:
                pass
    if p_surface is None or temp_surface is None:
        return False, "config missing P_surface or surface_temp", None

    expected_p_gpa = p_surface / 1e10  # dyn/cm2 to GPa
    if rel_error(last_p_gpa, expected_p_gpa) > 1e-7:
        return False, f"pressure mismatch: {last_p_gpa} vs {expected_p_gpa}", None
    if rel_error(last_t_k, temp_surface) > 2e-6:
        return False, f"temperature mismatch: {last_t_k} vs {temp_surface}", None

    return True, "", last_r_re


def validate_checked_csv(checked_csv_path: Path, case: Dict[str, Any],
                         runtime: Dict[str, Any]) -> Tuple[bool, str]:
    if not checked_csv_path.is_file():
        return False, "checked CSV missing"

    # Read model.dat from same directory
    model_path = checked_csv_path.parent / 'model.dat'
    if not model_path.is_file():
        return False, "model.dat missing in same directory"
    with open(model_path, 'r', encoding='utf-8') as f:
        model_lines = f.readlines()
    # Parse model data lines (skip header)
    model_data = []
    first_nonempty_idx = None
    for i, line in enumerate(model_lines):
        if line.strip():
            first_nonempty_idx = i
            break
    if first_nonempty_idx is None:
        return False, "model.dat empty"
    # Skip header line
    for line in model_lines[first_nonempty_idx+1:]:
        if line.strip():
            parts = line.split(maxsplit=6)
            if len(parts) != 7:
                return False, f"model.dat line has {len(parts)} parts, expected 7"
            try:
                index = int(parts[0])
                r_re = float(parts[1])
                p_gpa = float(parts[2])
                m_me = float(parts[3])
                rho = float(parts[4])
                t_k = float(parts[5])
                phase = parts[6].strip()
            except Exception as e:
                return False, f"model.dat parse error: {e}"
            model_data.append((index, r_re, p_gpa, m_me, rho, t_k, phase))

    # Read CSV
    try:
        with open(checked_csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        return False, f"CSV read error: {e}"
    if len(rows) == 0:
        return False, "checked CSV empty"

    # Check row count matches model
    if len(rows) != len(model_data):
        return False, f"row count mismatch: CSV {len(rows)}, model {len(model_data)}"

    # Check header fields
    expected_fields = ['index', 'R_RE', 'P_GPa', 'M_ME', 'T_K', 'rho_saved',
                       'rho_recomputed', 'rho_relerr', 'phase', 'selected_id',
                       'domain', 'thermal_code', 'dTdP_K_per_GPa', 'nabla',
                       'rejected_delta']
    if reader.fieldnames is None:
        return False, "CSV header missing"
    for field in expected_fields:
        if field not in reader.fieldnames:
            return False, f"CSV missing field: {field}"

    # Parse config for surface_temp (needed for gas temperature check)
    cfg_path = checked_csv_path.parent / 'run.cfg'
    if not cfg_path.is_file():
        return False, "run.cfg missing in same directory"
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg_text = f.read()
    temp_surface = None
    for line in cfg_text.splitlines():
        line = line.strip()
        if line.startswith('surface_temp'):
            try:
                temp_surface = float(line.split('=')[1].strip())
            except Exception:
                pass
    if temp_surface is None:
        return False, "config missing surface_temp"

    # Iterate rows and validate
    for i, row in enumerate(rows):
        # Check index matches model
        try:
            csv_index = int(row['index'])
        except Exception:
            return False, f"row {i}: index invalid"
        if csv_index != model_data[i][0]:
            return False, f"row {i}: index mismatch: CSV {csv_index}, model {model_data[i][0]}"

        # Check numeric fields against model with tolerance 1e-12
        for field, model_val in [('R_RE', model_data[i][1]),
                                 ('P_GPa', model_data[i][2]),
                                 ('M_ME', model_data[i][3]),
                                 ('T_K', model_data[i][5]),
                                 ('rho_saved', model_data[i][4])]:
            try:
                csv_val = float(row[field])
            except Exception:
                return False, f"row {i}: {field} invalid"
            if not is_finite_number(csv_val):
                return False, f"row {i}: {field} not finite"
            if abs(csv_val - model_val) > 1e-12 * max(1.0, abs(model_val)):
                return False, f"row {i}: {field} mismatch: CSV {csv_val}, model {model_val}"

        # Check phase string matches exactly
        if row['phase'].strip() != model_data[i][6]:
            return False, f"row {i}: phase mismatch: CSV '{row['phase']}', model '{model_data[i][6]}'"

        # Check rho_recomputed positive finite
        try:
            rho_recomp = float(row['rho_recomputed'])
        except Exception:
            return False, f"row {i}: rho_recomputed invalid"
        if not is_finite_number(rho_recomp) or rho_recomp <= 0:
            return False, f"row {i}: rho_recomputed invalid: {rho_recomp}"

        # Check rho_relerr signed and within tolerance, and matches recomputed ratio
        try:
            rho_relerr = float(row['rho_relerr'])
        except Exception:
            return False, f"row {i}: rho_relerr invalid"
        if not is_finite_number(rho_relerr):
            return False, f"row {i}: rho_relerr not finite"
        if abs(rho_relerr) > 2e-6:
            return False, f"row {i}: rho_relerr out of tolerance: {rho_relerr}"
        rho_saved = float(row['rho_saved'])
        expected_relerr = (rho_recomp - rho_saved) / rho_saved
        if abs(rho_relerr - expected_relerr) > 1e-12:
            return False, f"row {i}: rho_relerr inconsistent: {rho_relerr} vs expected {expected_relerr}"

        # Check domain and rejected_delta
        if row.get('domain') != 'true':
            return False, f"row {i}: domain not true: {row.get('domain')}"
        if row.get('rejected_delta') != '0':
            return False, f"row {i}: rejected_delta not 0: {row.get('rejected_delta')}"

        # Check dTdP and nabla finite and relation
        try:
            dtdp = float(row['dTdP_K_per_GPa'])
            nabla = float(row['nabla'])
        except Exception:
            return False, f"row {i}: dTdP or nabla invalid"
        if not is_finite_number(dtdp) or not is_finite_number(nabla):
            return False, f"row {i}: dTdP or nabla not finite"
        p_gpa = float(row['P_GPa'])
        t_k = float(row['T_K'])
        expected_nabla = (p_gpa / t_k) * dtdp
        if abs(nabla - expected_nabla) > 1e-10 * max(1.0, abs(expected_nabla)) + 1e-12:
            return False, f"row {i}: nabla inconsistent: {nabla} vs expected {expected_nabla}"

        # Check selected_id restrictions
        selected_id = row.get('selected_id', '')
        # Gas restrictions
        if selected_id.startswith('Gas'):
            if selected_id not in ['Gas_hhe', 'Gas_hhe_iso100']:
                return False, f"row {i}: invalid gas selected_id: {selected_id}"
            # Low pressure gas temperature check
            if p_gpa <= 0.01:  # 100 bar = 0.01 GPa
                if rel_error(t_k, temp_surface) > 2e-6:
                    return False, f"row {i}: low-pressure gas temperature mismatch: {t_k} vs {temp_surface}"
        # Water restrictions
        if case['fractions'][2] == 0:
            # zero water: any water-related ID rejected
            water_phases = ['H2O', 'Water', 'Ice', 'vdW_H2O']
            if any(phase in selected_id for phase in water_phases):
                return False, f"row {i}: water selected_id present despite zero water fraction: {selected_id}"
        else:
            # water present: only H2O_AQUA allowed
            if 'H2O' in selected_id or 'Water' in selected_id or 'Ice' in selected_id or 'vdW_H2O' in selected_id:
                if selected_id != 'H2O_AQUA':
                    return False, f"row {i}: invalid water selected_id: {selected_id}"
        # Silicate restrictions
        if case['fractions'][1] == 0:
            silicate_phases = ['Si_', 'Fo', 'Wds', 'Rwd']
            if any(phase in selected_id for phase in silicate_phases):
                return False, f"row {i}: silicate selected_id present despite zero silicate fraction: {selected_id}"

    return True, ""


def check_runtime_phase_counts(runtime: Dict[str, Any], case: Dict[str, Any]) -> Tuple[bool, str]:
    density_counts = runtime.get('density_audit_counts', {})
    gradient_counts = runtime.get('gradient_audit_counts', {})

    # Validate dictionaries
    if not isinstance(density_counts, dict) or not isinstance(gradient_counts, dict):
        return False, "audit counts not dict"

    # Check all keys and values are finite non-negative integers
    for counts_dict in [density_counts, gradient_counts]:
        for key, value in counts_dict.items():
            if not isinstance(key, str):
                return False, f"audit count key not string: {key}"
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"audit count value not integer: {key}={value}"
            if value < 0:
                return False, f"audit count negative: {key}={value}"

    # Zero water fraction: all water-related counts must be zero
    if case['fractions'][2] == 0:
        water_prefixes = ['H2O', 'Water', 'Ice', 'vdW_H2O']
        for key in density_counts:
            if any(key.startswith(prefix) for prefix in water_prefixes):
                if density_counts[key] != 0:
                    return False, f"water phase {key} called despite zero water fraction"
        for key in gradient_counts:
            if any(key.startswith(prefix) for prefix in water_prefixes):
                if gradient_counts[key] != 0:
                    return False, f"water phase {key} called despite zero water fraction"

    # Zero silicate fraction: all silicate-related counts must be zero
    if case['fractions'][1] == 0:
        silicate_prefixes = ['Si_', 'Fo', 'Wds', 'Rwd']
        for key in density_counts:
            if any(key.startswith(prefix) for prefix in silicate_prefixes):
                if density_counts[key] != 0:
                    return False, f"silicate phase {key} called despite zero silicate fraction"
        for key in gradient_counts:
            if any(key.startswith(prefix) for prefix in silicate_prefixes):
                if gradient_counts[key] != 0:
                    return False, f"silicate phase {key} called despite zero silicate fraction"

    # Wet water: only H2O_AQUA allowed, no other water phases
    if case['fractions'][2] > 0:
        for key in density_counts:
            if key.startswith('H2O') or key.startswith('Water') or key.startswith('Ice') or key.startswith('vdW_H2O'):
                if key != 'H2O_AQUA' and density_counts[key] != 0:
                    return False, f"non-AQUA water phase {key} called with non-zero count"
        for key in gradient_counts:
            if key.startswith('H2O') or key.startswith('Water') or key.startswith('Ice') or key.startswith('vdW_H2O'):
                if key != 'H2O_AQUA' and gradient_counts[key] != 0:
                    return False, f"non-AQUA water phase {key} called with non-zero count"

    # Gas restrictions: Gas and Gas_iso must be zero
    for key in ['Gas', 'Gas_iso']:
        if density_counts.get(key, 0) != 0:
            return False, f"density_audit_counts has {key}"
        if gradient_counts.get(key, 0) != 0:
            return False, f"gradient_audit_counts has {key}"

    return True, ""


def execute(campaign, backend, solver, checker, target_radius, max_launches, timeout, stop_after_failures):
    import csv
    import fcntl
    import hashlib
    import json
    import math
    import os
    import subprocess
    import sys
    import time
    from pathlib import Path
    from typing import Any, Dict, List, Optional, Tuple

    # Helper functions (nested)
    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def atomic_write_json(path: Path, data: Any) -> None:
        tmp = path.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def read_json(path: Path) -> Any:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_finite_number(x: Any) -> bool:
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

    def rel_error(a: float, b: float) -> float:
        if b == 0:
            return abs(a)
        return abs(a - b) / abs(b)

    # Validate input parameters
    if not is_finite_number(target_radius) or target_radius <= 0:
        raise ValueError("target_radius must be a positive finite number")
    if not is_finite_number(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    if max_launches is not None:
        if isinstance(max_launches, bool) or not isinstance(max_launches, int) or max_launches < 0:
            raise ValueError("max_launches must be a non-negative integer or None")
    if isinstance(stop_after_failures, bool) or not isinstance(stop_after_failures, int) or stop_after_failures <= 0:
        raise ValueError("stop_after_failures must be a positive integer")

    # Resolve paths
    campaign = Path(campaign).resolve()
    backend = Path(backend).resolve()
    solver = Path(solver).resolve()
    checker = Path(checker).resolve()

    # Check existence and executability
    if not campaign.is_dir():
        raise ValueError(f"campaign directory does not exist: {campaign}")
    if not backend.is_dir():
        raise ValueError(f"backend directory does not exist: {backend}")
    if not solver.is_file() or not os.access(solver, os.X_OK):
        raise ValueError(f"solver is not an executable file: {solver}")
    if not checker.is_file() or not os.access(checker, os.X_OK):
        raise ValueError(f"checker is not an executable file: {checker}")

    # Table directory: backend/tabulated
    table_dir = backend / 'tabulated'
    if not table_dir.is_dir():
        raise ValueError(f"tabulated directory does not exist: {table_dir}")
    table_files = []
    for entry in sorted(table_dir.iterdir()):
        if entry.is_file() and not entry.is_symlink():
            table_files.append(entry)
        else:
            raise ValueError(f"tabulated contains non-regular file or symlink: {entry}")
    if not table_files:
        raise ValueError("tabulated directory is empty")

    # Import scan_compositions from same directory as this script
    import importlib.util
    script_dir = Path(__file__).parent.resolve()
    sc_path = script_dir / 'scan_compositions.py'
    if not sc_path.is_file():
        raise ValueError(f"scan_compositions.py not found in {script_dir}")
    spec = importlib.util.spec_from_file_location('scan_compositions', sc_path)
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)

    # Read manifest
    manifest_path = campaign / 'manifest.json'
    if not manifest_path.is_file():
        raise ValueError(f"manifest.json not found in campaign directory: {manifest_path}")
    try:
        manifest = read_json(manifest_path)
    except Exception as e:
        raise ValueError(f"Failed to read manifest.json: {e}")
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")
    cases = manifest.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest.json must contain a non-empty list of cases")

    # Validate manifest cases
    case_keys = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Each case in manifest must be a JSON object")
        key = case.get('key')
        if not isinstance(key, str) or len(key) != 16 or not all(c in '0123456789abcdef' for c in key):
            raise ValueError(f"Invalid case key: {key!r}")
        if key in case_keys:
            raise ValueError(f"Duplicate case key: {key}")
        case_keys.add(key)
        case_path = (campaign / key).resolve()
        # Ensure case_path is contained within campaign and no symlinks
        try:
            case_path.relative_to(campaign)
        except ValueError:
            raise ValueError(f"Case {key}: case path escapes campaign directory")
        if case_path.is_symlink():
            raise ValueError(f"Case {key}: case path is a symlink")
        # Check for symlinks in path components? We'll check later in artifact snapshot.
        # For now, ensure case_dir exists and is a directory
        if not case_path.is_dir():
            raise ValueError(f"Case {key}: case_dir does not exist or is not a directory: {case_path}")
        # Check cfg symlink
        cfg_path = case_path / 'run.cfg'
        if cfg_path.is_symlink():
            raise ValueError(f"Case {key}: run.cfg is a symlink")
        # Validate case using provided validate_case
        ok, error = validate_case(case, campaign, sc.build_cases, sc.configuration)
        if not ok:
            raise ValueError(f"Case {key}: validation failed: {error}")

    # Compute identity
    manifest_sha = sha256_file(manifest_path)
    solver_sha = sha256_file(solver)
    checker_sha = sha256_file(checker)
    sc_file_sha = sha256_file(sc_path)
    # Table files: relative paths and hashes
    table_entries = []
    for f in table_files:
        rel = f.relative_to(table_dir).as_posix()
        table_entries.append((rel, sha256_file(f)))
    identity_data = {
        'manifest_sha': manifest_sha,
        'solver_sha': solver_sha,
        'checker_sha': checker_sha,
        'sc_file_sha': sc_file_sha,
        'execute_sha': sha256_file(Path(__file__).resolve()),
        'target_radius': target_radius,
        'table_files': table_entries,
    }
    identity = sha256_bytes(json.dumps(identity_data, sort_keys=True, separators=(',', ':')).encode('utf-8'))

    # Acquire lock
    lock_path = campaign / '.scan.lock'
    lock_file = open(lock_path, 'w')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        raise ValueError("Another scan is in progress (lock held)")

    try:
        # Read existing execution.json if present
        ledger_path = campaign / 'execution.json'
        ledger = None
        if ledger_path.exists():
            try:
                ledger = read_json(ledger_path)
            except Exception as e:
                raise ValueError(f"Failed to read execution.json: {e}")
            if not isinstance(ledger, dict):
                raise ValueError("execution.json must contain a JSON object")
            # Check identity
            if ledger.get('identity') != identity:
                raise ValueError("execution.json identity mismatch; manual review required")
            # Check launch_count
            lc = ledger.get('launch_count')
            if isinstance(lc, bool) or not isinstance(lc, int) or lc < 0:
                raise ValueError("execution.json launch_count invalid")
            # Check cases: only known keys
            ledger_cases = ledger.get('cases')
            if not isinstance(ledger_cases, dict):
                raise ValueError("execution.json cases must be an object")
            for key in ledger_cases:
                if key not in case_keys:
                    raise ValueError(f"execution.json contains unknown case key: {key}")
            # Check statuses: if RUNNING or unknown, raise
            for key, rec in ledger_cases.items():
                if not isinstance(rec, dict):
                    raise ValueError(f"execution.json case {key}: record must be object")
                status = rec.get('status')
                if status == 'RUNNING' or status not in ('STORED_STATE_CHECKED', 'FAILED'):
                    raise ValueError(f"execution.json case {key}: status {status!r} requires manual review")
        else:
            # New ledger
            ledger = {
                'identity': identity,
                'launch_count': 0,
                'cases': {},
                'physical_acceptance': False,
            }

        # Define allowed artifact filenames
        allowed_artifacts = {'runtime.json', 'model.dat', 'checked.csv', 'solver.stdout', 'solver.stderr', 'checker.stdout', 'checker.stderr'}

        def artifact_snapshot(case_dir: Path) -> Dict[str, str]:
            """Return dict of artifact filename to sha256 for existing allowed files.
            Reject any other files, subdirectories, or symlinks."""
            snap = {}
            for entry in case_dir.iterdir():
                if entry.name == 'run.cfg':
                    continue
                if entry.is_symlink():
                    raise ValueError(f"Case {case_dir.name}: symlink not allowed: {entry.name}")
                if entry.is_dir():
                    raise ValueError(f"Case {case_dir.name}: subdirectory not allowed: {entry.name}")
                if entry.is_file():
                    if entry.name not in allowed_artifacts:
                        raise ValueError(f"Case {case_dir.name}: unexpected file: {entry.name}")
                    snap[entry.name] = sha256_file(entry)
                else:
                    raise ValueError(f"Case {case_dir.name}: unexpected entry: {entry.name}")
            return snap

        # Pre-check all cases: snapshots must match ledger if terminal, empty if not in ledger
        for case in cases:
            key = case['key']
            case_dir = (campaign / case['key']).resolve()
            snap = artifact_snapshot(case_dir)
            if key in ledger['cases']:
                rec = ledger['cases'][key]
                status = rec.get('status')
                if status in ('STORED_STATE_CHECKED', 'FAILED'):
                    # Compare snapshots
                    if snap != rec.get('artifacts', {}):
                        raise ValueError(f"Case {key}: artifact mismatch with ledger")
            else:
                # Not in ledger: snapshot must be empty
                if snap:
                    raise ValueError(f"Case {key}: artifacts present but case not in ledger")

        # Process cases
        consecutive_failures = 0
        for case in cases:
            key = case['key']
            case_dir = (campaign / case['key']).resolve()
            # Check if terminal
            if key in ledger['cases']:
                rec = ledger['cases'][key]
                status = rec.get('status')
                if status in ('STORED_STATE_CHECKED', 'FAILED'):
                    continue  # skip terminal
            # Check max launches
            if max_launches is not None and ledger['launch_count'] >= max_launches:
                break
            # Create new record
            rec = {
                'status': 'RUNNING',
                'R_RE': None,
                'residual_RE': None,
                'artifacts': {},
                'physical_acceptance': False,
            }
            ledger['cases'][key] = rec
            ledger['launch_count'] += 1
            atomic_write_json(ledger_path, ledger)

            # Launch solver
            cfg_path = case_dir / 'run.cfg'
            runtime_path = case_dir / 'runtime.json'
            model_path = case_dir / 'model.dat'
            checked_path = case_dir / 'checked.csv'
            solver_stdout_path = case_dir / 'solver.stdout'
            solver_stderr_path = case_dir / 'solver.stderr'
            checker_stdout_path = case_dir / 'checker.stdout'
            checker_stderr_path = case_dir / 'checker.stderr'

            start_time = time.monotonic()
            solver_returncode = None
            checker_returncode = None
            error_reason = None
            try:
                # Run solver
                with open(solver_stdout_path, 'wb') as f_out, open(solver_stderr_path, 'wb') as f_err:
                    proc = subprocess.run(
                        [str(solver), '--run', str(cfg_path), str(runtime_path)],
                        cwd=str(backend),
                        stdout=f_out,
                        stderr=f_err,
                        timeout=timeout,
                    )
                solver_returncode = proc.returncode
                if solver_returncode != 0:
                    raise RuntimeError(f"solver exited with code {solver_returncode}")

                # Validate runtime
                runtime_data = read_json(runtime_path)
                ok, error = validate_runtime(runtime_data)
                if not ok:
                    raise RuntimeError(f"runtime validation failed: {error}")
                ok, error = check_runtime_phase_counts(runtime_data, case)
                if not ok:
                    raise RuntimeError(f"runtime phase counts failed: {error}")

                # Validate model
                cfg_text = cfg_path.read_text(encoding='utf-8')
                ok, error, R = validate_model(model_path, case, cfg_text)
                if not ok:
                    raise RuntimeError(f"model validation failed: {error}")

                # Run checker
                with open(checker_stdout_path, 'wb') as f_out, open(checker_stderr_path, 'wb') as f_err:
                    proc = subprocess.run(
                        [str(checker), '--profile', str(model_path), str(checked_path)],
                        cwd=str(backend),
                        stdout=f_out,
                        stderr=f_err,
                        timeout=timeout,
                    )
                checker_returncode = proc.returncode
                if checker_returncode != 0:
                    raise RuntimeError(f"checker exited with code {checker_returncode}")

                # Validate checked CSV
                ok, error = validate_checked_csv(checked_path, case, runtime_data)
                if not ok:
                    raise RuntimeError(f"checked CSV validation failed: {error}")

                # Success
                rec['status'] = 'STORED_STATE_CHECKED'
                rec['R_RE'] = R
                rec['residual_RE'] = R - target_radius
                rec['physical_acceptance'] = False
            except Exception as e:
                rec['status'] = 'FAILED'
                rec['R_RE'] = None
                rec['residual_RE'] = None
                rec['physical_acceptance'] = False
                error_reason = str(e)
                # Optionally store error reason? Not specified, but we can add to record for debugging.
                # The spec says "reason错误" but not explicitly stored. We'll add a 'reason' field.
                rec['reason'] = error_reason
            finally:
                # Record elapsed time and exit codes
                elapsed = time.monotonic() - start_time
                rec['elapsed'] = elapsed
                rec['solver_returncode'] = solver_returncode
                rec['checker_returncode'] = checker_returncode
                # Snapshot artifacts
                rec['artifacts'] = artifact_snapshot(case_dir)
                # Write ledger
                atomic_write_json(ledger_path, ledger)

            # Update consecutive failures
            if rec['status'] == 'FAILED':
                consecutive_failures += 1
                if consecutive_failures >= stop_after_failures:
                    break
            else:
                consecutive_failures = 0

        # Write summary CSV
        summary_path = campaign / 'summary.csv'
        with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['key', 'M', 'fFe', 'fSi', 'fWater', 'fGas', 'aliases', 'families', 'R_RE', 'residual_RE', 'status', 'reason', 'elapsed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for case in cases:
                key = case['key']
                rec = ledger['cases'].get(key)
                # Extract input data from case
                mass_earth = case.get('mass_earth', '')
                fractions = case.get('fractions', [])
                if isinstance(fractions, list) and len(fractions) >= 4:
                    fFe, fSi, fWater, fGas = fractions[0], fractions[1], fractions[2], fractions[3]
                else:
                    fFe = fSi = fWater = fGas = ''
                aliases = case.get('aliases', [])
                families = case.get('families', [])
                row = {
                    'key': key,
                    'M': mass_earth,
                    'fFe': fFe,
                    'fSi': fSi,
                    'fWater': fWater,
                    'fGas': fGas,
                    'aliases': json.dumps(aliases),
                    'families': json.dumps(families),
                    'R_RE': '',
                    'residual_RE': '',
                    'status': 'NOT_RUN',
                    'reason': '',
                    'elapsed': '',
                }
                if rec is not None:
                    row['status'] = rec['status']
                    row['reason'] = rec.get('reason', '')
                    row['elapsed'] = rec.get('elapsed', '')
                    if rec['status'] == 'STORED_STATE_CHECKED':
                        row['R_RE'] = rec['R_RE']
                        row['residual_RE'] = rec['residual_RE']
                writer.writerow(row)

        # Print summary counts
        success_count = sum(1 for rec in ledger['cases'].values() if rec['status'] == 'STORED_STATE_CHECKED')
        failed_count = sum(1 for rec in ledger['cases'].values() if rec['status'] == 'FAILED')
        notrun_count = len(cases) - len(ledger['cases'])
        print(f"Success: {success_count}, Failed: {failed_count}, Not run: {notrun_count}")

        return 0

    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()



def main():
    parser = argparse.ArgumentParser(description='Serial scientific computation executor')
    parser.add_argument('campaign', help='Campaign directory')
    parser.add_argument('--backend', required=True, help='Backend directory')
    parser.add_argument('--solver', required=True, help='Path to solver executable')
    parser.add_argument('--checker', required=True, help='Path to checker executable')
    parser.add_argument('--target-radius', type=float, required=True,
                        help='Target radius for residual calculation')
    parser.add_argument('--max-launches', type=int, default=None,
                        help='Maximum cumulative launches')
    parser.add_argument('--timeout', type=int, default=180,
                        help='Timeout per process in seconds')
    parser.add_argument('--stop-after-failures', type=int, default=3,
                        help='Stop after N consecutive failures')
    args = parser.parse_args()

    try:
        ret = execute(args.campaign, args.backend, args.solver, args.checker,
                      args.target_radius, args.max_launches, args.timeout,
                      args.stop_after_failures)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        ret = 1
    sys.exit(ret)


if __name__ == '__main__':
    main()
