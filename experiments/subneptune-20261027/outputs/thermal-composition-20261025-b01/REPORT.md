# 温度边界与气层质量：两项比较实验

日期：2026-10-25。合成模型；不是目标行星拟合，也不是完整 T–P 曲线接入。

## 先看什么

1. 本报告的恢复表及局限。
2. `composition_recovery.png`：同半径对应的不同气层质量。
3. `forward_grid.png`、`forward.csv`：温度与气层质量的正向影响。
4. `recovery.csv`、`recovery.json`：恢复值、残差和数值括区间。
5. `verification.json`、`controls.json`、`eos_comparison.csv`、`gas_diagnostics.json`。
6. `batch-*/` 中每次独立 cfg、完整剖面、stdout、状态及哈希；`all_runs.json` 汇总。

## 实验一：固定组成比较温度

总质量为5、8.04 M⊕；气层质量分数0.3%、1%、3%；温度边界300、360、450 K，共18个组合。核占岩石部分32.5%，其余为幔；无水层、界面温差为0、外边界压力0.05 bar。使用相同 Fe_default/Si_default/gas_default。

|质量 M⊕|气层质量分数|R(300 K) R⊕|R(360 K) R⊕|R(450 K) R⊕|300→450相对半径变化|
|---:|---:|---:|---:|---:|---:|
|5|0.3%|1.7013440|1.7410737|1.8034750|+6.00%|
|5|1.0%|1.7677068|1.8259387|1.9182691|+8.52%|
|5|3.0%|1.8440225|1.9283311|2.0714410|+12.33%|
|8.04|0.3%|1.8742681|1.9094496|1.9642724|+4.80%|
|8.04|1.0%|1.9302622|1.9811274|2.0603992|+6.74%|
|8.04|3.0%|1.9890251|2.0610267|2.1863171|+9.92%|

## 实验二：相同半径，反推气层质量

各质量的合成真值设为360 K、气层1%。仅将假定温度改为300或450 K，用mode0反复求解，通过气层质量的对数二分搜索匹配真值半径；总质量、核幔比例、EOS和外边界压力保持不变。360 K使用已计算的1%作为同温度控制。

|质量 M⊕|假定温度 K|合成半径 R⊕|恢复气层质量分数|相对真值1%的偏差|半径相对残差|
|---:|---:|---:|---:|---:|---:|
|5|300|1.8259387|2.34399%|+134.40%|+9.64e-06|
|5|450|1.8259387|0.39385%|-60.62%|+6.19e-06|
|8.04|300|1.9811274|2.60665%|+160.67%|-8.48e-06|
|8.04|450|1.9811274|0.38042%|-61.96%|-1.73e-05|

括区间是搜索中有符号残差保留的数值区间，不是统计置信区间。停止条件为相对半径残差≤2×10⁻⁵；它不表示真实行星组成达到相同精度。

## 追加对照与验收

- 共67次求解，均通过剖面有限值、质量、表面温度/压力及R/M/P单调检查。CLI未显式导出内部收敛状态，不能仅凭exit 0断言内部误差全部收敛。
- 新增4项逻辑测试与原驱动4项测试均通过；独立核查全部输入/剖面/日志哈希及求解器源码和二进制一致。实际气层上层严格等温，深层T/P^(2/7)相对漂移不超过9.41×10⁻⁸，见independent_numeric_checks.json。
- 6个1%气层温度基准与此前批跑的半径逐项相同。
- 2个真值及4个恢复值收紧ODE/拟合容差，最大相对半径变化为2.46e-06，小于本轮半径匹配停止阈值。
- 18点在各固定气层比例下的半径均随温度上升；各搜索使用已检查的采样括区间。没有证明全参数域单调或唯一解。

|质量 M⊕|温度 K|gas_default R⊕|HHe_tabulated R⊕|相对变化|
|---:|---:|---:|---:|---:|
|5|360|1.8259387|1.9444567|+6.49%|
|5|450|1.9182691|2.0245600|+5.54%|
|8.04|360|1.9811274|2.1233943|+7.18%|
|8.04|450|2.0603992|2.1886638|+6.23%|

该对照更换了整套气层EOS/热结构处方；不可拆解为单独的EOS效应或纯TP效应。两者低压均沿用Gas_iso，高压分别为理想气体和Chabrier表。

## 物理假设和解释边界

- 本轮改变的是外边界温度，而非在相同边界下比较不同内部TP形状。当前mode0没有外部完整TP输入入口。本轮结果只能称为温度边界造成的合成组成恢复偏移。
- gas_default在100 bar使用固定相界，并从低压mmol=3切换到高压mmol=2，同时改变热结构。所有主比较固定这套处方，所以不把它的相界当自洽计算的RCB，也没有通过移动相界制造纯热效应。
- 理想气体、固定热容等近似在深层可能失效；气层最大P/T及实际相名保存在gas_diagnostics.json。未执行能量/辐射对流平衡或化学平衡，不能将此结果直接解释为真实H/He丰度偏差。
- 只在固定质量、固定核幔比、无水层、固定边界压力下匹配单个半径。真实观测误差、丰度约束、水/金属丰度、先验和额外组成自由度尚未纳入。改变温度边界也会通过连续温度条件影响固体层，本实验不是仅气层受热的干预。
- 下一项真正检验TP形状的实验，应保持同一外边界和密度EOS，通过可回退接口导入两套TP，再独立做组成恢复。当前结果不能替代它。

## 可追溯性与审核

本机Windows→WSL→现有mode0，串行运行；每案例无模型调用；另有一次并行进行的DeepSeek审核调用。Codex编写实验驱动；DeepSeek做一次只读审核，原始输出和逐条裁决另存，不能把其原始否决写成通过。
求解器为隔离worktree，源码基线9e74aac2ccd62cd70102ce9dda922149afcb531b；本轮未修改C++。工具来源、模板、每批源文件/二进制哈希、每个输入和剖面哈希均保存。先前错误的主仓库planet不参与本轮。

源文件依据：MAGRATHEA `src/phase.cpp` 的gas_default/HHe_tabulated选择；`src/EOSlist.cpp` 的Gas/Gas_iso定义；`src/main.cpp` 的mode0配置读取。代码基线对应 https://github.com/yt2523/Magrathea/tree/9e74aac2ccd62cd70102ce9dda922149afcb531b 。本轮未新增文献结论或声称复现具体观测行星。

## English abstract

Two controlled synthetic tests map radius against boundary temperature and gas mass, then recover gas fractions at fixed synthetic radius using an incorrect boundary temperature. These quantify conditional boundary-temperature sensitivity within one fixed atmospheric prescription, not full TP-shape bias, an observational posterior, or self-consistent radiative/chemical equilibrium. Independent tighter-tolerance runs and a whole-prescription H/He comparison delimit numerical and modelling sensitivity.
