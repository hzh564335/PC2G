# PC2G 机制证据冻结

冻结日期为 2026-11-19。研究主题定为**跨工况故障诊断中多源伪标签质量差异及其影响研究**。本报告依据已经归档的结果、协议和审计记录，保留全部已报告方向和种子。本阶段未训练模型、未新增目标域读取或推理。冻结范围截至三种子 Oracle 纠错，M 尚无结果。

**核心发现。** HUSTbearing 的有标签源角色改变了同一无标签源的伪标签质量。固定 20 Hz 有标签、80 Hz 留出以及 A 的逐步入选轨迹后，纠正 65 Hz 入选错标使三个配对种子的 Accuracy 和 Macro-F1 均提高。该干预还表明，把故障从“正常”预测转移出去，与把故障判成正确类别，是两个可以分开观察的结果。[角色轮换](../../output/pc2g_hust_role_rotation_20261118/PC2G_role_rotation_final_report.md) · [Oracle 结果](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_final_report.md)

## 1. 标签与样本筛选的交叉控制

PC2G 复用 MSDGN 主辅骨架。将硬伪标签的来源和逐类低熵筛选的概率来源独立控制。用原始概率得到硬标签和掩码，用有标签先验与源预测历史对概率校正后也得到硬标签和掩码。两者按下表交叉。B 表示扰动一致性，形成独立开关。表中的 B 与第 4 节的实验臂 B 使用同一字母，含义由所在实验分辨。[目标函数与筛选实现](../../experiments/msdgn_distribution/train.py) · [四个配置的轨迹审计](../../output/pc2g_cross_dataset_pilot_20261117/PILOT_REPORT.md)

| 配置 | 硬标签来源 | 入选掩码来源 |
| --- | --- | --- |
| Raw | 原始 | 原始 |
| Label | 校正 | 原始 |
| Select | 原始 | 校正 |
| Full | 校正 | 校正 |

- **标签内容**可用 Label−Raw 或 Full−Select 比较，分别固定原始、校正掩码。
- **样本筛选**可用 Select−Raw 或 Full−Label 比较，分别固定原始、校正标签。更换筛选来源可以同时改变入选成员、类别组成和数量。入选正确率、覆盖率及特定类别错配分别报告。
- 同一 B 状态下以 Full−Label−Select+Raw 描述标签×筛选交互。解释时同时给出配对差和种子方向。若要讨论一致性作用，另用同一监督配置下的 B 开关对照。[历史因素与交互定义](../../output/pc2g_research_audit_20260924/FINAL_REPORT.md)

## 2. 不同数据集给出的边界

| 数据与协议 | 归档结果 | 在论文中承担的证据 |
| --- | --- | --- |
| 旧 C-PU，十二标签预处理矩阵，四目标、五种子 | B 开启时 Full 相对 Raw 的 Accuracy 为 +2.694 ± 1.504 个百分点，5/5 种子为正。Full+B 的均值为 76.181%，Raw+B 为 73.488%。 | 说明固定矩阵上存在条件性收益。追溯仅到预处理矩阵，物理类别和原采集独立性未获确认。 |
| DIRG，四目标、五种子 | 同一 B 口径下 Full 相对 Raw 为 +0.830 ± 1.730 个百分点，2/5 种子为正。Full−Label 为 −0.661，Select−Raw 为 −1.143 个百分点。 | 保留不同配置方向及全量对照，说明完整配置的优势依赖任务。目标为同轴承未见速度/载荷组合。 |
| PU-RS3-15-v1，三类、15 个轴承、四工况 | 预定 100 次验证中 Full+B−Raw 为 +0.117 个百分点，未调整 95% 种子区间 [−1.305, 1.539]，2/5 种子为正。 | 分列记录级补验。类别定义与数据划分均不同于旧 C-PU。 |
| CWRU 试跑，0 HP 有标签、3 HP 留出 | Full+B−Raw 的 Accuracy 和 Macro-F1 分别为 +1.333、+1.312 个百分点。Accuracy 净增 6 次正确判定，来自内圈 5 次、正常 1 次。 | 探索性证据。正常记录从 48 kHz 降至 12 kHz，故障记录为原生 12 kHz。源端高频功率占比范围分离，采样链贡献无法拆分。 |
| HUSTbearing 试跑，20 Hz 有标签、80 Hz 留出 | Full+B−Raw 为 +0.229、+0.481 个百分点。B 关闭的 Full−Select 为 −0.046、−0.214 个百分点。 | 单目标探索，支持检查具体源域、入选类别和误标去向。 |

资料入口 [C-PU / DIRG 冻结结果](../../output/pc2g_research_audit_20260924/FINAL_REPORT.md) · [原数据审计](../../output/pc2g_research_audit_20260924/data_audit/DATA_AUDIT.md) · [PU-RS3 事前固定补验](../../output/pc2g_validation_complete_20261021/补验结果与解释.md) · [CWRU / HUST 八配置试跑](../../output/pc2g_cross_dataset_pilot_20261117/PILOT_REPORT.md) · [CWRU 类别分解](../../output/pc2g_cross_dataset_diagnostic_20261118/CWRU_class_analysis.md) · [CWRU 采样链核查](../../output/pc2g_source_diagnostic_20261118/CWRU_preprocessing_audit.md)

## 3. 有标签源角色与无标签源监督质量

HUSTbearing 固定留出 80 Hz，分别以 20、35、65 Hz 为有标签源。每个角色 8 配置×3 种子，第 5,000 步评价。20 Hz 组的 24 个模型来自试跑，新增两个角色共 48 个模型。Full+B 的目标 Accuracy/Macro-F1 依次为 12.803%/5.495%、20.622%/13.967% 和 25.423%/19.004%。35 Hz 有标签时 Full+B 相对同角色 Raw 的 Accuracy 平均下降 2.423 个百分点，65 Hz 有标签时平均提高 1.692 个百分点。[角色轮换结果](../../output/pc2g_hust_role_rotation_20261118/PC2G_role_rotation_final_report.md) · [逐种子与逐类对照](../../output/pc2g_hust_role_rotation_20261118/HUST_role_rotation_comparison.md)

- **共享的 65 Hz 无标签源随有标签角色改变。** 20 Hz 提供标签时，其 Full+B 入选错误率为 55.957%。35 Hz 提供标签时，降到 26.181%。按真实中度滚动体的入选次数计算，误标为正常的比例为 96.594% → 0.439%。角色轮换同时改变真值训练域、无标签源组合及辅助分支任务，因此该结果识别的是对角色配置的敏感性。[源端逐类轨迹](../../output/pc2g_hust_role_rotation_20261118/HUST_role_rotation_pseudo_label.csv)
- **同一角色内部的两个无标签源分开看。** 20 Hz 有标签时，Full 在 35 Hz 的入选错误率为 1.766%（9,226/522,324），在 65 Hz 为 55.957%（292,087/521,989）。65 Hz 占两源全部入选错误的 96.938%。该源的中度滚动体入选后被判为正常的比例从训练前 1,000 步的 91.69% 升到最后 2,500 步的 99.81%。[两源对照](../../output/pc2g_source_diagnostic_20261118/HUST_35Hz_comparison.md) · [65 Hz 错配轨迹](../../output/pc2g_source_diagnostic_20261118/HUST_65Hz_error_analysis.md)
- **标签调整的效果随源变化。** 20 Hz 有标签时，固定校正后的入选集合，Full−Select 在 35 Hz 净减 1,405 次错误，在 65 Hz 净增 1,099 次错误。固定原始标签而比较 Select−Raw，65 Hz 错误净减 963 次。分母是各比较所定义的采样出现数，按种子合并，两种 B 水平的辅助轨迹相同，计数一次。[源域计数](../../output/pc2g_source_diagnostic_20261118/HUST_source_pseudo_label_by_domain.csv) · [逐类监督去向](../../output/pc2g_source_diagnostic_20261118/HUST_source_pseudo_label_by_class.csv)

## 4. 65 Hz 监督路径干预

在 20 Hz 有标签、80 Hz 留出的同一任务，单独门控 65 Hz 的两个主分类头伪标签 CE 和一致性直接项。A 两条开启，B 关闭 65 Hz 分类 CE，C 关闭 65 Hz 一致性直接项，D 两条关闭。全过程保留三源同批前向及一致性原分母 192。A 复用试跑 Full+B。B/C/D 共新增九个模型，第 5,000 步评价。[事前方案](../../output/pc2g_hust_65hz_path_preregistration_20261119/HUST_65Hz_supervision_path_preregistration.md) · [四臂结果与配对](../../output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_report.md)

B−A 的平均 Accuracy/Macro-F1 差为 −0.549/−0.787 个百分点，配对方向混合。三种子共 1,944 次真实故障评价，B 使判为正常从 1,330 降至 951，判对具体故障从 37 降至 25，判为其他故障从 577 升至 968。关分类 CE 同时移除原本正确及原错误的 65 Hz 监督，能检验整组分类路径的净效应。C−A 的平均 Accuracy 差为 −0.320 个百分点，D−B 为 0.000 个百分点，两项用于定位一致性直接项在该任务中的作用范围。[完整配对差](../../output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_paired_contrasts.csv)

## 5. Oracle 固定集合纠错

O 恢复 A 在两个主头使用的逐步批内顺序。保留 A 的 521,989 次 65 Hz 入选、每次出现的位置、CE 分母和调度系数。原正确 229,902 次保留标签，原错标 292,087 次替换为 65 Hz 真值。35 Hz 监督和覆盖全源批的一致性继续按原规则计算。三种子 120 步技术检查通过后，各训练 5,000 步，再评价 80 Hz。源端闸门记录无未入选项进入 CE。计数是训练出现次数。[预注册](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_preregistration.md) · [源端放行](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/all_sources_complete.json) · [技术审查](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_implementation_audit.json)

| 对照 | Accuracy（%） | Macro-F1（%） | 故障判为正常（次） | 判对具体故障（次） |
| --- | ---: | ---: | ---: | ---: |
| A 原入选标签 | 12.803 ± 2.255 | 5.495 ± 3.233 | 1,330 | 37 |
| B 关闭 65 Hz CE | 12.254 ± 0.554 | 4.707 ± 0.720 | 951 | 25 |
| O 固定集合纠错 | 18.884 ± 3.745 | 12.548 ± 2.679 | 960 | 170 |

O−A 的三种子 Accuracy 差为 +0.960/+5.213/+12.071，Macro-F1 差为 +1.706/+6.765/+12.689，均差为 +6.081/+7.053 个百分点。O−B 的两项均差为 +6.630/+7.840 个百分点，两项指标也是三个配对均为正。O 和 B 判为正常的次数接近，O 相比 B 多判对 145 次具体故障。这是正确监督的恢复相对于关闭整组监督的对照。O−A 包含撤掉错误目标和加入正确目标的联合效应。[逐种子结果](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_seed_results.csv) · [全部配对差](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_paired_comparison.csv)

**收益集中于特定类别。** 对 A，O 的中度滚动体 Recall 差为 +6.173/+7.407/+8.642 个百分点。重度复合故障的逐种子差为 −1.235/+45.679/+98.765，分别少判对 1 次、多判对 37 次和 80 次。该类净增 116 次，占 133 次净增具体故障正确判定的约 87%。中度内圈均值下降 2.058 个百分点，两种外圈及中度复合在 A 和 O 中均为零召回。O 的三种子真实故障正确判定率为 170/1,944（8.745%），正常类召回均为 100%。[九类支持数、召回与预测去向](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_class_metrics.csv)

## 6. 研究结论与适用边界

| 概念 | 当前操作化和可观察量 | 证据边界 |
| --- | --- | --- |
| 伪标签质量 | 固定某个集合时的标签正确率、类别错误流向 | 全部抽样与入选子集的分母不同。 |
| 样本筛选质量 | 入选覆盖率、成员变化、正确样本留存和错误富集 | 总体错误可减少，同时保留某类严重错配。 |
| 有标签源角色 | 哪个源提供真值并参与先验与辅助监督 | 角色改变时多个训练路径同时改变，不能从性能差证明单一中介。 |
| 目标域分类边界泛化 | 80 Hz 的 Accuracy、Macro-F1、各类 Recall 及预测混淆 | 错标纠正的收益随类和种子变化。当前对照无法识别表示偏移、样本覆盖、35 Hz 残余错误和决策边界分别贡献多少。 |

三条已获支持的主张是：有标签源角色改变固定无标签源的监督质量；关闭整组 65 Hz 分类监督可改变混淆去向；在 A 的固定入选轨迹上纠正错标能改善该 80 Hz 任务的整体识别。Oracle 仍保留多个低召回类别，说明纠正这一条监督路径只解决了部分错误。该结果给出了进一步辨别机制的方向，现有数据尚不能分离未见工况、轴承身份、特定记录及其他监督路径的影响。三个优化种子描述固定任务的训练波动。同工况每类一条原记录，种子和切窗均不能作为独立采集重复。Oracle 使用额外 65 Hz 真值，论文中作为受控机制参照。适用边界与补证条件见 [局限性](PC2G_LIMITATIONS.md)。

## 冻结源文件指纹

| 已归档证据 | SHA-256 |
| --- | --- |
| [C-PU / DIRG 主报告](../../output/pc2g_research_audit_20260924/FINAL_REPORT.md) | `62c60ece893d53862fd06b67b0077bc5fa9576dbdbc08dbc0b4fa35c68134916` |
| [PU-RS3 固定 100 次结果与解释](../../output/pc2g_validation_complete_20261021/补验结果与解释.md) | `909f9c83d65ba1234284f58074d133317ebb81ddfa66704844e04a575cfb1a86` |
| [CWRU / HUST 试跑结果](../../output/pc2g_cross_dataset_pilot_20261117/results.json) | `d82eb950b67d9c3418c09da99dbd8f4206ab09cc0120d6aed9eb339111e37786` |
| [HUST 角色轮换结果](../../output/pc2g_hust_role_rotation_20261118/results.json) | `7b0b07cf4f085bf2ed680d00577a66b1462e53310cf9da372e7a9a47b50e0548` |
| [HUST 逐源伪标签诊断](../../output/pc2g_source_diagnostic_20261118/HUST_source_pseudo_label_by_domain.csv) | `6595e81a68bf5baed51a9e1e228a45c480ce21618ae2d247dea16a4413c22023` |
| [四臂路径干预结果](../../output/pc2g_hust_65hz_path_20261119/results.json) | `890df32cd15d004b0463a470d6d0277ea1624a15ade96740bc1e696288c769c1` |
| [Oracle 三臂九条种子结果](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_seed_results.csv) | `a3026e144e277cba429b232e2a13450bb7f70d0cce98d78278f5ce350fc8f969` |
| [Oracle 全部配对差](../../output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_paired_comparison.csv) | `e5dcc5a746d2cb818251655564aa417f55257a43b299a22047d50f8ba5677d45` |

配套文件为 [主张与证据矩阵](PC2G_CLAIM_EVIDENCE_MATRIX.csv)、[实验协议审计](PC2G_EXPERIMENT_PROTOCOL_AUDIT.md)、[论文重构方案](PC2G_PAPER_RESTRUCTURE.md) 和 [局限性](PC2G_LIMITATIONS.md)。
