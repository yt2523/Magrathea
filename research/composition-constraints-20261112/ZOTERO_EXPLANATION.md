# AQUA与有水/无水代表检查 — Data_explanation / Graph_explanation

## 中文

本阶段为条件模型比较，未完成组成网格或质量误差。固定M8.04ME、P0=.1bar、T0=350K，100bar是规定热分界而非测得RCB。DeepSeek编写诊断，Codex固定验收/执行和未参与实现的Codex审核。用户已选择AQUA为有水主方案，旧拼接有限对照，并保留两种无水模型。

同组成水模型比较：grid14默认拼接2.3688889RE→AQUA2.4251107RE；grid20 2.5427244→2.5186717RE。旧水模型1280K源拼接密度下降约19.36%/15.65%，IceX热参数缺失形成等温段，700GPa源切换再下降约9.04%。这些不是均已证实的真实物态转变。AQUA提供整套水层密度和热梯度处理，改变的不是输出曲线外观。

两种无水对照水质量严格0，气体均.001：Fe.333/Si.666/HHe.001模型R1.8759446RE；Fe.999/HHe.001端元R1.4500168RE。两点偏小不证明行星必须有水，尚未扫描更高气体比例。

10次启动含2失败、8成功；初始T10000K子表导致试探到P6815.66GPa时被拒绝，无模型、exit0不算成功。之后仅扩大到原表已有且温度轴完全一致的范围（最高48978K），不外推/改数值；仓库原表未改。八份结果8752保存状态密度重算最大相对误差7.3748e-8，4组半径加严相对差均<1e-5；严格域拒绝0，理想气体查询0，无水模型水EOS调用0。没有内部ODE状态/原始拟合残差认证。

本地原AQUA表高温坐标不一致；独立验证子表793压力段×270温度。官方PT包SHA已按LFS验证；66个相关范围比较，密度最大差.038004%，无量纲梯度最大差.479430%。官方nabla转本地K/GPa采用dT/dP=nabla*T/P_GPa。官方logP/logT插值与本地linearP/linearT区别保留；不能据此认证整个物理域。[Haldemann2020,§§2–3; officialAQUArelease]

图左是实际保存水层TP，右是代表半径；灰区[2.28,2.49]RE只是既有半径比较范围，不是组成后验，也没有质量误差。之后才接外部TP初始化、质量向量和三元/气体比例/质量切片图。

## English

This is a conditional model comparison, not a completed composition grid or mass-uncertainty analysis. M=8.04ME,P0=.1bar,T0=350K;100bar is a prescribed thermal break, not an established RCB. DeepSeek implemented the diagnostic; Codex fixed/executed acceptance and an uninvolved reviewer checked actual artifacts. The user selected AQUA as the wet main model, preserving limited stitched-EOS comparisons and both dry controls.

At identical wet compositions, radii change2.3688889→2.4251107RE and2.5427244→2.5186717RE. The default1280K Brown/Mazevet source stitch decreases density about19.36%/15.65%; thermal-code-zero IceX is isothermal and the700GPa source switch drops about9.04%. These are not all certified physical phase transitions. AQUA changes the full water density/thermal treatment. Dry Fe/silicate/HHe fractions.333/.666/.001 yieldR1.8759446RE; dryFe/HHe.999/.001 yields1.4500168RE. Water is exactlyzero in inputs and actualEOS calls; these two low-gas examples do not establish a need forwater.

Ten launches include two failedinitializations and eight saved models. The initial10000K diagnosticguard—not the earlier10000bar TPcutoff—was too restrictive for an initialization trial. Exact source rows were then retained up to48978K on common axes, with no extrapolation or value edits. Canonical tables and productionC++ remain unchanged. All8752savedstates pass density rechecks(maxrelative7.3748e-8); four tolerancepairs differ<1e-5 inradius. No internalODEstatus/rawfitresidual certification is supplied.

The local fullAQUA file has high-temperature coordinate mismatches. Verifiedsubset793×270 has commonaxes. OfficialPTarchive matches itsLFShash;66sample comparisons give density discrepancy<=.038004%,gradient<=.479430%. ConversiondT/dP=nabla*T/P_GPa and differing officiallog-coordinate versus nativelinear-coordinate interpolation are explicit. These checks corroborate units and the sampled region, not full physical validity.[Haldemann2020,§§2–3;officialrelease]

The figure shows actualsavedwaterTP and representative radii. GrayRinterval is an adoptedcomparisonrange, not a compositioncrediblearea; Munc/grid/ternary/gas/mass-slice outputs remain unfinished.

## Fixed source and data

Commit6f3732fc03f7c077d121682a047333407ea99f9d; source/data https://github.com/yt2523/Magrathea/blob/6f3732fc03f7c077d121682a047333407ea99f9d/research/composition-constraints-20261112/README.md . AQUA DOI https://doi.org/10.1051/0004-6361/202038367 ; officialrelease https://github.com/mnijh/AQUA . Newtask7DeepSeekcalls, resetepoch11/88; prior88epochretained.
