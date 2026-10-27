import json,os,subprocess,hashlib
from pathlib import Path
root=Path(r'D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench')
files={n:(root/n).read_text(encoding='utf-8-sig') for n in ['compare_tp.py','mode0_batch.py']}
prompt='Review only important reproducible correctness defects. This is Codex-authored external research tooling, not changes to solver C++ source. Independent reviewer must not run tools or edit files. Numerical wrapper original12 acceptance tests passed. Batch driver4 tests passed. Batch uses unchanged MAGRATHEA in WSL, CSV->cfg->one mode0 per row, validates profile, and does not claim solver internal convergence status which CLI does not expose. Planet rows are synthetic mass/temperature recipes, not observed planet fits. Note built-in gas_default changes molecular weights across100bar, so this batch is explicitly NOT pure TP-shape inference. Check wrapper equations/units/default+pilot config and finite output; batch path/config handling, append-avoidance, timeout, failure gates, caching/summary. Single writer only. Return ONLY JSON {"model":"deepseek","approved":true/false,"issues":[strings]}. Avoid unrelated feature requests. SOURCE:\n'+json.dumps(files)
cmd=[r'D:\Codex\tools\cline\node_modules\@cline\cli-windows-x64\bin\cline.exe','--config',r'D:\Codex\cline-home','--cwd',str(root),'--provider','deepseek','--model','deepseek-v4-pro','--system','Independent read-only code reviewer. No tools. Return exactly JSON model,approved,issues.','--thinking','none','--json','--auto-approve','false','--timeout','60','--retries','1',prompt]
(root/'independent-review-input.md').write_text(prompt,encoding='utf-8')
env={**os.environ,'TEMP':r'D:\Codex\tmp','TMP':r'D:\Codex\tmp','DO_NOT_TRACK':'1','OTEL_SDK_DISABLED':'true'}
with (root/'independent-review.events.jsonl').open('w',encoding='utf-8') as f:
 proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=75)
if proc.returncode:raise SystemExit('Independent review failed; inspect saved event log')
rows=[]
for line in (root/'independent-review.events.jsonl').read_text(encoding='utf-8').splitlines():
 try:rows.append(json.loads(line))
 except ValueError:pass
result=[x for x in rows if x.get('type')=='run_result'][-1];text=result['text'].strip()
if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
verdict=json.loads(text);verdict['model_metadata']=result.get('model');verdict['usage']=result.get('aggregateUsage');verdict['source_sha256']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}
(root/'independent-review.json').write_text(json.dumps(verdict,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:verdict[k] for k in ['model','approved','issues']},ensure_ascii=False))
