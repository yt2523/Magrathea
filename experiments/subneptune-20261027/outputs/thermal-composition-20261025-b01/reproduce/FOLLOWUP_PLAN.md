# Follow-up comparison plan — 2026-10-25

User authorizes continuing comparisons and adding uncertainty controls. Source baseline 9e74aac; unchanged clean mode0 worktree. No downloads, source changes, push, or new environments.

Ruling: saved two earlier outputs already complete. Continue with (A) temperature boundary x gas fraction forward grid and (B) synthetic radius recovery under a wrong temperature, rather than rerunning identical earlier cases. This still does NOT inject a full TP curve; it measures boundary-temperature sensitivity within gas_default, whose built-in mu transition remains fixed. Full TP-shape bias remains future work.

A: M=5,8.04 Earth masses; fgas=.003,.01,.03; Ts=300,360,450K; rock core/mantle=.325/.675; Psurface=.05bar, no water, zero layer T jumps. 18 forward runs. Check radius monotonicity in sampled temperature/fraction.
B: target each mass at Ts360,f=.01. Recover f via bracketed log-space bisection at Ts300 and450, keeping total mass/rock ratio/pressure/EOS fixed. Use grid brackets if available, expand only within [.0001,.1]. Max12 iterations per recovery, relative radius residual <=2e-5; save signed residual bracket and all evaluations, no statistical posterior claims. Same-temperature recovery is the .01 control.
Controls: baseline and each recovered midpoint with tighter ODE/fit tolerances (6); compare gas_default against HHe_tabulated at f=.01, Ts360/450 for both masses (4). EOS change is an EOS+thermal-law package sensitivity, not a pure EOS or TP effect. Inspect phase coverage and base temperatures. Stop unphysical/numerically invalid profiles; retain failures.
Budget: sequential, 45s each, <=100 runs, no per-case LLM calls. Reuse existing driver, immutable per-call CSV+output and persisted case summaries. Final CSV, plots, report, manifest; independent final review. Re-run unit checks only for new experiment logic, numerical bracket and tighter tolerance checks are the science gates.
Rollback: remove only this follow-up tooling commit with git revert if desired; all solver C++ and existing results untouched. Deliverables use a new D: folder.
