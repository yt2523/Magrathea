"""Controlled mode0 comparisons. Run inside WSL; never modifies solver source."""
import csv,json,math,subprocess,sys
from pathlib import Path
from mode0_batch import save,sha

FIELDS=('case_id','mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm','surface_temp','P_surface','tight')
REPO=Path('/mnt/d/GPT/projects/Sub-Neptune/work/magrathea-mode0-clean-20261025-a17b')
TEMPLATE=Path('/mnt/d/GPT/projects/Sub-Neptune/Magrathea/experiments/archive/20261018/literature-cases/configs/gasdwarf_1pct_ideal_gas.cfg')

def recipe(case_id,mass,fraction,temp,tight=False):
    if not (math.isfinite(mass) and mass>0 and math.isfinite(fraction) and 0<fraction<1 and math.isfinite(temp) and temp>0):
        raise ValueError('positive mass/temperature and fraction in (0,1) required')
    return dict(zip(FIELDS,[case_id,format(mass*(1-fraction)*.325,'.17g'),format(mass*(1-fraction)*.675,'.17g'),'0',format(mass*fraction,'.17g'),str(temp),'50000',str(int(tight))]))

def select_bracket(points,target):
    ordered=sorted(points)
    if any(b[1]<a[1]-1e-6*target for a,b in zip(ordered,ordered[1:])):
        raise ValueError('nonmonotonic sampled mass-radius curve')
    for a,b in zip(ordered,ordered[1:]):
        if a[1]<=target<=b[1]:return a,b
    raise ValueError('target radius is not bracketed')

def main():
    out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parent
    template=TEMPLATE.read_text();(out/'gas_default.cfg').write_text(template)
    assert template.count('atm_phasedgm="gas_default"')==1
    (out/'HHe_tabulated.cfg').write_text(template.replace('atm_phasedgm="gas_default"','atm_phasedgm="HHe_tabulated"'))
    save(out/'plan.json',dict(masses_me=[5,8.04],fractions=[.003,.01,.03],temperatures_K=[300,360,450],target_temperature_K=360,target_fraction=.01,radius_relative_tolerance=2e-5,max_inverse_iterations=12,source_changes=False,scope='boundary-temperature sensitivity, not imported TP curves',budget_max_cases=100))
    all_runs=[];counter=0
    def batch(rows,eos='gas_default'):
        nonlocal counter
        counter+=len(rows)
        if counter>100:raise RuntimeError('case budget exhausted')
        label=f'batch-{len(list(out.glob("batch-*.csv")))+1:03d}'
        table=out/(label+'.csv')
        with table.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
        runout=out/label
        cmd=[sys.executable,'-B',str(root/'mode0_batch.py'),'--repo',str(REPO),'--table',str(table),'--template',str(out/(eos+'.cfg')),'--output',str(runout),'--timeout','45']
        with (out/(label+'.log')).open('w') as f:
            r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=50*len(rows)+20)
        print((out/(label+'.log')).read_text(),end='',flush=True)
        if r.returncode:raise RuntimeError('batch failure: '+str(runout))
        data=json.loads((runout/'results.json').read_text())
        if data['status']!='completed':raise RuntimeError('incomplete batch')
        for run in data['runs']:
            run['atmosphere_recipe']=eos
            all_runs.append(run)
        save(out/'all_runs.json',all_runs)
        return data['runs']
    lookup={}
    rows=[]
    for mass in [5,8.04]:
        for temp in [300,360,450]:
            for frac in [.003,.01,.03]:
                rows.append(recipe(f'm{str(mass).replace(".","p")}_t{temp}_f{int(frac*1000)}',mass,frac,temp))
    grid=batch(rows)
    for mass in [5,8.04]:
        for temp in [300,360,450]:
            for frac in [.003,.01,.03]:
                lookup[mass,temp,frac]=grid.pop(0)
        for frac in [.003,.01,.03]:
            radii=[lookup[mass,t,frac]['radius_re'] for t in [300,360,450]]
            if not all(b>a for a,b in zip(radii,radii[1:])):raise RuntimeError('temperature monotonicity check failed')
    forward=[dict(mass_me=m,temperature_K=t,fraction=f,radius_re=r['radius_re'],case_id=r['case_id']) for (m,t,f),r in lookup.items()]
    save(out/'forward.json',forward)
    recoveries=[]
    for mass in [5,8.04]:
        target=lookup[mass,360,.01]['radius_re']
        for temp in [300,450]:
            points=[(f,lookup[mass,temp,f]['radius_re']) for f in [.003,.01,.03]]
            try:lo,hi=select_bracket(points,target)
            except ValueError:
                expanded=batch([recipe(f'expand_m{mass}_t{temp}_f{i}'.replace('.','p'),mass,f,temp) for i,f in enumerate([.0001,.1])])
                points.extend(zip([.0001,.1],[r['radius_re'] for r in expanded]));lo,hi=select_bracket(points,target)
            history=[]
            for iteration in range(12):
                fraction=math.sqrt(lo[0]*hi[0])
                run=batch([recipe(f'inverse_m{mass}_t{temp}_i{iteration}'.replace('.','p'),mass,fraction,temp)])[0]
                radius=run['radius_re'];residual=(radius-target)/target
                if not lo[1]-target*1e-6<=radius<=hi[1]+target*1e-6:raise RuntimeError('radius outside monotone bracket')
                history.append(dict(iteration=iteration,fraction=fraction,radius_re=radius,relative_radius_residual=residual,case_id=run['case_id']))
                if radius<target:lo=(fraction,radius)
                else:hi=(fraction,radius)
                if abs(residual)<=2e-5:break
            else:raise RuntimeError('inverse iteration limit exceeded')
            recoveries.append(dict(mass_me=mass,assumed_temperature_K=temp,target_temperature_K=360,target_fraction=.01,target_radius_re=target,recovered_fraction=fraction,fraction_relative_bias=fraction/.01-1,bracket_low=list(lo),bracket_high=list(hi),relative_radius_residual=residual,history=history))
            save(out/'recovery.json',recoveries)
    control_rows=[recipe(f'baseline_tight_m{m}'.replace('.','p'),m,.01,360,True) for m in [5,8.04]]
    control_rows.extend(recipe(f'inverse_tight_{i}',r['mass_me'],r['recovered_fraction'],r['assumed_temperature_K'],True) for i,r in enumerate(recoveries))
    controls=batch(control_rows)
    eos_runs=batch([recipe(f'hhe_m{m}_t{t}'.replace('.','p'),m,.01,t) for m in [5,8.04] for t in [360,450]],'HHe_tabulated')
    checks=[]
    for m,run in zip([5,8.04],controls[:2]):
        checks.append(dict(case_id=run['case_id'],kind='baseline_tight',relative_radius_change=abs(run['radius_re']/lookup[m,360,.01]['radius_re']-1)))
    for inv,run in zip(recoveries,controls[2:]):
        nominal=inv['history'][-1]['radius_re']
        checks.append(dict(case_id=run['case_id'],kind='inverse_tight',relative_radius_change=abs(run['radius_re']/nominal-1),target_relative_residual=run['radius_re']/inv['target_radius_re']-1))
    save(out/'controls.json',checks)
    if any(r['relative_radius_change']>2e-5 for r in checks):raise RuntimeError('tolerance sensitivity larger than inverse stopping tolerance')
    eos_comparison=[]
    for (mass,temp),run in zip([(m,t) for m in [5,8.04] for t in [360,450]],eos_runs):
        base=lookup[mass,temp,.01]['radius_re']
        eos_comparison.append(dict(mass_me=mass,temperature_K=temp,gas_default_radius_re=base,HHe_tabulated_radius_re=run['radius_re'],relative_radius_change=run['radius_re']/base-1))
    save(out/'eos_comparison.json',eos_comparison)
    for name,data in [('forward',forward),('recovery',[{k:v for k,v in r.items() if k not in ('history','bracket_low','bracket_high')} for r in recoveries]),('eos_comparison',eos_comparison)]:
        with (out/(name+'.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    save(out/'verification.json',dict(status='completed',total_cases=counter,passed_profile_checks=len(all_runs),tight_controls=checks,temperature_monotonicity=True,source_changes=False,driver_model_calls=0,limitations=['synthetic recipes, no observed target fit','boundary temperature changes, not full TP imports','gas_default mu and thermal phase prescription fixed','inverse brackets are deterministic numerical brackets, not confidence intervals','EOS comparison changes whole atmospheric prescription']))
    save(out/'manifest.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'})
    print(json.dumps(dict(completed=True,total_cases=counter,recoveries=recoveries,EOS=eos_comparison)),flush=True)
if __name__=='__main__':main()
