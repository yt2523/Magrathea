# 外部TP深部绝热接续：单例验收（TEST）

用户2026-11-16明确批准：新增深部接续，验证单例后停，不扫描。基线a47bb0a。代码由DeepSeek实现/修复，Codex固定检查、执行及独立验收。唯一交接Zotero VDGBVMRW。

## 结构与方程

新增tools/extend_tp.cpp为显式前处理工具，不改EOS公式、表或行星求解器默认行为。读取原CSV，用原TPProfile严格解析，在**最后原节点**接续（本例10000bar、1258.3591163K），保留原文件字节作为输出前缀，接点只出现一次。程序支持不同输入末端；第一版不支持在表内部指定接点，以免静默删除原温度节点。

下面积分同一H/He表的绝热线：x=ln(P_GPa)，dT/dx=P_GPa*dT/dP_S。原生EOS::dTdP_S输入GPa、输出K/GPa；密度及table_domain_contains输入cgs，1GPa=1e10dyn/cm²、1bar=1e6dyn/cm²。RK4每级及接受点检查P/T域、有限正密度/斜率/温度，最多200000步。原表以上仍由T-lnP插值，不增加等温段或切换理想气体。

接点T连续、相同(P,T)下HHe密度一致；**斜率允许从原表末端约0.238切到EOS约0.400，不能称斜率连续或自洽RCB**。接点由用户批准的测试假设指定，后续需要对流/通量资料才能作物理解释。输出显式TEST_CONDITIONAL_HHE_ADIABATIC_EXTENSION；建议调用者同时保存命令、原表/新表/二进制/表SHA及manifest。本目录已提供该记录。

## 实测与判决

只算同一个代表组成grid17普通/加严，加一个已成功控制grid20：总3次，未扫其余点。保留旧水EOS以同条件解释原叉，有水正式主方案AQUA不在此处替换。

- 原grid17：Fe89.91%、水9.99%、HHe0.10%，M8.04M_E；原10000bar截表下无有效括区。
- 接续到100000bar后，R=1.7151876277707623R_E；气底11171.307796bar、T1310.867474K。这是新的条件情景结果，**不证明原截表一定没有其它解**。
- 步长dlnP=.01和.005；末端T2005.56752349/2005.56873668K，相对差6.0491e-7。对两份插值函数在全部粗/细节点并集比较，最大相对温差7.22406e-6（约12523bar）；只看粗节点为2.31563e-6，末端误差不是全域最大值。两份TP原字节前缀均保持、接点一次、压力递增，数值有限正。
- 加密TP并加严ODE/拟合后R=1.7151876666389796R_E，差3.88682e-8R_E。这是组合加严证据，未独立分离各误差来源。
- 控制grid20气底低于10000bar，接续前后R完全一致=2.5470246531826537R_E。
- 三个模型均通过**原封不动**tests/check_pilot_model.py：质量、TP覆盖/温度、逐行密度/材料相态、严格表域与R/P/T拟合检查。退出0不单独算通过。普通代表14415行、加严15380行、控制13546行。密度最大相对差约6.8e-16；不把数值通过称为全面物理认证。
- 5个负例通过：nan、过大步长、Pmax<=join、超EOS域、已有输出文件；不覆盖文件，不写域错误的残缺TP。原解析器对非法CSV抛异常；工具没有捕获所有异常，不承诺所有错误都返回同一文本/退出码。输出写入使用O_EXCL防覆盖；I/O完整性另由文件回读/哈希验收。

**数值单例验收通过，随后停止。** R1.715仍不在观测半径盒[2.28,2.49]；本情景不能称该组成符合观测。未处理其它旧叉、未扫描、未宣称10000bar真实RCB，也不把PICASO探索曲线当正式交付。

## 手动使用（Linux/WSL，固定仓库）

程序依赖项目现有GSL和EOS，不调用AI。必须从仓库根运行以找到tabulated。新构建输出放D盘，输出TP文件须不存在。以下命令会重编但不运行行星：

```bash
cd /mnt/d/Codex/downloads/subneptune-research-workflow
make -B -j2
mkdir -p /mnt/d/Codex/tmp/deep-tp-build
g++ -std=c++11 -O2 -Isrc -Dmain=unused_planet_main -c src/main.cpp -o /mnt/d/Codex/tmp/deep-tp-build/native_globals.o
objs=(); for o in src/*.o; do if [[ "$o" != src/main.o ]]; then objs+=("$o"); fi; done
g++ -std=c++11 -O2 -Isrc tools/extend_tp.cpp /mnt/d/Codex/tmp/deep-tp-build/native_globals.o "${objs[@]}" -lgsl -lgslcblas -lm -o /mnt/d/Codex/tmp/deep-tp-build/extend_tp
/mnt/d/Codex/tmp/deep-tp-build/extend_tp input.csv /mnt/d/Codex/downloads/my-extended-tp.csv 100000 .01
```

原main的重命名对象只提供项目EOS依赖的全局变量，不执行行星main。此轮验证使用旧叉冻结源对应对象以严格保持旧物理处理；源码/表来源见manifest。将新CSV作为原有tp_profile_file显式传给mode0/gas_hhe_prescribed；表内surface_temp需继续匹配，不额外强制100bar等温。输出本身有P_bar,T_K头，旧节点全保留。

验收数据inputs、profile-checks.json、negative-checks.json、model-checks.json、manifest.json；原始模型和诊断侧文件无损gzip，失败证据保留前一任务目录。默认未选此工具的普通计算无变化。新窗口先看共享Zotero及统一规则，不自动重启扫描。
