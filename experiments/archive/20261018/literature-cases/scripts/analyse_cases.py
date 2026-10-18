from pathlib import Path
import json,re,csv,os,platform
ROOT=Path('D:/GPT/projects/Sub-Neptune');OUT=ROOT/'outputs/literature-cases-20261018';WORK=ROOT/'work/literature-cases-20261018'
os.environ['MPLCONFIGDIR']=str(WORK/'matplotlib-cache');os.environ['TEMP']=os.environ['TMP']=str(WORK)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
plan=manifest['plan'];runs=manifest['runs'];cases=[dict(c) for c in plan['cases']];byid={r['id']:r for r in runs}
for c in cases:
    if c['id']=='steam50':c.update(id='steam50_P0_0p2bar',label='50%水岩蒸汽 · 0.2bar对照',P0_bar=.2)
arrays={};phase_lists={};checks={};table_ranges={}
source=(ROOT/'Magrathea/src/EOSlist.cpp').read_text(encoding='utf-8')
for label,file in re.findall(r'new EOS\("([^"\n]+)", "\./tabulated/([^"\n]+)"\)',source):
    if label not in ['Water (Bollengier/SF)','Water (IAPWS)','Water Liq&SC (Brown)','H20 Vapor (IAPWS)','H/He (Chabrier)','Ice Ih (SeaFreeze)','Ice II (SeaFreeze)','Ice III (SeaFreeze)','Ice V (SeaFreeze)','Ice VI (SeaFreeze)']:continue
    data=np.loadtxt(ROOT/'Magrathea/tabulated'/file,skiprows=1)
    table_ranges[label]={'file':file,'Pmin_GPa':float(data[:,0].min()),'Pmax_GPa':float(data[:,0].max()),'Tmin_K':float(data[:,1].min()),'Tmax_K':float(data[:,1].max())}
for r in runs:
    assert r['exit_code']==0 and r['status']==0,(r['id'],r['status'])
    text=Path(r['profile']).read_text(encoding='utf-8');assert sum(l.startswith('Index') for l in text.splitlines())==1
    rows=[];phases=[]
    for line in text.splitlines():
        if not line.strip() or line.startswith('Index'):continue
        f=line.split(maxsplit=6);assert len(f)==7
        rows.append(list(map(float,f[:6])));phases.append(f[6])
    a=np.array(rows);arrays[r['id']]=a;phase_lists[r['id']]=phases
    pressure_up=float(max(0.,np.diff(a[:,2]).max()))
    test={
      'status0':r['status']==0,'finite':bool(np.isfinite(a).all()),'P_rho_T_positive':bool((a[:,[2,4,5]]>0).all()),
      'mass_sorted':bool((np.diff(a[:,3])>=-1e-7).all()),'radius_sorted':bool((np.diff(a[:,1])>=-1e-8).all()),
      'center_r_m_zero':bool(abs(a[0,1])<1e-12 and abs(a[0,3])<1e-12),
      'total_mass':bool(abs(a[-1,3]/r['mass_ME']-1)<1e-6),
      'surface_P':bool(abs(a[-1,2]/(r['P0_bar']*1e-4)-1)<1e-5),
      'surface_T':bool(abs(a[-1,5]-r['T0_K'])<1e-4),
      'no_large_outward_pressure_increase':bool(pressure_up/a[:,2].max()<1e-4)}
    checks[r['id']]=test;assert all(test.values()),(r['id'],test)
    r['profile_points']=len(a);r['phase_labels']=list(dict.fromkeys(phases));r['Tmin_K']=float(a[:,5].min());r['Tmax_K']=float(a[:,5].max());r['max_pressure_increase_GPa']=pressure_up
    r['surface_density_gcm3']=float(a[-1,4]);r['physical_flags']=[]
    if r['case_id']=='steam50' and r['P0_bar']==.05:
        r['physical_flags'].append('Low-pressure vdW branch: surface density0.44762g/cm3 at400K/0.05bar versus gas root2.70668e-5; direct EOS probe confirms initial-guess dependent roots. Excluded from recommended composition comparison.')
    r['accepted_table_box_outliers']=[]
    for label,bounds in table_ranges.items():
        mask=np.array([p==label for p in phases]);d=a[mask]
        if not len(d):continue
        bad=(d[:,2]<bounds['Pmin_GPa']*(1-1e-6))|(d[:,2]>bounds['Pmax_GPa']*(1+1e-6))|(d[:,5]<bounds['Tmin_K']-1e-3)|(d[:,5]>bounds['Tmax_K']+1e-3)
        if bad.any():r['accepted_table_box_outliers'].append({'label':label,'count':int(bad.sum()),'examples':d[bad][:3].tolist()})
    if r['case_id']=='hycean_rigby':
        j=int(np.argmin(abs(a[:,1]-r['interfaces_RE'][2])))
        r['HHB']={'P_bar':float(a[j,2]*1e4),'T_K':float(a[j,5]),'radius_RE':float(a[j,1]),'mass_ME':float(a[j,3]),'water_side_phase_label':phases[j],'method':'nearest printed point to water-layer radius; rounded output'}
stability=[]
for c in cases:
    b=byid[c['id']];t=byid[c['id']+'_tight']
    stability.append({'id':c['id'],'relative_radius_change':(t['radius_RE']-b['radius_RE'])/b['radius_RE'],'relative_Pc_change':(t['Pc_GPa']-b['Pc_GPa'])/b['Pc_GPa'],'relative_Tc_change':(t['Tc_K']-b['Tc_K'])/b['Tc_K']})
gas=byid['gasdwarf_1pct'];ideal=byid['gasdwarf_1pct_ideal_gas'];hy=byid['hycean_rigby'];st=byid['steam50']
gas_change=(ideal['radius_RE']-gas['radius_RE'])/gas['radius_RE'];maxchange=max(abs(s['relative_radius_change']) for s in stability)
summary={'source_commit':plan['source_commit'],'plan':plan,'display_cases':cases,'runs':runs,'checks':checks,'stability':stability,'max_relative_radius_change_joint_refinement':maxchange,'gas_option_relative_R_change':gas_change,'table_bounding_boxes':table_ranges,'accepted_table_box_outliers_total':sum(len(r['accepted_table_box_outliers']) for r in runs),'physical_flags_count':sum(bool(r['physical_flags']) for r in runs),'initial_guess_diagnostic':'The ave_rho_hydro=3 config did not change the used global initial density: main.cpp line250 declares a local ave_rho inside try, shadowing the global used by mode0 at line405. This is NOT counted as an effective sensitivity test. No source fix applied.','plot_environment':{'Python':platform.python_version(),'NumPy':np.__version__,'Matplotlib':matplotlib.__version__}}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['id','mass_ME','f_Fe','f_silicate','f_water','f_HHe','T0_K','P0_bar','status','R_RE','Pc_GPa','Tc_K','R_core_RE','R_rock_RE','R_water_RE','solver_seconds','warnings','HHB_P_bar','HHB_T_K','accepted_table_box_outliers','physical_flags'])
    for r in runs:w.writerow([r['id'],r['mass_ME'],*r['fractions_Fe_Si_water_gas'],r['T0_K'],r['P0_bar'],r['status'],r['radius_RE'],r['Pc_GPa'],r['Tc_K'],*r['interfaces_RE'][:3],r['solver_seconds'],len(r['warnings_errors']),r.get('HHB',{}).get('P_bar',''),r.get('HHB',{}).get('T_K',''),len(r['accepted_table_box_outliers']),'; '.join(r['physical_flags'])])

colors=['#65534b','#377f87','#59a9ac','#ca8241','#b74e43','#6d65a5']
english=['Dry rock','30% water','90% water','1% H/He','50% steam (0.2bar)','Hycean recipe (7.1 ME)']
plt.rcParams.update({'font.size':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'savefig.facecolor':'white'})
figdir=OUT/'figures'
fig,ax=plt.subplots(figsize=(8.4,5.4),constrained_layout=True)
for i,c in enumerate(cases):
    r=byid[c['id']];ax.barh(i,r['radius_RE'],color=colors[i],height=.58)
    ax.text(r['radius_RE']+.025,i,f'{r["radius_RE"]:.4f} RE; {r["mass_ME"]:g} ME',va='center',fontsize=9)
ax.set_yticks(range(6),english);ax.invert_yaxis();ax.set_xlim(0,2.95);ax.set_xlabel('MAGRATHEA radius / Earth radius')
ax.set_title('Different literature recipes; boundary conditions differ',fontsize=12)
fig.savefig(figdir/'radii.png',dpi=180);plt.close(fig)

layercolors=['#785548','#c29a5f','#2d8c9f','#a0ced8'];layernames=['Iron','Silicate','Water','H/He']
for kind in ('mass','radial'):
    fig,ax=plt.subplots(figsize=(8.4,5.4),constrained_layout=True)
    for i,c in enumerate(cases):
        r=byid[c['id']]
        values=r['fractions_Fe_Si_water_gas'] if kind=='mass' else np.diff([0]+r['interfaces_RE']).tolist()
        left=0.
        for j,v in enumerate(values):
            ax.barh(i,v,left=left,color=layercolors[j],height=.6,label=layernames[j] if i==0 else None);left+=v
    ax.set_yticks(range(6),english);ax.invert_yaxis();ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1.0),frameon=False,fontsize=9)
    ax.set_xlabel('Layer mass / total mass' if kind=='mass' else 'Radial layer thickness / Earth radius')
    ax.set_xlim(0,1.03 if kind=='mass' else max(byid[c['id']]['radius_RE'] for c in cases)*1.1)
    ax.set_title('Mass fractions' if kind=='mass' else 'Same layer masses mapped into radial thickness',fontsize=12,pad=36)
    fig.savefig(figdir/f'layers_{kind}.png',dpi=180);fig.savefig(figdir/f'layers_{kind}.pdf');plt.close(fig)
panels=[('radius_mass',3,1,'Enclosed mass / total mass','Radius / Earth radius',False,False),('pressure_radius',1,2,'Radius / Earth radius','Pressure / GPa',False,True),('temperature_pressure',2,5,'Pressure / GPa','Temperature / K',True,True),('density_pressure',2,4,'Pressure / GPa','Density / (g cm$^{-3}$)',True,True)]
def draw(ax,panel):
    name,x,y,xlabel,ylabel,xlog,ylog=panel
    for i,c in enumerate(cases):
        a=arrays[c['id']];xx=a[:,x]/c['mass_ME'] if name=='radius_mass' else a[:,x]
        ax.plot(xx,a[:,y],color=colors[i],label=english[i],lw=1.6)
    if xlog:ax.set_xscale('log')
    if ylog:ax.set_yscale('log')
    ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.legend(fontsize=8,frameon=False)
combined,axes=plt.subplots(2,2,figsize=(11.5,9),constrained_layout=True)
for ax,p in zip(axes.flat,panels):
    draw(ax,p)
    fig,sax=plt.subplots(figsize=(8,5),constrained_layout=True);draw(sax,p);fig.savefig(figdir/(p[0]+'.png'),dpi=180);plt.close(fig)
combined.savefig(figdir/'profiles.png',dpi=180);combined.savefig(figdir/'profiles.pdf');plt.close(combined)
fig,ax=plt.subplots(figsize=(7.5,4.7),constrained_layout=True)
ax.axhspan(273,400,color='#d9ece1',alpha=.7,label='Paper-adopted 273-400 K range')
ax.scatter([270],[399],marker='*',s=160,color='#555555',label='HyRIS published example')
ax.scatter([hy['HHB']['P_bar']],[hy['HHB']['T_K']],s=65,color=colors[-1],label='MAGRATHEA mapped recipe')
ax.set_xlim(230,350);ax.set_ylim(380,435);ax.set_xlabel('H/He-water interface pressure / bar');ax.set_ylabel('Interface temperature / K');ax.legend(frameon=False,fontsize=9)
fig.savefig(figdir/'hycean_boundary.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.5,4.7),constrained_layout=True)
for key,label,color in [('steam50','Original0.05bar: flagged outer root','#b74e43'),('steam50_P0_0p2bar','Alternative0.2bar boundary','#216d70')]:
    a=arrays[key];outer=a[:,2]<.001;ax.loglog(a[outer,2]*1e4,a[outer,4],label=label,color=color,lw=2)
ax.set_xlabel('Pressure / bar');ax.set_ylabel('Density / (g cm$^{-3}$)');ax.legend(frameon=False,fontsize=9)
ax.set_title('Steam low-pressure diagnostic; boundaries differ',fontsize=11)
fig.savefig(figdir/'steam_branch_diagnostic.png',dpi=180);plt.close(fig)

bon='https://arxiv.org/html/2311.12577v2#S5.SS2';rig='https://academic.oup.com/mnras/article/529/1/409/7617367'
ledger=f'''# 文献参数与映射 / Literature inputs and mapping

## Bonfanti et al. (2024), §5.2, Fig.5, Table5
**中** 原文给出 TOI-732 c 的 M=8.04(+0.50/-0.48) M⊕、R=2.39(+0.10/-0.11) R⊕、Teq=359±10 K；讨论 1% 质量 H/He 与 50:50 水岩两种解释。Fig.5 的 Earth-like 定义为32.5%铁、67.5%硅酸盐，气体曲线用Teq360 K，蒸汽曲线用Teq400 K。

**EN** Table5 supplies M=8.04(+0.50/-0.48) ME, R=2.39(+0.10/-0.11) RE, Teq359±10 K. Section5.2 discusses 1% H/He and a50:50 water-rock interpretation. Figure5 defines Earth-like rock as32.5%Fe/67.5%silicate; its gas and steam reference curves use Teq360 and400 K.

Source: {bon}

**中 · 本次假设** 取8.04M⊕，将曲线的Teq映射为外边界T0，并选P0=0.05bar；这是用于比较的代理设置，未复现BICEPS、Aguichine大气与演化模型，不能将所得半径当成原文曲线的精确重现。

**EN · Experiment assumption** We map Teq to boundary T0 and choose P0=0.05bar at8.04ME. This proxy does not reproduce the original BICEPS or Aguichine atmospheric/evolutionary models.

## Rigby & Madhusudhan (2024), §2.4/Fig.5; §3.2.3/Fig.9c
**中** 验证曲线采用30%与90%水，其余Earth-like部分为1/3铁与2/3硅酸盐，T0=300K、P0=1bar。本次在8.04M⊕评估。Fig.9c具体配方为M7.10M⊕、80%水、0.0132%H/He、剩余Earth-like、T0297K、P00.05bar；其HyRIS结果为R2.41R⊕、水气界面399K/270bar。本次只移植这些输入，EOS和热关系采用MAGRATHEA。

**EN** The validation curves use30%/90%water, remaining rock1/3Fe+2/3silicate,300K and1bar; we evaluate them at8.04ME. The Fig.9c recipe is7.10ME,80%water,0.0132%H/He,remaining Earth-like,T0297K,P00.05bar; its HyRIS outputs are2.41RE and399K/270bar at the interface. Inputs are mapped into MAGRATHEA with different EOS/thermal relations.

Source: {rig}

## 代码与诊断 / Code and diagnostics
**中** HHe_tabulated在低于100bar使用摩尔质量3g/mol的等温理想气体，深处使用Y0.275的Chabrier/Debras2021表，与HyRIS的Chabrier2019实现不相同。gas_default对照同时改变气体密度和热处理，不能仅归因密度。真实混合H₂O–H/He包层未实现。表格边界检查只针对保存点和矩形范围，不等于完整EOS有效域验证。

**EN** HHe_tabulated uses a3g/mol isothermal ideal gas below100bar and aY0.275 Chabrier/Debras2021 table deeper down. The gas_default comparison changes both density and thermal handling. Mixed H2O-H/He envelopes are not implemented here. Saved-point table-box checks are necessary checks, not full EOS-domain validation.

**中** 初猜配置诊断发现main.cpp:250在try块内重新声明局部ave_rho，遮蔽mode0实际使用的全局ave_rho；改ave_rho_hydro配置无效，未计作有效初猜敏感性实验。本次未修源码。文献查询为定向查参数，未开启探索/假设验证循环，未写回Zotero。

**EN** main.cpp:250 declares a local ave_rho inside try, shadowing the global used by mode0. The config initial-density probe was ineffective and is excluded from sensitivity evidence. No source fix, Zotero write, or autonomous exploration loop was performed.
'''
ledger+='\n## 蒸汽补充诊断 / Additional steam diagnostic\n\n**中** 原0.05bar蒸汽配方虽status0，但表面密度0.44762g/cm3与蒸汽支不符。独立调用同一EOS，在400K/0.05bar下，未知初猜返回高根0.44762，而气体初猜返回低根2.70668e-5；两根均满足压强方程，说明求根收敛不等于选对相支。主表改展示补做的0.2bar代理边界，避开P<0.1bar的vdW分支；这是物理边界变更，不是原0.05bar结果的等价修复。新案例无日志警告，原结果完整保留并标记。\n\n**EN** The original0.05bar steam run returned status0 but selected a dense surface root. Direct EOS calls at400K/0.05bar yield0.44762g/cm3 from an unknown guess and2.70668e-5 from a gas-like guess; both satisfy pressure. The main table uses an additional0.2bar boundary case to avoid the low-pressure vdW branch. This changes the physical boundary and is not an equivalent numerical repair. Original flagged runs are retained.\n'
(OUT/'sources.md').write_text(ledger,encoding='utf-8')

table=''.join(f'<tr><td>{c["label"]}</td><td>{c["mass_ME"]:g}</td><td>{c["water_fraction"]*100:g}%</td><td>{c["gas_fraction"]*100:g}%</td><td>{c["T0_K"]:g}</td><td>{c["P0_bar"]:g}</td><td>{byid[c["id"]]["radius_RE"]:.5f}</td><td>0'+(' · 警告见下' if c['id']=='steam50' else '')+'</td></tr>' for c in cases)
stabletable=''.join(f'<tr><td>{next(c["label"] for c in cases if c["id"]==s["id"])}</td><td>{s["relative_radius_change"]:.3e}</td><td>{s["relative_Pc_change"]:.3e}</td><td>{s["relative_Tc_change"]:.3e}</td></tr>' for s in stability)
def image(name,caption):return f'<figure class="report-figure"><a href="../assets/literature-cases-20261018/{name}.png"><img src="../assets/literature-cases-20261018/{name}.png" alt="{caption}" loading="lazy"></a><figcaption>{caption} 点击查看大图。</figcaption></figure>'
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>文献中的亚海王星配方 · 实测对照</title><link rel="stylesheet" href="../assets/style.css?v=20261018"></head><body><main><nav class="course-nav"><a href="../index.html">课程目录</a><a href="capstone-20261018.html">上一组类地球实践</a></nav><p class="meta">2026-10-18 · Ubuntu / MAGRATHEA · 文献参数移植</p><h1>六种构成，跑出来有什么不同？</h1><p class="lead">六组主案例及六组联合容限加严对照都返回状态0。另完成气体模型对照，并记录了蒸汽试算警告和一处配置变量遮蔽问题。</p><p class="note">这些是文献配方在 MAGRATHEA 中的前向计算。蒸汽与气体案例把文献Teq当作T0代理；Hycean案例虽移植具体输入，也没有复现HyRIS的全部物性。不能据此认定哪种结构就是TOI-732 c的真实组成。</p><h2>01 · 参数从哪来？</h2><p><a href="{bon}">Bonfanti等（2024）§5.2、Fig.5</a>提供1%H/He和50:50水岩两类解释；取其8.04M⊕质量，在本次计算中选择T0=360/400K、P0=0.05bar。Teq与T0的这一映射是我们的假设，文献的辐射/演化模型没有随之移植。</p><p><a href="{rig}">Rigby & Madhusudhan（2024）§2.4、Fig.5</a>给出30%和90%水的参照配方，300K、1bar；§3.2.3的具体Hycean案例用7.10M⊕、80%水、0.0132%H/He、297K、0.05bar。百分数都是总质量分数，0.0132%=0.000132，不是0.0132。</p><p>前三组共用1/3铁、2/3硅酸盐的岩石比例；Bonfanti两组岩石部分用32.5%铁、67.5%硅酸盐。所有界面Tgap=0。水用water_default，含H/He的主案例用HHe_tabulated。全局等温开关仍为false。</p><details><summary>English · Source mapping</summary><p>Recipes and boundary definitions are traced to Bonfanti2024§5.2/Fig.5 and Rigby2024§2.4/§3.2.3. Only the dry,30%water and90%water cases share mass,T0,P0 and rock ratio. Teq-to-T0 mapping in the gas/steam examples is an experimental assumption. The7.10ME Hycean recipe is a separate published example.</p></details><h2>02 · 主案例结果</h2><div class="table-scroll"><table><tr><th>配方</th><th>M/M⊕</th><th>水</th><th>H/He</th><th>T0/K</th><th>P0/bar</th><th>R/R⊕</th><th>状态</th></tr>{table}</table></div><p>干燥岩石是参照组。不同模型使用不同热边界，最后一组质量也不同；不能把六组半径差都解释成仅由水或气体比例造成。文献8.04M⊕、2.39R⊕观测值可以作背景参照，但这里没有计算拟合优度、后验或组成约束。</p>{image('radii','实测半径；标签同时标明质量。不同配方的热边界见表格。')}{image('layers_mass','质量分数：极薄的氢包层在质量条上几乎看不见。')}{image('layers_radial','径向厚度：同样的层质量分配经过EOS与静力求解后，占据的半径比例不同。')}<h2>03 · 剖面展示</h2>{image('radius_mass','r–m图：横轴按各自总质量归一化；归一化不消除质量本身的物理影响。')}{image('pressure_radius','P–r图：显示不同结构的压强分布。')}{image('temperature_pressure','T–P图：蒸汽和气体路径的热结构与冷水参照差别很大。')}{image('density_pressure','ρ–P图：使用对数轴显示稀薄气层至高密度内部。')}<h2>04 · Hycean配方：为什么没直接得到论文答案？</h2><p>论文HyRIS示例给出R=2.41R⊕，界面399K/270bar。本次MAGRATHEA得到R={hy['radius_RE']:.5f}R⊕，水—气界面约{hy['HHB']['T_K']:.2f}K/{hy['HHB']['P_bar']:.2f}bar，水侧模型标签为{hy['HHB']['water_side_phase_label']}。</p><p>它的界面温度高于论文采用的400K上限，因此不满足那篇论文选定的273–400K条件。液态水模型标签与“符合本文选定条件的Hycean解”是不同判断。此例展示跨代码移植配方后应重新检查边界，而不能只沿用类型名称。</p>{image('hycean_boundary','同一文献配方的界面比较：星形是论文示例，圆点是本次计算。两点不是观测测量。')}<details><summary>English · Hycean check</summary><p>The mapped recipe yields{hy['radius_RE']:.5f}RE and an interface near{hy['HHB']['T_K']:.2f}K/{hy['HHB']['P_bar']:.2f}bar, versus the paper example2.41RE,399K/270bar. The code-selected liquid-water boundary exceeds the paper-adopted400K ceiling. This is not a reproduction of the published habitable-range result.</p></details><h2>05 · 数值稳定性和气体物性对照</h2><p>六组均同时把ode_eps_rel1从10⁻¹⁰收紧为10⁻¹¹、fit_eps_rel从10⁻⁴收紧为10⁻⁵。最大半径相对变化为{maxchange:.3e}；这是联合细化的敏感性检查，不把变化归因于某一个容限，也不是绝对误差上限。</p><div class="table-scroll"><table><tr><th>案例</th><th>ΔR/R</th><th>ΔPc/Pc</th><th>ΔTc/Tc</th></tr>{stabletable}</table></div><p>1%气层案例若把HHe_tabulated改为gas_default，半径从{gas['radius_RE']:.5f}变为{ideal['radius_RE']:.5f}R⊕，变化{gas_change*100:.2f}%。该设置同时改变气体密度与热处理，不能仅归因为密度EOS。这一物理模型差异远大于本轮容限变化。</p><p class="meta">HHe_tabulated在100bar以下沿用摩尔质量3g/mol的等温理想气体，深部采用Y=0.275的Chabrier/Debras2021表；HyRIS采用Chabrier2019。混合H₂O–H/He包层不在本次四个分层材料的实现范围内。</p><h2>06 · 警告、检查与边界</h2><p>蒸汽案例在试探中报告约196.9K的IAPWS表格越界并返回端点密度；最终保存剖面Tmin=400K。主计算和加严对照都保留这一警告。保存点的表格矩形P/T范围检查发现{summary['accepted_table_box_outliers_total']}组越界记录；这不覆盖试探过程、输出筛掉的点或解析EOS的完整有效域。</p><p>进一步尝试只改ave_rho_hydro配置时，发现main.cpp:250在try块中声明了局部ave_rho，遮蔽随后mode0使用的全局变量。因此该次初猜探测实际无效，未计作敏感性证据；源码未修。日志与配置均保留，避免将配置改变误认为模型已改变。</p><p>14次运行均记录状态和退出码，保存点通过有限性、正P/ρ/T、质量/半径排序、质量总量及表面边界检查。程序状态0与这些检查支持数值执行成功，仍不代表完整验证材料物理、辐射热结构或真实行星组成。本次未做MCMC、混合物化学或HPC计算。</p><details><summary>English · Numerical limits</summary><p>All runs returned status0 and passed saved-profile checks. Joint refinement changed radii by at most{maxchange:.3e}; this is not a certified error bound. The steam run retains an intermediate table-clamping warning. The initial-density config probe was ineffective because of a local/global variable shadow in main.cpp. No source correction was made.</p></details><h2>下载与复现</h2><p><a href="../assets/literature-cases-20261018/summary.csv">结果CSV</a> · <a href="../assets/literature-cases-20261018/profiles.pdf">剖面图PDF</a> · <a href="../assets/literature-cases-20261018/sources.md">双语参数来源与假设</a></p><p>完整配置、日志、剖面和哈希保存在D盘outputs/literature-cases-20261018。原fork科学源码未修改，沿用已验证过的临时状态日志构建。每组配置使用独立输出名，避免追加混合。</p><nav class="pager"><a href="capstone-20261018.html">← 类地球实践</a><a href="../index.html">全部课程 →</a></nav></main></body></html>'''
page=page.replace('六组主案例及六组联合容限加严对照都返回状态0。另完成气体模型对照，并记录了蒸汽试算警告和一处配置变量遮蔽问题。','共完成16次行星计算与一个单点EOS探针。主表展示六种构成及其容限对照；蒸汽采用补做的0.2bar边界，原0.05bar结果因密度分支异常仅作诊断保留。')
page=page.replace('在本次计算中选择T0=360/400K、P0=0.05bar。','气体案例取T0=360K、P0=0.05bar；蒸汽最初取400K/0.05bar，发现低压分支异常后另做400K/0.2bar对照，主表采用后者。')
page=page.replace('这不覆盖试探过程、输出筛掉的点或解析EOS的完整有效域。','这不覆盖试探过程、输出筛掉的点或解析EOS的完整有效域。')
steam_note='<p class="note"><strong>原0.05bar蒸汽结果不作为可信的构成对照。</strong>虽然status0且基本数值检查通过，表面密度却达到0.44762g/cm³。独立EOS探针在同样400K/0.05bar下，以气体初猜得到2.70668×10⁻⁵g/cm³，以未知初猜得到0.44762g/cm³；两个根都满足压强方程。原半径2.41348R⊕被标记异常，未用来讨论组成。</p><p>主表展示补跑的0.2bar蒸汽边界：R=2.38480R⊕、表面密度约1.086×10⁻⁴g/cm³，无日志警告。它避开低于0.1bar的vdW模型，但同时改变了物理边界与热路径，不能把半径差归因于单一数值错误。原0.05bar配方仍需正确的相支选择或低压气体模型后才能严谨重算。</p>'+image('steam_branch_diagnostic','原低压结果在最外侧跳到高密度支；0.2bar是另一个物理边界的对照。')+'<p><a href="../assets/literature-cases-20261018/vdw-root-probe.log">查看同一P、T下的EOS多根探针</a></p>'
page=page.replace('<p>进一步尝试只改ave_rho_hydro配置时，',steam_note+'<p>进一步尝试只改ave_rho_hydro配置时，')
page=page.replace('14次运行均记录状态和退出码，','16次运行均记录状态和退出码，')
page=page.replace('这些检查支持数值执行成功，仍不代表完整验证','这些检查支持数值执行成功，原低压蒸汽异常也说明它们不足以验证物理分支；仍不代表完整验证')
page=page.replace('The steam run retains an intermediate table-clamping warning.','The original0.05bar steam run also selects a dense vdW surface root and is excluded from the composition comparison. The table uses an additional0.2bar boundary scenario, which changes the physical problem.')
(OUT/'course-report.html').write_text(page,encoding='utf-8')
md='# 文献构成计算 / Literature recipe calculations\n\n**中** 六组主案例及其联合容限加严对照均status0；不能视作原论文完整复现。\n\n**EN** Six main recipes and their joint tolerance-refinement runs returned status0; these are not full reproductions of the source models.\n\n|案例/Case|M/ME|水/Water|HHe|T0/K|P0/bar|R/RE|\n|---|---:|---:|---:|---:|---:|---:|\n'
for c in cases:md+=f'|{c["label"]}/{c["id"]}|{c["mass_ME"]}|{c["water_fraction"]}|{c["gas_fraction"]}|{c["T0_K"]}|{c["P0_bar"]}|{byid[c["id"]]["radius_RE"]:.8f}|\n'
md+=f'\n**中** 联合细化最大半径相对变化{maxchange:.3e}。Hycean配方界面{hy["HHB"]["T_K"]:.2f}K/{hy["HHB"]["P_bar"]:.2f}bar，高于文献400K条件上限。蒸汽试算警告与无效初猜配置探测见summary.json和sources.md。\n\n**EN** Maximum radius change under joint refinement is{maxchange:.3e}. The Hycean-recipe boundary is{hy["HHB"]["T_K"]:.2f}K/{hy["HHB"]["P_bar"]:.2f}bar, above the paper-adopted400K ceiling. Steam trial warnings and the ineffective config probe are retained in summary.json and sources.md.\n'
md+='\n**中** 主表蒸汽行采用补跑0.2bar边界；原0.05bar结果虽收敛，却在表面选中高密度vdW支，已标记，不作可信组成对照。直接EOS探针见logs/vdw-root-probe.log。\n\n**EN** The displayed steam case uses an additional0.2bar boundary. Original0.05bar runs converged to a dense surface vdW root and are flagged/excluded from the composition comparison; see the direct EOS probe log.\n'
(OUT/'README.md').write_text(md,encoding='utf-8')
print(json.dumps({'runs':len(runs),'all_status0':all(r['status']==0 for r in runs),'checks_passed':sum(sum(v.values()) for v in checks.values()),'max_relative_R_change':maxchange,'gas_option_delta_R':gas_change,'HHB':hy['HHB'],'accepted_table_box_outliers':summary['accepted_table_box_outliers_total'],'radii':{c['id']:byid[c['id']]['radius_RE'] for c in cases}},ensure_ascii=False,indent=2))
