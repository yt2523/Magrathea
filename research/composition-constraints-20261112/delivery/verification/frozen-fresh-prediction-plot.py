import argparse
import csv
import json
import hashlib
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.tri import Triangulation, LinearTriInterpolator


matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


def read_samples(paths):
    import csv, json, hashlib
    from pathlib import Path
    import numpy as np

    samples = {}
    source_hashes = {}
    for path in paths:
        p = Path(path)
        with p.open('r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    M = float(row['M'])
                    fFe = float(row['fFe'])
                    fSi = float(row['fSi'])
                    fWater = float(row['fWater'])
                    fGas = float(row['fGas'])
                    R_RE = row['R_RE'].strip()
                    status = row['status'].strip()
                    reason = row.get('reason', '').strip()
                    elapsed = row.get('elapsed', '').strip()
                    aliases = json.loads(row['aliases'])
                    families = json.loads(row['families'])
                except Exception as e:
                    raise ValueError(f"Error parsing row in {path}: {e}")

                
                if not np.isfinite(M) or M <= 0:
                    raise ValueError(f"Invalid M in {path}: {M}")
                
                fracs = [fFe, fSi, fWater, fGas]
                if not all(np.isfinite(x) and x >= 0 for x in fracs):
                    raise ValueError(f"Invalid fractions in {path}: {fracs}")
                if abs(sum(fracs) - 1.0) > 1e-12:
                    raise ValueError(f"Fractions do not sum to 1 in {path}: {fracs}")
                if not (0 < fGas < 1):
                    raise ValueError(f"fGas must be between 0 and 1 exclusive in {path}: {fGas}")
                
                if status not in ('STORED_STATE_CHECKED', 'FAILED', 'NOT_RUN'):
                    raise ValueError(f"Invalid status in {path}: {status}")
                
                if status == 'STORED_STATE_CHECKED':
                    try:
                        R = float(R_RE)
                        if not np.isfinite(R) or R <= 0:
                            raise ValueError
                    except:
                        raise ValueError(f"Invalid R_RE for successful sample in {path}: {R_RE}")
                else:
                    if R_RE != '':
                        raise ValueError(f"R_RE must be empty for non-successful sample in {path}: {R_RE}")
                    R = None
                
                if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
                    raise ValueError(f"aliases must be list of strings in {path}")
                if not isinstance(families, list) or not all(isinstance(fam, str) for fam in families):
                    raise ValueError(f"families must be list of strings in {path}")

                
                key_fracs = tuple(round(x, 14) for x in (fFe, fSi, fWater, fGas))
                key = (round(M, 14), key_fracs)

                if key in samples:
                    existing = samples[key]
                    
                    if existing['status'] != status:
                        raise ValueError(f"Duplicate sample with conflicting status: {key}")
                    if status == 'STORED_STATE_CHECKED':
                        if abs(existing['R_RE'] - R) > 1e-8:
                            raise ValueError(f"Duplicate sample with conflicting R: {key}")
                    
                else:
                    samples[key] = {
                        'M': M,
                        'fFe': fFe,
                        'fSi': fSi,
                        'fWater': fWater,
                        'fGas': fGas,
                        'R_RE': R,
                        'status': status,
                        'aliases': aliases,
                        'families': families,
                        'reason': reason,
                        'elapsed': elapsed
                    }
        
        with p.open('rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        source_hashes[str(p)] = file_hash

    return samples, source_hashes

def family_samples(samples, kind):
    result = []
    for s in samples.values():
        if kind == 'wet':
            if s['fSi'] == 0:
                result.append(s)
        elif kind == 'dryrocky':
            if s['fWater'] == 0:
                result.append(s)
        elif kind == 'dryFe':
            if s['fSi'] == 0 and s['fWater'] == 0:
                result.append(s)
        else:
            raise ValueError(f"Unknown kind: {kind}")
    return result

def apply_phase_groups(samples, path=None):
    """
    Apply phase group labels to samples based on an external diagnostic report.

    Parameters
    ----------
    samples : dict
        Dictionary of sample records keyed by sample ID. Each sample must have
        'M', 'fFe', 'fSi', 'fWater', 'fGas' fields.
    path : str or Path, optional
        Path to JSON report file. If None, all samples get phase_group='unspecified'
        and no extra masking is applied; metadata notes no phase gating.

    Returns
    -------
    None
        Modifies samples in place by adding 'phase_group' key.

    Raises
    ------
    FileNotFoundError
        If path is provided but file does not exist.
    ValueError
        If report format invalid, missing water>0 samples, or conflicting/illegal groups.
    """
    import json
    from pathlib import Path

    if path is None:
        for s in samples.values():
            s['phase_group'] = 'unspecified'
        return

    report_path = Path(path)
    if not report_path.exists():
        raise FileNotFoundError(f'Phase report file not found: {path}')

    with open(report_path, 'r') as f:
        report = json.load(f)

    if 'rows' not in report or not isinstance(report['rows'], list):
        raise ValueError('Phase report must contain a "rows" list')

    
    mapping = {}
    for row in report['rows']:
        if not all(k in row for k in ('M', 'fractions', 'diagnostic_group')):
            raise ValueError('Each row must have M, fractions, diagnostic_group')
        M = row['M']
        fractions = row['fractions']
        if not isinstance(fractions, list) or len(fractions) != 4:
            raise ValueError('fractions must be a list of 4 numbers [fFe, fSi, fWater, fGas]')
        fFe, fSi, fWater, fGas = fractions
        group = row['diagnostic_group']
        if group not in ('vapor', 'dense_fluid', 'unresolved_phase_cell'):
            raise ValueError(f'Illegal diagnostic_group: {group}')
        
        key = (round(M, 14), round(fFe, 14), round(fSi, 14), round(fWater, 14), round(fGas, 14))
        if key in mapping and mapping[key] != group:
            raise ValueError(f'Conflicting phase groups for sample {key}')
        mapping[key] = group

    
    for sample_id, s in samples.items():
        M = s['M']
        fFe = s['fFe']
        fSi = s['fSi']
        fWater = s['fWater']
        fGas = s['fGas']
        key = (round(M, 14), round(fFe, 14), round(fSi, 14), round(fWater, 14), round(fGas, 14))
        if fWater == 0:
            s['phase_group'] = 'no_water'
        elif key in mapping:
            s['phase_group'] = mapping[key]
        else:
            
            raise ValueError(f'Missing phase group for water>0 sample {sample_id} with key {key}')

    
def interpolate(samples, kind, mass, U, V):
    import numpy as np
    from matplotlib.tri import Triangulation, LinearTriInterpolator

    fam = family_samples(samples, kind)
    
    pts = [s for s in fam if s['M'] == mass]
    if len(pts) < 3:
        return np.ma.masked_all_like(U)

    
    x = []
    y = []
    R = []
    valid = []
    phase_groups = []
    for s in pts:
        x.append(s['fFe'] / (1 - s['fGas']))
        y.append(np.log10(s['fGas']))
        if s['status'] == 'STORED_STATE_CHECKED' and s['R_RE'] is not None:
            R.append(s['R_RE'])
            valid.append(True)
        else:
            R.append(0.0)  
            valid.append(False)
        
        phase_groups.append(s.get('phase_group', 'unspecified'))

    x = np.array(x)
    y = np.array(y)
    R = np.array(R)
    valid = np.array(valid)
    phase_groups = np.array(phase_groups)

    try:
        tri = Triangulation(x, y)
    except:
        return np.ma.masked_all_like(U)

    
    mask = np.zeros(tri.triangles.shape[0], dtype=bool)
    for i, tri_verts in enumerate(tri.triangles):
        if not all(valid[tri_verts]):
            mask[i] = True
            continue
        
        
        groups = phase_groups[tri_verts]
        
        relevant = [g for g in groups if g not in ('no_water', 'unspecified')]
        if relevant:
            
            if 'unresolved_phase_cell' in relevant:
                mask[i] = True
                continue
            
            if 'vapor' in relevant and 'dense_fluid' in relevant:
                mask[i] = True
                continue
            
    tri.set_mask(mask)

    
    if np.all(mask):
        return np.ma.masked_all_like(U)

    
    interp = LinearTriInterpolator(tri, R)
    result = interp(U, V)
    
    if not isinstance(result, np.ma.MaskedArray):
        result = np.ma.array(result)
    return result

import numpy as np
from scipy.interpolate import PchipInterpolator

def interpolate_track(samples, kind, mass, U, V):
    
    filtered = family_samples(samples, kind)
    rows = [s for s in filtered if s['M'] == mass]
    if not rows:
        return np.ma.masked_all(U.shape)

    
    U = np.asarray(U, dtype=float)
    V = np.asarray(V, dtype=float)
    if U.shape != V.shape:
        raise ValueError('U and V must have same shape')
    if U.ndim != 2:
        raise ValueError('U and V must be 2D')
    
    if not np.allclose(U, U[0:1, :]):
        raise ValueError('U must have identical rows (meshgrid)')
    if not np.allclose(V, V[:, 0:1]):
        raise ValueError('V must have identical columns (meshgrid)')
    uq = U[0, :]
    vq = V[:, 0]

    
    all_u = []
    for s in rows:
        fFe = s['fFe']
        g = s['fGas']
        if g >= 1.0:
            continue
        u_val = round(fFe / (1.0 - g), 12)
        all_u.append(u_val)
    if not all_u:
        return np.ma.masked_all(U.shape)
    uniqueu = np.unique(np.array(all_u))

    
    branchgroups = ['dense_fluid', 'vapor', 'generic']
    
    def map_phase(pg):
        if pg == 'dense_fluid':
            return 'dense_fluid'
        elif pg == 'vapor':
            return 'vapor'
        elif pg == 'no_water':
            
            
            pass

    
    def phase_matches(pg, branch):
        if branch == 'dense_fluid':
            return pg in ('dense_fluid', 'no_water')
        elif branch == 'vapor':
            return pg in ('vapor', 'no_water')
        elif branch == 'generic':
            return pg == 'unspecified'
        else:
            return False

    
    G_list = []
    for branch in branchgroups:
        
        Z = np.full((len(uniqueu), len(vq)), np.nan)
        
        
        u_to_rows = {}
        for s in rows:
            fFe = s['fFe']
            g = s['fGas']
            if g >= 1.0:
                continue
            u_val = round(fFe / (1.0 - g), 12)
            if u_val not in u_to_rows:
                u_to_rows[u_val] = []
            u_to_rows[u_val].append(s)
        
        for iu, u_val in enumerate(uniqueu):
            if u_val not in u_to_rows:
                continue
            rows_u = u_to_rows[u_val]
            
            rows_u_sorted = sorted(rows_u, key=lambda s: s['fGas'] if 'fGas' in s else 0.0)  
            
            
            segments = []
            current_seg = []
            for s in rows_u_sorted:
                
                if s.get('status') != 'STORED_STATE_CHECKED':
                    
                    if len(current_seg) >= 2:
                        segments.append(current_seg)
                    current_seg = []
                    continue
                R = s.get('R_RE')
                if R is None or not np.isfinite(R) or R <= 0:
                    if len(current_seg) >= 2:
                        segments.append(current_seg)
                    current_seg = []
                    continue
                pg = s.get('phase_group')
                if not phase_matches(pg, branch):
                    if len(current_seg) >= 2:
                        segments.append(current_seg)
                    current_seg = []
                    continue
                
                current_seg.append(s)
            
            if len(current_seg) >= 2:
                segments.append(current_seg)
            
            for seg in segments:
                
                lgs = np.array([np.log10(s['fGas']) for s in seg])
                Rs = np.array([s['R_RE'] for s in seg])
                
                if np.any(np.diff(lgs) <= 0):
                    continue  
                
                pchip = PchipInterpolator(lgs, Rs, extrapolate=False)
                
                min_lg = lgs[0]
                max_lg = lgs[-1]
                
                for j, v in enumerate(vq):
                    if min_lg <= v <= max_lg:
                        Z[iu, j] = pchip(v)
        
        
        G = np.full(U.shape, np.nan)
        for j in range(len(vq)):
            col = Z[:, j]
            finite_mask = np.isfinite(col)
            
            run_indices = []
            i = 0
            while i < len(finite_mask):
                if finite_mask[i]:
                    start = i
                    while i < len(finite_mask) and finite_mask[i]:
                        i += 1
                    end = i - 1
                    run_indices.append((start, end))
                else:
                    i += 1
            for start, end in run_indices:
                if end - start + 1 < 2:
                    continue
                run_u = uniqueu[start:end+1]
                run_R = col[start:end+1]
                
                
                pchip_u = PchipInterpolator(run_u, run_R, extrapolate=False)
                
                min_u = run_u[0]
                max_u = run_u[-1]
                for iu_global, u_val in enumerate(uq):
                    if min_u <= u_val <= max_u:
                        G[j, iu_global] = pchip_u(u_val)
        G_list.append(G)

    
    G_stack = np.ma.masked_invalid(np.stack(G_list, axis=0))  
    
    
    out = np.ma.masked_all(U.shape)
    
    for i in range(U.shape[0]):
        for j in range(U.shape[1]):
            vals = G_stack[:, i, j].compressed()  
            if len(vals) == 0:
                continue
            elif len(vals) == 1:
                out[i, j] = vals[0]
            else:
                
                rng = np.ptp(vals)
                if rng <= 1e-8:
                    out[i, j] = np.mean(vals)
                else:
                    
                    pass
    return out


def grids(samples, kind, masses, central_mass, R0, Rminus, Rplus, n=241, method='linear-tri'):
    import numpy as np

    
    if not np.isfinite(R0) or not np.isfinite(Rminus) or not np.isfinite(Rplus):
        raise ValueError("R0, Rminus, Rplus must be finite")
    if R0 <= 0 or Rminus <= 0 or Rplus <= 0:
        raise ValueError("R0, Rminus, Rplus must be positive")
    if R0 <= Rminus:
        raise ValueError("R0 must be greater than Rminus")
    if central_mass not in masses:
        raise ValueError("central_mass must be in masses")
    masses = sorted(masses)
    if len(masses) != len(set(masses)):
        raise ValueError("masses must be unique")

    fam = family_samples(samples, kind)
    if not fam:
        raise ValueError("No samples for this family")

    
    us = []
    vs = []
    for s in fam:
        us.append(s['fFe'] / (1 - s['fGas']))
        vs.append(np.log10(s['fGas']))
    umin, umax = min(us), max(us)
    vmin, vmax = min(vs), max(vs)

    
    U, V = np.meshgrid(np.linspace(umin, umax, n), np.linspace(vmin, vmax, n))

    R_by_mass = {}
    for m in masses:
        if method == 'linear-tri':
            R_by_mass[m] = interpolate(samples, kind, m, U, V)
        elif method == 'track-pchip':
            R_by_mass[m] = interpolate_track(samples, kind, m, U, V)
        else:
            raise ValueError(f"Unknown interpolation method: {method}")

    R_central = R_by_mass[central_mass]

    
    band_radius = np.ma.array(
        (R_central >= R0 - Rminus) & (R_central <= R0 + Rplus),
        mask=np.ma.getmaskarray(R_central)
    )

    
    any_masked = np.zeros(U.shape, dtype=bool)
    for m in masses:
        any_masked |= np.ma.getmaskarray(R_by_mass[m])

    
    minR = np.ma.masked_all(U.shape)
    maxR = np.ma.masked_all(U.shape)

    
    valid_indices = ~any_masked
    if np.any(valid_indices):
        
        R_stack = np.ma.stack([R_by_mass[m] for m in masses], axis=0)
        
        
        minR_full = np.ma.min(R_stack, axis=0)
        maxR_full = np.ma.max(R_stack, axis=0)
        
        minR[valid_indices] = minR_full[valid_indices]
        maxR[valid_indices] = maxR_full[valid_indices]

    
    band_mass = np.ma.array(
        (minR <= R0 + Rplus) & (maxR >= R0 - Rminus),
        mask=np.ma.getmaskarray(minR) | np.ma.getmaskarray(maxR)
    )

    return {
        'U': U,
        'V': V,
        'R_by_mass': R_by_mass,
        'R_central': R_central,
        'band_radius': band_radius,
        'band_mass': band_mass
    }


def render(samples, source_hashes, wet_grid, dry_grid, args, masses):
    """
    Render three figures (gas fractions, ternary diagrams, mass slices) and write analysis.json.
    Assumes output directory already exists.
    """
    outdir = Path(args.out)
    
    outdir.mkdir(parents=True, exist_ok=True)

    
    wet_U = wet_grid['U']
    wet_V = wet_grid['V']
    wet_R_by_mass = wet_grid['R_by_mass']
    wet_R_central = wet_grid['R_central']
    wet_band_radius = wet_grid['band_radius']
    wet_band_mass = wet_grid['band_mass']

    dry_U = dry_grid['U']
    dry_V = dry_grid['V']
    dry_R_by_mass = dry_grid['R_by_mass']
    dry_R_central = dry_grid['R_central']
    dry_band_radius = dry_grid['band_radius']
    dry_band_mass = dry_grid['band_mass']

    
    R0 = args.radius
    Rminus = args.radius_minus
    Rplus = args.radius_plus
    central_mass = args.central_mass

    
    def plot_gas_fraction_panel(ax, U, V, R_central, band_radius, band_mass, family_label, samples_family):
        
        
        ax.contourf(U, 10**V, band_mass.astype(float), levels=[0.5, 1.5], colors=['#FFDAB9'], alpha=0.5)
        
        ax.contourf(U, 10**V, band_radius.astype(float), levels=[0.5, 1.5], colors=['#ADD8E6'], alpha=0.5)

        
        try:
            cs = ax.contour(U, 10**V, R_central, levels=[R0], colors='black', linewidths=1.5)
        except Exception:
            
            pass

        
        central_samples = [s for s in samples_family if s['M'] == central_mass and s['status'] == 'STORED_STATE_CHECKED']
        if central_samples:
            us = [s['fFe'] / (1 - s['fGas']) for s in central_samples]
            vs = [s['fGas'] for s in central_samples]  
            ax.plot(us, vs, 'o', color='black', markersize=4, label='Central mass samples')

        
        failed_samples = [s for s in samples_family if s['status'] == 'FAILED']
        if failed_samples:
            us_fail = [s['fFe'] / (1 - s['fGas']) for s in failed_samples]
            vs_fail = [s['fGas'] for s in failed_samples]
            ax.plot(us_fail, vs_fail, 'x', color='red', markersize=5, label='Failed samples')

        
        ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, label='Pure Fe boundary')

        
        ax.set_xlabel('Fe fraction within non-gas material')
        ax.set_ylabel('H/He mass fraction')
        ax.set_yscale('log')
        ax.set_title(f'{family_label} family')

        
        handles = [
            Patch(facecolor='#FFDAB9', alpha=0.5, label='Mass envelope band'),
            Patch(facecolor='#ADD8E6', alpha=0.5, label='Radius band'),
            Line2D([0], [0], color='black', linewidth=1.5, label=f'R = {R0}'),
            Line2D([0], [0], color='gray', linestyle='--', label='Pure Fe boundary')
        ]
        if central_samples:
            handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=4, label='Central mass samples'))
        if failed_samples:
            handles.append(Line2D([0], [0], marker='x', color='red', markersize=5, linestyle='None', label='Failed samples'))
        ax.legend(handles=handles, loc='best', fontsize='small')

    
    fig1, axes1 = plt.subplots(1, 2, figsize=(12, 6))
    plot_gas_fraction_panel(axes1[0], wet_U, wet_V, wet_R_central, wet_band_radius, wet_band_mass, 'Wet', family_samples(samples, 'wet'))
    plot_gas_fraction_panel(axes1[1], dry_U, dry_V, dry_R_central, dry_band_radius, dry_band_mass, 'Dry Rocky', family_samples(samples, 'dryrocky'))
    fig1.suptitle('Gas Fraction Grids with Observational Bands')
    fig1.tight_layout(rect=[0, 0.14, 1, 0.95])
    fig1.text(0.5, 0.025, f'Mass envelope is conditional piecewise-linear in 3 sampled masses, not posterior. Temporary thermal boundary: T={args.surface_temperature} K, P={args.surface_bar} bar, transition bar={args.transition_bar}', ha='center', fontsize=8)
    fig1.savefig(outdir / 'gas-fractions.png', dpi=300)
    fig1.savefig(outdir / 'gas-fractions.pdf')
    plt.close(fig1)

    
    def plot_ternary_panel(ax, U, V, R_central, band_radius, band_mass, family_label, samples_family, component='water'):
        
        
        gas = 10**V
        x = (1 - gas) * (1 - U) + 0.5 * gas
        y = (np.sqrt(3) / 2) * gas

        
        ax.contourf(x, y, band_mass.astype(float), levels=[0.5, 1.5], colors=['#FFDAB9'], alpha=0.5)
        ax.contourf(x, y, band_radius.astype(float), levels=[0.5, 1.5], colors=['#ADD8E6'], alpha=0.5)

        
        try:
            ax.contour(x, y, R_central, levels=[R0], colors='black', linewidths=1.5)
        except Exception:
            pass

        
        central_samples = [s for s in samples_family if s['M'] == central_mass and s['status'] == 'STORED_STATE_CHECKED']
        if central_samples:
            us = [s['fFe'] / (1 - s['fGas']) for s in central_samples]
            vs = [np.log10(s['fGas']) for s in central_samples]
            gas_s = 10**np.array(vs)
            x_s = (1 - gas_s) * (1 - np.array(us)) + 0.5 * gas_s
            y_s = (np.sqrt(3) / 2) * gas_s
            ax.plot(x_s, y_s, 'o', color='black', markersize=4, label='Central mass samples')

        
        failed_samples = [s for s in samples_family if s['status'] == 'FAILED']
        if failed_samples:
            us_fail = [s['fFe'] / (1 - s['fGas']) for s in failed_samples]
            vs_fail = [np.log10(s['fGas']) for s in failed_samples]
            gas_f = 10**np.array(vs_fail)
            x_f = (1 - gas_f) * (1 - np.array(us_fail)) + 0.5 * gas_f
            y_f = (np.sqrt(3) / 2) * gas_f
            ax.plot(x_f, y_f, 'x', color='red', markersize=5, label='Failed samples')

        
        ax.plot([0, 1], [0, 0], 'k-', linewidth=1)
        ax.plot([0, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=1)
        ax.plot([1, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=1)
        
        for i in range(1, 10):
            frac = i / 10.0
            
            y_level = frac * np.sqrt(3) / 2
            ax.plot([frac/2, 1 - frac/2], [y_level, y_level], 'gray', linestyle=':', linewidth=0.5)
            
            x1 = 0.5 * (1 - frac)
            y1 = np.sqrt(3)/2 * (1 - frac)
            x2 = 1 - frac
            y2 = 0
            ax.plot([x1, x2], [y1, y2], 'gray', linestyle=':', linewidth=0.5)
            
            x1 = frac
            y1 = 0
            x2 = 0.5 + 0.5 * frac
            y2 = np.sqrt(3)/2 * (1 - frac)
            ax.plot([x1, x2], [y1, y2], 'gray', linestyle=':', linewidth=0.5)
        
        ax.text(-0.05, -0.05, 'Fe', ha='right', va='top', fontsize=12)
        if component == 'water':
            ax.text(1.05, -0.05, 'H2O', ha='left', va='top', fontsize=12)
        else:
            ax.text(1.05, -0.05, 'Silicate', ha='left', va='top', fontsize=12)
        ax.text(0.5, np.sqrt(3)/2 + 0.05, 'H/He', ha='center', va='bottom', fontsize=12)
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, np.sqrt(3)/2 + 0.1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'{family_label} family')

        
        handles = [
            Patch(facecolor='#FFDAB9', alpha=0.5, label='Mass envelope band'),
            Patch(facecolor='#ADD8E6', alpha=0.5, label='Radius band'),
            Line2D([0], [0], color='black', linewidth=1.5, label=f'R = {R0}'),
            Line2D([0], [0], color='gray', linestyle='--', label='Pure Fe boundary')
        ]
        if central_samples:
            handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=4, label='Central mass samples'))
        if failed_samples:
            handles.append(Line2D([0], [0], marker='x', color='red', markersize=5, linestyle='None', label='Failed samples'))
        ax.legend(handles=handles, loc='upper right', fontsize='small', bbox_to_anchor=(1.15, 1))

    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 6))
    plot_ternary_panel(axes2[0], wet_U, wet_V, wet_R_central, wet_band_radius, wet_band_mass, 'Wet', family_samples(samples, 'wet'), component='water')
    plot_ternary_panel(axes2[1], dry_U, dry_V, dry_R_central, dry_band_radius, dry_band_mass, 'Dry Rocky', family_samples(samples, 'dryrocky'), component='silicate')
    fig2.suptitle('Ternary Diagrams with Observational Bands')
    fig2.tight_layout(rect=[0, 0, 1, 0.95])
    fig2.text(0.5, 0.02, f'Mass envelope is conditional piecewise-linear in 3 sampled masses, not posterior. Temporary thermal boundary: T={args.surface_temperature} K, P={args.surface_bar} bar, transition bar={args.transition_bar}', ha='center', fontsize=8)
    fig2.savefig(outdir / 'ternary.png', dpi=300)
    fig2.savefig(outdir / 'ternary.pdf')
    plt.close(fig2)

    
    fig3, axes3 = plt.subplots(1, 3, figsize=(18, 6))

    
    def plot_composition_slices(ax, grid, family_label, masses):
        U = grid['U']
        V = grid['V']
        R_by_mass = grid['R_by_mass']
        
        colors = ['blue', 'black', 'orange']
        for i, m in enumerate(masses):
            R_m = R_by_mass[m]
            
            Rlow = R0 - Rminus
            Rhigh = R0 + Rplus
            mask = (R_m >= Rlow) & (R_m <= Rhigh)
            
            ax.contourf(U, 10**V, mask.astype(float), levels=[0.5, 1.5], colors=[colors[i % len(colors)]], alpha=0.3)
            
            try:
                ax.contour(U, 10**V, R_m, levels=[R0], colors=colors[i % len(colors)], linewidths=1.5)
            except Exception:
                pass
        
        ax.set_xlabel('Fe fraction within non-gas material')
        ax.set_ylabel('H/He mass fraction')
        ax.set_yscale('log')
        ax.set_title(f'{family_label} family composition compatibility')
        
        handles = [Line2D([0], [0], color=colors[i % len(colors)], lw=2, label=f'M={m}') for i, m in enumerate(masses)]
        ax.legend(handles=handles, loc='best', fontsize='small')

    
    plot_composition_slices(axes3[0], wet_grid, 'Wet', masses)
    
    plot_composition_slices(axes3[1], dry_grid, 'Dry Rocky', masses)

    
    ax = axes3[2]
    pure_fe_samples = family_samples(samples, 'dryFe')
    
    masses_pure = sorted(set(s['M'] for s in pure_fe_samples))
    for m in masses_pure:
        samples_m = [s for s in pure_fe_samples if s['M'] == m]
        
        samples_m_sorted = sorted(samples_m, key=lambda s: s['fGas'])
        gas = [s['fGas'] for s in samples_m_sorted]
        R = [s['R_RE'] if s['status'] == 'STORED_STATE_CHECKED' else np.nan for s in samples_m_sorted]
        
        R_masked = np.ma.masked_invalid(R)
        ax.plot(gas, R_masked, marker='o', linestyle='-', label=f'M={m}')
        
        failed = [s for s in samples_m_sorted if s['status'] == 'FAILED']
        if failed:
            gas_f = [s['fGas'] for s in failed]
            ax.plot(gas_f, [0.03]*len(gas_f), 'x', color='red', markersize=5, transform=ax.get_xaxis_transform(), label='FAILED: radius unavailable')
    ax.axhline(y=R0, color='black', linestyle='-', linewidth=1.5, label='R0')
    ax.axhspan(R0 - Rminus, R0 + Rplus, color='blue', alpha=0.2, label='Radius band')
    ax.set_xscale('log')
    ax.set_xlabel('Gas fraction')
    ax.set_ylabel('Radius (R_E)')
    ax.set_title('Pure Fe family')
    ax.legend(fontsize='small')

    fig3.suptitle('Mass Slices')
    fig3.tight_layout(rect=[0, 0, 1, 0.95])
    fig3.text(0.5, 0.02, f'Composition compatibility slices are conditional, not posterior. Temporary thermal boundary: T={args.surface_temperature} K, P={args.surface_bar} bar, transition bar={args.transition_bar}', ha='center', fontsize=8)
    fig3.savefig(outdir / 'mass-slices.png', dpi=300)
    fig3.savefig(outdir / 'mass-slices.pdf')
    plt.close(fig3)

    
    analysis = {
        'source_hashes': source_hashes,
        'samples': list(samples.values()),
        'masses': masses,
        'observational_box': {
            'R0': R0,
            'Rminus': Rminus,
            'Rplus': Rplus,
            'central_mass': central_mass
        },
        'interpolation_assumptions': 'spatial linear in (u, log10 gas) per exact mass; common-valid min/max sampledR envelope; intermediate masses assume continuous piecewise-linear branch; 3 samples do not bound unsampled extrema; not posterior' if args.interpolation == 'linear-tri' else 'PCHIP first loggas then nongasFe on continuous valid same-boundary-group tracks, noextrapolation; common-valid min/max sampledR envelope; intermediate masses assume continuous piecewise-linear branch; 3 samples do not bound unsampled extrema; not posterior; independent native holdouts still required',
        'thermal_parameters': {
            'surface_temperature': args.surface_temperature,
            'surface_bar': args.surface_bar,
            'transition_bar': args.transition_bar
        },
        'physical_acceptance': False,
        'success_count': sum(1 for s in samples.values() if s['status'] == 'STORED_STATE_CHECKED'),
        'fail_count': sum(1 for s in samples.values() if s['status'] == 'FAILED'),
        'notrun_count': sum(1 for s in samples.values() if s['status'] == 'NOT_RUN'),
        'family_band_touch': {},
        'phase_audit_provenance': {
            'enabled': args.phase_groups is not None,
            'path': args.phase_groups if args.phase_groups else None,
            'sha': hashlib.sha256(Path(args.phase_groups).read_bytes()).hexdigest() if args.phase_groups else None,
            'constraint': 'Vapor/dense-water crossing cells withheld when phase audit supplied'
        }
    }
    
    for fam_name, grid in [('wet', wet_grid), ('dryrocky', dry_grid)]:
        band_mass = grid['band_mass']
        U = grid['U']
        V = grid['V']
        
        touch_umin = np.any(band_mass[:, 0])
        touch_umax = np.any(band_mass[:, -1])
        touch_vmin = np.any(band_mass[0, :])
        touch_vmax = np.any(band_mass[-1, :])
        analysis['family_band_touch'][fam_name] = {
            'umin': bool(touch_umin),
            'umax': bool(touch_umax),
            'vmin': bool(touch_vmin),
            'vmax': bool(touch_vmax),
            'bounds': {
                'umin': float(np.min(U)),
                'umax': float(np.max(U)),
                'vmin': float(np.min(V)),
                'vmax': float(np.max(V)),
                'gasmin': float(10**np.min(V)),
                'gasmax': float(10**np.max(V))
            }
        }
        if touch_umin or touch_umax or touch_vmin or touch_vmax:
            analysis['family_band_touch'][fam_name]['note'] = 'UNRESOLVED DOMAIN EDGE'

    with open(outdir / 'analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description='Plot compositions from synthesis samples.')
    parser.add_argument('--summaries', nargs='+', required=True, help='CSV summary files')
    parser.add_argument('--out', required=True, help='Output directory (must not exist)')
    parser.add_argument('--radius', type=float, required=True, help='Central radius R0')
    parser.add_argument('--radius-minus', type=float, required=True, help='Radius minus band')
    parser.add_argument('--radius-plus', type=float, required=True, help='Radius plus band')
    parser.add_argument('--central-mass', type=float, required=True, help='Central mass')
    parser.add_argument('--surface-temperature', type=float, default=350.0, help='Surface temperature (K)')
    parser.add_argument('--transition-bar', type=float, default=100.0, help='Transition bar')
    parser.add_argument('--surface-bar', type=float, default=0.1, help='Surface bar')
    parser.add_argument('--phase-groups', type=str, default=None, help='Optional JSON file with phase group diagnostics')
    parser.add_argument('--interpolation', choices=['linear-tri', 'track-pchip'], default='linear-tri', help='Interpolation method')
    args = parser.parse_args()

    
    for val_name in ['radius', 'radius_minus', 'radius_plus', 'central_mass', 'surface_temperature', 'transition_bar', 'surface_bar']:
        val = getattr(args, val_name)
        if not np.isfinite(val) or val <= 0:
            raise ValueError(f'{val_name} must be finite positive')
    if args.radius <= args.radius_minus:
        raise ValueError('radius must be greater than radius_minus')

    
    samples, source_hashes = read_samples(args.summaries)

    
    if args.phase_groups:
        apply_phase_groups(samples, args.phase_groups)
    else:
        apply_phase_groups(samples, None)

    
    masses = sorted(set(s['M'] for s in samples.values()))
    if len(masses) != 3:
        raise ValueError('This tool requires exactly 3 distinct masses in samples')
    if args.central_mass not in masses:
        raise ValueError('central_mass must be one of the sample masses')

    
    wet_grid = grids(samples, 'wet', masses, args.central_mass, args.radius, args.radius_minus, args.radius_plus, method=args.interpolation)
    dry_grid = grids(samples, 'dryrocky', masses, args.central_mass, args.radius, args.radius_minus, args.radius_plus, method=args.interpolation)

    
    out_path = Path(args.out)
    if out_path.exists():
        raise FileExistsError(f'Output directory {args.out} already exists')
    out_path.mkdir(parents=True)

    
    render(samples, source_hashes, wet_grid, dry_grid, args, masses)

    print(f'Plots and analysis written to {args.out}')


if __name__ == '__main__':
    main()

