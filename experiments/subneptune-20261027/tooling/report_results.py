from pathlib import Path
import csv,json,hashlib,shutil,sys,platform,importlib.metadata as meta
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path(r'D:\GPT\projects\Sub-Neptune\outputs\mode0-inputs-20261025-a17b');tools=Path(r'D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench')
d=json.loads((out/'results.json').read_text());v=json.loads((out/'verification.json').read_text());new=json.loads((out/'inputs_manifest.json').read_text());old=json.loads((out/'inputs_manifest.before_clean_build.json').read_text())
assert d['status']=='completed' and d['completed_cases']==8
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=Path(r'D:\GPT\projects\Sub-Neptune\Magrathea');source_equal=new['source_sha256']==old['source_sha256'];original_binary_retained=sha(original/'planet')==old['solver_binary_sha256']
assert source_equal and original_binary_retained and new['solver_binary_sha256']!=old['solver_binary_sha256']
# Compare repaired wrapper against all54 independently checked prior fixed-input evaluations.
a=json.loads((out/'repaired_tp_results.json').read_text(encoding='utf-8-sig'));b=json.loads(Path(r'D:\GPT\projects\Sub-Neptune\outputs\tp-comparison-20261025-dedb3d\results.json').read_text())
key=lambda r:(r['nlevel'],r['tint_K'],r['gamma'],r['anchor_bar']);index={key(r):r for r in b['rows']};max_difference=0.
for r in a['rows']:
 ref=index[key(r)]
 for name,value in r.items():
  if isinstance(value,(int,float)) and not isinstance(value,bool):max_difference=max(max_difference,abs(value-ref[name])/max(1,abs(ref[name])))
assert len(a['rows'])==54 and max_difference<1e-12
review=json.loads((tools/'independent-review.json').read_text())
assert review['approved'] and all(hashlib.sha256((tools/name).read_text(encoding='utf-8-sig').encode()).hexdigest()==h for name,h in review['source_sha256'].items())
shutil.copyfile(tools/'demo_cases.csv',out/'input_table.csv');shutil.copyfile(tools/'MODE0_PLAN.json',out/'plan.json');shutil.copyfile(tools/'clean-build.log',out/'clean-build.log');shutil.copyfile(tools/'independent-review.json',out/'independent-review.json')
fields=['case_id','mass_me','surface_temperature_K','radius_re','central_pressure_GPa','central_temperature_K','elapsed_seconds','profile_rows','status']
with (out/'comparison.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(d['runs'])
normal=[r for r in d['runs'] if not any(s in r['case_id'] for s in ('repeat','tight'))]
fig,ax=plt.subplots(figsize=(7.5,4.8))
for mass in (5.,8.04):
 group=sorted([r for r in normal if r['mass_me']==mass],key=lambda r:r['surface_temperature_K'])
 ax.plot([r['surface_temperature_K'] for r in group],[r['radius_re'] for r in group],'o-',label=f'{mass:g} Earth masses')
ax.set(xlabel='Outer boundary temperature [K]',ylabel='Radius [Earth radii]',title='Unmodified MAGRATHEA: repeated mode0 inputs')
ax.grid(alpha=.25);ax.legend();fig.text(.5,.015,'Synthetic recipes; 1% gas mass; unchanged gas_default; not observed-planet fits',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.04,1,1));fig.savefig(out/'radius_vs_temperature.png',dpi=170);fig.savefig(out/'radius_vs_temperature.pdf');plt.close(fig)
rows={r['case_id']:r for r in normal}
table='\n'.join('| '+str(t)+' | '+f"{rows['demo5_T'+str(t)]['radius_re']:.7f}"+' | '+f"{rows['demo8p04_T'+str(t)]['radius_re']:.7f}"+' |' for t in (300,360,450))
report=f'''# 程序修复与 mode0 输入批跑报告

## 已完成

1. **通用 TP 比较外壳已修复**，不再只运行挑选出的核心。原来失败的12项验收全部通过；默认完整CLI生成54个结果，试跑配置和严格JSON输出也通过。对照上一轮受控计算，最大归一差为{max_difference:.3g}，处于浮点舍入量级。
2. 新建“CSV→独立cfg→逐次mode0”入口。两个示例质量、三种边界温度共6个组合，另加同输入重复和收紧容差，共8次，全部通过剖面及边界检查。
3. 发现并绕开现有编译产物问题：旧程序在8.04M⊕输入中只输出7.9596M⊕，少了气层质量，已被检查拦下。当前源码在隔离目录强制重编后输出恢复正确，半径1.9811274R⊕与历史基准的输出精度一致。两份源码逐字节一致，旧二进制仍保留，没有覆盖。
4. **没有修改 MAGRATHEA C++ 源码。** 新编译目录在独立分支，原仓库的未提交修改保留。用户后续允许源码修改的授权已记录；本轮不需要改算法。

## 本次计算结果

以下是示例模型，不是两个真实观测行星的拟合。质量5及8.04M⊕，均为1%气层、99%岩石部分；岩石部分核/幔质量比0.325/0.675，水层质量为0，表面压力0.05bar，界面温差为0。EOS选择固定为原配置的Fe_default、Si_default、water_default、gas_default。

| 外边界温度 [K] | 5 M⊕ 半径 [R⊕] | 8.04 M⊕ 半径 [R⊕] |
|---|---|---|
{table}

这是**同一组成模型的外边界温度敏感性**，不是把完整TP文件输入了求解器，也不是组成推断偏差。没有使用观测半径作反演。

## 验证

- 原TP程序12项验收通过；新增批跑4项测试通过。
- 独立DeepSeek审核了本次Codex修复的两个Python文件，通过且无待修意见；原始输出和源文件摘要已保存。
- 每次mode0都检查新输出文件、有限正P/rho/T、中心边界、表面总质量/温度/压强、质量/半径/压强顺序。每次有45秒超时，并记录配置、日志、原始剖面和哈希。
- 8.04M⊕、360K的两次剖面逐字节相同。
- 收紧ode_eps_rel1及fit_eps_rel后，半径相对变化为{v['tight_relative_radius_change']:.9g}；这是本次观测到的稳定性诊断，不是严格误差上界或全局收敛证明。输出本身只有8位有效数字。
- 再次恢复及Windows启动器检查均跳过全部8个已完成任务，未追加重复剖面。原失败尝试也保留在独立attempt目录。
- 未修改的CLI没有暴露内部model-status字段，因此报告只标记profile_checks_passed，不把退出码0或剖面存在当作完整的物理/收敛认证。

## 怎么跑下一批

入口目录：`{tools}`。

编辑一份新的CSV，每行一个模型，再运行：

```powershell
.\\Run-Mode0.ps1 -Table .\\你的输入表.csv
```

默认输出到新的D盘目录。所有任务都是`input_mode=0`，不需要使用其他mode。每个模型的EOS仍由明确的cfg模板选择；更换模板时必须核对单位、EOS适用区间和热结构。

同一批中断后：

```powershell
.\\Run-Mode0.ps1 -Table .\\你的输入表.csv -Output '原结果目录' -Resume
```

已完成且输入/二进制/源码/配置/剖面摘要匹配的任务才会跳过；未完成或失效的任务使用新的attempt目录重新运行，不覆盖先前文件。运行前不要把原目录里已知异常的旧planet当成当前可用程序。

## TP接口与科学解释边界

源码`src/main.cpp`的mode0读取层质量、表面温度与压力、温差、容差和内置EOS选择，没有完整外部TP剖面文件入口。

此外，`src/phase.cpp`在100bar切换Gas_iso/Gas；`src/EOSlist.cpp`中其第5号参数分别为3与2，`src/EOS.cpp`将该参数映射到mmol。因此直接移动该相图切换点会同时改变热梯度和气体摩尔质量/密度，不能称为纯TP效应。现阶段只是固定该默认模型、改变边界温度。后续若加入TP文件接口，应单独控制mu、EOS与热结构，并证明默认输入的回归结果保持一致。

## 回退与版本

- 原MAGRATHEA仓库和可执行文件未覆盖；没有源码补丁需要回退。
- 新工作目录：`D:\\GPT\\projects\\Sub-Neptune\\work\\magrathea-mode0-clean-20261025-a17b`。
- 独立分支：`workflow/mode0-inputs-20261025`，基于9e74aac；仅做重新编译。
- 外部脚本的Git仓库：`{tools}`；原失败脚本已在提交81df8b4保存，修复另有提交。可用git show或revert查看/撤销，不需要reset原仓库。
- 未推送GitHub，未修改Zotero。

## 优先阅读

1. 本报告。
2. radius_vs_temperature.png及comparison.csv。
3. input_table.csv和每个case下的input.cfg。
4. verification.json及independent-review.json。
5. 每个attempt的stdout.log/profile.txt、inputs_manifest.json及旧编译产物记录。
'''
(out/'REPORT.md').write_text(report,encoding='utf-8')
checks={'wrapper_original_tests_passed':12,'batch_tests_passed':4,'wrapper_full_rows':54,'wrapper_vs_previous_max_scaled_difference':max_difference,'mode0_runs_passed':8,'repeat_bytewise_identical':True,'resume_all8_cached':True,'source_files_equal_between_original_and_clean_build':source_equal,'original_executable_retained':original_binary_retained,'clean_executable_differs':True,'independent_review_approved':review['approved']}
(out/'repair_verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
manifest={'code_author':'Codex (explicit user authorization)','reviewer':'DeepSeek independent context','scientific_scope':'boundary-temperature batch at fixed built-in EOS; no full-TP-file import or composition inversion','solver_source_modified':False,'solver_head':'9e74aac2ccd62cd70102ce9dda922149afcb531b','branch':'workflow/mode0-inputs-20261025','python':platform.python_version(),'versions':{n:meta.version(n) for n in ['numpy','scipy','matplotlib']},'source_files':{n:sha(tools/n) for n in ['compare_tp.py','mode0_batch.py','Run-Mode0.ps1','demo_cases.csv']},'checks':checks}
manifest['artifact_sha256']={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'}
(out/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
