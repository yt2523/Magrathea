from pathlib import Path
import subprocess, time, re, json, hashlib, difflib, os

ROOT=Path('D:/GPT/projects/Sub-Neptune')
SRC=ROOT/'Magrathea'
OUT=ROOT/'outputs/capstone-20261018'
WORK=ROOT/'work/capstone-20261018'
SL='/mnt/d/GPT/projects/Sub-Neptune/Magrathea'
WL='/mnt/d/GPT/projects/Sub-Neptune/work/capstone-20261018'
OL='/mnt/d/GPT/projects/Sub-Neptune/outputs/capstone-20261018'
os.environ['TEMP']=str(WORK)
os.environ['TMP']=str(WORK)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(name,args,timeout=240):
    cmd=['wsl','-d','Ubuntu','--cd',SL,'--exec']+args
    start=time.perf_counter()
    result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    elapsed=time.perf_counter()-start
    log=OUT/'logs'/f'{name}.log'
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    record={'command':cmd,'exit_code':result.returncode,'wall_seconds':elapsed,'log':str(log)}
    print(json.dumps({'step':name,**record},ensure_ascii=False),flush=True)
    if result.returncode: raise RuntimeError(f'{name} failed: see {log}')
    return result.stdout,record

# Only a temporary copy of main.cpp gains read-only result logging.
# All solver/EOS object files are those built from the unchanged checkout.
original=(SRC/'src/main.cpp').read_text(encoding='utf-8')
needle='      planet->print(outputfile, false);'
assert original.count(needle)==1
addition='''      cout << std::setprecision(17);
      cout << "CAPSTONE_STATUS " << planet->getstatus() << endl;
      cout << "CAPSTONE_R_RE " << planet->getRs().back() << endl;
      cout << "CAPSTONE_PC_GPA " << planet->getP(0)/1E10 << endl;
      cout << "CAPSTONE_TC_K " << planet->getT(0) << endl;
      cout << "CAPSTONE_INTERFACES_RE";
      for (double capstone_r : planet->getRs()) cout << ' ' << capstone_r;
      cout << endl;
'''
instrumented=original.replace(needle,addition+needle)
(WORK/'main-diagnostic.cpp').write_text(instrumented,encoding='utf-8')
(OUT/'diagnostic-logging.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),instrumented.splitlines(True),fromfile='original/src/main.cpp',tofile='temporary/main-diagnostic.cpp')),encoding='utf-8')
_,compile_record=run('diagnostic-compile',['g++','-std=c++0x','-O3','-Wall','-I'+SL+'/src','-c',WL+'/main-diagnostic.cpp','-o',WL+'/main-diagnostic.o'])
objects=[SL+'/src/'+p.name for p in sorted((SRC/'src').glob('*.o')) if p.name!='main.o']
assert len(objects)==7,objects
_,link_record=run('diagnostic-link',['g++',WL+'/main-diagnostic.o']+objects+['-lgsl','-lgslcblas','-lm','-o',WL+'/planet-diagnostic'])
base=(SRC/'run/mode0.cfg').read_text(encoding='utf-8')
cases=[
 {'id':'baseline_300K','changes':{},'purpose':'Repository Earth-like baseline'},
 {'id':'warm_1000K','changes':{'surface_temp':'1000'},'purpose':'Physical input: change only surface temperature'},
 {'id':'ode_tighter','changes':{'ode_eps_rel1':'1E-11'},'purpose':'Numerical input: tighten second-stage ODE tolerance by 10'},
 {'id':'ode_and_fit_tighter','changes':{'ode_eps_rel1':'1E-11','fit_eps_rel':'1E-5'},'purpose':'Relative to ode_tighter: tighten matching tolerance by 10'},
]
plan={'source_commit':'4c560f36d2734f6b63ae5118d4074e0c255b59f0','cases':cases,'prediction':'Increasing temperature may increase radius through thermal EOS terms; check which phases and thermal treatment are actually active. Numerical tolerance changes should approach stable results but matching tolerance may dominate.'}
(OUT/'run-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')

def config(case_id,changes):
    data=base
    values={'verbose':'true','output_file':f'"{OL}/profiles/{case_id}.txt"',**changes}
    for key,value in values.items():
        data,count=re.subn(r'^'+re.escape(key)+r'=.*$',key+'='+value,data,flags=re.M)
        assert count==1,(key,count)
    path=OUT/'configs'/f'{case_id}.cfg'
    path.write_text(data,encoding='utf-8')
    assert not (OUT/'profiles'/f'{case_id}.txt').exists(),'Prevent appending to existing profile'
    return f'{OL}/configs/{case_id}.cfg'

# Compare the original executable to the diagnostics-only build on the baseline.
original_config=config('baseline_original',{})
_,original_run=run('baseline_original',['./planet',original_config])
records=[]
for case in cases:
    cfg=config(case['id'],case['changes'])
    stdout,record=run(case['id'],[WL+'/planet-diagnostic',cfg])
    def field(key):
        m=re.search(r'^CAPSTONE_'+key+r' (.+)$',stdout,re.M)
        assert m,(case['id'],key,'model may not have been returned')
        return m.group(1)
    record.update(case)
    record.update(status=int(field('STATUS')),radius_RE=float(field('R_RE')),Pc_GPa=float(field('PC_GPA')),Tc_K=float(field('TC_K')),interfaces_RE=list(map(float,field('INTERFACES_RE').split())))
    record['profile']=str(OUT/'profiles'/f'{case["id"]}.txt')
    record['config_sha256']=sha(OUT/'configs'/f'{case["id"]}.cfg')
    record['profile_sha256']=sha(Path(record['profile']))
    records.append(record)
    (OUT/'runs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'result':record},ensure_ascii=False),flush=True)
assert sha(OUT/'profiles/baseline_original.txt')==sha(OUT/'profiles/baseline_300K.txt'),'Diagnostics changed baseline profile'
manifest={'plan':plan,'runs':records,'original_baseline':original_run,'diagnostic_compile':compile_record,'diagnostic_link':link_record,'diagnostics_baseline_profile_identical':True,'original_main_sha256':sha(SRC/'src/main.cpp'),'diagnostic_main_sha256':sha(WORK/'main-diagnostic.cpp'),'binary_sha256':sha(SRC/'planet'),'diagnostic_binary_sha256':sha(WORK/'planet-diagnostic')}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('EXPERIMENTS_COMPLETE',flush=True)
