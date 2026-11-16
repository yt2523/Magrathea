from pathlib import Path
import subprocess,json,time,hashlib
p=Path('/mnt/d/Codex/downloads/toi732c-old-cross-audit-20261116');q=p/'search40';binary=q/'planet'
for name in ['grid-17','grid-21']:
 d=q/name;d.mkdir();cfg=d/'run.cfg';original=(p/'campaign/cases'/name/'config').read_text();oldout=p/'campaign/cases'/name/'model.dat';cfg.write_text(original.replace(str(oldout),str(d/'model.dat')));receipt={'diagnostic_only':True,'search_cap':40,'config_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'state':'STARTED'};(d/'attempt.json').write_text(json.dumps(receipt));start=time.monotonic()
 with (d/'stdout.log').open('w') as fo,(d/'stderr.log').open('w') as fe:
  try:rc=subprocess.run([str(binary),str(cfg)],cwd=q,stdout=fo,stderr=fe,timeout=180).returncode
  except subprocess.TimeoutExpired:rc=124
 receipt.update(state='FINISHED',exit=rc,elapsed=time.monotonic()-start);(d/'attempt.json').write_text(json.dumps(receipt));print(name,rc,flush=True)
