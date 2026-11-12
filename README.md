# TOI-732 c — 统一 H/He 密度、100 bar 只切热方程

开发分支：`research/unified-hhe-100bar-20261112`；远端只用 **yt2523/Magrathea**。`cid02399021/Magrathea` 保留为手动发行仓库，本任务不向它推送测试开发内容。

## 接手 AI 先读

1. `AGENTS.md`、`docs/workflow/SHORT_RULES.md`、本README和 [当前计划](research/unified-hhe-100bar-20261112/PLAN.md)。
2. [已有接口速查](research/100bar-control-20261112/INTERFACE_NOTES.md)、`docs/TP_INTERFACE_SPEC.md`、`docs/TP_ACCEPTANCE.md`。旧TP spec的fixedmu2工程夹具不是本模式的物理设定。
3. Codex负责固定测试/诊断/控制器；**DeepSeek编写及修复实现**；未参与实现的Codex审核。不要改验收标准来配合结果，不要读取旧聊天或重跑历史实验。

## 这一步只改什么

新增可选 `atm_phasedgm="gas_hhe_iso_adiabatic100"`：低压与高压都查相同Chabrier H/He密度表，100bar以内温度方程为等温，深处为原表绝热梯度。保留旧`HHe_tabulated`和所有旧选择器。新模式无外部TP，仅mode0，运行前自动严格表域审计。

低压采用独立表格实例`Gas_hhe_iso100`并设热标签0，高压沿用`Gas_hhe`热标签10；两个标签表示热结构处理，不是不同成分/真实物态。不改密度公式、EOS表、结构微分方程或水层EOS。

## 当前任务与停止点

已完成grid14、grid20及各一次加严，共4次行星启动。R约2.36889/2.54272RE，气体密度接缝消除，固定数值检查通过；物理认证仍为false。详见 [任务README](research/unified-hhe-100bar-20261112/README.md)。不跑新网格、30/300bar扫描、质量误差或反演。旧100bar混合EOS对照结果完整保留在 [上一任务](research/100bar-control-20261112/README.md)。

构建必须使用 `make -B -j2` 强制重编。复用旧`.o`时曾出现内存错误，强制全量重编后消失；不沿用陈旧对象文件。精确构建、运行命令和已验证结果会记录在任务README。新输出路径必须为空，原生打印会追加。

仍为示范边界M8.04ME、P0=.1bar、T0=350K、纯铁核/独立水层/气层。即使气体密度接缝消失，100bar仍是规定的热分界；水EOS拼接、真实对流边界和旧外部TP初始化问题不会自动解决。
