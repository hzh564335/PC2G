# PC2G 实验协议审计

冻结日期为 2026 年 11 月 19 日。本文按已有方案、运行回执与结果表核对研究任务、比较单位和结论边界。保留历史协议、原始结果、全部优化种子与失败记录。证据冻结仅整理归档，训练预算为零。

## 1. 实验性质及证据来源

| 实验 | 设计和评价口径 | 归档性质及论文用途 |
|---|---|---|
| C-PU、DIRG 原始监督构造 | 每库四个留出工况、五种子、八个配置。源训练最多 5,000 步，按给定有标签源验证交叉熵选择检查点。两库的析因主矩阵共 320 条，另有 80 条一致性覆盖对照和 40 条同骨架软权重对照。440 条中 176 条来自历史复用，264 条为新增。 | 既有固定研究矩阵。用于报告标签与筛选的交叉控制、条件依赖性和有限正负结果。关于结果的后续分层分析标为事后诊断，历史复用与新增回放的轨迹证据分别交代。[协议](../../output/pc2g_research_audit_20260924/protocol.json) · [完整结果](../../output/pc2g_research_audit_20260924/FINAL_REPORT.md) · [复用审计](../../output/pc2g_research_audit_20260924/reuse/REUSE_AUDIT.md) |
| PU-RS3-15-v1 记录级补验及 Paderborn 源角色扩展 | 按另一数据构建协议组织三类、15 轴承。正式补验为四目标 × 五配置 × 五种子，共 100 次。角色扩展为八个新增任务 × 四个 B 开启配置 × 五种子，共 160 次。两轮分别采用各自冻结的主比较。 | 训练前固定的正式补验。两轮均未支持 Full+B 稳定领先。应单独报告协议和结果，作为历史 C-PU 发现的适用范围证据。[正式补验分析计划](../../output/pc2g_recordsplit_preparation_20261020/分析计划_正式训练前.md) · [100 次结果](../../output/pc2g_formal100_acceptance_20261020/完整验证结果报告.md) · [160 次结果](../../output/pc2g_source_roles_20261028/完整结果与解释_20261029.md) |
| CWRU 固定 3 HP 与 HUSTbearing 固定 80 Hz 试跑 | 每库一个目标、一个有标签源、八配置 × 三种子，共 48 次。CWRU 以 0 HP 提供有标签数据，HUST 以 20 Hz 提供有标签数据。两库各用整记录分组，源验证记录数为零，固定第 5,000 步。新目标评价在全部试跑源训练及配对核验后释放。 | 有冻结执行协议的探索试跑。历史 CWRU10 和 HUST 20/40/60/80 Hz 结果在任务制定前已查看。仅用于量化这两个新任务的现象，不作独立跨库确认。[执行协议](../../output/pc2g_cross_dataset_pilot_20261117/protocol.json) · [试跑结果](../../output/pc2g_cross_dataset_pilot_20261117/PILOT_REPORT.md) · [数据分组](../../output/pc2g_cross_dataset_stage2/domain_split_report.md) |
| HUST 有标签源轮换 | 固定源集合 20/35/65 Hz、目标 80 Hz。复用 20 Hz 有标签角色的 24 个模型，35、65 Hz 有标签角色各新增 24 个，共 72 个末步检查点。每个任务继续使用八配置和种子 0–2。相同种子按物理域顺序采样，再按角色排列张量，扰动仍遵循角色槽位。 | 冻结执行方案的正式角色检查。角色切换同时改变真值来源、无标签组合及辅助分支任务，结果描述角色敏感性。[执行协议](../../output/pc2g_hust_role_rotation_20261118/protocol.json) · [配对核验](../../output/pc2g_hust_role_rotation_20261118/source_pairing_audit.json) · [结果](../../output/pc2g_hust_role_rotation_20261118/PC2G_role_rotation_final_report.md) |
| 65 Hz 错标专项诊断 | 按原始 24 份源轨迹和冻结记录清单离线对照源真值。共享辅助轨迹的两个 B 水平各自相同，汇总时每种子只计一次，并按域、真实类、原始文件与步段记录。 | 事后来源诊断。支持定位错标、区分标签与筛选效应和提出机制假设。固定集合的错误次数依然是源端统计。[65 Hz 专项](../../output/pc2g_source_diagnostic_20261118/HUST_65Hz_error_analysis.md) · [35 Hz 对照](../../output/pc2g_source_diagnostic_20261118/HUST_35Hz_comparison.md) |
| 65 Hz 四臂监督路径干预 | 固定 20 Hz 有标签、35/65 Hz 无标签、80 Hz 留出。仅切换 65 Hz 主头伪标签交叉熵和一致性直接项。复用 A 的三个模型，B、C、D 各新增三个，统一第 5,000 步。 | 本地预注册的机制对照，主对比为 B−A Accuracy，按三种子报告描述性配对差。[预注册](../../output/pc2g_hust_65hz_path_preregistration_20261119/HUST_65Hz_supervision_path_preregistration.md) · [冻结协议](../../output/pc2g_hust_65hz_path_20261119/protocol.json) · [结果](../../output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_report.md) |
| 65 Hz Oracle 纠错 | 在同一任务逐步回放 A 的入选顺序和原标签，仅在两个主分类头中把错标替换为已入选源真值。保留原分母和权重。120 步短检通过后新增三个 O 模型，每个 5,000 步。A、B 沿用原档，80 Hz 在全部源端审计后评价。 | 本地预注册的机制对照，主对比 O−A。O 额外使用源真值，结果用于说明固定集合下标签内容的净作用。[预注册](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_preregistration.md) · [完成回执](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/execution_status.json) · [结果](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_final_report.md) |

## 2. 交叉控制的比较口径

原始预测记为 p，校正预测记为 q。由各自预测类别及逐类低熵规则得到集合 Sₚ、S_q。Raw 为 p/Sₚ，Label 为 q/Sₚ，Select 为 p/S_q，Full 为 q/S_q。每种配置分别考察扰动一致性关闭和开启。Label−Raw 与 Full−Select 固定各自的候选集合，比较硬标签内容。Select−Raw 与 Full−Label 固定各自的硬标签，比较入选成员。固定一致性水平下的交互差为 Full−Label−Select+Raw。标签、成员、实际纳入的交叉熵和目标成绩需要分别登记。两无标签源的交叉熵各自取入选均值，辅助交叉熵使用当轮有标签源真值。一致性开启时覆盖三源批的 192 个样本，含分类未入选者。[现有研究审查](../../PC2G_RESEARCH_AUDIT.md) · [损失实现](../../experiments/msdgn_distribution/train.py) · [监督交叉控制实现](../../experiments/pc2g_research_audit/core.py)

四臂实验中的“臂 B”表示关掉 65 Hz 两个主头的整组伪标签 CE，同时保留该源一致性直接项。与八配置中“一致性因素 B”的含义分开。臂 C 仅屏蔽 65 Hz 一致性直接项，臂 D 同时屏蔽两项。C、D 的一致性归约分母仍为 192，65 Hz 仍参与共享前向，且可通过批归一化及辅助分支产生间接影响。B−A 同时删除正确标签和错标的损失。O−A 在已有入选处把错标签替换为正确标签，包含移除错误类别信息与加入正确类别信息的共同作用。当前冻结结果尚无仅将错标损失置零的 M 观测，无法从 A、B、O 分别估计两种作用。[四臂定义与逐路损失](../../output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_report.md) · [Oracle 对照定义](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_preregistration.md)

## 3. 分组、选模与记录完整性

### 旧 C-PU 与 DIRG

C-PU 原发布矩阵每个工况 12 类，每类 800 个发布训练窗和 200 个发布测试窗。历史源验证划分取 800 行中的后 80 行。事后精确时移核查发现每工况 960 个源验证窗均与源训练窗有部分重叠，900 个最长共享 2,200 点，60 个最长共享 1,200 点。四折源训练或源验证与留出目标测试窗的同类精确时移检查均未发现此类匹配。该检查覆盖精确跨窗重复。重叠发生在源端选模使用的验证窗，影响对独立源验证的解释及选步敏感性，无法估计原 Full+B−Raw 增益的偏差大小或方向。历史 C-PU 的物理记录映射也不完整。DIRG 每折 21 条源记录与 7 条目标记录互斥，但同类轴承跨工况复用。每条源记录前 128 窗作训练，间隔一窗后再留 31 窗作源验证。四工况重复留出和五种子均保留，采集单位独立性的结论以实际记录和轴承为准。[划分与选模审查](../../PC2G_RESEARCH_AUDIT.md) · [记录级补验](../../output/pc2g_formal100_acceptance_20261020/完整验证结果报告.md)

### CWRU 与 HUST 固定末步

CWRU 正常驱动端信号经 48→12 kHz 抗混叠降采样，三个故障类别保留原生 12 kHz。0–2 HP 的 12 条已审查源记录中，正常与故障类 5.5–6 kHz 功率占比的窗口范围未相交。处理链和类别共变，对 +1.333 个百分点的 Full+B−Raw 试跑差值所贡献的幅度仍未知。HUST 以电机设定频率定义工况，每工况每类一份独立采集记录，同一状态跨频率复用同一轴承。80 Hz 九类各 81 窗，整记录留出，源真值访问与目标评分有分别的回执。原 HUST 与新 HUST 在源工况、训练窗数和选模规则上同时变化，历史分数用于背景描述。[CWRU 预处理审查](../../output/pc2g_source_diagnostic_20261118/CWRU_preprocessing_audit.md) · [数据分组与重叠审查](../../output/pc2g_cross_dataset_stage2/leakage_audit.md) · [试跑审计](../../output/pc2g_cross_dataset_pilot_20261117/audit_checks.json)

### Oracle 的顺序恢复与源端放行

历史 A 的掩码给出成员集合，逐类筛选顺序借配对归档的校正 logits 和同版 CUDA 排序重建。全三种子逐步核对归档掩码、原标签及采样，并保留同一窗口在一个批次中重复入选的批内位置。短检以实际段末保存状态，学习率与损失调度使用原 5,000 步分母。成功短检每种子包含原生 A 12 步、回放 A 12 步和 O 16 步，共 120 步。首次短检第一个 12 步段因未按段末保存状态而停止，失败记录另行归档。本次冻结的 O 结果来自修复后从头执行且通过放行的三个种子。[归档顺序核验](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/frozen_archive/manifest.json) · [首次短检记录](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/failed_attempt_01/execution_status.json) · [通过的技术短检](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/preflight_complete.json) · [正式源端放行](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/all_sources_complete.json)

## 4. 计量单位与结果引用

| 量 | 分母或配对单位 | 可作的解释 |
|---|---|---|
| 伪标签正确率、错标流向 | 某源、某标签口径下全体或已入选的有放回批内出现。逐真实类流向的分母为该真实类的入选出现。 | 反映标签内容。521,989 为 Oracle 的 65 Hz 入选出现，229,902 次原本正确，292,087 次被纠正。相同物理窗口重复出现会重复计数。 |
| 筛选差异 | 在同一步、同一辅助分支及同一采样序列上比较交集、新增、移除。质量对照保持标签口径，核对成员构成、覆盖和实际 CE 纳入。 | 反映监督范围的差异。仅比较入选数量会遗漏同数换成员及换类别。 |
| 目标 Accuracy、Macro-F1、逐类 Recall | Accuracy 为判对窗数占比，Macro-F1 对固定类别等权，Recall 的分母为该类真实窗口。主对比先在同一目标、同一种子内相减。 | C-PU、DIRG 原矩阵按五种子汇总每种子四目标等权结果。HUST 的 Oracle、四臂和角色轮换分别按固定 80 Hz 上的三组种子配对。跨任务的均值依各自协议报告。 |
| 故障判正常与具体故障判对 | 每个种子有 648 个真实故障窗口。三种子合计为同一 648 窗在三次模型评价中的 1,944 次预测。 | 反映混淆去向。A、B、O 将故障判为正常分别 1,330、951、960 次，判对具体故障分别 37、25、170 次。两个计数应共同报告。 |

O−A 的 Accuracy 三种子差为 +0.960、+5.213、+12.071 个百分点，Macro-F1 差为 +1.706、+6.765、+12.689 个百分点。均值分别为 +6.081 和 +7.053 个百分点。三个优化种子的同向结果陈述当前任务的方向与波动。保持同一目标记录、标签清单和种子，顺序援引原协议的主对比与描述统计。引用时保留 CWRU 的混杂、DIRG 的异质性、B−A 的混合方向及 Oracle 的类别差异，依据各自的独立记录范围陈述结果。[逐种子对比](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_paired_comparison.csv) · [标签与出现数审计](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_label_correction_audit.csv) · [逐类结果](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_class_metrics.csv)
