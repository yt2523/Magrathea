# TOI-732 c：有水与无水组成约束（进行中）

开发分支research/composition-constraints-20261112，仅发布yt2523/Magrathea。DeepSeek编程，Codex定义检查/执行，独立Codex验收；cid02399021手动仓库及master/run本轮不变。

- 已通过：[AQUA来源/接缝与两种无水代表](research/composition-constraints-20261112/README.md)。用户已选AQUA为有水主方案，旧拼接有限对照。
- 已通过：[三质量代表切片](research/composition-constraints-20261112/mass-slices/README.md)，有水/无水岩石/无水铁端元都保留。
- 已通过：[外部TP初始化修复](research/composition-constraints-20261112/stageB/README.md)，最终版已合入根src；零根、反向斜率、无效屏障和极小区间回归全部通过。

截至2026-11-13，29次行星启动。用户取消本次任务的DeepSeek调用次数上限，仍逐次记账，不代表无限购买。质量向量生成器已生成96个唯一组成配置，尚未启动此网格；扫描执行器正在用明确标记的假求解器验收。检查通过后继续有水、无水岩石和无水铁端元的组成扫描与图。已有三质量图仅为固定组成敏感性，不是组成后验。[长程计划](docs/superpowers/plans/2026-11-12-composition-constraints-long-task.md)保留180次行星启动规划。

示范350K/.1bar/100bar热分界不等于正式TOI-732c气候模型，physical_acceptance=false。水AQUA比较使用验证公用轴的逐行子表；仓库原表不改。构建用make -B，新输出路径；原生exit0不代表有解。已有[统一HHe里程碑](research/unified-hhe-100bar-20261112/README.md)封存。
