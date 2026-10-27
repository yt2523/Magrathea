"""Batch unchanged MAGRATHEA mode0 from CSV; run this driver inside WSL/Linux."""
import argparse,csv,hashlib,json,math,os,re,subprocess,time,uuid
from pathlib import Path

NUMERIC=('mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm','surface_temp','P_surface')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,path)
def validate_case(row):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',row.get('case_id','')):raise ValueError('unsafe case ID')
    for key in NUMERIC:
        try:value=float(row[key])
        except (ValueError,KeyError,TypeError,OverflowError) as exc:raise ValueError('invalid '+key) from exc
        if not math.isfinite(value) or value<0 or (key in ('surface_temp','P_surface') and value==0):raise ValueError('invalid '+key)
    if sum(float(row[k]) for k in NUMERIC[:4])<=0:raise ValueError('positive total mass required')
    if row.get('tight','0') not in ('0','1'):raise ValueError('tight must be0 or1')
def render_config(template,row,destination):
    validate_case(row)
    if '"' in destination or '\n' in destination:raise ValueError('unsafe output path')
    replacements={k:row[k] for k in NUMERIC}
    replacements.update(input_mode='0',output_file='"'+destination+'"')
    if row.get('tight')=='1':replacements.update(ode_eps_rel1='1e-11',fit_eps_rel='1e-5')
    for key,value in replacements.items():
        template,count=re.subn(r'(?m)^\s*'+re.escape(key)+r'\s*=[^\r\n]*',lambda _:key+'='+value,template)
        if count!=1:raise ValueError('missing/duplicate config key: '+key)
    return template

def parse_profile(path,row):
    lines=Path(path).read_text().splitlines()
    if sum(s.strip().startswith('Index') for s in lines)!=1:raise ValueError('missing or appended profile header')
    values=[]
    for line in lines:
        if not line.strip() or line.strip().startswith('Index'):continue
        parts=line.split()
        if len(parts)<7:raise ValueError('malformed profile row')
        try:v=[float(x) for x in parts[:6]]
        except ValueError as exc:raise ValueError('invalid numeric profile') from exc
        if not all(math.isfinite(x) for x in v) or min(v[1],v[3])<0 or min(v[2],v[4],v[5])<=0:raise ValueError('invalid physical profile values')
        values.append(v)
    if len(values)<2:raise ValueError('empty profile')
    total=sum(float(row[k]) for k in NUMERIC[:4]);surface=values[-1]
    if values[0][1]!=0 or values[0][3]!=0:raise ValueError('missing central boundary')
    if surface[1]<=0 or not math.isclose(surface[3],total,rel_tol=2e-7,abs_tol=1e-9):raise ValueError('incorrect surface mass')
    if not math.isclose(surface[5],float(row['surface_temp']),rel_tol=2e-7):raise ValueError('incorrect surface temperature')
    if not math.isclose(surface[2],float(row['P_surface'])/1e10,rel_tol=2e-6):raise ValueError('incorrect surface pressure units')
    for a,b in zip(values,values[1:]):
        if b[1]<a[1]-1e-7*max(1,surface[1]) or b[3]<a[3]-1e-7*max(1,total) or b[2]>a[2]*(1+1e-7)+1e-12:raise ValueError('nonmonotonic radius, mass or pressure')
    return dict(radius_re=surface[1],mass_me=surface[3],surface_temperature_K=surface[5],surface_pressure_GPa=surface[2],central_pressure_GPa=values[0][2],central_temperature_K=values[0][5],profile_rows=len(values))
def sources(repo):
    return {p.relative_to(repo).as_posix():sha(p) for p in sorted((repo/'src').iterdir()) if p.suffix in ('.cpp','.h')}
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--table',type=Path,required=True);p.add_argument('--template',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--limit',type=int);p.add_argument('--timeout',type=float,default=45)
    a=p.parse_args();repo=a.repo.resolve();out=a.output.resolve();binary=repo/'planet'
    if os.name!='posix':raise SystemExit('Run this driver with WSL Python; no Windows solver required.')
    if not math.isfinite(a.timeout) or a.timeout<=0:raise ValueError('positive finite timeout required')
    if a.limit is not None and a.limit<1:raise ValueError('positive limit required')
    with a.table.open(newline='') as f:rows=list(csv.DictReader(f))
    if not rows or len({r['case_id'] for r in rows})!=len(rows):raise ValueError('nonempty unique cases required')
    for row in rows:validate_case(row)
    template=a.template.read_text();source_before=sources(repo);binary_hash=sha(binary);template_hash=sha(a.template)
    if out.exists() and not a.resume:raise ValueError('new output directory or explicit --resume required')
    out.mkdir(parents=True,exist_ok=True)
    initial=dict(solver_binary_sha256=binary_hash,source_sha256=source_before,template_sha256=template_hash,table_sha256=sha(a.table),mode=0)
    save(out/'inputs_manifest.json',initial)
    all_records=[]
    for row in rows[:a.limit]:
        case=out/row['case_id'];case.mkdir(exist_ok=True)
        signature=hashlib.sha256(json.dumps(dict(row=row,inputs=initial),sort_keys=True).encode()).hexdigest()
        record_file=case/'case.json';old=json.loads(record_file.read_text()) if record_file.exists() else None
        if a.resume and old and old.get('status')=='profile_checks_passed' and old.get('signature')==signature:
            if Path(old['profile']).is_file() and Path(old['config']).is_file() and sha(old['profile'])==old.get('profile_sha256') and sha(old['config'])==old.get('config_sha256'):
                print(row['case_id']+' cached',flush=True);continue
        attempt=case/('attempt-'+uuid.uuid4().hex[:10]);attempt.mkdir();profile=attempt/'profile.txt';config=attempt/'input.cfg';log=attempt/'stdout.log'
        config.write_text(render_config(template,row,str(profile)),encoding='utf-8');start=time.monotonic()
        record=dict(case_id=row['case_id'],row=row,signature=signature,config=str(config),profile=str(profile),config_sha256=sha(config),status='running')
        save(record_file,record)
        try:
            env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
            with log.open('w') as f:r=subprocess.run([str(binary),str(config)],cwd=repo,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout,env=env)
            text=log.read_text()
            if r.returncode!=0 or 'No solution found' in text or 'Exception:' in text or 'Planet saved:' not in text:raise ValueError('solver failed; inspect '+str(log))
            record.update(parse_profile(profile,row),status='profile_checks_passed',returncode=r.returncode,profile_sha256=sha(profile),log_sha256=sha(log),solver_internal_status='not_exposed_by_unmodified_CLI')
        except (ValueError,subprocess.TimeoutExpired,OSError) as exc:
            record.update(status='failed',error=str(exc))
        record['elapsed_seconds']=time.monotonic()-start;save(attempt/'result.json',record);save(record_file,record)
        with (out/'audit.jsonl').open('a') as f:f.write(json.dumps({'event':'case_finished','case_id':row['case_id'],'status':record['status'],'attempt':str(attempt),'signature':signature})+'\n')
        print(row['case_id']+' '+record['status']+' '+str(round(record['elapsed_seconds'],3))+'s',flush=True)
        if record['status']!='profile_checks_passed':raise SystemExit('Stopped at failed case; preserve artifacts and inspect before resuming')
    for row in rows:
        path=out/row['case_id']/'case.json'
        if path.exists():
            record=json.loads(path.read_text())
            expected=hashlib.sha256(json.dumps(dict(row=row,inputs=initial),sort_keys=True).encode()).hexdigest()
            if record.get('signature')==expected and record.get('status')=='profile_checks_passed' and Path(record['profile']).is_file() and Path(record['config']).is_file() and sha(record['profile'])==record.get('profile_sha256') and sha(record['config'])==record.get('config_sha256'):
                all_records.append(record)
    if sources(repo)!=source_before or sha(binary)!=binary_hash:raise RuntimeError('solver changed during batch; results not certified')
    save(out/'results.json',{'mode':0,'requested_cases':len(rows),'completed_cases':len(all_records),'status':'completed' if len(all_records)==len(rows) else 'partial','runs':all_records,'source_unchanged':True})
if __name__=='__main__':main()
