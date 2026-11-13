# TOI-732 c — 有水/无水组成粗约束交付 — 2026-11-13

## 中文：Data_explanation / Graph_explanation

本组是**真实原生求解器、真实EOS，配测试热边界**，不是假结果，也不是正式TP/组成后验。350K、.1bar、规定100barHHe等温-绝热分界；统一表格H/He密度，水用AQUA，Fe/硅酸盐用原选择器。100bar不等于实测RCB。水和气体分层，不是混合包层。

M输入向量7.56/8.04/8.54M⊕，每次重新算m_i=f_iM并正向积分R，得到模型以后才比较Robs。观测M8.04(+.50/−.48)、R2.39(+.10/−.11)，来自Bonfanti2024 DOI10.1051/0004-6361/202348180。未知M/R协方差，三质量节点/矩形比较框不是后验或联合68%置信区。

中心质量的实际例子：有水Fe44.8254%/水54.7866%/HHe.38803%，R2.389738；无水Fe32.4737%/硅酸盐64.9475%/HHe2.57876%，R2.3799843；纯铁Fe94.5003%/HHe5.49966%，R2.3896619。三者都可匹配当前质量半径，故本条件模型不能说必须含水。

175次扫描/验证计算全部通过独立保存状态审核：170542行，最大密度重算相对误差1.36e-7，73个无水点水密度和梯度调用0，121个零硅点硅调用0。任务累计204次启动/199模型/保留5旧失败；原180自定规划因两点插值略超.01而补24局部计算，阈值未放宽。现已停止，不自动加密/拟合。

最后150点用于插值，25点作验证未进入拟合。六个事先冻结的新离轨点，三个质量各有水/无水各一，最大中心线误差.00311R⊕；12个边缘检查仍最大.01142，不能声称整片面积的精度或物理认证。旧粗线性误差.18779及早期PCHIP误差.06393保留，没有改成成功证据。

图：黑线中心质量R=2.39；蓝带中心质量R落在2.28..2.49；橙带是三质量共同可评估域上的样本R范围与观测框相交，假设中间质量分段连续。横轴Fe/(1−气体)不是总Fe比例。灰色为可评估域，白色未评估不等于物理排除。三元图是实际三质量分数；无水纯铁为端元线，非虚构二维面积。干燥低铁u<1/3未扫，蒸气边界分支未完整追踪。

极低HHe富水模型出现R非单调：官方AQUA四个包围格点相态诊断验证外水边界蒸气ID3与液体ID4/超临界-超离子ID5不同。以M8.04,u=.1为例，g1e-7外水P=.2463bar/T350K/ρ.0001533；g1e-5为23.61bar/T350K/ρ.9747。边界熵不同，可导致更热、更膨胀的水绝热线；这不是排除数值问题或认证整层相态。跨边界组插值留空。AQUA来源Haldemann2020 DOI10.1051/0004-6361/202038367，https://github.com/mnijh/AQUA 。

子表只保留原数据T≤50000K行，实际48978K，793×270共同坐标轴，无EOS值编辑/外推；原表不改。无TP计算内部ODE/原始拟合残差未全部公开，存储密度一致不能替代其认证。physical_acceptance=false。

代码/逐次原始结果/输入哈希/验证与解释已固定Git版本。大规模原始输出留Git ZIP；Zotero保存摘要、输入说明、图与必要验证。新入口仅三个普通Python文件，运行不需AI API；src仍是C++主程序。开发只yt2523，cid手动仓库及master/run不动。

## English

Real native forward models with real EOS under TEST thermal boundaries (350K,.1bar,prescribed100bar), not mock results or a formal atmospheric TP/posterior. Layer masses are recomputed at each of three masses, and observed radius is compared only after integration. Wet and both dry controls have actual matching examples; water is not required by this conditional M/R exercise alone.

All175 new computations pass independent stored-state checks over170542rows; maximum density relative difference1.36e-7. Final150 interpolation points are separate from25 validation points. Six fresh frozen off-track centreline predictions pass within.00311Earthradii, but padding-edge error reaches.01142; no whole-area precision, stability, full ODE, or physical certification is claimed. Earlier failed checks remain archived.

Blue denotes central-mass radius compatibility, orange the common-valid sampled-mass envelope under continuous piecewise-linear mass interpolation. Unknown joint covariance means this rectangle is not a posterior/joint68% region. Gray is assessed, white unassessed and not excluded. Outer-water vapor/dense-fluid groups prevent unsupported cross-branch interpolation; this classifies boundary cells, not the whole water profile.

Raw outputs, code, input identities and limitations are versioned below. This round is stopped at coarse conditional delivery. Do not automatically launch more grids merely because budget remains.

## Fixed source / 固定来源

https://github.com/yt2523/Magrathea/tree/b41ff6344b4a6928ac1c011ec6a54b3fb587273f/research/composition-constraints-20261112/delivery/README.md

https://github.com/yt2523/Magrathea/tree/b41ff6344b4a6928ac1c011ec6a54b3fb587273f/docs/TOI732C_RUN_GUIDE.md
