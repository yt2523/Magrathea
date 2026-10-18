"""Requires existing NumPy/Matplotlib; reads results without changing scientific data."""
from pathlib import Path
import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
out = args.output.resolve()
os.environ.setdefault('MPLCONFIGDIR', str(out / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

runs = {r['id']: r for r in json.loads((out / 'results.json').read_text())['runs']}
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), layout='constrained')
for key, label in [('paper_baseline', '2022 Brg/PPv recipe'),
                   ('current_default_control', 'Current default mantle')]:
    # Phase labels contain spaces; read the first six numeric columns only.
    values = np.loadtxt(out / runs[key]['profile'], skiprows=1, usecols=range(6))
    for ax, column, ylabel in zip(axes, [4, 2, 5], ['Density [g cm$^{-3}$]', 'Pressure [GPa]', 'Temperature [K]']):
        ax.plot(values[:, 1], values[:, column], label=label, lw=1.6)
        ax.set(xlabel=r'Radius [$R_\oplus$]', ylabel=ylabel)
        ax.grid(alpha=0.25)
axes[0].legend(fontsize=8)
fig.suptitle('Huang et al. (2022), Fig. 4 default model: independent rerun')
figures = out / 'figures'
figures.mkdir(exist_ok=True)
fig.savefig(figures / 'profiles.png', dpi=180)
fig.savefig(figures / 'profiles.pdf')
plt.close(fig)
keys = ['paper_baseline', 'paper_tighter', 'current_default_control']
values = [runs[k]['radius_RE'] for k in keys]
fig, ax = plt.subplots(figsize=(7.2, 3.6), layout='constrained')
ax.scatter(values, range(3), s=45, zorder=3)
ax.axvspan(0.96675, 0.96685, alpha=0.3, color='green', label='Paper rounding interval')
ax.axvline(0.9668, color='green', lw=1)
for i, value in enumerate(values):
    ax.annotate(f'{value:.9f}', (value, i), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=9)
ax.set(yticks=range(3), yticklabels=['Paper recipe', 'Tighter ODE + fitting', 'Current default mantle'],
       xlabel=r'Planet radius [$R_\oplus$]', ylim=(-0.5, 2.5), xlim=(0.965, 0.9855))
ax.grid(axis='x', alpha=0.25)
ax.legend(loc='lower right', fontsize=8)
fig.savefig(figures / 'radii.png', dpi=180)
fig.savefig(figures / 'radii.pdf')
print('Wrote profiles/radii PNG and PDF.')
