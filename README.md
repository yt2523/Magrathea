# TOI-732 c — 100 bar 热结构对照开发分支

分支：`research/100bar-control-20261112`。开发/测试远端：**https://github.com/yt2523/Magrathea**。`cid02399021/Magrathea` 是手动运行发行仓库，本分支不向其推送。旧 master/run/manual-run 和历史结果保留。

## 给接手 AI 的最短入口

1. 读 [AGENTS.md](AGENTS.md)、[短规则](docs/workflow/SHORT_RULES.md) 和本README；不要载入旧聊天或重跑历史网格。
2. 读本任务 [实验计划](research/100bar-control-20261112/RESUME_PLAN.md)、[当前状态](research/100bar-control-20261112/README.md) 和 [接口速查](research/100bar-control-20261112/INTERFACE_NOTES.md)。
3. Codex负责规格、诊断、固定验收、执行与归档；**DeepSeek编写/修复代码**；最终由未参与实现的Codex审核。调用额度每次先记账。密钥不入Git或日志。
4. 优先复用 `tests/test_pilot_eos.cpp`、`tests/test_interface_temperature.cpp`、`tests/check_pilot_model.py`。旧prescribed-TP检查器的前提不同，不能直接用来冒充本次无外部TP结果验收。

## 本分支已完成什么

沿用纯铁核＋独立水层＋气层、总质量8.04ME、示范外边界0.1bar/350K。原生 `HHe_tabulated` 在100bar以内等温，深处用真实H/He表绝热梯度。已完成旧grid14和grid20及各一次加严复算，共4次行星启动；不扫描组成、不反演、不探索30/300bar。

**限制：** 100bar是规定的试验分界，非已测对流边界。原生低压ideal mu3与深层HHe表在100bar/350K的密度相差26.341%，不能称真实相变或纯温度对照。任何数值通过都不自动成为物理认证。

结果：R14≈2.34667RE，R20≈2.51714RE，固定保存剖面与容差复算检查通过；物理接缝未解决。详见任务README及实际数据。

## 目录与运行

- `src/`、`tabulated/`：既有求解器和EOS，本任务不改物理公式/表。
- `run/`、`input/`：既有运行配置/输入；不覆盖旧结果。
- `tests/`：既有固定检查和本任务验收辅助工具。
- `research/100bar-control-20261112/`：本任务配置、接口说明、运行身份、原始日志、验收结论和接手说明。
- `workflow/`、`docs/`：开发规范与历史接口说明，均保留供协作者使用。

常规构建：`make -j2`（C++/GSL，推荐WSL）。本任务的准确命令和结果以任务README为准；**不要仅凭退出0或文件存在判成功**。新输出使用新目录。

历史开发版说明：[DEVELOPMENT_BASE_README](docs/DEVELOPMENT_BASE_README.md)。本地当前预算台账在 `.runs/project-budget-latest.json`，Git内预算仅供了解历史，接手者应明确自己的授权和实际账本。
