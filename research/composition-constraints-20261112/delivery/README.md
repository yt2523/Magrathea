# TOI-732 c：有水与两种无水的粗组成约束交付（2026-11-13）

本轮按约停止计算。**在当前测试热结构下，有水、铁＋硅酸盐＋H/He、纯铁＋H/He 都能匹配观测质量和半径；不能据此说行星必须含水。** 这是一批真实正向模型和条件粗约束，不是正式大气模型或组成后验。

## 实际结果

中心质量8.04 M⊕下，下面都是实际原生计算，不是把R指定成观测值。数值仅作不同模型均可匹配的例子，不是唯一最优成分。

|模型|Fe质量分数|硅酸盐|H₂O|H/He|实际R/R⊕|
|---|---:|---:|---:|---:|---:|
|有水|44.8254%|0|54.7866%|0.38803%|2.3897380|
|无水，固体Fe:硅酸盐=1:2|32.4737%|64.9475%|0|2.57876%|2.3799843|
|无水纯铁端元|94.5003%|0|0|5.49966%|2.3896619|

采用Bonfanti等2024的M=8.04(+0.50/−0.48) M⊕、R=2.39(+0.10/−0.11) R⊕；质量节点7.56/8.04/8.54，半径比较区间2.28..2.49。来源DOI：[10.1051/0004-6361/202348180](https://doi.org/10.1051/0004-6361/202348180)。未获得M/R联合协方差，不把两个边缘±1σ组成的矩形说成联合68%可信区。

## 构建思路与方程

复用MAGRATHEA C++结构积分、材料选择器和EOS；DeepSeek编写三个普通Python入口，Codex定义固定验收/执行，未参与实现的Codex独立审核。运行不需要AI账号、模型API或私有workflow。

`scan_compositions.py`读质量向量与四成分分数，检查有限正质量、非负分数与和为1。各层质量m_i=f_i M，每个质量和成分组合都另算一遍，不按比例缩放已有半径。零水层写精确0，并检查实际水EOS调用为0。

原生程序正向求解dm/dr=4πr²ρ、dP/dr=−Gmρ/r²；材料EOS用同一状态(P,T)求ρ。温度沿所选热结构更新，绝热段满足dT/dP=∇ad T/P。气层同一H/He表在100bar两侧都算密度；低压等温、高压用EOS绝热线，未切理想气体。水层使用AQUA自身密度和温度梯度；水与H/He分层，没有采用混合密度近似。

测试热边界是T0=350K、P0=.1bar、规定100bar热分界；**100bar不是推导或观测得到的RCB**。当前网格不读外部TP文件，不是假装使用同学尚未正式交付的TP。外部TP接口与初始化修复仍保留，须经单例检查后另立扫描配置；不能静默替换热模型。

`execute_scan.py`预先检查所有配置；保存每次stdout/stderr、runtime、模型与独立密度复算CSV。启动前写入RUNNING和计数；成功和失败都保留指纹，续跑不自动重算；输入/程序/表/目标变化和中断均阻止无声复用。状态名STORED_STATE_CHECKED只表示保存状态检查通过。

得到真实R以后才计算ΔR=Rmodel−Robs。观测半径只用于比较和选择下一批组成点，不作为前向程序的半径边界；平均密度仅估初始半径。

## 两类边界问题怎样处理

外部TP原先把.8/1.2倍平均密度半径估计直接交求根，首个试探越TP域就失败。DeepSeek final17改为有限次数寻找可计算且异号的括区，无效试探作为屏障、保留原因，不赋假残差。零根、反斜率、无效区间与极小区间都有固定回归。旧失败代表恢复为R2.5226744277，加严2.5226743960；最终气底约7765bar，小于10000bar。短TP仍拒绝，未截断或外推TP。根src已合入；不是声称原8个历史叉都被逐一重跑修复。

新网格初始气体上限1%时，无水/富铁R仍偏小；那只是范围不够，不能当物理排除。扩到10%后包围匹配区间，再局部加密，实际找到上表的无水匹配点。

另发现富水端气体极少时R非单调。以M8.04、非气体Fe比.1为例，g=1e-7的水层外边界P=.2463bar、T350K、ρ=.0001533g/cm³；g=1e-5时P23.61bar、T350K、ρ=.9747。官方AQUA原表包围格点分别全为蒸气ID3和液体ID4，边界熵差很大；改变气体质量也改变了水层的起点熵和温度路径。因此少气体不保证小半径。这是物理机制线索，不能证明数值唯一性/稳定性或整层相态。插值保留蒸气/致密流体分组，跨组和未覆盖区域留白，不作物理排除。来源：[AQUA官方表与说明](https://github.com/mnijh/AQUA)、[Haldemann等2020](https://doi.org/10.1051/0004-6361/202038367)。

AQUA公用轴子表保留原始T≤50000K行，实际Tmax48978K，793×270；原库高温行坐标不一致的问题不被掩盖。原始表不改，隔离backend只使用确切字节子表；不是外推或编辑EOS数值。

## 质量和半径不确定性怎样进入图

蓝带：固定中心质量的模型R落在2.28..2.49。橙带：三个质量切片共同可评估域上，样本R范围与半径比较框相交；切片之间假定连续分段线性，未证明未采样极值。黑线为M8.04的R=2.39近似等值线。它们是条件兼容带，不是先验加权或后验概率。

横轴u=Fe/(1−气体)是非气体部分的铁比例，**不是总铁比例**。三元图则使用真实三质量分数。灰色表示中心质量已有插值评估但未必匹配；白色为未评估/相态跨越/覆盖不足，不表示物理排除。干燥族只覆盖u≥1/3，低铁干燥区域未扫；极低气体的水蒸气边界分支也未完整追踪。

## 验收、精度和停止点

96点粗网格、27范围点及其余局部/验证共175次扫描计算均通过独立保存状态审核：170542行、1225产物哈希、700次验证，最大密度相对误差1.36e-7；73个无水点水密度/梯度调用0，121个零硅点硅调用0。本任务连同前期诊断共204次启动、199模型、保留5份旧失败；没有删除或冒充成功。

线性粗预测在21个点最大误差.18779R⊕；旧粗点的一维PCHIP仍可达.06393，故没有直接发布成精确组成线。局部加密后，6个事前冻结的新离轨点、三个质量两种族全部通过，最大中心线误差.00311R⊕。25个验证点没有进入最终150点插值数据；其中12个区间边缘检查最大误差仍.01142R⊕。**因此中心线局部检验通过，整片面积精度未全域认证；本图不是论文最终置信区。** 原始失败和超阈值证据都保留，未改.01目标阈值。

完整无外部TP内部ODE终止码/原始拟合残差未公开；密度复算不能替代全部ODE收敛和稳定性证明。正式TP、Tint、云雾、混合包层、气候-内部一致性不在本轮认证范围。physical_acceptance=false。

## 文件与复现

[三元图](figures/ternary.png) · [气体比例图](figures/gas-fractions.png) · [质量切片图](figures/mass-slices.png)，均有同名矢量PDF。图的解释必须与上述精度/热边界限制一起使用。

[最终150点插值输入](data/final-fit.csv)；[175次全部结果摘要](data/all-new-native.csv)；独立检查及冻结预测在data与reviews。96点/27点原始字节ZIP在上级coarse-and-edges，52次后续完整产物在data/followup-campaigns.zip，各有解压后SHA。生成图的原始8CSV清单及哈希保留，验证点列表明确排除。

[手动使用指南](../../../docs/TOI732C_RUN_GUIDE.md)说明构建、单例、质量向量扫描和只读重画图。新入口在run的三个Python文件；C++主求解器及EOS仍在src。开发/审计档案不是手动运行前置依赖。仅上传yt2523开发分支，cid02399021手动仓库及master/run未动。

下一段最小工作：收到正式TP后先验证三种模型各一例；若仍用本热结构，则单独规划干燥低铁区、蒸气边界和误差较大的约束边缘，不能自动把本轮留白补成结论。此处停止，不再自动扫描/拟合。

## English handoff

Coarse conditional delivery complete. Three masses are forward-integrated; observed radius is compared only afterwards. Wet and both dry families have real native matches.175 scan/validation fits pass stored-state audit;150 enter interpolation and25 remain validation only. Six fresh local centreline tests are within.00311 Earth radii; padding-edge error reaches.01142, so no whole-area precision, posterior or physical certification. Thermal boundaries are test350K/.1bar/prescribed100bar. Phase gating uses outer-water boundary groups only. No more native computations are authorized automatically by this handoff. Follow the root README and run guide; preserve archived output bytes.

Zotero已按规则分类归档：Theoretical data/K3VH6S6R、Output data/X43W8E4D、Output graphs/UXA543K4（均为Composition constraints wet+dry —2026-11-13）。[Data顶层/代码协作索引](https://www.zotero.org/groups/6595176/items/TA6RVZGT)；三份stored附件MD5和HTML笔记回读验证见zotero-delivery.json。旧条目/笔记未改。
