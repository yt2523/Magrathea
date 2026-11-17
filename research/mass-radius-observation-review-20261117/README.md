# TOI-732 c 三组质量—半径测量核查：方法差异与基准选择

核查日期 / Review date：2026-11-17（Europe/London）。对象LTT 3780 c = TOI-732 c，不能与内侧b混用。证据等级：C20/N20/B24/W26均阅读已下载PDF的相关方法、表格及结论；补核arXiv HTML、DOI元数据和NASA目录。不是重新拟合RV，也没有运行行星模型。以下“判断/derived/my assessment”明确区别于论文原结论。

## 1. 我的判断 / Assessment

**中：** Rigby2024列出的三组中，我最推荐Bonfanti2024作为本项目当前完整M/R基准：它合并两组早期RV，增加高精度MAROON-X和新的TESS/CHEOPS，并联合拟合光变与RV。但若问最新质量信息，必须纳入Weisserman2026的7.89±0.26M_E；不能只因项目旧输入是8.04就忽略它。新质量中心与B24一致，尚不足以证明任一误差条代表全部系统误差。建议当前代码保留B24完整输入组，论文必须做W26更新质量敏感性；将W26升为主输入前明确恒星尺度、半径来源与协方差，而非自动拼成一个“新联合后验”。这是我的条件性推荐，不是证明B24质量客观优于W26。[S3 §3–5; S4 §2.3,3.1,4.1–4.2/Table B.3]

**EN:** Among the three measurements discussed by Rigby2024, Bonfanti2024 is my preferred complete M/R baseline. Its combined observations and global fit justify that choice. Weisserman2026 supplies a credible, more precise updated mass and must be included as a sensitivity case. Keeping the B24 baseline preserves a coherent published pair; it does not establish that its mass is intrinsically superior. Promoting W26 requires explicit radius provenance, stellar-scale consistency and covariance treatment.

## 2. 数值对照 / Measurements

|来源 / Source|M / Earth masses|R / Earth radii|说明 / Scope|
|---|---:|---:|---|
|S1 Cloutier2020|8.60 +1.60/−1.30|2.30 +0.16/−0.15|早期HARPS/HARPS-N / Early optical RV|
|S2 Nowak2020|6.29 +0.63/−0.61|2.42 ±0.10|另一组独立早期RV分析 / Separate early analysis|
|S3 Bonfanti2024|8.04 +0.50/−0.48|2.39 +0.10/−0.11|联合更新，本文推荐完整基准 / Updated global baseline|
|S4 Weisserman2026|7.89 ±0.26|未重新给出c半径 / No new c radius tabulated|更新RV与恒星尺度 / Updated RV and stellar scale|

**中：** S5 Rigby2024 §3.2.3确实列出前三组，并在其后计算/Fig6采用C20。这是她选择的基准，不能解释为她证明C20比更新数据更可靠。Bonfanti在2023年上传预印本、2024年刊出，因此“B23/B24”通常是同一研究，非第四次独立测量。W26主组成样本针对b，虽联合拟合系统并报告c质量，但没有新发布的c半径；不能把b的1.31R_E误当c。[S5 §3.2.3; S3 title/DOI; S4 §2.3,Table A.2/B.3]

**EN:** Rigby lists the first three estimates and adopts C20 for subsequent calculations, without establishing its superiority. B23 and B24 refer to the preprint and journal versions of one study. W26 fits c’s RV signal but does not tabulate a new c radius; its b-radius results must not be assigned to c.

## 3. 物理上实际测了什么？ / What is measured?

**中：** 忽略M_p相对M_star的微小修正，RV给出 M_p∝K P^(1/3) M_star^(2/3) sqrt(1−e²)/sin i；凌星给出R_p=(R_p/R_star)R_star，近似深度∝(R_p/R_star)²，但还受临边昏暗、冲击参数和污染光影响。这些是由标准Kepler/RV和凌星关系得到的解释。不是天体真实质量在几年内变化，而是数据及推断模型改变。

**EN:** RV inference scales approximately as M_p∝K P^(1/3) M_star^(2/3) sqrt(1−e²)/sin i, while R_p=kR_star. Transit geometry, limb darkening and dilution affect k. Differences describe inference from different observations/models, not physical mass evolution over a few years. These relations explain possible dependencies; they do not identify a unique causal contribution without controlled refits.

**中（derived）：** C20与N20恒星质量分别0.401和0.379M_sun，单独重标定只给行星质量约3.83%的差，而其行星质量中心相差36.7%。故恒星质量不能单独解释早期分歧，RV振幅估计/采样/噪声/偏心率处理必须一起看。不能由此断言某台仪器有已证实偏差。[S1 Table1/§IV; S2 Table2/§5; derived-checks.json]

**EN (derived):** The early stellar-mass scales account for only a 3.83% planet-mass scaling, versus a 36.7% difference between reported central planet masses. RV inference must therefore contribute substantially. No instrument-specific bias is established by this calculation.

## 4. 三篇原论文的方法 / Methods of the original studies

### S1 — Cloutier2020

**中：** 63条HARPS/HARPS-N RV（33+30）；TESS sector9，凌星仅覆盖早期短窗口。主分析先拟合TESS再用周期/历元约束RV；光变SHO GP，RV准周期GP+各仪器jitter，c偏心率自由并有先验。另用EXOFASTv2做联合拟合/白噪声RV对照，关键行星参数大体一致。K_c=4.44 +0.82/−0.68m/s，质量区间较宽。优势是显式比较分析方式；局限是早期数据量/采样及GP超参数约束，不能凭“大误差”认定质量高估。[S1 §III.5–6,IV.1–3,Table3/6]

**EN:** C20 uses 63 optical RVs and early TESS observations. The fiducial sequential transit/RV analysis includes activity GPs; an alternative global EXOFASTv2 analysis provides a useful robustness comparison. The broad K uncertainty limits mass precision. A high central value is not evidence of bias by itself.

### S2 — Nowak2020

**中：** CARMENES提供52条主要RV，并取得IRD/iSHELL近红外跟进；PyTransit联合拟合TESS SAP及多色地面光变/RV，对污染光和临边昏暗作显式处理。观测主要在2019末–2020初，和C20的RV集合不同。原文§5.2正文说最终RV包括CARMENES+IRD，但Fig7及TableB.1也列iSHELL/其零点；因此“最终恰好56还是64条进入后验”存在报道歧义，本核查不强行定数。其CARMENES活动指标没有轨道周期显著峰，不等于已证明所有相关噪声为零；论文的GP出现在长期测光活动分析，不要把它误说成最终RV已用同一GP。[S2 §3.4,4.3,5.1–5.2,Fig7,TableB.1]

**EN:** N20 uses a different, predominantly CARMENES RV set and a joint transit/RV fit with explicit contamination treatment. The text’s CARMENES+IRD description is not fully consistent with the iSHELL figure/parameter listing; exact fitted row membership needs the original analysis. Absence of activity-period peaks is not proof of zero correlated noise. The photometric activity GP must not be confused with an explicitly documented RV GP.

### S3 — Bonfanti2024

**中：** 合并前期RV并加MAROON-X，共165个RV数据行；MAROON-X是19次双通道观测，不是38个独立夜晚。三TESS sector和25次CHEOPS访问增加光度信息（约140次凌星为系统两星球合计，不是c单独140次）。MCMCI全局拟合；c偏心率自由；考虑污染、误差重标定、BIC选择的去趋势。CHEOPS预处理用GP，RV使用各组多项式/零点和jitter；MAROON-X分三次运行×两通道，共六组。它不是“全过程都用恒星活动GP”。K_c=4.22±0.16m/s。采样更完整、K更精确，支持主基准选择；去趋势选择仍有模型依赖。[S3 §3–5,Tables4–6/C.3]

**EN:** B24 combines old and new observations in a global fit. Its 165 RV rows include paired-channel MAROON-X observations; these are not independent nights. Additional space photometry improves transit constraints. Its RV noise treatment uses detrending/jitter, with MAROON-X run/channel subdivisions, rather than the activity GP used in C20/W26. This is a stronger observational baseline, not a systematics-free result.

## 5. 为什么不能忽略W26？ / The 2026 update

**中：** W26重新分析170个RV行：HARPS33、HARPS-N30、CARMENES52、MAROON-X19×2、NIRPS17。37张新NIRPS谱经夜合并为17条RV；22张同期HARPS不纳入，旧IRD/iSHELL也未使用。它延长时间基线并加独立近红外波段，不是“只加5条数据”。逐仪器SHO活动GP，共享部分超参数；c偏心率自由（报告<0.11），周期/历元先验来自B24。[S4 §2.3,4.1,TableB.3]

**EN:** W26 changes the data selection and activity model, and adds 17 nightly NIRPS RVs. The extension in time/wavelength provides real additional information. Much of its dataset is nevertheless reused; it is not independent confirmation of the earlier posterior.

**中（derived/判断）：** K误差从3.79%降至2.99%，M误差却从约6.1%降至3.3%；W26把M_star改为Mann经验标定的0.363±0.008M_sun，B24采用较宽的等龄线约束0.381 +0.024/−0.034。误差传播近似 σ_Mp²/Mp²≈σ_K²/K²+(2/3 σ_Mstar/Mstar)²+…，说明恒星标定显著参与精度提升。对M矮星，经验标定可能比等龄线更适合；不能认定“更窄先验一定造假”。[S3 §2/Table1; S4 §3.1/TableA.1; derived-checks.json]

**EN (derived/assessment):** The smaller mass error reflects both RV constraints and the tighter empirical stellar-mass scale. Empirical M-dwarf calibration can be an advantage. This does not by itself prove that the new uncertainty covers all model systematics.

**中（未决）：** W26正文/参数表未明确列出类似B24的MAROON-X六运行/通道零点和额外白噪声jitter；两个通道作为两组列出。这是需要核对代码/作者说明的稳健性问题，不是已证实的错误，也不构成否定新质量的理由。本轮没有做leave-one-instrument-out、GP核对照或统一先验重拟合，因此不能定量分摊“数据、恒星先验、噪声模型”各贡献多少。[S3 §4.2/TableC.3; S4 §4.1/TableB.3]

**EN (unresolved):** Run-offset and extra white-jitter handling need clarification before interpreting the full precision gain. No controlled RV refits were performed here, so these are robustness questions, not detected methodological failures.

## 6. 差异显著吗、对内部结构有多重要？ / Statistical and interior implications

**中：** 三组半径区间大量重叠，主要不是半径冲突。C20/N20质量差用独立高斯近似归一化仅约1.6；B24/N20约2.2；B24/W26约0.27。这些只作量级说明，**不是正式显著性**：误差不对称、后两者共享数据，差值方差应含−2Cov，不能把它们当独立实验。中心值不同不足以挑出“错误论文”。禁止把C20/N20/B24/W26逆方差平均为更精确的新质量。[S1–S4; own derived approximation]

**EN:** Radii overlap strongly. Independent-Gaussian difference diagnostics are only illustrative; shared data and asymmetric posteriors invalidate a formal tension interpretation. Averaging the published posteriors would double-count observations.

**中（derived）：** 按相同地球密度常数5.514估算，三组中心密度约3.90、2.45、3.25g/cm³；这不是新密度测量。rho∝M/R³意味着这些输入足以改变推断的水/气比例。观察基准的系统选择必须与“分层/混合、Tint”模型假设的差异分开，不能换一套观测就宣称混合模型更好，也不能用更容易匹配的M/R反过来选观测。[measurements.csv; S1–S3]

**EN (derived):** The central-density changes are large enough to matter for interior composition. The observation-set effect must be separated from mixing/thermal-model effects; fit quality must not determine which observation is declared reliable.

## 7. 给本项目的执行建议 / Project policy

**中：** (1) 继续明确标记B24完整M/R为当前基准，不自动改代码；(2) W26质量作为论文必须包含的更新检验，半径仍明确引用B24或统一恒星尺度重建，不能冒称W26给新R；(3) N20作为低质量端的文献系统差异情景，C20作为与Rigby复现有关的历史情景，不把多套结果当独立概率权重；(4) 每套观测分别比较分层/混合，尽量用同一观测的联合M/R后验；没有链时把独立误差近似写明，不画成已知协方差椭圆；(5) 统一R观测的波段/参考压力与结构半径。没有获取/发送作者邮件，建议后续索取RV模型细节和联合后验链，获授权后再联络。

**EN:** Retain an explicitly named B24 baseline; require a W26 mass-update test, with radius provenance and covariance caveats. Use older alternatives as systematic scenarios, not independent likelihood factors. Compare layered/mixed models under each fixed observation set. Match the observational and model-radius definitions. No configurations were changed or authors contacted.

**中：** JWST白光曲线提供按仪器/波段不同的k，并含星斑/光斑处理；这是核对半径定义的重要补充，但不能把某个更小k误差直接当全行星绝对半径更精准，因为恒星半径及污染仍参与。此处只补核公开表格，不对JWST重新做检索。[S7 Table1/§2.4]

**EN:** Wavelength-dependent JWST transit ratios and stellar-contamination treatment are relevant to radius definitions, but do not automatically produce a more precise absolute bulk radius. This cross-check did not reanalyse spectra.

## 8. 全部来源 / Sources and access

- S1 Cloutier et al.2020, AJ160:3, DOI [10.3847/1538-3881/ab91c2](https://doi.org/10.3847/1538-3881/ab91c2). Downloaded [arXiv2003.01136](https://arxiv.org/pdf/2003.01136), PDF header May14,2020,31pages. Full relevant methods/tables read; publisher21pp pagination differs, use section/Table6 identifiers.
- S2 Nowak et al.2020, A&A642:A173, DOI [10.1051/0004-6361/202037867](https://doi.org/10.1051/0004-6361/202037867). Downloaded published21pp [institutional PDF](https://orbi.uliege.be/bitstream/2268/248887/1/Nowak_2020.pdf). Publisher direct download returned403; institutional mirror used. §5.2pp8–9; TableB.1p19.
- S3 Bonfanti et al.2024, A&A682:A66, DOI [10.1051/0004-6361/202348180](https://doi.org/10.1051/0004-6361/202348180). Downloaded [arXiv2311.12577v2](https://arxiv.org/pdf/2311.12577v2),28pages; §2–5,Tables1/4/5/C.3. arXiv year2023 is not a separate study. Existing Zotero5C5WVZNW reused; its incomplete DOI metadata is not silently overwritten.
- S4 Weisserman et al.2026, A&A709:A165, DOI [10.1051/0004-6361/202558011](https://doi.org/10.1051/0004-6361/202558011). Downloaded [arXiv2604.07447](https://arxiv.org/pdf/2604.07447),24pages,headerApril10,2026; §2.3pp3–4,§3.1p5,§4p7,TableA.1p19,TableB.3p22. Reviewed PDF is a preprint; journal metadata/result cross-checked, not claiming all published-version wording identical.
- S5 Rigby & Madhusudhan2024, MNRAS529:409–424, DOI [10.1093/mnras/stae413](https://doi.org/10.1093/mnras/stae413), [§3.2.3 HTML](https://arxiv.org/html/2402.12330v1#S3.SS2.SSS3), ZoteroKPV6Z75G; starting-point citation audit, not a new measurement.
- S6 [NASA Exoplanet Archive LTT3780 multi-solution page](https://exoplanetarchive.ipac.caltech.edu/overview/LTT%203780), accessed2026-11-17. Cross-index only; default-solution selection is not a quality verdict. Not used to replace primary methods.
- S7 Rigby et al.2025, ApJL995:L70, DOI [10.3847/2041-8213/ae247d](https://doi.org/10.3847/2041-8213/ae247d); [institutional published PDF](https://orca.cardiff.ac.uk/id/eprint/183413/1/pdf.pdf), Table1, sharedZotero6A8GSVBK. Targeted published-table/abstract cross-check only, not full-paper re-review this round.

所有下载在D盘；PDF SHA-256、文件大小、DOI元数据、测量CSV、推导检查和图随报告存档。PDF表格提取有旋转文字警告，关键值以HTML/正文/表格交叉核对；不把全文提取的串栏数字直接当数据。原文无逐字长引述。报告与阅读笔记为本次核查版本，原用户笔记保留；科研进展只追加共享交接VDGBVMRW。没有行星计算/DeepSeek调用。

All downloads are on D:. Hashes, metadata, source values, derived checks and plots are retained. Text-extraction artefacts were cross-checked against tables/HTML; no long verbatim quotations are included. Existing notes are preserved; the shared handoff is updated separately. No planetary or DeepSeek calls were made.
