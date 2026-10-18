from pathlib import Path
import subprocess,json,re,time,hashlib,math,os
ROOT=Path('D:/GPT/projects/Sub-Neptune')
OUT=ROOT/'outputs/literature-cases-20261018'
WORK=ROOT/'work/literature-cases-20261018'
SOURCE=ROOT/'Magrathea'
SL='/mnt/d/GPT/projects/Sub-Neptune/Magrathea'
OL='/mnt/d/GPT/projects/Sub-Neptune/outputs/literature-cases-20261018'
BINARY='/mnt/d/GPT/projects/Sub-Neptune/work/capstone-20261018/planet-diagnostic'
for folder in ('configs','profiles','logs','figures'): (OUT/folder).mkdir(parents=True,exist_ok=True)
WORK.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(WORK)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((ROOT/'outputs/capstone-20261018/manifest.json').read_text(encoding='utf-8'))
assert sha(ROOT/'work/capstone-20261018/planet-diagnostic')==previous['diagnostic_binary_sha256']
assert sha(SOURCE/'src/main.cpp')==previous['original_main_sha256']
assert sha(SOURCE/'planet')==previous['binary_sha256']

BON='https://arxiv.org/html/2311.12577v2#S5.SS2'
RIG='https://academic.oup.com/mnras/article/529/1/409/7617367'
cases=[
 {'id':'rock_reference','label':'干燥岩石参照','mass_ME':8.04,'water_fraction':0.,'gas_fraction':0.,'rock_Fe_fraction':1/3,'T0_K':300.,'P0_bar':1.,'source':'rigby2024 §2.4 / Fig.5; bonfanti2024 Table5 for common mass','source_url':RIG,'mapping':'Fig.5 Earth-like Fe:silicate=1:2; mass8.04 chosen for this comparison; T300/P1 same reference boundary as water curves; dry control is not itself a volatile-rich sub-Neptune.'},
 {'id':'water30','label':'30% 水层','mass_ME':8.04,'water_fraction':.3,'gas_fraction':0.,'rock_Fe_fraction':1/3,'T0_K':300.,'P0_bar':1.,'source':'rigby2024 §2.4 / Fig.5 (Nixon & Madhusudhan 2021 curves); bonfanti2024 Table5 mass','source_url':RIG,'mapping':'Composition and T/P copied from validation-curve definition; evaluated at chosen mass8.04; MAGRATHEA EOS differs from HyRIS.'},
 {'id':'water90','label':'90% 水层','mass_ME':8.04,'water_fraction':.9,'gas_fraction':0.,'rock_Fe_fraction':1/3,'T0_K':300.,'P0_bar':1.,'source':'rigby2024 §2.4 / Fig.5 (Nixon & Madhusudhan 2021 curves); bonfanti2024 Table5 mass','source_url':RIG,'mapping':'Same as water30, with 90% water. These labels describe composition, not an inferred ocean depth.'},
 {'id':'gasdwarf_1pct','label':'岩石 + 1% H/He','mass_ME':8.04,'water_fraction':0.,'gas_fraction':.01,'rock_Fe_fraction':.325,'T0_K':360.,'P0_bar':.05,'source':'bonfanti2024 §5.2 / Fig.5','source_url':BON,'mapping':'1% H/He and Earth-like rock definition copied; mapping Teq360 to T0 at0.05bar is this experiment assumption, not a self-consistent atmosphere; use existing HHe_tabulated.'},
 {'id':'steam50','label':'50% 水岩蒸汽配方','mass_ME':8.04,'water_fraction':.5,'gas_fraction':0.,'rock_Fe_fraction':.325,'T0_K':400.,'P0_bar':.05,'source':'bonfanti2024 §5.2 / Fig.5, citing Aguichine et al.2021','source_url':BON,'mapping':'50%water+50%Earth-like from cited curve; Teq400 mapped to T0 at0.05bar for illustration; no radiative-convective atmosphere or age evolution from the original steam model is reproduced.'},
 {'id':'hycean_rigby','label':'Hycean 文献参照','mass_ME':7.10,'water_fraction':.8,'gas_fraction':.000132,'rock_Fe_fraction':1/3,'T0_K':297.,'P0_bar':.05,'source':'rigby2024 §3.2.3 / Fig.9c, §3.2 reference pressure, §2.4 rock definition','source_url':RIG,'mapping':'Published example M7.10,water80%,gas0.0132%,T0297,P00.05bar; target from HyRIS R2.41,HHB399K270bar. Use MAGRATHEA EOS/thermal path; assess discrepancy rather than tune inputs.','paper_R_RE':2.41,'paper_HHB_T_K':399.,'paper_HHB_P_bar':270.},
]
shared={'core_phasedgm':'"Fe_default"','mantle_phasedgm':'"Si_default"','hydro_phasedgm':'"water_default"','atm_phasedgm':'"HHe_tabulated"','temp_jump_1':'0','temp_jump_2':'0','temp_jump_3':'0','verbose':'true'}
plan={'source_commit':previous['plan']['source_commit'],'cases':cases,'shared_changes':shared,'source_evidence_level':'primary full-text sections inspected; targeted parameter lookup, not a new deep-read round','gas_EOS_note':'HHe_tabulated uses isothermal ideal gas with molar mass3g/mol below100bar, Chabrier/Debras2021 Y0.275 table at and above100bar. This is not identical to HyRIS Chabrier2019.','comparison_note':'Only rock_reference,water30,water90 share mass,T0,P0 and rock ratio. Other rows are literature-inspired scenarios, not a controlled composition-only experiment.'}
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
base=(SOURCE/'run/mode0.cfg').read_text(encoding='utf-8')
records=[]
def execute(case,tight=False,ideal=False):
    name=case['id']+('_tight' if tight else '')+('_ideal_gas' if ideal else '')
    profile=OUT/'profiles'/f'{name}.txt'
    if profile.exists():raise RuntimeError('Refuse to append to existing output: '+str(profile))
    m=case['mass_ME'];fg=case['gas_fraction'];fw=case['water_fraction'];fr=1-fw-fg
    fractions=[fr*case['rock_Fe_fraction'],fr*(1-case['rock_Fe_fraction']),fw,fg]
    assert all(v>=0 for v in fractions) and math.isclose(sum(fractions),1,abs_tol=1e-14)
    masses=[v*m for v in fractions]
    settings={**shared,'surface_temp':format(case['T0_K'],'.17g'),'P_surface':format(case['P0_bar']*1e6,'.17g'),'output_file':f'"{OL}/profiles/{name}.txt"'}
    settings.update(dict(zip(['mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm'],[format(v,'.17g') for v in masses])))
    if tight:settings.update(ode_eps_rel1='1E-11',fit_eps_rel='1E-5')
    if ideal:settings['atm_phasedgm']='"gas_default"'
    cfg=base
    for key,value in settings.items():
        cfg,n=re.subn(r'^'+re.escape(key)+r'=.*$',key+'='+value,cfg,flags=re.M);assert n==1,key
    configpath=OUT/'configs'/f'{name}.cfg';configpath.write_text(cfg,encoding='utf-8')
    cmd=['wsl','-d','Ubuntu','--cd',SL,'--exec',BINARY,OL+'/configs/'+name+'.cfg']
    t=time.perf_counter()
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        stdout=result.stdout+result.stderr;exit_code=result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout=str(exc.stdout or '')+'\nTIMEOUT after 180s';exit_code=None
    log=OUT/'logs'/f'{name}.log';log.write_text(stdout,encoding='utf-8')
    record={'id':name,'case_id':case['id'],'tight':tight,'ideal_gas_comparison':ideal,'mass_ME':m,'fractions_Fe_Si_water_gas':fractions,'layer_masses_ME':masses,'T0_K':case['T0_K'],'P0_bar':case['P0_bar'],'config':str(configpath),'config_sha256':sha(configpath),'profile':str(profile) if profile.exists() else None,'log':str(log),'command':cmd,'exit_code':exit_code,'wall_seconds':time.perf_counter()-t,'status':None}
    match=re.search(r'^CAPSTONE_STATUS (\d+)',stdout,re.M)
    if match:
        record['status']=int(match.group(1))
        for key,label in [('R_RE','radius_RE'),('PC_GPA','Pc_GPa'),('TC_K','Tc_K')]:record[label]=float(re.search(r'^CAPSTONE_'+key+r' (.+)$',stdout,re.M).group(1))
        record['interfaces_RE']=list(map(float,re.search(r'^CAPSTONE_INTERFACES_RE (.+)$',stdout,re.M).group(1).split()))
    timing=re.search(r'run time ([\d.eE+-]+)s',stdout)
    if timing:record['solver_seconds']=float(timing.group(1))
    record['warnings_errors']=[l for l in stdout.splitlines() if re.search(r'Error:|Warning:|No solution|TIMEOUT',l)]
    records.append(record)
    (OUT/'runs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False),flush=True)
for case in cases:execute(case)
# Joint refinement checks numerical sensitivity, without attributing changes to one tolerance.
for case in cases:execute(case,tight=True)
execute(next(c for c in cases if c['id']=='gasdwarf_1pct'),ideal=True)
(OUT/'manifest.json').write_text(json.dumps({'plan':plan,'runs':records,'diagnostic_binary_sha256':previous['diagnostic_binary_sha256'],'original_binary_sha256':previous['binary_sha256']},ensure_ascii=False,indent=2),encoding='utf-8')
print('LITERATURE_CASES_COMPLETE',flush=True)
