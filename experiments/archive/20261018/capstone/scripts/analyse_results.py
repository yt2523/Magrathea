from pathlib import Path
import json, re, csv, os, platform
ROOT=Path('D:/GPT/projects/Sub-Neptune')
OUT=ROOT/'outputs/capstone-20261018'
WORK=ROOT/'work/capstone-20261018'
os.environ['MPLCONFIGDIR']=str(WORK/'matplotlib-cache')
os.environ['TEMP']=os.environ['TMP']=str(WORK)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
runs=manifest['runs']
byid={r['id']:r for r in runs}
labels={'baseline_300K':'基准 · 300 K','warm_1000K':'温度对照 · 1000 K','ode_tighter':'仅 ODE 容限 /10','ode_and_fit_tighter':'在上一项上匹配容限 /10'}
arrays={}
checks={}
example='1 0.1 100 0.01 5 300 Fe hcp (Smith)'.split(maxsplit=6)
assert len(example)==7 and example[-1]=='Fe hcp (Smith)'
for r in runs:
    text=Path(r['profile']).read_text(encoding='utf-8')
    assert sum(line.startswith('Index') for line in text.splitlines())==1,'Multiple appended models'
    rows=[]; phases=[]
    for line in text.splitlines():
        if not line.strip() or line.startswith('Index'):continue
        fields=line.split(maxsplit=6)
        assert len(fields)==7,(r['id'],line)
        rows.append(list(map(float,fields[:6])))
        phases.append(fields[6])
    a=np.array(rows);arrays[r['id']]=a
    log=Path(r['log']).read_text(encoding='utf-8')
    r['solver_seconds']=float(re.search(r'run time ([\d.eE+-]+)s',log).group(1))
    counts=re.search(r'# of shots (\d+), # of total steps (\d+)',log)
    r['shots'],r['total_steps']=map(int,counts.groups())
    r['profile_points']=len(a)
    r['phase_labels']=list(dict.fromkeys(phases))
    core=int(np.argmin(abs(a[:,3]-.325)))
    r['core_boundary_profile_mass']=float(a[core,3])
    pressure_increase=float(max(0.,np.diff(a[:,2]).max()))
    r['max_outward_pressure_increase_GPa']=pressure_increase
    tests={
      'status_0':r['status']==0,
      'finite_values':bool(np.isfinite(a).all()),
      'positive_P_rho_T':bool((a[:,[2,4,5]]>0).all()),
      'radius_nondecreasing':bool((np.diff(a[:,1])>=-1e-9).all()),
      'mass_nondecreasing':bool((np.diff(a[:,3])>=-1e-9).all()),
      'center_r_m_zero':bool(abs(a[0,1])<1e-12 and abs(a[0,3])<1e-12),
      'total_mass_1ME':bool(abs(a[-1,3]-1)<1e-7),
      'surface_pressure_1e-5GPa':bool(abs(a[-1,2]/1e-5-1)<1e-5),
      'surface_temperature_matches':bool(abs(a[-1,5]-float(r['changes'].get('surface_temp','300')))<1e-4),
      'core_mass_0_325ME':bool(abs(a[core,3]-.325)<5e-6),
      'no_large_outward_pressure_increase':bool(pressure_increase/max(a[:,2])<1e-4),
      'no_error_or_warning_logged':not bool(re.search(r'Error:|Warning:|No solution found',log)),
    }
    checks[r['id']]=tests
    assert all(tests.values()),(r['id'],tests)
assert manifest['diagnostics_baseline_profile_identical']
comparisons=[]
for new,reference,purpose in [('warm_1000K','baseline_300K','温度改变'),('ode_tighter','baseline_300K','积分容限改变'),('ode_and_fit_tighter','ode_tighter','匹配容限改变')]:
    n,b=byid[new],byid[reference]
    comparisons.append({'new':new,'reference':reference,'purpose':purpose,'delta_R_RE':n['radius_RE']-b['radius_RE'],'delta_R_km':(n['radius_RE']-b['radius_RE'])*6378.1,'relative_R_change':(n['radius_RE']-b['radius_RE'])/b['radius_RE'],'relative_Pc_change':(n['Pc_GPa']-b['Pc_GPa'])/b['Pc_GPa'],'relative_Tc_change':(n['Tc_K']-b['Tc_K'])/b['Tc_K'],'relative_core_radius_change':(n['interfaces_RE'][0]-b['interfaces_RE'][0])/b['interfaces_RE'][0]})
environment={'os':'Windows 11 + Ubuntu 26.04 LTS WSL 2 (disk on D:)','cpu':'Intel Core i5-13500H','host_RAM_GB':15.7,'gxx':'15.2.0','make':'4.4.1','GSL':'2.8','plotting_location':'existing Windows Python, reading Ubuntu-produced data on D:','python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__}
summary={'source_commit':manifest['plan']['source_commit'],'environment':environment,'runs':runs,'comparisons':comparisons,'checks':checks,'diagnostics_baseline_profile_identical':True,'limitations':['One composition and two temperatures; not a TOI-732 c model.','Two tolerance comparisons are sensitivity checks, not a certified global error bound.','The original CLI does not report getstatus; a temporary main.cpp copy prints status and high-precision result values without modifying the solver/EOS sources.','Exact matching residual components are not exposed by this run logger.','Wall-clock timings include WSL process startup; solver times come from the original program timer.','Output profiles are decimated and rounded by hydro::print.']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['case','status','R_RE','R_km','Pc_GPa','Tc_K','R_core_RE','solver_seconds','wall_seconds','shots','total_steps','profile_points'])
    for r in runs:writer.writerow([r['id'],r['status'],r['radius_RE'],r['radius_RE']*6378.1,r['Pc_GPa'],r['Tc_K'],r['interfaces_RE'][0],r['solver_seconds'],r['wall_seconds'],r['shots'],r['total_steps'],r['profile_points']])

plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.22,'savefig.facecolor':'white'})
figdir=OUT/'figures';figdir.mkdir(exist_ok=True)
panels=[('radius_mass',3,1,'Enclosed mass / Earth mass','Radius / Earth radius',False),('pressure_radius',1,2,'Radius / Earth radius','Pressure / GPa',False),('temperature_pressure',2,5,'Pressure / GPa','Temperature / K',True),('density_pressure',2,4,'Pressure / GPa','Density / (g cm$^{-3}$)',True)]
def panel(ax,item):
    name,x,y,xlabel,ylabel,xlog=item
    for key,label,color in [('baseline_300K','300 K surface','#216d70'),('warm_1000K','1000 K surface','#bb632c')]:
        a=arrays[key];ax.plot(a[:,x],a[:,y],label=label,color=color,lw=1.8)
    if xlog:ax.set_xscale('log')
    if name=='pressure_radius':ax.set_yscale('log')
    ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.legend(frameon=False,fontsize=10)
    ax.margins(x=.02)
combined,axes=plt.subplots(2,2,figsize=(11,8.4),constrained_layout=True)
for ax,item in zip(axes.flat,panels):
    panel(ax,item)
    single,sax=plt.subplots(figsize=(7.2,4.5),constrained_layout=True);panel(sax,item)
    single.savefig(figdir/(item[0]+'.png'),dpi=180);single.savefig(figdir/(item[0]+'.svg'));plt.close(single)
combined.suptitle('MAGRATHEA: 1 Earth mass, 32.5% core + 67.5% mantle',fontsize=13)
combined.savefig(figdir/'profiles.png',dpi=180);combined.savefig(figdir/'profiles.pdf');plt.close(combined)
fig,ax=plt.subplots(figsize=(7.2,4.5),constrained_layout=True)
values=[abs(c['relative_R_change']) for c in comparisons]
ax.bar(['Surface T\n300 to 1000 K','ODE tolerance\n1e-10 to 1e-11','Fit tolerance\n1e-4 to 1e-5'],values,color=['#bb632c','#216d70','#547da1'],width=.55)
ax.set_yscale('log');ax.set_ylabel('|Delta R| / R of reference case');ax.set_title('Measured sensitivity; not an absolute error bound',fontsize=11)
for i,v in enumerate(values):ax.text(i,v*1.6,f'{v:.2e}',ha='center',fontsize=10)
ax.set_ylim(min(values)/5,max(values)*12);fig.savefig(figdir/'sensitivity.png',dpi=180);plt.close(fig)

heat,ode,fit=comparisons
table=''.join(f'<tr><td>{labels[r["id"]]}</td><td>{r["status"]}</td><td>{r["radius_RE"]:.11f}</td><td>{r["Pc_GPa"]:.6f}</td><td>{r["Tc_K"]:.6f}</td><td>{r["solver_seconds"]:.3f}</td></tr>' for r in runs)
phase_text='；'.join(byid['baseline_300K']['phase_labels'])
captions={'radius_mass':'半径与包围质量：相同总质量，温度对照的外半径稍大。','pressure_radius':'压强与半径：压强向外降低；对数轴展示从中心到外边界的跨度。','temperature_pressure':'温度与压强：这两条路径来自所选热模型，Tgap=0；表面温度是输入。','density_pressure':'密度与压强：材料层和模型切换可产生折点或跳变，不能要求全局光滑。'}
imagehtml=''.join(f'<figure class="report-figure"><a href="../assets/capstone-20261018/{p[0]}.png"><img src="../assets/capstone-20261018/{p[0]}.png" alt="{captions[p[0]]}" loading="lazy"></a><figcaption>{captions[p[0]]} 点击可打开大图。</figcaption></figure>' for p in panels)
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第十七课 · 实际运行记录</title><link rel="stylesheet" href="../assets/style.css"></head><body><main><nav class="course-nav"><a href="../index.html">课程目录</a><a href="../lessons/0017-capstone.html">返回第十七课</a></nav><p class="meta">2026-10-18 · 本机 Ubuntu WSL 2 实测</p><h1>第一次把完整求解链跑通</h1><p class="lead">编译和两个内置测试通过；四个模型均返回正常状态 0。温度对照使半径增大 {heat['relative_R_change']*100:.3f}%，约 {heat['delta_R_km']:.2f} km。</p><h2>01 · 这次具体算了什么？</h2><p>使用仓库 mode0.cfg 的类地球案例：总质量 1 M⊕，铁核 0.325 M⊕、岩幔 0.675 M⊕，水层与气层质量均为零。使用 Fe_default、Si_default，三个层间温差均为零，Psurface=10⁵ µbar=10⁻⁵ GPa=0.1 bar。</p><p>main 的 mode 0 调用 fitting_method，并传入 isothermal=false；温度沿各材料的热处理计算。Rloop 生成初猜，随后从中心和表面积分，在 Mfit≈0.2 Mtot 处匹配 r、P、T。核幔材料边界位于 0.325 Mtot，与数值匹配点不同。</p><p>“类地球”在这里描述质量与核幔比例。300 K 外边界及所用热闭合给出约 610 K 的中心温度；本次没有用地球地温资料校准模型，也没有求解冷却演化。这也不是 TOI-732 c 的模型。</p><h2>02 · 测试、状态与复现信息</h2><ul><li>原源码编译成功；Vinet EOS 反演和常密度球解析半径测试通过。</li><li>源码固定在 <code>4c560f36d2734f6b63ae5118d4074e0c255b59f0</code>。</li><li>环境：Ubuntu 26.04 / WSL 2，g++ 15.2.0，Make 4.4.1，GSL 2.8。</li><li>原 main 不打印收敛状态，因此只在临时 main 副本中添加 getstatus、半径和中心量的日志。原 fork 科学源码未修改。</li><li>原可执行文件与日志构建的基准剖面 SHA-256 完全相同。</li><li>四个案例均检查了有限性、正密度、质量/半径排序、总质量、表面条件和材料边界；未记录错误或警告。</li></ul><p><a href="../assets/capstone-20261018/builtin-tests.log">查看内置测试日志</a> · <a href="../assets/capstone-20261018/summary.csv">下载结果表 CSV</a></p><h2>03 · 四个案例的实测结果</h2><div class="table-scroll"><table><tr><th>案例</th><th>状态</th><th>R / R⊕</th><th>Pc / GPa</th><th>Tc / K</th><th>求解耗时 / s</th></tr>{table}</table></div><p class="meta">R⊕ 按源码定义为 6378.1 km。耗时为程序内部计时；含 WSL 启动等开销的单次进程时间约 5–6 秒。没有用一次计时评估严格的性能差异。</p><h2>04 · 从图上读结果</h2>{imagehtml}<p>基准文件记录的模型标签包括：{phase_text}。这些标签标识使用的 EOS/相模型，不应仅凭名字变化就认定发生了严格热力学相变。</p><h2>05 · 把物理变化和数值变化分别比较</h2><p><strong>温度实验：</strong>只将表面温度从 300 K 改为 1000 K，半径增加 {heat['delta_R_km']:.2f} km，中心压强从 {byid['baseline_300K']['Pc_GPa']:.3f} 降到 {byid['warm_1000K']['Pc_GPa']:.3f} GPa。结果与温度通过 EOS 影响密度、结构随之调整的机制相容；没有把这一结果推广到任意组成或气层模型。</p><p><strong>积分实验：</strong>保持物理输入与匹配容限不变，将 ode_eps_rel1 从 10⁻¹⁰ 收紧至 10⁻¹¹，半径相对变化 {ode['relative_R_change']:.3e}。</p><p><strong>匹配实验：</strong>在更严格的 ODE 设置下，再将 fit_eps_rel 从 10⁻⁴ 收紧至 10⁻⁵，半径相对变化 {fit['relative_R_change']:.3e}。两次都只改变一个数值设置；这组结果中，匹配容限调整带来的变化更大。</p><figure class="report-figure"><img src="../assets/capstone-20261018/sensitivity.png" alt="温度、积分容限与匹配容限三组实验的半径相对变化" loading="lazy"><figcaption>纵轴为各自对照组的半径变化绝对值；这不是全局误差的认证上限。</figcaption></figure><p class="note">更严格设置下半径变化很小，支持这一个案例在所试设置间相对稳定。仅两次容限比较不能证明精确解已找到，也不能认证材料物理。中心量和材料界面半径也应一起检查，完整数值在 CSV 中。</p><h2>06 · 你现在可以复现哪一步？</h2><p>先在 Ubuntu 中打开 D 盘仓库，重新运行现有测试：</p><pre>cd /mnt/d/GPT/projects/Sub-Neptune/Magrathea
make -j4
./planet --test</pre><p>模型运行前，复制一份配置并设置新的输出文件名：hydro::print 会追加写入，重复使用同一路径会混入多个模型。本次每个案例都使用独立文件，完整配置与日志保存在 D 盘实践目录。</p><p>阅读任务：对照两个温度案例的 T–P 与 ρ–P 图，沿第七、八课的调用链说明温度如何影响最终半径。可以直接带图或函数继续提问，无需先提交答案。</p><h2>本次验证的范围</h2><p>本次跑通了编译 → 简单数值测试 → 单模型 → 单变量对照 → 剖面检查与绘图。没有运行 MCMC、连接 HPC 或安装新依赖；没有直接记录三个匹配残差分量，状态 0 来自求解器的返回状态。普通剖面文件经过筛点并按 8 位有效数字输出，高精度半径比较使用临时日志中的值。</p><p><a href="https://github.com/Huang-CL/Magrathea/blob/{manifest['plan']['source_commit']}/src/main.cpp#L401">源码：mode 0 调用</a> · <a href="https://github.com/Huang-CL/Magrathea/blob/{manifest['plan']['source_commit']}/src/hydro.cpp#L1699">源码：两端匹配与状态</a></p><nav class="pager"><a href="../lessons/0017-capstone.html">← 返回结课实践</a><a href="../index.html">全部课程 →</a></nav></main></body></html>'''
(OUT/'report.html').write_text(page,encoding='utf-8')
md=f'''# MAGRATHEA 结课实践实测 · 2026-10-18

编译成功；两个内置测试通过；四个模型均返回 status=0。源码版本 {manifest['plan']['source_commit']}。

## 模型
总质量 1 M⊕，铁核 0.325 M⊕、岩幔 0.675 M⊕，无水和气层。Psurface=0.1 bar，三个界面温差均为零。类地球指质量和核幔比例，不代表真实地球热结构或 TOI-732 c。

|案例|R/R⊕|Pc/GPa|Tc/K|求解耗时/s|
|---|---:|---:|---:|---:|
'''
for r in runs:md+=f'|{labels[r["id"]]}|{r["radius_RE"]:.11f}|{r["Pc_GPa"]:.6f}|{r["Tc_K"]:.6f}|{r["solver_seconds"]:.3f}|\n'
md+=f'''\n表面温度 300→1000 K，半径增加 {heat['relative_R_change']*100:.6f}%（{heat['delta_R_km']:.6f} km）。ODE 容限 1e-10→1e-11，半径相对变化 {ode['relative_R_change']:.6e}；在该设置上匹配容限 1e-4→1e-5，半径相对变化 {fit['relative_R_change']:.6e}。这些是设置敏感性，不是绝对误差上限。

原 CLI 不打印模型状态，临时 main 副本只增加只读日志，链接原始求解器/EOS 对象。原科学源码未修改；两种构建的基准剖面逐字节一致。未直接记录三分量匹配残差。

四个剖面均通过有限性、正 P/ρ/T、质量/半径排序、总质量、外边界和核幔边界检查。普通输出筛点并四舍五入，高精度比较使用诊断日志值。

运行命令、配置及哈希见 manifest.json；完整数值与检查见 summary.json / summary.csv；绘图见 figures；原始剖面见 profiles；日志见 logs。图由现有 Windows Python {platform.python_version()} / NumPy {np.__version__} / Matplotlib {matplotlib.__version__} 读取 Ubuntu 结果生成，没有安装依赖。

仅完成这一组成的小规模实践；未运行 MCMC、HPC 或完整科学验证。重复运行必须换输出名，防止追加混合。\n'''
(OUT/'README.md').write_text(md,encoding='utf-8')
print(json.dumps({'comparisons':comparisons,'checks':checks,'phase_labels':{r['id']:r['phase_labels'] for r in runs},'environment':environment},ensure_ascii=False,indent=2))
