# Native audit adapter interface notes — 2026-11-12

This is the current adapter contract, not a replacement for the historical prescribed-TP v1 spec. Read the targeted files listed below, then compile and probe before any planet run.

|Concern|Actual interface|Required behavior|
|---|---|---|
|EOS variable vs human name|Gas_iso / Gas_hhe are global EOS*; getEOS() is an instance getter with no arguments|Construct vector<EOS*> from allowed IDs and match pointer->getEOS() to saved full phase label; no static name lookup exists|
|Native audit IDs|configure_prescribed_hhe_audit() in phase.cpp registers IDs and enables strict table audit|Call before every standalone --run/--probe/--check; it does not impose external TP by itself|
|Density pressure|EOS::density(P_cgs,T,rho_guess)|1bar=1e6cgs;1GPa=1e10cgs;100bar=1e8cgs|
|Adiabatic-gradient pressure|EOS::dTdP_S(P_GPa,T,rho_guess)|100bar=.01GPa; returned derivative is K/GPa|
|Native selectors|find_phase_HHe_tabulated(P_cgs,T)|Gas_iso if P<1e8cgs, Gas_hhe otherwise. Pointer comparison, not human string==variable name|
|Human gas names|Gas_iso->getEOS()="Isothermal Ideal Gas"; Gas_hhe->getEOS()="H/He (Chabrier)"|Variable IDs are different strings; use audit_id() for machine output|
|Native .dat|Index,R_earth,P_GPa,M_earth,rho_g_cm3,T_K,remaining full phase name|Eight significant digits and subsampled stored states; check all stored rows, not all integrator states|
|Legacy output behavior|hydro::print appends; native CLI can return0 with nullptr and no output|Preflight absent model/runtime files; require new model saved, not exit0 alone|
|Serialization|Already-working tests/tp_off_probe.cpp gives a valid C++ JSON example|After JSON model reply is decoded, C++ newline must be backslash-n once, not double-backslash-n. Numeric end pointer compares '\0', not multi-character '\\0'|
|TP spec historical scope|docs/TP_INTERFACE_SPEC.md v1 initially used ideal fixedmu2|Do not silently impose its old ideal fixture on present real-HHe native control. No external TP in this control|
|Physical interpretation|Native switch also changes EOS/composition approximation|Previously verified26.341% common-state density drop stays a limitation even if runs converge|

Reuse tests/test_pilot_eos.cpp for registered audit IDs, strict-domain behavior and unit examples. Reuse tests/test_interface_temperature.cpp for stored-density-at-stored-T checking. check_pilot_model.py has independently validated float-axis bilinear interpolation. Existing prescribed-TP checkers assume TP sidecars and are not drop-in validators for a noTP native run.
