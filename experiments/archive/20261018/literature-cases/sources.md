# 文献参数与映射 / Literature inputs and mapping

## Bonfanti et al. (2024), §5.2, Fig.5, Table5
**中** 原文给出 TOI-732 c 的 M=8.04(+0.50/-0.48) M⊕、R=2.39(+0.10/-0.11) R⊕、Teq=359±10 K；讨论 1% 质量 H/He 与 50:50 水岩两种解释。Fig.5 的 Earth-like 定义为32.5%铁、67.5%硅酸盐，气体曲线用Teq360 K，蒸汽曲线用Teq400 K。

**EN** Table5 supplies M=8.04(+0.50/-0.48) ME, R=2.39(+0.10/-0.11) RE, Teq359±10 K. Section5.2 discusses 1% H/He and a50:50 water-rock interpretation. Figure5 defines Earth-like rock as32.5%Fe/67.5%silicate; its gas and steam reference curves use Teq360 and400 K.

Source: https://arxiv.org/html/2311.12577v2#S5.SS2

**中 · 本次假设** 取8.04M⊕，将曲线的Teq映射为外边界T0，并选P0=0.05bar；这是用于比较的代理设置，未复现BICEPS、Aguichine大气与演化模型，不能将所得半径当成原文曲线的精确重现。

**EN · Experiment assumption** We map Teq to boundary T0 and choose P0=0.05bar at8.04ME. This proxy does not reproduce the original BICEPS or Aguichine atmospheric/evolutionary models.

## Rigby & Madhusudhan (2024), §2.4/Fig.5; §3.2.3/Fig.9c
**中** 验证曲线采用30%与90%水，其余Earth-like部分为1/3铁与2/3硅酸盐，T0=300K、P0=1bar。本次在8.04M⊕评估。Fig.9c具体配方为M7.10M⊕、80%水、0.0132%H/He、剩余Earth-like、T0297K、P00.05bar；其HyRIS结果为R2.41R⊕、水气界面399K/270bar。本次只移植这些输入，EOS和热关系采用MAGRATHEA。

**EN** The validation curves use30%/90%water, remaining rock1/3Fe+2/3silicate,300K and1bar; we evaluate them at8.04ME. The Fig.9c recipe is7.10ME,80%water,0.0132%H/He,remaining Earth-like,T0297K,P00.05bar; its HyRIS outputs are2.41RE and399K/270bar at the interface. Inputs are mapped into MAGRATHEA with different EOS/thermal relations.

Source: https://academic.oup.com/mnras/article/529/1/409/7617367

## 代码与诊断 / Code and diagnostics
**中** HHe_tabulated在低于100bar使用摩尔质量3g/mol的等温理想气体，深处使用Y0.275的Chabrier/Debras2021表，与HyRIS的Chabrier2019实现不相同。gas_default对照同时改变气体密度和热处理，不能仅归因密度。真实混合H₂O–H/He包层未实现。表格边界检查只针对保存点和矩形范围，不等于完整EOS有效域验证。

**EN** HHe_tabulated uses a3g/mol isothermal ideal gas below100bar and aY0.275 Chabrier/Debras2021 table deeper down. The gas_default comparison changes both density and thermal handling. Mixed H2O-H/He envelopes are not implemented here. Saved-point table-box checks are necessary checks, not full EOS-domain validation.

**中** 初猜配置诊断发现main.cpp:250在try块内重新声明局部ave_rho，遮蔽mode0实际使用的全局ave_rho；改ave_rho_hydro配置无效，未计作有效初猜敏感性实验。本次未修源码。文献查询为定向查参数，未开启探索/假设验证循环，未写回Zotero。

**EN** main.cpp:250 declares a local ave_rho inside try, shadowing the global used by mode0. The config initial-density probe was ineffective and is excluded from sensitivity evidence. No source fix, Zotero write, or autonomous exploration loop was performed.

## 蒸汽补充诊断 / Additional steam diagnostic

**中** 原0.05bar蒸汽配方虽status0，但表面密度0.44762g/cm3与蒸汽支不符。独立调用同一EOS，在400K/0.05bar下，未知初猜返回高根0.44762，而气体初猜返回低根2.70668e-5；两根均满足压强方程，说明求根收敛不等于选对相支。主表改展示补做的0.2bar代理边界，避开P<0.1bar的vdW分支；这是物理边界变更，不是原0.05bar结果的等价修复。新案例无日志警告，原结果完整保留并标记。

**EN** The original0.05bar steam run returned status0 but selected a dense surface root. Direct EOS calls at400K/0.05bar yield0.44762g/cm3 from an unknown guess and2.70668e-5 from a gas-like guess; both satisfy pressure. The main table uses an additional0.2bar boundary case to avoid the low-pressure vdW branch. This changes the physical boundary and is not an equivalent numerical repair. Original flagged runs are retained.
