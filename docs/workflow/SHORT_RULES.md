## 2026-11-13 交付并停止计算

粗组成任务完成：204次任务启动199模型5旧失败；175新扫描模型全通过保存状态独立验收，150插值/25验证分离。6新局部中心线误差.00311R⊕，边缘.01142仍近似，physical_acceptancefalse，非后验。三个用户入口在run，使用docs/TOI732C_RUN_GUIDE.md。正式TP、蒸气边界、干燥低铁区为下一段，不能按历史条目自动开算。最新说明research/composition-constraints-20261112/delivery/README.md和HANDOFF.md。DeepSeek43次、用户取消调用上限；程序与EOS选择不能静默替换。仅yt2523开发分支，cid手动库不动。下文是历史记录。

## 2026-11-13 当前任务更新

用户取消DeepSeek本任务调用上限，保留逐次记账；勿按下文历史12/16/88上限暂停。29次行星启动，final17 TP初始化已通过限定独立验收并合入根src，固定回归重新通过。96点配置已生成但未执行；扫描器还在合成协议验收，不得声称已扫网格。开发与试验只推yt2523/Magrathea，此任务不动cid02399021手动仓库。DeepSeek继续编程，Codex独立验收。见根README与research/composition-constraints-20261112/stageB/README.md。

# Short rules / 开工前短规则

1. Do not reinstall or re-authenticate working tools; never print a key.
2. Read current state and exact relevant acceptance table; don't reread all history.
3. Existing 54/8/67 experiment sets are complete historical results; don't rerun them for packaging.
4. Old original-checkout planet had wrong total mass; build from identified source for new science, preserve that historical binary.
5. gas_default changes thermal law AND molar mass at 100 bar; no pure-thermal claim from moving that phase boundary.
6. Temperature used by density and integration must be identical; editing output T alone is invalid.
7. Exit 0 / profile existence / model approval is not full numerical or physical convergence.
8. Keep raw review verdict and adjudication separate; rejected review never becomes 'review passed' through narration.
9. One writer per run; test/review evidence belongs to exact code and contract hashes. A later edit invalidates it.
10. Scripts do arithmetic, hashing, batching and summaries. Send models narrow code + failures, no full history or per-case calls.
11. Stop with a reason and next action. Five ineffective valid repairs trigger Codex diagnosis, not an endless loop.
12. Archive each approved milestone and verify remote commit. Keep secrets/private event logs outside Git. These rules are concise index entries; original evidence lives in archived reports.


## 2026-11-02 operator budget update

The operator doubled the tracked project DeepSeek ceiling44→88; see `workflow/project-budget.json`. Historical TP implementation44/44 records describe that closed phase; they are not the current global authorization gate. This conversation’s authorized work may use DeepSeek without per-call confirmation; do not ask repeatedly about the superseded44-call ceiling. Generic per-run max_model_calls values were doubled (fallback12→24, live example6→12, offline demo12→24); that counter includes coder and reviewer logical launches, not DeepSeek-only billing. Project88 policy does not automatically aggregate independent operators/portable runs. Scientific fit ceiling20 and closed historical contracts remain unchanged; no new physics experiment is authorized by increasing API budget.


## 2026-11-07 用户报告要求：解释原理与设计

以后进展和最终报告不能只罗列“做了什么”。使用简单中文，按实际任务说明：
- 构建思路：复用了什么、增加了什么、各模块怎样连接，为什么采用这个最小设计。
- 计算原理：关键状态量、单位、必要公式，以及TP插值、物态选择、EOS密度和结构积分的关系；明确外部TP的作用范围。
- 每个问题分别说明：症状、定位证据、根因、实际代码改动、为什么有效、如何验证。
- 严格区分“已修复”“仅定位现象”“尚未解决”；不把失败点的排除/记录说成解决，也不把数值通过说成物理模型已认证。
- 最后给出结果、剩余限制和下一步最小改动。代码片段只放帮助理解的几行；统计量要解释含义。
