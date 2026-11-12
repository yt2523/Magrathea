# TOI-732 c：有水与无水组成约束（进行中）

开发分支research/composition-constraints-20261112，仅发布yt2523/Magrathea。DeepSeek编程，Codex定义检查/执行，独立Codex验收；cid02399021手动仓库本轮不变。

当前[阶段报告与实际结果](research/composition-constraints-20261112/README.md)：AQUA水EOS来源/接缝比较与两种无水代表通过有限数值检查。10次启动含2失败、8成功，四组普通/加严；尚未完成网格和质量误差。用户已选择AQUA为有水主方案，旧拼接有限对照；无水保留Fe+硅酸盐+HHe及纯Fe+HHe。

下一步修复外部TP初始化，再接质量向量和有水/无水网格。最终交付三元图、气体比例图、质量切片图，标明条件模型/数值有效范围。详见[长程计划](docs/superpowers/plans/2026-11-12-composition-constraints-long-task.md)。全任务180次行星启动/12次DeepSeek上限，当前10次/7次。物理认证false，不把示范热边界或固定质量结果当正式行星后验。

已有[统一HHe密度100bar里程碑](research/unified-hhe-100bar-20261112/README.md)和[旧混合气体对照](research/100bar-control-20261112/README.md)保持封存，不重启。构建用make -B，输出使用全新路径；原生exit0不代表有解。
