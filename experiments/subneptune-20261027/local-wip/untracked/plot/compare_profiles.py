#!/usr/bin/env python3
"""Compare one or more MAGRATHEA mode-0 structure profiles; never alters inputs.

python plot/compare_profiles.py result1.txt result2.txt -o comparison.png
In WSL, bash plot/compare_profiles.sh ... also uses an existing Windows Python
when Ubuntu does not have NumPy/Matplotlib installed.
"""
import argparse
import math
import os
from pathlib import Path
import sys


def parse_profile(text, source='<profile>'):
    """Parse six numeric columns plus the complete, space-containing phase label."""
    rows, phases = [], []
    header_count = 0
    for number, line in enumerate(text.lstrip('\ufeff').splitlines(), 1):
        if not line.strip():
            continue
        if line.strip().startswith('Index'):
            header_count += 1
            if header_count > 1:
                raise ValueError(f'{source}: appended runs detected; split the file before plotting')
            continue
        if header_count != 1:
            raise ValueError(f'{source}: missing MAGRATHEA Index header')
        parts = line.split(maxsplit=6)
        if len(parts) != 7:
            raise ValueError(f'{source}:{number}: expected six numeric columns and a phase label')
        try:
            values = [float(value) for value in parts[:6]]
        except ValueError as error:
            raise ValueError(f'{source}:{number}: invalid numeric column') from error
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f'{source}:{number}: values must be finite')
        if min(values[1:4]) < 0 or values[4] <= 0 or values[5] < 0:
            raise ValueError(f'{source}:{number}: invalid radius, pressure, mass, density or temperature')
        if rows and (values[1] < rows[-1][1] - 1e-9 or values[3] < rows[-1][3] - 1e-9):
            raise ValueError(f'{source}:{number}: radius and mass must be ordered from centre to surface')
        rows.append(values)
        phases.append(parts[6].strip())
    if len(rows) < 2:
        raise ValueError(f'{source}: at least two data rows are required')
    return rows, phases


def local_path(value):
    """Accept /mnt/d/... arguments when the WSL launcher uses Windows Python."""
    if os.name == 'nt' and len(value) > 7 and value.startswith('/mnt/') and value[6] == '/':
        value = value[5].upper() + ':/' + value[7:]
    return Path(value).expanduser().resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='+', help='Structure profile files, one planet per file')
    parser.add_argument('-o', '--output', help='Figure path ending in .png, .pdf or .svg')
    parser.add_argument('--labels', nargs='+', help='Optional names, exactly one per input file')
    parser.add_argument('--log-pressure', action='store_true', help='Logarithmic pressure axis for atmosphere comparisons')
    args = parser.parse_args(argv)
    if args.labels is not None and len(args.labels) != len(args.files):
        parser.error('--labels must contain exactly one name per input file')
    paths = [local_path(value) for value in args.files]
    output = local_path(args.output) if args.output else paths[0].parent / 'profiles-comparison.png'
    if output.suffix.lower() not in {'.png', '.pdf', '.svg'}:
        parser.error('output must end in .png, .pdf or .svg')
    if output in paths:
        parser.error('the figure cannot overwrite an input profile')
    tp_output = output.with_name(output.stem + '_tp' + output.suffix)
    if tp_output in paths:
        parser.error('the T-P figure cannot overwrite an input profile')
    profiles = []
    for i, path in enumerate(paths):
        try:
            rows, phases = parse_profile(path.read_text(encoding='utf-8-sig'), str(path))
        except (OSError, ValueError) as error:
            parser.error(str(error))
        profiles.append((args.labels[i] if args.labels else path.stem, rows, phases))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep configurable plotting caches beside the requested D-drive output.
    os.environ.setdefault('MPLCONFIGDIR', str(output.parent / '.plot-cache'))
    try:
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError as error:
        parser.error(f'{error}. Requires existing NumPy and Matplotlib; WSL users can use compare_profiles.sh.')

    for font in [Path('C:/Windows/Fonts/msyh.ttc'), Path('/mnt/c/Windows/Fonts/msyh.ttc')]:
        if font.is_file():
            font_manager.fontManager.addfont(str(font))
            plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font)).get_name()
            break

    legend_rows = math.ceil(len(profiles) / 2)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.6 + 0.3 * legend_rows))
    tp_fig, tp_ax = plt.subplots(figsize=(8, 6.5 + 0.3 * len(profiles)))
    colours = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9']
    styles = ['-', '--', '-.', ':']
    print('Case | M [ME] | R [RE] | surface T [K] | surface P [bar]')
    for i, (label, rows, phases) in enumerate(profiles):
        values = np.asarray(rows)
        surface = values[-1]
        legend = f'{label}: M={surface[3]:g}, R={surface[1]:.5f}, T0={surface[5]:g} K, P0={surface[2]*1e4:g} bar'
        for ax, column in zip(axes.flat, [4, 2, 5, 3]):
            y = values[:, column].copy()
            if column == 2 and args.log_pressure:
                y[y <= 0] = np.nan
            ax.plot(values[:, 1], y, color=colours[i % len(colours)],
                    linestyle=styles[i % len(styles)], linewidth=1.6, label=legend)
        # Pressure is plotted in bar; nonpositive points break the logarithmic curve.
        tp_pressure = np.where(values[:, 2] > 0, values[:, 2] * 1e4, np.nan)
        tp_ax.plot(values[:, 5], tp_pressure, color=colours[i % len(colours)],
                   linestyle=styles[i % len(styles)], linewidth=1.6, label=legend)
        print(f'{label} | {surface[3]:.8g} | {surface[1]:.8g} | {surface[5]:.8g} | {surface[2]*1e4:.8g}')

    for ax, title, ylabel in zip(axes.flat,
            ['Density profile', 'Pressure profile', 'Temperature profile', 'Enclosed mass profile'],
            [r'Density [g cm$^{-3}$]', 'Pressure [GPa]', 'Temperature [K]', r'Enclosed mass [$M_\oplus$]']):
        ax.set(title=title, xlabel=r'Radius from centre [$R_\oplus$]', ylabel=ylabel)
        ax.grid(alpha=0.25, linewidth=0.6)
        ax.set_xlim(left=0)
        if title != 'Pressure profile' or not args.log_pressure:
            ax.set_ylim(bottom=0)
    if args.log_pressure:
        axes[0, 1].set_yscale('log')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    # Long metadata labels are kept on separate lines, readable in saved figures.
    bottom = 0.065 + 0.027 * len(profiles)
    fig.legend(handles, labels, loc='lower center', ncol=1, fontsize=8,
               bbox_to_anchor=(0.5, 0.025), frameon=False)
    fig.suptitle('MAGRATHEA structure comparison', fontsize=15)
    fig.tight_layout(rect=(0, min(bottom, 0.55), 1, 0.95))
    fig.savefig(output, dpi=180)
    plt.close(fig)
    tp_ax.set(title='MAGRATHEA temperature-pressure profile', xlabel='Temperature [K]', ylabel='Pressure [bar]')
    tp_ax.set_yscale('log')
    tp_ax.invert_yaxis()
    tp_ax.set_xlim(left=0)
    tp_ax.grid(which='both', alpha=0.25, linewidth=0.6)
    tp_fig.legend(*tp_ax.get_legend_handles_labels(), loc='lower center', ncol=1,
                  fontsize=8, bbox_to_anchor=(0.5, 0.015), frameon=False)
    tp_fig.tight_layout(rect=(0, min(bottom, 0.55), 1, 1))
    tp_fig.savefig(tp_output, dpi=180)
    plt.close(tp_fig)
    print(f'Saved: {output}')
    print(f'Saved T-P: {tp_output}')
    print('Radius is actual R/RE, not radius normalised to each planet. Values reflect printed profile precision.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
