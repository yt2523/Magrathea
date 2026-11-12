# TOI-732 c：有水与无水组成约束（进行中）

开发分支research/composition-constraints-20261112，仅发布yt2523/Magrathea。DeepSeek编程，Codex定义检查/执行，独立Codex验收；cid02399021手动仓库及master/run本轮不变。

- 已通过：[AQUA来源/接缝与两种无水代表](research/composition-constraints-20261112/README.md)。用户已选AQUA为有水主方案，旧拼接有限对照。
- 已通过：[三质量代表切片](research/composition-constraints-20261112/mass-slices/README.md)，有水/无水岩石/无水铁端元都保留。
- 候选：[外部TP初始化](research/composition-constraints-20261112/stageB/README.md)已恢复实际失败代表并通过完整接受状态检查；独立审核另发现两个漏解边界，尚未修复，**没有合入根src/hydro.cpp**。

目前24次行星启动含20份模型与4份保留失败，12次DeepSeek调用含末次截断响应（未应用）；总重置周期16/88。正在等待本任务上限12→16的选择，未自动超额调用。完整组成网格、三元/气体比例约束区及生产扫描入口尚未完成。三质量敏感性图不能叫组成后验。下一步先修复候选边界，再质量向量/扫描入口和有水无水网格；[长程计划](docs/superpowers/plans/2026-11-12-composition-constraints-long-task.md)总行星上限180。

示范350K/.1bar/100bar热分界不等于正式TOI-732c气候模型，physical_acceptance=false。水AQUA比较使用验证公用轴的逐行子表；仓库原表不改。构建用make -B，新输出路径；原生exit0不代表有解。已有[统一HHe里程碑](research/unified-hhe-100bar-20261112/README.md)封存。
