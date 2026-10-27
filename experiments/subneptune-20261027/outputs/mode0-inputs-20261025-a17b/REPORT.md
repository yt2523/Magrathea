# 程序修复与 mode0 输入批跑报告

## 已完成

1. **通用 TP 比较外壳已修复**，不再只运行挑选出的核心。原来失败的12项验收全部通过；默认完整CLI生成54个结果，试跑配置和严格JSON输出也通过。对照上一轮受控计算，最大归一差为4.44e-16，处于浮点舍入量级。
2. 新建“CSV→独立cfg→逐次mode0”入口。两个示例质量、三种边界温度共6个组合，另加同输入重复和收紧容差，共8次，全部通过剖面及边界检查。
3. 发现并绕开现有编译产物问题：旧程序在8.04M⊕输入中只输出7.9596M⊕，少了气层质量，已被检查拦下。当前源码在隔离目录强制重编后输出恢复正确，半径1.9811274R⊕与历史基准的输出精度一致。两份源码逐字节一致，旧二进制仍保留，没有覆盖。
4. **没有修改 MAGRATHEA C++ 源码。** 新编译目录在独立分支，原仓库的未提交修改保留。用户后续允许源码修改的授权已记录；本轮不需要改算法。

## 本次计算结果

以下是示例模型，不是两个真实观测行星的拟合。质量5及8.04M⊕，均为1%气层、99%岩石部分；岩石部分核/幔质量比0.325/0.675，水层质量为0，表面压力0.05bar，界面温差为0。EOS选择固定为原配置的Fe_default、Si_default、water_default、gas_default。

| 外边界温度 [K] | 5 M⊕ 半径 [R⊕] | 8.04 M⊕ 半径 [R⊕] |
|---|---|---|
| 300 | 1.7677068 | 1.9302622 |
| 360 | 1.8259387 | 1.9811274 |
| 450 | 1.9182691 | 2.0603992 |

这是**同一组成模型的外边界温度敏感性**，不是把完整TP文件输入了求解器，也不是组成推断偏差。没有使用观测半径作反演。

## 验证

- 原TP程序12项验收通过；新增批跑4项测试通过。
- 独立DeepSeek审核了本次Codex修复的两个Python文件，通过且无待修意见；原始输出和源文件摘要已保存。
- 每次mode0都检查新输出文件、有限正P/rho/T、中心边界、表面总质量/温度/压强、质量/半径/压强顺序。每次有45秒超时，并记录配置、日志、原始剖面和哈希。
- 8.04M⊕、360K的两次剖面逐字节相同。
- 收紧ode_eps_rel1及fit_eps_rel后，半径相对变化为1.00952619e-07；这是本次观测到的稳定性诊断，不是严格误差上界或全局收敛证明。输出本身只有8位有效数字。
- 再次恢复及Windows启动器检查均跳过全部8个已完成任务，未追加重复剖面。原失败尝试也保留在独立attempt目录。
- 未修改的CLI没有暴露内部model-status字段，因此报告只标记profile_checks_passed，不把退出码0或剖面存在当作完整的物理/收敛认证。

## 怎么跑下一批

入口目录：`D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench`。

编辑一份新的CSV，每行一个模型，再运行：

```powershell
.\Run-Mode0.ps1 -Table .\你的输入表.csv
```

默认输出到新的D盘目录。所有任务都是`input_mode=0`，不需要使用其他mode。每个模型的EOS仍由明确的cfg模板选择；更换模板时必须核对单位、EOS适用区间和热结构。

同一批中断后：

```powershell
.\Run-Mode0.ps1 -Table .\你的输入表.csv -Output '原结果目录' -Resume
```

已完成且输入/二进制/源码/配置/剖面摘要匹配的任务才会跳过；未完成或失效的任务使用新的attempt目录重新运行，不覆盖先前文件。运行前不要把原目录里已知异常的旧planet当成当前可用程序。

## TP接口与科学解释边界

源码`src/main.cpp`的mode0读取层质量、表面温度与压力、温差、容差和内置EOS选择，没有完整外部TP剖面文件入口。

此外，`src/phase.cpp`在100bar切换Gas_iso/Gas；`src/EOSlist.cpp`中其第5号参数分别为3与2，`src/EOS.cpp`将该参数映射到mmol。因此直接移动该相图切换点会同时改变热梯度和气体摩尔质量/密度，不能称为纯TP效应。现阶段只是固定该默认模型、改变边界温度。后续若加入TP文件接口，应单独控制mu、EOS与热结构，并证明默认输入的回归结果保持一致。

## 回退与版本

- 原MAGRATHEA仓库和可执行文件未覆盖；没有源码补丁需要回退。
- 新工作目录：`D:\GPT\projects\Sub-Neptune\work\magrathea-mode0-clean-20261025-a17b`。
- 独立分支：`workflow/mode0-inputs-20261025`，基于9e74aac；仅做重新编译。
- 外部脚本的Git仓库：`D:\GPT\projects\Sub-Neptune\scripts\mode0-workbench`；原失败脚本已在提交81df8b4保存，修复另有提交。可用git show或revert查看/撤销，不需要reset原仓库。
- 未推送GitHub，未修改Zotero。

## 优先阅读

1. 本报告。
2. radius_vs_temperature.png及comparison.csv。
3. input_table.csv和每个case下的input.cfg。
4. verification.json及independent-review.json。
5. 每个attempt的stdout.log/profile.txt、inputs_manifest.json及旧编译产物记录。

## 精确版本记录
外部脚本基线：81df8b4；修复提交：4a54bdd。若明确要撤销本次外部脚本修复，可在其独立Git仓库执行git revert 4a54bdd；这不涉及原MAGRATHEA目录。原求解器源码未改。测试fixture的TEMP/TMP显式指向D:/Codex/tmp，避免默认Windows沙箱临时目录的写权限问题。
