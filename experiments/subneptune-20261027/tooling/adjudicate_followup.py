import hashlib,json
from pathlib import Path
root=Path(r'D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench');out=Path(r'D:\GPT\projects\Sub-Neptune\outputs\thermal-composition-20261025-b01')
rows=[]
for line in (out/'review.events.jsonl').read_text(encoding='utf-8').splitlines():
 try:rows.append(json.loads(line))
 except ValueError:pass
r=[x for x in rows if x.get('type')=='run_result'][-1];text=r['text'].strip();v,n=json.JSONDecoder().raw_decode(text)
v.update(model_metadata=r.get('model'),usage=r.get('aggregateUsage'),format_deviation=text[n:],source_sha256={name:hashlib.sha256((root/name).read_text(encoding='utf-8-sig').encode()).hexdigest() for name in ['followup_comparisons.py','test_followup.py','FOLLOWUP_PLAN.md']})
(out/'independent-review.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
dispositions=[
 'False: select_bracket sorts and checks every merged point; expansion explicitly calls it again after points.extend. Existing rejection test covers nonmonotonic input.',
 'False: hydro is deliberately zero in this experiment; core+mantle=mass*(1-f), atmosphere=mass*f. Rock ratio denominator excludes atmosphere, independent of whether atmosphere is zero. Tests cover nonzero fractions.',
 'False: only abs(residual)<=2e-5 breaks; otherwise for/else raises. Geometric midpoints remain inside initial bounded brackets. All persisted final residuals will be independently recomputed.',
 'False: mode0_batch.NUMERIC explicitly expects surface_temp, not temperature_K. Generated CSV uses its exact required fields. Per-run surface-temperature integrity check passed.',
 'False: counter>100 raises before subprocess is called or a completed status is saved. Upper bound without expansions is18+48+6+4=76; maximum two expansion cases for each of4 recoveries gives84. No executed batch may exceed100.',
 'No actionable defect: sampled monotonicity cannot establish continuous uniqueness, already stated in scope. Bisection uses actual solver evaluations, never linear interpolation. Report will explicitly limit uniqueness claims.',
 'No actionable defect: template count assertion fails if template differs; both generated files use that checked content. Whole-prescription confounding is explicitly admitted and intentionally measured, not claimed as pure EOS.'
]
(out/'review-adjudication.json').write_text(json.dumps(dict(reviewer_original_approved=v['approved'],reviewer_issues_preserved=True,adjudicator='Codex',unresolved_reproducible_issues=[],dispositions=[dict(issue_number=i+1,decision=d) for i,d in enumerate(dispositions)],note='Raw review included one extra closing brace; parsed object preserved separately. No extra model call. Numerical completion gates remain independent of this adjudication.'),indent=2),encoding='utf-8')
print('Original negative reviewer verdict preserved; seven findings adjudicated against source. No second model call.')
