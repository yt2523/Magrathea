from pathlib import Path
import json,subprocess,sys,hashlib
p=Path('/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112');t=p/'stageC-driver/SYNTHETIC_PROTOCOL_TESTS';r=p/'stageC-driver/source/run';o=t/'acceptance28-resume';base=[sys.executable,str(r/'execute_scan.py'),str(o),'--backend',str(t/'backend'),'--solver',str(t/'MOCK_audit.py'),'--checker',str(t/'MOCK_checker.py'),'--target-radius','2','--max-launches','2'];res=[]
def rejects(name,change,restore,args=base):
 before=(o/'execution.json').read_bytes();change()
 try:
  a=subprocess.run(args,capture_output=True,text=True);assert a.returncode!=0,(name,a.stdout,a.stderr);assert(o/'execution.json').read_bytes()==before;res.append({'test':name,'pass':True,'message':(a.stdout+a.stderr).strip()})
 finally:restore()
l=json.loads((o/'execution.json').read_text());key=next(iter(l['cases']));model=o/key/'model.dat';raw=model.read_bytes();rejects('tampered model',lambda:model.write_bytes(raw+b'\n'),lambda:model.write_bytes(raw));runtime=o/key/'runtime.json';raw2=runtime.read_bytes();rejects('tampered runtime',lambda:runtime.write_bytes(raw2+b' '),lambda:runtime.write_bytes(raw2));table=t/'backend/tabulated/SYNTHETIC_TABLE.txt';raw3=table.read_bytes();rejects('table identity changed',lambda:table.write_bytes(raw3+b' '),lambda:table.write_bytes(raw3));stray=o/key/'unrecorded.dat';rejects('unrecorded output',lambda:stray.write_text('SYNTHETIC'),lambda:stray.unlink());rejects('target identity changed',lambda:None,lambda:None,base[:-4]+['--target-radius','3','--max-launches','2'])
rawled=(o/'execution.json').read_bytes();bad=json.loads(rawled);bad['cases'][key]['status']='RUNNING';rejects('interrupted RUNNING',lambda:(o/'execution.json').write_text(json.dumps(bad)),lambda:(o/'execution.json').write_bytes(rawled)) if False else None
# RUNNING: compare ledger to deliberate input, not old terminal snapshot.
(o/'execution.json').write_text(json.dumps(bad));interrupted=(o/'execution.json').read_bytes();a=subprocess.run(base,capture_output=True,text=True);assert a.returncode!=0;assert(o/'execution.json').read_bytes()==interrupted;(o/'execution.json').write_bytes(rawled);res.append({'test':'RUNNING needs review','pass':True})
(t/'hardening28-results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
