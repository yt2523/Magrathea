"""Independent persisted-data checks; does not invoke driver, solver, or models."""
import hashlib,json,math,sys
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def disk(s):return Path(s.replace('/mnt/d/','D:/'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=Path(sys.argv[1]);runs=read(out/'all_runs.json');verification=read(out/'verification.json')
 assert verification['status']=='completed' and len(runs)==verification['total_cases']
 manifests=[read(p) for p in sorted(out.glob('batch-*/inputs_manifest.json'))]
 assert manifests and all(m['solver_binary_sha256']==manifests[0]['solver_binary_sha256'] and m['source_sha256']==manifests[0]['source_sha256'] for m in manifests)
 repo=Path(r'D:\GPT\projects\Sub-Neptune\work\magrathea-mode0-clean-20261025-a17b')
 assert sha(repo/'planet')==manifests[0]['solver_binary_sha256']
 for name,digest in manifests[0]['source_sha256'].items():assert sha(repo/name)==digest
 lookup={r['case_id']:r for r in runs};laws=[]
 forward=read(out/'forward.json')
 for mass in [5,8.04]:
  for temp in [300,360,450]:
   points=sorted((r['fraction'],r['radius_re']) for r in forward if r['mass_me']==mass and r['temperature_K']==temp)
   assert len(points)==3 and all(b[1]>a[1] for a,b in zip(points,points[1:]))
 for r in runs:
  for key,filekey in [('profile_sha256','profile'),('config_sha256','config')]:assert sha(disk(r[filekey]))==r[key]
  assert sha(disk(r['profile']).parent/'stdout.log')==r['log_sha256']
  row=r['row'];mass=sum(float(row[k]) for k in ['mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm'])
  assert math.isclose(mass,r['mass_me'],rel_tol=2e-7)
  assert math.isclose(float(row['mass_of_core'])/(float(row['mass_of_core'])+float(row['mass_of_mantle'])),.325,rel_tol=1e-14)
  config=disk(r['config']).read_text()
  assert 'atm_phasedgm="'+r['atmosphere_recipe']+'"' in config
  if r['atmosphere_recipe']=='gas_default':
   invariant=[];isothermal=[]
   for line in disk(r['profile']).read_text().splitlines():
    v=line.split()
    if len(v)<7:continue
    phase=' '.join(v[6:])
    if phase=='Ideal Gas':invariant.append(math.log(float(v[5]))-2/7*math.log(float(v[2])))
    if phase=='Isothermal Ideal Gas':isothermal.append(float(v[5]))
   drift=math.expm1(max(invariant)-min(invariant)) if invariant else 0
   iso=(max(isothermal)/min(isothermal)-1) if isothermal else 0
   laws.append(dict(case_id=r['case_id'],ideal_adiabat_relative_invariant_drift=drift,isothermal_relative_drift=iso))
   assert drift<5e-4 and iso<1e-7,(r['case_id'],drift,iso)
 for r in read(out/'recovery.json'):
  f=r['recovered_fraction'];run=lookup[r['history'][-1]['case_id']]
  assert math.isclose(float(run['row']['mass_of_atm'])/r['mass_me'],f,rel_tol=1e-14)
  residual=(run['radius_re']-r['target_radius_re'])/r['target_radius_re']
  assert residual==r['relative_radius_residual'] and abs(residual)<=2e-5
  assert r['bracket_low'][1]<=r['target_radius_re']<=r['bracket_high'][1]
  for h in r['history']:
   actual=lookup[h['case_id']];assert actual['radius_re']==h['radius_re']
   assert float(actual['row']['surface_temp'])==r['assumed_temperature_K']
 save=dict(status='passed',verified_runs=len(runs),all_source_binary_hashes_match=True,all_config_profile_log_hashes_match=True,recovery_residuals_and_brackets_match=True,rock_ratio_and_mass_check=True,gas_default_thermal_law_check=laws,max_adiabat_drift=max(r['ideal_adiabat_relative_invariant_drift'] for r in laws),max_isothermal_drift=max(r['isothermal_relative_drift'] for r in laws),test_environment_note='First Windows fixture attempt hit sandbox C temp permission; re-run with TEMP/TMP D:/Codex/tmp passed all8. No code fix required.')
 (out/'independent_numeric_checks.json').write_text(json.dumps(save,indent=2))
 print(json.dumps({k:v for k,v in save.items() if k!='gas_default_thermal_law_check'},indent=2))
if __name__=='__main__':main()
