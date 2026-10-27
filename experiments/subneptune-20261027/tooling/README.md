# TP wrapper repair and mode0 input workbench

The user authorized Codex to repair this external code directly. MAGRATHEA source is unchanged. The original failing wrapper is retained at local commit81df8b4. The repaired wrapper passed its original12 acceptance tests, and all54 output rows agree with the previously independently checked fixed-input experiment to floating-point precision. DeepSeek independently reviewed the Codex-authored repair and batch driver.

## Use

PowerShell, from this directory:

```powershell
# Check repaired TP utility; uses existing Python environment, no installation.
& 'D:\GPT\projects\Sub-Neptune\tp-lab\.venv\Scripts\python.exe' -B check_tp.py .
& 'D:\GPT\projects\Sub-Neptune\tp-lab\.venv\Scripts\python.exe' -B compare_tp.py
# Optional small pilot: '{"levels":[181]}' | & <python> -B compare_tp.py

# Run one mode0 per CSV row; a unique D: output directory is created by default.
.\Run-Mode0.ps1 -Table .\demo_cases.csv
# Pilot: add -Limit 1.
# Resume a given output directory; existing valid profiles are hashed and skipped.
.\Run-Mode0.ps1 -Table .\demo_cases.csv -Output 'D:\GPT\projects\Sub-Neptune\outputs\mode0-inputs-20261025-a17b' -Resume
```

CSV masses are layer masses in Earth masses, surface_temp is Kelvin, P_surface is microbar, tight0/1 controls only the two documented solver tolerances. IDs must be unique simple filenames. Copy the CSV to create a new set of cases; do not overwrite a prior run. These demo masses5 and8.04 and gas fraction1% are synthetic test recipes, not observed-planet fits. The initial template selects gas_default; this version keeps its EOS selections fixed. To change EOS selections, prepare and explicitly validate a different template through the underlying driver --template option.

The driver runs only input_mode0. It invokes the unchanged solver once per input, writes a unique attempt folder, validates output mass/temperature/pressure units and profiles, imposes a timeout, records hashes and can resume. It does not expose a full generic TP-table interface or claim convergence from exit code0 alone. Internal solver status is not printed by the unchanged CLI; repeat and tighter-tolerance comparisons are numerical checks, not a proof of global convergence.

## Why the new solver directory exists

The executable in the original Magrathea directory produced only7.9596 Mearth for an8.04 Mearth input, omitting the specified atmosphere mass. The same unchanged tracked source, freshly compiled with make -B -j2 in an isolated worktree, produces the correct8.04 mass and historical baseline radius1.9811274 Rearth. The failed attempt and original binary hash are preserved. Do not use the old executable for research until its provenance is resolved.

Default clean build: D:\GPT\projects\Sub-Neptune\work\magrathea-mode0-clean-20261025-a17b.
Branch: workflow/mode0-inputs-20261025, based on9e74aac. No C++ edits. The original repo, dirty configs/plot scripts and executable are retained unchanged.

## Scientific boundaries

mode0 currently accepts masses, boundary temperatures/pressure, temperature jumps, tolerances and built-in EOS choices; it does not accept a complete external TP profile. Built-in gas_default also changes its molar-mass parameter from3 on the isothermal side to2 on the adiabatic side. A simple movement of the100bar phase boundary would therefore mix thermal and density assumptions. This batch changes the outer temperature at fixed model choices; it is not a pure TP-shape or composition-inference experiment.

Source changes are permitted by the latest user instruction if reversible. If a file-based TP interface is needed next, implement it on the isolated branch with an optional field and unchanged-default regression; do not silently modify the100bar logic and call it a pure thermal comparison.

## Read results / rollback

Start with D:\GPT\projects\Sub-Neptune\outputs\mode0-inputs-20261025-a17b\REPORT.md, then comparison.csv, input_table.csv and per-case attempt files. Original wrapper failures remain in the earlier workflow run. Local Git contains a baseline and repair commit; use git show 81df8b4:compare_tp.py to inspect the old code. There is no solver source edit to undo. Do not reset or clean the user's original checkout. Nothing was pushed to GitHub.
