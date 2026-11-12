import pathlib,json,hashlib,subprocess,time,sys
r=pathlib.Path('D:/Codex/downloads/subneptune-research-workflow');p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');old=pathlib.Path('D:/Codex/downloads/toi732c-unified-hhe-100bar-20261112');case=sys.argv[1] if len(sys.argv)>1 else 'grid14-aqua'
basecase='grid14' if case.startswith('grid14') else 'grid20';tight=case.endswith('-tight');sourcecase=basecase+('-tight' if tight else '')
d=p/'results'/case;d.mkdir(exist_ok=False);s=(old/'results'/sourcecase/'run.cfg').read_text()
s=s.replace('verbose=false','verbose=true')
s=s.replace('hydro_phasedgm="water_default"','hydro_phasedgm="water_tabulated"')
s='\n'.join('output_file="'+(d/'model.dat').as_posix().replace('D:','/mnt/d')+'"' if a.startswith('output_file=') else a for a in s.splitlines())+'\n'
(d/'run.cfg').write_text(s)
bin=old/'source/native_audit';assert hashlib.sha256(bin.read_bytes()).hexdigest()=='afb5f9c42652489f770b54a92ddcf41c1452852ae2fe89e34aa3541df3b2ad60'
# Verify every linked production source against the fresh stage source; whole ELF reuse, not stale-object linkage.
for f in (old/'source/src').glob('*'):
 if f.suffix in ['.cpp','.h']:assert f.read_bytes()==(p/'source/src'/f.name).read_bytes(),f.name
c=json.loads((p/'contract.json').read_text());assert len(c['native_attempts'])<12
rec={'case':case,'stage':'A','status':'STARTED','config_sha256':hashlib.sha256(s.encode()).hexdigest(),'binary_sha256':hashlib.sha256(bin.read_bytes()).hexdigest(),'AQUA_fixture_sha256':hashlib.sha256((p/'source/tabulated/AQUA.txt').read_bytes()).hexdigest()};c['native_attempts'].append(rec);(p/'contract.json').write_text(json.dumps(c,indent=2))
args=['wsl','--cd',(p/'source').as_posix().replace('D:','/mnt/d'),'--exec',bin.as_posix().replace('D:','/mnt/d'),'--run',(d/'run.cfg').as_posix().replace('D:','/mnt/d'),(d/'runtime.json').as_posix().replace('D:','/mnt/d')]
t=time.time()
try:
 with (d/'stdout.log').open('wb') as f,(d/'stderr.log').open('wb') as g:z=subprocess.run(args,stdout=f,stderr=g,timeout=180)
 rec.update(status='COMPLETED',exit_code=z.returncode,seconds=time.time()-t,model_exists=(d/'model.dat').is_file())
 if (d/'runtime.json').is_file():rec['runtime']=json.loads((d/'runtime.json').read_text())
 if (d/'model.dat').is_file():
  a=[line.split(maxsplit=6) for line in (d/'model.dat').read_text().splitlines()[1:] if line.strip()];rec['rows']=len(a);rec['R_RE']=float(a[-1][1]);rec['max_saved_T']=max(float(x[5]) for x in a)
except subprocess.TimeoutExpired:rec.update(status='TIMEOUT',seconds=time.time()-t)
(p/'contract.json').write_text(json.dumps(c,indent=2));(d/'attempt.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec),flush=True)
