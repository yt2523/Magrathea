from pathlib import Path
import json,subprocess,sys,hashlib,shutil
p=Path('/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112'); t=p/'stageC-driver/SYNTHETIC_PROTOCOL_TESTS'; r=p/'stageC-driver/source/run'; results=[]
def call(args):
 a=subprocess.run([sys.executable,*map(str,args)],capture_output=True,text=True); return a.returncode,a.stdout+a.stderr
def gen(name,mode=None):
 cfg=t/'MOCK_template.cfg'; text=cfg.read_text(); f=t/(name+'.cfg'); f.write_text(text+('MOCK_MODE='+mode+'\n' if mode else '')); inp=t/(name+'.json'); inp.write_text(json.dumps({'masses_earth':[1,2],'compositions':[{'id':'MOCK','family':'SYNTHETIC_ONLY','fractions':[.9,0,0,.1]}],'template_cfg':str(f)})); out=t/name; assert call([r/'scan_compositions.py','--generate',inp,out])[0]==0; return out
def run(out,cap=2,extra=[]):return call([r/'execute_scan.py',out,'--backend',t/'backend','--solver',t/'MOCK_audit.py','--checker',t/'MOCK_checker.py','--target-radius',2,'--max-launches',cap,*extra])
def record(name,fn):
 try:fn(); results.append({'test':name,'pass':True})
 except Exception as e:results.append({'test':name,'pass':False,'detail':str(e)})
def resume():
 o=gen('acceptance28-resume');assert run(o,1)[0]==0; l=json.loads((o/'execution.json').read_text());assert l['launch_count']==1;assert run(o,2)[0]==0; a=(o/'execution.json').read_bytes(); assert run(o,2)[0]==0; assert (o/'execution.json').read_bytes()==a
record('bounded launch and idempotent resume',resume)
for mode in ['NO_MODEL','WRONG_MASS','GHOST_WATER','HANG']:
 def check(mode=mode):
  o=gen('acceptance28-'+mode,mode);run(o,2,['--timeout','1']);l=json.loads((o/'execution.json').read_text());assert l['launch_count']==2;assert all(v['status']=='FAILED' for v in l['cases'].values()), l; a=(o/'execution.json').read_bytes();assert run(o,2)[0]==0;assert(o/'execution.json').read_bytes()==a
 record('fail-and-preserve-'+mode,check)
def latebad():
 o=gen('acceptance28-latebad');m=json.loads((o/'manifest.json').read_text());cfg=o/m['cases'][-1]['key']/'run.cfg';cfg.write_text(cfg.read_text()+'# tamper\n');code,msg=run(o);assert code!=0,(code,msg);assert not(o/'execution.json').exists() or json.loads((o/'execution.json').read_text())['launch_count']==0
record('all configs preflight before any launch',latebad)
(t/'acceptance28-results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));sys.exit(not all(x['pass'] for x in results))
