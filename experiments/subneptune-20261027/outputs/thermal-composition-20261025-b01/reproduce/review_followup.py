import json,os,subprocess,hashlib
from pathlib import Path
root=Path(r'D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench')
out=Path(r'D:\GPT\projects\Sub-Neptune\outputs\thermal-composition-20261025-b01')
files={n:(root/n).read_text(encoding='utf-8-sig') for n in ['followup_comparisons.py','test_followup.py','FOLLOWUP_PLAN.md']}
prompt='Independent review: return only important reproducible defects in this controlled synthetic numerical experiment. No tools or edits. Underlying mode0_batch.py already tested and independently reviewed: validates cfg/profile, positive finite values, mass/surface boundaries, monotonic radius/mass/pressure, immutable attempt dirs, source/binary hashes. Now assess experiment design, bisection bounds, mass accounting, claims and error gates. It measures Ts boundary sensitivity, NOT full TP shape or observed planet fits. EOS sensitivity deliberately changes entire atmospheric prescription, NOT pure EOS. Monotonicity is only sampled, uncertainty not posterior. Four helper tests passed. Return JSON {"model":"deepseek","approved":true/false,"issues":[strings]}. Source:\n'+json.dumps(files)
cmd=[r'D:\Codex\tools\cline\node_modules\@cline\cli-windows-x64\bin\cline.exe','--config',r'D:\Codex\cline-home','--cwd',str(root),'--provider','deepseek','--model','deepseek-v4-pro','--system','Read-only independent numerical code reviewer. No tools. Return only JSON model,approved,issues.','--thinking','none','--json','--auto-approve','false','--timeout','60','--retries','1',prompt]
env={**os.environ,'TEMP':r'D:\Codex\tmp','TMP':r'D:\Codex\tmp','DO_NOT_TRACK':'1','OTEL_SDK_DISABLED':'true'}
with (out/'review.events.jsonl').open('w',encoding='utf-8') as f:
 p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=75)
if p.returncode:raise SystemExit('review failed; preserved events')
rows=[]
for line in (out/'review.events.jsonl').read_text(encoding='utf-8').splitlines():
 try:rows.append(json.loads(line))
 except ValueError:pass
r=[x for x in rows if x.get('type')=='run_result'][-1];answer=r['text'].strip()
if answer.startswith('```'):answer='\n'.join(answer.splitlines()[1:-1])
v,end=json.JSONDecoder().raw_decode(answer);v["format_deviation"]=answer[end:];v.update(model_metadata=r.get('model'),usage=r.get('aggregateUsage'),source_sha256={k:hashlib.sha256(s.encode()).hexdigest() for k,s in files.items()})
(out/'independent-review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(v,ensure_ascii=False))
