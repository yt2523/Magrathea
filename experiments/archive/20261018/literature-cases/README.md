# 文献构成计算 / Literature recipe calculations

**中** 六组主案例及其联合容限加严对照均status0；不能视作原论文完整复现。

**EN** Six main recipes and their joint tolerance-refinement runs returned status0; these are not full reproductions of the source models.

|案例/Case|M/ME|水/Water|HHe|T0/K|P0/bar|R/RE|
|---|---:|---:|---:|---:|---:|---:|
|干燥岩石参照/rock_reference|8.04|0.0|0.0|300.0|1.0|1.71695082|
|30% 水层/water30|8.04|0.3|0.0|300.0|1.0|1.98068487|
|90% 水层/water90|8.04|0.9|0.0|300.0|1.0|2.31688144|
|岩石 + 1% H/He/gasdwarf_1pct|8.04|0.0|0.01|360.0|0.05|2.12339428|
|50%水岩蒸汽 · 0.2bar对照/steam50_P0_0p2bar|8.04|0.5|0.0|400.0|0.2|2.38479811|
|Hycean 文献参照/hycean_rigby|7.1|0.8|0.000132|297.0|0.05|2.29997931|

**中** 联合细化最大半径相对变化2.668e-06。Hycean配方界面416.86K/310.98bar，高于文献400K条件上限。蒸汽试算警告与无效初猜配置探测见summary.json和sources.md。

**EN** Maximum radius change under joint refinement is2.668e-06. The Hycean-recipe boundary is416.86K/310.98bar, above the paper-adopted400K ceiling. Steam trial warnings and the ineffective config probe are retained in summary.json and sources.md.

**中** 主表蒸汽行采用补跑0.2bar边界；原0.05bar结果虽收敛，却在表面选中高密度vdW支，已标记，不作可信组成对照。直接EOS探针见logs/vdw-root-probe.log。

**EN** The displayed steam case uses an additional0.2bar boundary. Original0.05bar runs converged to a dense surface vdW root and are flagged/excluded from the composition comparison; see the direct EOS probe log.
