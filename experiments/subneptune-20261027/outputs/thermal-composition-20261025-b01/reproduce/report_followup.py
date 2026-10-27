"""Render persisted results; no solver or model calls."""
import csv,hashlib,json,math,sys,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def windows(p):return Path(p.replace('/mnt/d/','D:/'))
def main():
 out=Path(sys.argv[1]);root=Path(__file__).resolve().parent
 check=load(out/'verification.json');assert check['status']=='completed'
 grid=load(out/'forward.json');recover=load(out/'recovery.json');eos=load(out/'eos_comparison.json');runs=load(out/'all_runs.json')
 assert len(runs)==check['total_cases']<=100
 assert len(recover)==4 and all(abs(r['relative_radius_residual'])<=2e-5 for r in recover)
 fig,axes=plt.subplots(1,2,figsize=(9,3.5),layout='constrained')
 for ax,m in zip(axes,[5,8.04]):
  for t in [300,360,450]:
   rows=sorted([r for r in grid if r['mass_me']==m and r['temperature_K']==t],key=lambda r:r['fraction'])
   ax.plot([r['fraction']*100 for r in rows],[r['radius_re'] for r in rows],'o-',label=f'{t} K')
  ax.set(xscale='log',xlabel='Gas mass fraction (%)',ylabel='Radius (Earth radii)',title=f'{m} Earth masses')
  ax.grid(alpha=.25);ax.legend()
 fig.savefig(out/'forward_grid.png',dpi=180);fig.savefig(out/'forward_grid.pdf');plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(9,3.7),layout='constrained')
 for ax,m in zip(axes,[5,8.04]):
  rr=sorted([r for r in recover if r['mass_me']==m],key=lambda r:r['assumed_temperature_K'])
  vals=[rr[0]['recovered_fraction']*100,1,rr[1]['recovered_fraction']*100]
  ax.bar(['300 K','360 K\ntruth','450 K'],vals,color=['#4477AA','#777777','#CC6677'])
  for i,v in enumerate(vals):ax.text(i,v,f'{v:.3f}%',ha='center',va='bottom')
  ax.axhline(1,color='black',ls=':',lw=1);ax.set(ylabel='Inferred gas mass fraction (%)',title=f'{m} Earth masses: same synthetic radius',ylim=(0,max(vals)*1.2))
 fig.savefig(out/'composition_recovery.png',dpi=180);fig.savefig(out/'composition_recovery.pdf');plt.close(fig)
 diagnostics=[]
 for r in runs:
  gas=[]
  for line in windows(r['profile']).read_text().splitlines():
   fields=line.split()
   if len(fields)<7 or fields[0]=='Index':continue
   phase=' '.join(fields[6:])
   if 'Gas' in phase or 'H/He' in phase:
    gas.append((float(fields[2])*1e4,float(fields[5]),float(fields[4]),phase))
  if gas:
   diagnostics.append(dict(case_id=r['case_id'],atmosphere_recipe=r['atmosphere_recipe'],gas_points=len(gas),max_gas_pressure_bar=max(x[0] for x in gas),max_gas_temperature_K=max(x[1] for x in gas),phases=sorted(set(x[3] for x in gas))))
 (out/'gas_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
 old=load(Path(r'D:\GPT\projects\Sub-Neptune\outputs\mode0-inputs-20261025-a17b\results.json'))['runs']
 diffs=[]
 for r in grid:
  if r['fraction']==.01:
   hits=[x for x in old if math.isclose(float(x['row']['mass_of_core'])+float(x['row']['mass_of_mantle'])+float(x['row']['mass_of_atm']),r['mass_me']) and float(x['row']['surface_temp'])==r['temperature_K'] and x['row'].get('tight','0')=='0']
   assert hits
   diffs.append(abs(r['radius_re']-hits[0]['radius_re']))
 assert max(diffs)==0
 check['previous_six_baselines_exact_radius_match']=True
 check['inverse_checks_recomputed']=True
 (out/'verification.json').write_text(json.dumps(check,indent=2))
 lines=['# 温度边界与气层质量：两项比较实验','', '日期：2026-10-25。合成模型；不是目标行星拟合，也不是完整 T–P 曲线接入。', '', '## 先看什么','', '1. 本报告的恢复表及局限。','2. `composition_recovery.png`：同半径对应的不同气层质量。','3. `forward_grid.png`、`forward.csv`：温度与气层质量的正向影响。','4. `recovery.csv`、`recovery.json`：恢复值、残差和数值括区间。','5. `verification.json`、`controls.json`、`eos_comparison.csv`、`gas_diagnostics.json`。','6. `batch-*/` 中每次独立 cfg、完整剖面、stdout、状态及哈希；`all_runs.json` 汇总。','', '## 实验一：固定组成比较温度','', '总质量为5、8.04 M⊕；气层质量分数0.3%、1%、3%；温度边界300、360、450 K，共18个组合。核占岩石部分32.5%，其余为幔；无水层、界面温差为0、外边界压力0.05 bar。使用相同 Fe_default/Si_default/gas_default。', '', '|质量 M⊕|气层质量分数|R(300 K) R⊕|R(360 K) R⊕|R(450 K) R⊕|300→450相对半径变化|','|---:|---:|---:|---:|---:|---:|']
 for m in [5,8.04]:
  for f in [.003,.01,.03]:
   v=[next(r['radius_re'] for r in grid if r['mass_me']==m and r['fraction']==f and r['temperature_K']==t) for t in [300,360,450]]
   lines.append(f'|{m}|{f:.1%}|{v[0]:.7f}|{v[1]:.7f}|{v[2]:.7f}|{v[2]/v[0]-1:+.2%}|')
 lines+=['','## 实验二：相同半径，反推气层质量','', '各质量的合成真值设为360 K、气层1%。仅将假定温度改为300或450 K，用mode0反复求解，通过气层质量的对数二分搜索匹配真值半径；总质量、核幔比例、EOS和外边界压力保持不变。360 K使用已计算的1%作为同温度控制。', '', '|质量 M⊕|假定温度 K|合成半径 R⊕|恢复气层质量分数|相对真值1%的偏差|半径相对残差|','|---:|---:|---:|---:|---:|---:|']
 for r in recover:
  lines.append(f"|{r['mass_me']}|{r['assumed_temperature_K']}|{r['target_radius_re']:.7f}|{r['recovered_fraction']:.5%}|{r['fraction_relative_bias']:+.2%}|{r['relative_radius_residual']:+.3g}|")
 lines+=['','括区间是搜索中有符号残差保留的数值区间，不是统计置信区间。停止条件为相对半径残差≤2×10⁻⁵；它不表示真实行星组成达到相同精度。','', '## 追加对照与验收','', f"- 共{len(runs)}次求解，均通过剖面有限值、质量、表面温度/压力及R/M/P单调检查。CLI未显式导出内部收敛状态，不能仅凭exit 0断言内部误差全部收敛。",'- 新增4项逻辑测试与原驱动4项测试均通过；独立核查全部输入/剖面/日志哈希及求解器源码和二进制一致。实际气层上层严格等温，深层T/P^(2/7)相对漂移不超过9.41×10⁻⁸，见independent_numeric_checks.json。','- 6个1%气层温度基准与此前批跑的半径逐项相同。',f"- 2个真值及4个恢复值收紧ODE/拟合容差，最大相对半径变化为{max(x['relative_radius_change'] for x in check['tight_controls']):.3g}，小于本轮半径匹配停止阈值。",'- 18点在各固定气层比例下的半径均随温度上升；各搜索使用已检查的采样括区间。没有证明全参数域单调或唯一解。','', '|质量 M⊕|温度 K|gas_default R⊕|HHe_tabulated R⊕|相对变化|','|---:|---:|---:|---:|---:|']
 for r in eos:lines.append(f"|{r['mass_me']}|{r['temperature_K']}|{r['gas_default_radius_re']:.7f}|{r['HHe_tabulated_radius_re']:.7f}|{r['relative_radius_change']:+.2%}|")
 lines+=['', '该对照更换了整套气层EOS/热结构处方；不可拆解为单独的EOS效应或纯TP效应。两者低压均沿用Gas_iso，高压分别为理想气体和Chabrier表。','', '## 物理假设和解释边界','', '- 本轮改变的是外边界温度，而非在相同边界下比较不同内部TP形状。当前mode0没有外部完整TP输入入口。本轮结果只能称为温度边界造成的合成组成恢复偏移。','- gas_default在100 bar使用固定相界，并从低压mmol=3切换到高压mmol=2，同时改变热结构。所有主比较固定这套处方，所以不把它的相界当自洽计算的RCB，也没有通过移动相界制造纯热效应。','- 理想气体、固定热容等近似在深层可能失效；气层最大P/T及实际相名保存在gas_diagnostics.json。未执行能量/辐射对流平衡或化学平衡，不能将此结果直接解释为真实H/He丰度偏差。','- 只在固定质量、固定核幔比、无水层、固定边界压力下匹配单个半径。真实观测误差、丰度约束、水/金属丰度、先验和额外组成自由度尚未纳入。改变温度边界也会通过连续温度条件影响固体层，本实验不是仅气层受热的干预。','- 下一项真正检验TP形状的实验，应保持同一外边界和密度EOS，通过可回退接口导入两套TP，再独立做组成恢复。当前结果不能替代它。','', '## 可追溯性与审核','', '本机Windows→WSL→现有mode0，串行运行；每案例无模型调用；另有一次并行进行的DeepSeek审核调用。Codex编写实验驱动；DeepSeek做一次只读审核，原始输出和逐条裁决另存，不能把其原始否决写成通过。', '求解器为隔离worktree，源码基线9e74aac2ccd62cd70102ce9dda922149afcb531b；本轮未修改C++。工具来源、模板、每批源文件/二进制哈希、每个输入和剖面哈希均保存。先前错误的主仓库planet不参与本轮。','', '源文件依据：MAGRATHEA `src/phase.cpp` 的gas_default/HHe_tabulated选择；`src/EOSlist.cpp` 的Gas/Gas_iso定义；`src/main.cpp` 的mode0配置读取。代码基线对应 https://github.com/yt2523/Magrathea/tree/9e74aac2ccd62cd70102ce9dda922149afcb531b 。本轮未新增文献结论或声称复现具体观测行星。','', '## English abstract','', 'Two controlled synthetic tests map radius against boundary temperature and gas mass, then recover gas fractions at fixed synthetic radius using an incorrect boundary temperature. These quantify conditional boundary-temperature sensitivity within one fixed atmospheric prescription, not full TP-shape bias, an observational posterior, or self-consistent radiative/chemical equilibrium. Independent tighter-tolerance runs and a whole-prescription H/He comparison delimit numerical and modelling sensitivity.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 bundle=out/'reproduce';bundle.mkdir(exist_ok=True)
 for name in ['FOLLOWUP_PLAN.md','followup_comparisons.py','test_followup.py','report_followup.py','mode0_batch.py','verify_followup.py','review_followup.py','adjudicate_followup.py']:
  shutil.copy2(root/name,bundle/name)
 manifest={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ['manifest.json','delivery_manifest.json','review.events.jsonl']}
 (out/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps(dict(total_cases=len(runs),max_tolerance_radius_shift=max(x['relative_radius_change'] for x in check['tight_controls']),max_gas_temperature_K=max(x['max_gas_temperature_K'] for x in diagnostics),recoveries=[{k:r[k] for k in ['mass_me','assumed_temperature_K','recovered_fraction','fraction_relative_bias']} for r in recover]),indent=2))
if __name__=='__main__':main()
