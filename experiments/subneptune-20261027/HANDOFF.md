# Sub-Neptune研究交接文档

更新：2026-10-27（Europe/London）。这是接续研究的状态快照，不是完整科研结论或新实验的执行记录。

## 1. 研究目标与用户偏好

核心问题：亚海王星内部组成推断对温压结构假设有多敏感，特别是等温/绝热的使用和连接位置。第一项成果优先量化热结构造成的组成推断偏移；化学剖面、平衡/淬灭等随后用作一致性或敏感性约束。当前不以行星演化为主线。

目标行星尚未锁定；TOI-732 c、K2-18 b、TOI-270 d等只是候选。现在的5及8.04 Mearth都是合成示例，不能直接贴真实行星标签。观测未来优先使用论文中的丰度区间、上限和已有反演样本，不从原始光谱处理开始。导师的C2/C3文件不可获得，勿把它们当现成输入。

用户要求简洁、省token：不要重装已可用工具、重复已完成的网格、每案例调用模型或无必要并行开Agent。数值求解在本机运行，允许云模型推理；将来可通过数据和操作文档交给学校HPC，不需先做复杂远程系统。新下载、安装、生成文件放D盘；技能D:/Codex/skills；通用交付D:/Codex/downloads；临时D:/Codex/tmp。不要输出任何API key。

用户最初倾向只改接入文件、批量运行mode0，后来明确允许必要且可回退的源码改动。优先保留mode0批跑；改变科学源码前保留基线、隔离改动、验证默认行为并给出回退方式。最新用户仅要求交接材料，完整TP接口尚未开工。

## 2. 接手先读这些文件

1. 本文档。
2. D:/GPT/projects/Sub-Neptune/outputs/thermal-composition-20261025-b01/REPORT.md
3. 同目录verification.json、independent_numeric_checks.json、delivery_state.json。
4. D:/GPT/projects/Sub-Neptune/outputs/mode0-inputs-20261025-a17b/REPORT.md
5. D:/GPT/projects/Sub-Neptune/outputs/tp-comparison-20261025-dedb3d/REPORT.md
6. D:/GPT/projects/Sub-Neptune/scripts/mode0-workbench/FOLLOWUP_PLAN.md 和 README.md。
7. D:/GPT/projects/Sub-Neptune/outputs/HANDOFF.md：包含早期背景，日期较新的状态优先；勿将历史未完成事项误认为当前仍未完成。

## 3. 已完成实验及结果

### A. 简化灰大气与绝热连接比较

输出：D:/GPT/projects/Sub-Neptune/outputs/tp-comparison-20261025-dedb3d

以Guillot 2010式49的全球平均半灰辐射曲线为参照；Teq350K、g10m/s²、kappa_IR=10^-1.5 cm²/g、mu2.3。Tint25/50K、gamma0.03/0.1/0.3、连接压力1/10/100bar，181/361/721层，共54次评价。

在连接压力下强行接T∝P^(2/7)，深层温度对连接点敏感。直接方程、单位、极限、连续性、积分和分辨率等检查完成；PICASO保存曲线对照也完成。一般TP程序外壳最初失败，已修复，12项原验收通过，全54项与先前受控实现的最大缩放差约4.44e-16。

限制：这些连接点不是算出的RCB；辐射曲线不是辐射对流平衡真值。理想气体恒重力层厚差不是行星半径或组成偏差。未使用真实行星、化学或演化，不能把简化灰模型称为更可信的现实参考。

### B. mode0外边界温度批跑

输出：D:/GPT/projects/Sub-Neptune/outputs/mode0-inputs-20261025-a17b

5及8.04 Mearth、1%气层、岩石部分核/幔=.325/.675、无水层；Ts300/360/450K、外边界.05bar、层间T跳跃0。6个组合加重复、收紧容差，共8次。质量、表面边界和剖面检查通过，重复剖面逐字节相同，--resume跳过已完成有效案例已验证。

### C. 正向温度网格与同半径气层恢复

输出：D:/GPT/projects/Sub-Neptune/outputs/thermal-composition-20261025-b01

共67次mode0：18个正向组合（2质量×3温度×3气层质量分数.003/.01/.03）、39次反演求解、6个加严容差对照、4个HHe_tabulated整套气层处方对照。

合成真值均为360K、气层质量分数1%；固定总质量、核幔比、表面压力及EOS，只在反演中改变温度和气层质量分数：

|总质量 Mearth|假定温度 K|恢复气层质量分数|相对真值1%的偏差|
|---:|---:|---:|---:|
|5|300|2.34399%|+134.40%|
|5|450|0.39385%|-60.62%|
|8.04|300|2.60665%|+160.67%|
|8.04|450|0.38042%|-61.96%|

通过实际mode0评价做对数二分搜索；半径相对残差≤2e-5。收紧ODE/拟合容差后的最大相对半径变化2.464462e-6。67份配置、剖面和stdout哈希全部核验；源码/二进制一致，实际等温段温度漂移0，深层T/P^(2/7)的最大相对漂移约9.404e-8。8项驱动/实验工具测试通过；第一次Windows夹具遇到C盘沙箱临时目录权限问题，改用D:/Codex/tmp后通过，无需改代码。

更换gas_default为HHe_tabulated时，4个对照的半径增加约5.54%–7.18%。这是整套EOS+热结构处方的差异，不能称纯EOS效应或纯TP效应。

重要限制：本轮只改变外边界温度，不是相同边界下的完整TP形状比较；也会通过连续温度影响固体层。合成恢复不是观测后验，搜索括区间不是置信区间。CLI未显式暴露内部收敛状态，仅报告独立剖面检查通过，不能将exit0当完整物理正确性证明。

## 4. 仓库、构建与运行入口

### 原学校GitHub仓库——保护现有修改

D:/GPT/projects/Sub-Neptune/Magrathea

远端：https://github.com/yt2523/Magrathea.git
分支：实验复现；研究源码基线9e74aac2ccd62cd70102ce9dda922149afcb531b。

这里有用户已有未提交文件（plot/、run/、result/等），不得reset、覆盖或清理。根目录planet二进制曾在8.04Mearth输入下输出7.9596Mearth，行为与当前源码不一致；不要用于新研究，不要覆盖它来掩盖历史。

### 已验证的求解器工作树——继续复用

Windows：D:/GPT/projects/Sub-Neptune/work/magrathea-mode0-clean-20261025-a17b
WSL：/mnt/d/GPT/projects/Sub-Neptune/work/magrathea-mode0-clean-20261025-a17b
分支：workflow/mode0-inputs-20261025；基线同上。

在这里以相同源码make -B -j2重新编译后质量正确、历史基准一致。上一轮结束时源码干净、无C++改动；新窗口先核对当前git状态，勿假设后来绝无外部变化。这是普通Git worktree，不是Codex托管worktree。执行solver时cwd必须为工作树，以便找到tabulated等相对路径。

### 外部实验工具——独立Git仓库

D:/GPT/projects/Sub-Neptune/scripts/mode0-workbench
分支：fix/tp-wrapper-mode0
已完成提交：4a54bdd（通用外壳与批跑修复）；240a641（67次比较实验工具）。

- compare_tp.py：已修复的简化灰大气/绝热外壳。
- check_tp.py：12项原验收。
- mode0_batch.py：CSV→独立cfg→mode0；超时、剖面验证、哈希、恢复。
- Run-Mode0.ps1：Windows入口；已有8案例的恢复跳过已验证。
- followup_comparisons.py：67次比较的编排；不是完整TP接口。
- verify_followup.py：不调用求解器/模型的持久化数据核查。
- report_followup.py：读取结果、生成图和报告，不运行求解器。
- review_followup.py、adjudicate_followup.py：审核和裁决记录工具。执行review脚本会产生新的模型调用，不要仅为了接手再次运行。

示例命令（了解接口，不要原样重跑已经完成的实验）：

```powershell
& 'D:/GPT/projects/Sub-Neptune/scripts/mode0-workbench/Run-Mode0.ps1' -Table '<新CSV>' -Output '<新的D盘输出目录>'
# 恢复既有批次需指定原Output和-Resume；不要覆盖结果。
```

67次实验的原始执行脚本保存在输出executed_driver.py。其原有“计算期间全部模型调用0”的元数据措辞过宽，现已纠正为数值驱动0调用、并行独立审核1调用；实际数值没有变化。不要重跑它来更新这项元数据。

## 5. 模型、环境与审核状态

本机Windows+WSL2 Ubuntu；Linux Python3.14.4、g++15.2、GSL2.8。Windows科学环境D:/GPT/projects/Sub-Neptune/tp-lab/.venv/Scripts/python.exe；有PICASO4.1及NumPy/SciPy/Matplotlib。不要假定当前日期下全局软件版本未变，执行前只需检查涉及的环境。

Cline CLI：D:/Codex/tools/cline/node_modules/@cline/cli-windows-x64/bin/cline.exe
已有DeepSeek配置目录：D:/Codex/cline-home。之前deepseek-v4-pro调用成功；无需让用户把Key发到聊天。不要读取或打印凭据；VSCode插件和CLI不默认共用凭据。模型服务当前可用性需在实际需要调用时核验，不为接手消耗API请求。

当前分工（用户2026-10-27明确更新）：GPT/Codex负责研究与工程决策、独立代码审核及验收；DeepSeek负责主要编码。Codex可直接修复范围清楚的小片段；若需要大篇幅修改、重写或整体返工，应给出具体问题、修改要求和验收标准，打回DeepSeek完成，再由GPT/Codex复审。不要把允许片段修复扩大解释为Codex接管大篇幅编码。

历史执行记录：上一轮实际由Codex编写实验驱动、DeepSeek做一次独立只读审核，没有逐案例LLM调用。此历史不作为后续默认分工；之后按上述更新执行。Codex自行修复的片段仍需运行相应验证，自审不能替代独立审核；需要独立复核时使用未参与该修改的审核实例。

最新审核原始verdict为false，回复还多了一个闭合花括号。七条问题经Codex逐条对照源码裁决为不成立或已明确的限制；原始意见和裁决均保存，不能伪称DeepSeek原始审核通过。见输出independent-review.json、review-adjudication.json、review.events.jsonl。数值验收独立于模型意见完成。

## 6. 下一步——已讨论的方向，尚未实现

研究目标从“边界温度变化”推进到“相同外边界、相同密度EOS和组成下，仅TP形状变化”。先小规模验证，再做组成恢复；不马上扩大网格或叠加化学自由度。

首要只读核查：
- src/main.cpp如何读mode0输入、构造层和边界。
- src/phase.cpp的find_phase_gas_default、find_phase_HHe_tabulated。
- src/EOSlist.cpp的Gas、Gas_iso、Gas_hhe。
- src/EOS.cpp及hydro.cpp中T(P)、密度求解、dT/dm和双向积分/拟合的路径。

关键已知混杂：gas_default在100bar（代码P<1e8，内部压力单位为cgs dyn/cm²）两侧从Gas_iso切换Gas；mmol从3变2，同时由等温切为绝热。HHe_tabulated低压同样使用Gas_iso，高压换成Chabrier表。因此单独移动相界会同时改变分子量/EOS，不能当纯热实验。

没有现成完整TP文件输入入口的证据；此前源码检查未找到。新窗口应确认是否有后续改动，不能直接宣称已接通。若需修改，做可选且默认关闭的最小接口，隔离源码并保留回退。验证输入压力/温度单位、排序、重复、插值、覆盖范围、越界策略；输出实际T(P)必须与给定曲线一致。不能仅改dT/dm而让密度仍用另一个温度，也不能仅覆盖最终输出温度。

验收顺序：
1. 默认路径保持既有基准结果。
2. 指定TP在独立可解析/可复现情况下正确进入求解并保持质量/压力边界。
3. 同一EOS/分子量处理下，固定外边界，比较等温接绝热与升温更缓的指定曲线；指定曲线先标为敏感性对照，不称自洽或真实。
4. 小网格检查插值分辨率、ODE容差、气层底部覆盖和异常处理。
5. 再做合成半径→不同TP恢复气层质量，报告偏移与适用范围。
6. 从有明确配置的文献/自洽大气计算获得外部参照后，再讨论现实可信度与化学一致性。

需留心：修改指定TP后，不能同时强制原来的绝热热方程；HHe表的P/T范围和热力学假设要核验；质量分数变化会改变气层底压，不应静默外推超出TP覆盖范围。单个半径匹配不能证明组成可辨识或化学打破简并。

## 7. 文献背景与存储

旧文献资料D:/workbuddy/LR-workspace；项目根D:/GPT/projects/Sub-Neptune。按当前可用技能目录加载D:/Codex/skills/LR-assistant/SKILL.md，不要误用名称带detached的历史快照，也不要假设旧Skill路径和配置仍有效。Zotero已存在既有文献，但本轮没有写Zotero；先查项目profile和相关笔记，再按实际需要只读检索。Rigby2024（arXiv2409.03683）和Guillot2010（arXiv1006.4702、DOI10.1051/0004-6361/200913396）是此前背景；具体图、方程和运行配置应回原文核验。文献笔记中的AI推测不当作事实。

历史Huang2022图4无气层双层基准已复现并曾推送；不能因此声称完整亚海王星模型复现。最近两轮输出和工具提交仅保存在本地，未推送。完整后续实验尚未授权在本次交接中启动。

## 8. 防止重复工作的接手规则

- 先读报告与Git状态，不重做安装、认证、下载、已完成67次网格或54项灰大气比较。
- 不调用旧主仓库planet；不清理原仓库已有改动。
- 不把Ts实验写成完整TP实验，不把合成案例贴成真实行星，不把收敛检查写成物理真值。
- 无需新建多Agent体系；沿用现有工具。发生真正的不确定性时，追加能区分原因的小对照。
- 接手先简短说明“已完成什么、尚缺什么、最小下一步是什么”，之后根据新窗口的用户指令推进。
