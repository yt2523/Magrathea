# TOI-732 c composition-constraint long task — execution plan

**Goal:** Deliver a reproducible first composition-compatibility region/central-radius locus with mass and radius uncertainty, under explicitly recorded thermal/material assumptions. No unique-composition or Bayesian credible-region claim without the corresponding statistical model.

**Base:** a81aa299f114a48ef52a6277c852b92500b4662c, research/unified-hhe-100bar-20261112. The gas100bar density seam is already fixed and independently checked; do not restart that task or spend its closed budget. User requested a long task plan first. This document is a proposed bounded execution contract, not evidence that later stages have run or an unlimited computation authorization.

**Architecture:** Existing C++ forward solver remains the calculator; DeepSeek implements minimal changes and drivers, Codex fixes interfaces/tests, diagnoses and orchestrates, uninvolved Codex reviews. Every model maps mass+composition+thermal input to radius/profile, then evaluates observation residuals. Observed radius never becomes a forward-solver boundary. Reuse existing EOS options before inventing new equations.

**Routing/storage:** fixed D:/Codex/downloads/subneptune-research-workflow; all new data/tmp onD. Development/new hypotheses/tests only yt2523/Magrathea. Each stage branch has an up-to-date README with base, source/config identity, exact command, acceptance evidence, unresolved issues and next action. cid02399021 manual release is unchanged; prepare a clean runnable release candidate without test/history payloads. Preserve old results and private transcripts/credentials outsideGit. No old chats or new user chats needed.

## What already passed, and must not be repeated as busywork

- Same-HHe density on both sides of100bar; same-state difference0.
- Both-direction thermal callback checks,144 oldEOS checks, strict-domain and parser/refusal gates.
- grid14/grid20 baseline+tight,4runs; R~2.36889/2.54272RE.
- Existing native profile/state audit and independent bilinear table checker.

Reuse these identities/evidence unless an actual dependency changes. Build fresh with make -B; no reliance on stale.o. New changed behavior gets a targeted failing test; do not rerun historical54/8/67sets or old24grid just for packaging.

## Budget proposed for the whole long task

New upper bound180 native planetary launch attempts, distributed below, including failures/timeouts/tight repeats. Each new launch <=180s initially; record aggregate walltime perstage and stop on a declared repeated cause, not a silent infinite retry. No more than12 new DeepSeek calls initially, against current reset epoch4/88; reserve calls before use. These caps apply only after this long plan is accepted; current completed-task ledgers remain immutable. PureEOS point queries/analytic fixtures do not count as full planets, but are bounded and logged separately (first water audit<=300paired P/T queries).

|Stage|Native-attempt allocation|Deliverable|
|---|---:|---|
|A waterEOS/phase consistency|12|Documented material/thermal model usable for representative planets|
|B domain-aware externalTP initialization|8|Clearly separated numerical failure vs TP coverage shortfall|
|C mass-vector/thermal sensitivity integration|12|Batch inputs, consistent model identities and mass slices|
|D coarse composition scan|72|Three mass slices, classified sparse composition map|
|E adaptive refinement|48|Central-radius branches and observation-compatible area boundary|
|F holdout/tightening/release checks|12|Error evidence, figures, independently reviewed runnable candidate|
|Reserve|16|Unresolved cells/boundary expansion or additional mass knots, never automatic reruns|

Total12+8+12+72+48+12+16=180. Reallocate unused earlier quota explicitly in the ledger before a dependent stage; unused quota is not a reason to run more cases. If coverage cannot be justified within budget, deliver an honest unresolved map or mass slices instead of claiming completion.

## A — Resolve the water seams that the actual trajectories cross

**Question:** Are the1280K Brown/Mazevet and encountered ice/highP changes true phase transitions or mismatched EOS source joins? A density jump at a genuine first-order phase transition is not automatically a bug.

- Read source validity/provenance of relevant current waterEOS tables and the existing optional water_tabulated route. Inspect only seams crossed by saved grid14/grid20 trajectories; avoid a general EOS rewrite.
- Evaluate both sides at the SAME P/T in valid overlaps, recordingrho and available thermal gradients plus phase category. Do not hide mismatch with arbitrary linear blending, constant offsets or pressure clamping; continuity alone does not guarantee thermodynamic consistency.
- Prefer an opt-in comparison using an already-available, adequately sourced unified table over changing physical formulas. water_tabulated is a candidate to assess, not a preapproved scientific default. Verify its tabulated axes/units/thermal closure and phase interpretation first.
- After pureEOS queries establish a justified candidate, use up to12representative native attempts including selected density/temperature extremes and tighter confirmations. Do not rerun the same old case when nothing changed.
- Exit: a traceable selected comparison model, no known unhandled artificial seam in the region used for inference, documented retained physical transitions and limits; actual saved-state checks pass.
- Decision requiring user discussion: replacing physical EOS formulae, mixing water/HHe or rock/water, changing actual phase boundaries, or choosing between materially different plausible model families with different conclusions. Prepare concrete comparative evidence first. Do not silently make the curves smooth to obtain a pass.

**Output:** research/water-eos-audit-<date>/README, source/overlap/phase map, paired-query data, representative profiles, decision record and independent review. Literature in Zotero as papers/child notes; input/theory/source vs solver outputs correctly separated.

## B — Restore externalTP as a viable route without inventing temperatures

Keep the existing T–lnP interpolation and default strict coverage rejection. Do not quietly change to lnT–lnP, clamp to the lastT or append an adiabat. This is a numerical search change separate from stageA model choices.

- Freeze old successful/failed input fixtures to isolate initialization behavior; their old water model is an engineering fixture, not the final scientific model selection.
- DeepSeek adds bounded search for evaluable radius trials before establishing a valid residual bracket. An invalid trial supplies no fabricated residual sign. Do not assume global monotonicity or that one invalid trial proves the composition impossible.
- Record attempted radius, remaining gas mass, pressure limit, rejection reason, successful bracket and final coverage. Limit the initial search to at most12trial radii per externalTP native launch, with existing walltime cap.
- Fixed tests: invalid first endpoint but valid later bracket; genuinely insufficient TP coverage; non-bracketed/multiple candidate intervals; no change in the old successful forward result beyond fixed numerical tolerance.
- Up to8full attempts with actual inputs and tight repeats. FiniteTP shortfall remains a named outcome; if a true solution needs deeperTP, source a physical profile or separately discuss continuation assumptions.
- Exit: recover valid domain-limited cases where supported, otherwise produce truthful coverage/nonconvergence statuses. No promise that all eight historical crosses disappear.

**Output:** optional initialized-search change, fixed RED/GREEN fixtures, true result or classified shortfall for representatives, no fake extrapolation.

## C — Consistent mass-vector input and thermal scenarios

- Reuse native single-case solver. Batch accepts a mass vector; for everymass recompute layer masses M_i=f_i*M, with fractions exactly normalized. Zero component mass stays0, not epsilon. All other parameters tied to an immutable scenarioID.
- Initial engineering vector[7.56,8.04,8.54]ME from previously adopted8.04(+.50/-.48). These three values demonstrate sensitivity, not completed mass-uncertainty propagation. Reverify observation provenance/units before scientific interpretation.
- Prefer the already-declared100bar approximate thermal scenario for a first conditional map. ExternalTP is a separate scenario when sourced and covered, not silently mixed point-by-point with fallback atmospheres.
- Evaluate30/300bar only on representatives if a pure thermal-sensitivity comparison is needed, using SAME HHe density/composition throughout. Use at most12stageC attempts including mass-vector checks; budget pressure expansion ahead of fullcomposition refinement if needed.
- Formal companion TP can be integrated when delivered, with pressure/radius reference, composition,flux/cloud assumptions and deeper closure explicit. Do not copy TOI-270d temperature nodes as TOI-732c data or stall all conditional software work awaiting a formal profile.

**Output:** minimal batch entry point + scenario manifest + three mass slices for tested representatives. GASTLI-style parameter separation is a design reference, not a reason to replace the solver.

## D — Scan a coarse domain to find regions, not one point

Tentative baseline:3masses x6nongas ratios x4gas fractions=72unique native attempts. Nongas ratio u=Fe/(Fe+H2O) in[.1,.3,.5,.7,.9,1]; gasg in[1e-5,1e-4,1e-3,1e-2]. FractionsFe=(1-g)u,H2O=(1-g)(1-u),HHe=g,Si0. This is a proposed exploration range, not a scientifically excluded exterior. Some u1points are dry iron endmembers; they are not a substitute for the later full no-water study.

Record for everypoint: input mass/fractions, scenario, source identities, R/P/T/phase outputs, signedradius residual, solver/domain status and runtime. Distinguish input-invalid, EOS-outside-domain, TP-shortfall, numerical nonconvergence, and valid-observation-mismatch. Preserve failures; plot them differently rather than deleting them.

At this stage produce actual three mass-slice maps and a coarse central-radius locus only where brackets exist. Do not draw a smooth closed uncertainty area through unresolved/failed cells.

## E — Refine area boundaries using residual information

- Use u vs log(g) grid and mass as a further coordinate; keep everyconnected candidate branch, not one Newton path to a bestpoint.
- Refine cells touching signchanges/observation thresholds, high residual curvature, phase/source changes and success/failure boundaries. Same-sign corners alone do not prove no interior solution. Reserve distributed off-boundary holdouts/global probes against missed islands.
- For each fixedu/M, bracket/refine ALL supported gas-fraction crossings. Use local residual slope/secant only inside an established valid bracket; never apply it acrossfailed points or phasechanges without checks.
- Cache by complete physical/numerical scenario identity (not fractions alone). No results reuse acrosschangedEOS/TP/solver/tolerances. Broad global surrogate/MCMC/parallel optimization is deferred until basic scanworks.
- If a compatible branch reaches a domainedge, spend explicit reserve to expand thatedge before labeling it excluded. Use48new attempts maximum in thisstage and preserve remaining unresolved cells.

**Output:** sampled best-radius branches plus observational-compatibility boundaries with interpolation/coverage quality masks; no unsupported global uniqueness claim.

## F — Propagate uncertainty honestly and release a reviewable result

The mass coordinate cannot be handled by one fixed-mass scan. Reuse coarse mass slices, add mass knots where radius-vs-mass interpolation fails holdout checks, preferentially around final region boundaries.

- If joint M/R posterior samples exist, use them consistently, preserving correlation; otherwise use an explicitly declared provisional likelihood/ellipse approximation with asymmetric axis errors. Do not invent covariance or call three mass nodes the full distribution.
- Distinguish: (i) three-mass sensitivity envelope, (ii) region mapping into a specified observational compatibility contour, (iii) composition posterior requiring priors/likelihood and marginalization. Deliver(i)/(ii) first. Do not relabel them as68%/95%composition credible regions.
- With a stated independent2DGaussian observational approximation, a joint68.3%M–R ellipse useschi²<=2.30, not<=1. Mapping it into compositions is an observational-compatibility region, not automatically a68.3%composition posterior. Unknown covariance/asymmetry are declared limitations.
- Representative mass expansion may use7knots spanningapproximately +/-3quoted mass errors[6.60,7.08,7.56,8.04,8.54,9.04,9.54]ME. This is a candidate discretization, not an accepted probability distribution or a requirement to run everycomposition at everymass. Mass interpolation is allowed only after off-grid forward checks and cell/phase validity screening; otherwise return explicit slices or reducecomposition refinement to fund newmass runs within reserve.
- Fix final numerical thresholds before their checks. Target radius interpolation/tightening error <0.01RE (aboutone tenth of adopted radius error) for plotted boundaries; insufficient cells remain masked rather than filled. Use up to12stageF attempts plus explicitly reallocatedreserve, no blind reruns.
- Figures: ternaryFe/H2O/HHe map; Fe(or nongas ratio)-vs-loggas central branch and compatibility area; mass-slice comparison; TP/EOS assumptions and validity/failure masks. Labels say conditional model and observational compatibility, with numerical interpolation limits.
- Package: self-run configs/commands, minimal driver, exact data/plots, frozen model/source identities, README/limitations, fresh uninvolved review. Prepare clean manual release candidate; do not move test/development histories into cid manual repo.

## Later extensions — recorded, not a blocker for the first conditional composition map

1. Both confirmed no-water controls: Fe+silicate+HHe as main rocky control, pureFe+HHe as endmember. Reuse the same mass/thermal conventions; literalwater mass0, no epsilon. Explicitly distinguish bulk water-free from trace water in atmosphere. A failed no-water model under one assumedthermalprofile does not prove the actual planet must containwater. New bounded contract after primarymap.
2. Self-consistent climate/TP and cloud/haze sensitivity (PICASO or partner-delivered model). Validate one profile and interfaces before adding it as a gridaxis. Do not install models/opacities or start a second expensivegrid by default.
3. Statistical composition posterior and scanning acceleration only once forward errors, interpolation and model assumptions are controlled.

## Autonomy and stop rules

Progress automatically between accepted dependent engineering steps and report only meaningful milestones. Stop for a physicalmodel decision identified above, budget cap, repeated rootcause requiring architecture change, or an external dependency that cannot be resolved. Never repeatedly ask to rerun passed checks. End eachstage with actual evidence and next action; user interruption/status requests do not restart work. No background execution promise after ending the turn.

First next action when execution is approved: stageA source/overlap probes at the actual1280K and encountered highP water joins, no planetary grid and no formula edits. Deliver a concrete selection/comparison dossier, then proceed through the gates above.

## Accepted scope amendment —2026-11-12

User authorized execution and requires wet AND both dry controls in the first deliverable, not a later extension. Wet:Fe/H2O/HHe with Si0. Dry main:Fe/silicate/HHe with H2O exactly0. Dry endmember:pureFe/HHe with H2O and Si exactly0. Use identical observation/mass/thermal conventions and separate validity masks. Wet ternary axesFe/H2O/HHe; dry-main axesFe/silicate/HHe; pureFe endmember lies on the dry ternary edge and gets its own gas-fraction/mass slice plots. Never fake nonzero water or draw a 2D region for a one-dimensional composition family.

Keep total180planet attempts/12DeepSeek calls. Coarse stageD expands72->96 by adding24dry-rocky trials (3masses x2Fe/silicate ratios x4gas), reallocate24from adaptive stageE48->24. Original72already contains12pureFe endmembers, so deduplicate exactly. Wet and dry families share compatible engineering work; audit actual silicate phases before science plotting, do not assume prior Fe/water checks cover silicates. Fixed budget remaining stages A12+B8+C12+D96+E24+F12+reserve16=180. Further enlargement requires a documented tradeoff/budget decision, not hidden extra runs. StageA starts with source and <=300pairedEOS comparisons, no physical formula changes. Execution accepted; per-stage physical decision gates remain.

## Accepted water-model decision

User selected AQUA as wet main, stitched default as finite comparison. StageA completed10nativeattempts incl2failedinitializations and4earlystageCdrychecks;8successfulprofiles/8752storedstates independentlychecked.7DeepSeekcallsused. Canonicalphysics/tablesunchanged; validatedexactrowcommonaxisAQUAfixture usedinrunworkspace. NextB externalTPinitialization, no repeatA. See research/composition-constraints-20261112/README.md.

## Checkpoint after12calls /24nativeattempts

A sources/representativespassed;userselectedAQUAwetmain. Cthree-massrepresentativespassed,notproductionmassvectordriver. BactualTPcasespassed,butexactzero/reverseslopefalsefailuresremain;12thresponsehadfinish_reasonlength/invalidJSONandwasnotapplied. Budgetcapreply12->16pending,noextraAPIcalls. NoD/E/Fstarted,nofullcompositionplots. Candidatecodearchivedunderresearch/stageB,notpromotedtorootsrc. NativecountsA6/C12/B6=24,20savedmodels/4no-model attempts. RawcfgSHAclarifiedseparatelyfromlegacyLFtexthash. Next: authorizedbuilderrepair,thenboundednative/gridcontinuation;nohistoryreruns.
