# TP假设受控比较 / Controlled TP-assumption comparison

## 先看结论 / Findings first

**中**：在本次固定参数、常数不透明度的灰大气实验中，强制提前接入绝热段会显著提高深层温度。这个结果量化的是**两种假设之间的差异**，不是以某个剖面为真值测得的物理误差，也不是组成后验偏差。

**EN**: In this fixed-input, constant-opacity semi-grey experiment, imposing an adiabat at a shallower pressure substantially raises deep temperatures. These are differences between assumptions, not errors against physical ground truth or measured composition-inference biases.

## 优先阅读 / Reading order

1. 本报告 / this report.
2. tp_comparison.png 或矢量 tp_comparison.pdf / profile comparison figure.
3. comparison.csv / all54 evaluations;18 parameter combinations at3 resolutions.
4. results.json / numerical checks, diagnostics and plotted data.
5. manifest.json / source, input hashes, dependencies and scope.

## 基准结果 / Baseline results

Teq=350 K，Tint=25 K，g=10 m/s²，gamma=0.1，mu=2.3，kappa_IR=10^-1.5 cm²/g。所有结果取721层；比较终点1000 bar。厚度在各自接点至1000 bar的相同区间上计算，不能直接跨行当作同一个区间比较。

| 接点 / join [bar] | 参考 T(1000bar) [K] | 强制绝热 T [K] | 温度差 / difference | 理想气体厚度差 [km] |
|---|---|---|---|---|
| 1 | 550.4 | 3840.8 | 597.8% | 2840.8 |
| 10 | 550.4 | 1998.5 | 263.1% | 952.7 |
| 100 | 550.4 | 1037.7 | 88.5% | 182.0 |

**中**：表中厚度采用恒定g、恒定mu的理想气体静水平衡积分。它不是完整行星半径，更不能换算为H/He包层质量或水质量分数偏差。所有参数组合的深层温度差约为38.1%至597.8%。最大强制绝热温度达4744 K，此时固定双原子比热、固定组成和理想气体近似尤其不可靠；极端结果只能说明外推敏感性。

**EN**: Thickness uses an ideal-gas hydrostatic integral at constant g and mu. It is not a full planetary radius or an envelope/water mass-fraction bias. Deep-temperature differences span about 38.1–597.8% across this chosen parameter set. The highest imposed temperature is 4744 K, where constant diatomic heat capacity, fixed composition and ideal-gas assumptions are particularly questionable. Extreme values indicate extrapolation sensitivity only.

## 本次实际算了什么 / Executed scope

**中**：Tint=25/50 K、gamma=0.03/0.1/0.3、接点=1/10/100 bar，共18组参数。每组用181/361/721层全压力网格，合计54次解析计算。积分时单独插入精确接点；高层保留同一辐射剖面。Teq350K和g10只是测试值，没有指定目标行星或用观测拟合。计算阶段约0.011秒，不包括Python启动、编码、审核及报告时间。

**EN**: Eighteen parameter combinations (two Tint values, three gamma values, three joins) were evaluated on three full pressure grids:54 analytic evaluations. Exact joins are inserted for integration, with the upper reference profile preserved. Teq350K and g10 are test values, not a fitted planet. Numerical compute time was about 0.011s, excluding startup, coding, review and reporting.

## 方程与来源 / Equations and provenance

1. Guillot (2010), Eq49, DOI 10.1051/0004-6361/200913396: https://arxiv.org/html/1006.4702v1 。全球平均T^4灰大气解析解；Teq采用该文Eq2定义，不用Tirr代替。论文§5.2明确说明这是纯辐射解，存在对流时会偏离该解。
2. 光学深度 / optical depth: tau=kappa_IR*P/g；kappa(cm²/g)乘0.1到m²/kg，bar乘1e5到Pa。
3. 强制绝热 / imposed adiabat: T=Ta*(P/Pa)^(2/7)。这是恒定双原子理想气体假设，不是EOS提供的真实绝热梯度。
4. 厚度 / thickness: h=kB/(mu*m_u*g)*integral(T dlnP)。独立检查包括等温精确积分及绝热精确积分。
5. PICASO4.1已保存的guillot_pt剖面用于实现交叉检查；该方法是解析参数化，不是完整PICASO RCE。源码和参考CSV的摘要见manifest。

## 对流判据与解读 / Convection interpretation

**中**：54次评估中，参考辐射剖面的最大dlnT/dlnP为0.205131，均未超过本实验采用的2/7。因此1/10/100bar都只是人为接点，不能称为该常数不透明度模型预测的RCB。这个检查只适用于这里均匀组成、理想气体的干绝热判据；实际EOS、组成梯度、凝结及随P/T变化的不透明度都会改变判断。不能由此断言真实亚海王星没有对流。

**EN**: The maximum reference dlnT/dlnP is 0.205131, below the imposed ideal-diatomic threshold2/7. The joins are prescribed, not model-predicted RCBs. This is only a homogeneous ideal-gas dry-adiabatic check; real EOS, composition gradients, condensation and variable opacity can change stability. It does not show that real sub-Neptunes lack convection.

## 数值验证 / Numerical verification

- 9项检查通过 / nine checks passed: intrinsic-flux and SI-unit limit; deep-irradiation limit; isothermal hydrostatic integral; saved PICASO comparison; anchor continuity; adiabat slope; analytic adiabat integral; resolution sensitivity; upper-profile preservation.
- 与保存的PICASO剖面最大相对差 / maximum relative difference: 0.05377%。PICASO内部在固定光学深度网格插值，本实验直接求Eq49；差异包含这种实现差异。
- 绝热积分最大相对离散误差 / maximum relative adiabatic quadrature error: 0.00902%。
- 361→721层厚度最大相对变化 / largest thickness change: 0.00169%。这是本次网格测试，不代表所有参数域已证明收敛。

## 工作流与失败记录 / Workflow and failures

**中**：原通用脚本被测试和GPT审核拒绝；两轮修复未成功（一次超时，一次补丁重叠且仍有问题），没有把失败版本投入正式比较。为避免继续耗费模型调用，本次保留DeepSeek原始程序中与PICASO和解析极限核对通过的38行核心，通过AST选择移除失败外壳，没有改动保留函数的文本。主调度的数值测试驱动负责固定输入、组装网格和独立积分检查；该驱动不是DeepSeek新写的物理模型。核心在收窄后的明确范围内重新经独立GPT审核通过。固定输入试跑通过后才进行了54次计算。这不表示原通用工具库已修好。

**EN**: The general wrapper was rejected and two repair attempts did not succeed (one timed out; one patch set overlapped and retained defects). It was not used for the final comparison. To avoid further model calls, AST selection retained the unchanged38-line DeepSeek kernel whose equations matched PICASO and analytic limits. The orchestrator's numerical test driver supplies fixed inputs, assembles grids and checks independent integrals; it is not a newly DeepSeek-authored physical model. The scoped kernel passed a fresh independent GPT review. The failed generic API remains uncertified.

过程记录 / audit: D:/GPT/projects/Sub-Neptune/workflow/runs/tp-comparison-20261025-145209-dedb3d。

## 下一步的科学关卡 / Next scientific gate

**中**：先用随P/T/组成变化的不透明度与真实EOS的绝热梯度确定参考TP及RCB，再把热结构变化接入同一套内部结构求解与相同观测约束，才有资格量化组成推断偏差。完整RCE还需要核验恒星输入、边界条件、通量守恒和收敛；化学与淬灭反馈需单独控制变量。本次没有下载恒星数据、运行RCE、改MAGRATHEA源码或推送GitHub，也没有把结果写入Zotero。

**EN**: A reference TP/RCB with variable opacity and EOS-based adiabatic gradients is needed before coupling to the same interior solver and observational constraints to estimate composition-inference bias. Full RCE requires validated stellar inputs, boundary conditions, flux balance and convergence; chemistry/quenching require separate controlled comparisons. No stellar download, RCE run, MAGRATHEA source edit, GitHub push or Zotero write occurred.
