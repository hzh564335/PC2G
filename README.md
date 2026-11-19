# PC2G 研究与投稿审阅

当前快照更新于 2026 年 11 月 19 日。论文研究跨工况轴承诊断中的多源伪标签质量，以标签与筛选的交叉控制、源域角色轮换、固定入选纠错为主线。

## 稿件

| 文件 | 用途 |
| --- | --- |
| [纯排版稿](投稿/PC2G_投稿正文（电子测量技术纯排版）.docx) | 直接使用桌面降 AIGC 后的稿件，保留原题名、摘要、正文、表格、图题和数值。英文信息整体前移，调整版式并去除旧刊页眉。 |
| [机制研究改写稿](投稿/跨工况轴承诊断的多源伪标签质量（电子测量技术）.docx) | 纳入 HUSTbearing 角色轮换、65 Hz 路径干预和 Oracle 结果，重新撰写题名、摘要及正文。 |

拟投《电子测量技术》。纯排版稿优先用于逐字保留原稿，机制研究改写稿供审阅最新实验叙事。两份均保留为独立版本。[期刊投稿须知](https://emt.etmchina.com/emt/ch/first_menu.aspx?parent_id=20150415013914001)

## 证据冻结

- [证据综述](投稿/PC2G_机制证据冻结_20261119/PC2G_EVIDENCE_FREEZE.md)
- [主张与证据矩阵](投稿/PC2G_机制证据冻结_20261119/PC2G_CLAIM_EVIDENCE_MATRIX.csv)
- [实验协议审计](投稿/PC2G_机制证据冻结_20261119/PC2G_EXPERIMENT_PROTOCOL_AUDIT.md)
- [论文重构方案](投稿/PC2G_机制证据冻结_20261119/PC2G_PAPER_RESTRUCTURE.md)
- [局限性与可用表述](投稿/PC2G_机制证据冻结_20261119/PC2G_LIMITATIONS.md)

## 实验进度与结果

| 实验 | 当前归档 |
| --- | --- |
| C-PU、DIRG 历史矩阵及记录级验证 | [C-PU 与 DIRG](output/pc2g_research_audit_20260924/FINAL_REPORT.md) · [记录级 100 次验证](output/pc2g_validation_complete_20261021/补验结果与解释.md) · [160 次源角色扩展](output/pc2g_source_roles_20261028/完整结果与解释_20261029.md) |
| CWRU 与 HUSTbearing 第 5,000 步试跑 | [八配置汇总及逐种子结果](output/pc2g_cross_dataset_pilot_20261117/PILOT_REPORT.md) · [CWRU 采样链审查](output/pc2g_source_diagnostic_20261118/CWRU_preprocessing_audit.md) |
| HUSTbearing 20、35、65 Hz 有标签源轮换 | [报告与数据表](output/pc2g_hust_role_rotation_20261118/PC2G_role_rotation_final_report.md) · [65 Hz 源端错标诊断](output/pc2g_source_diagnostic_20261118/HUST_65Hz_error_analysis.md) |
| 65 Hz 分类与一致性路径门控 | [四臂报告](output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_report.md) · [配对差](output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_paired_contrasts.csv) |
| 65 Hz Oracle 固定入选纠错 | [结果报告](output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_final_report.md) · [种子结果](output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_seed_results.csv) · [配对差](output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_paired_comparison.csv) · [执行审计](output/pc2g_hust_65hz_oracle_preregistration_20261119/oracle_implementation_audit.json) |

Oracle 的 120 步技术检查通过，三个新增模型均用第 5,000 步检查点评价 80 Hz。A、B 复用历史结果。O−A 的 Accuracy 和 Macro-F1 平均分别增加 6.081 和 7.053 个百分点。该比较固定 A 的逐步入选位置，使用额外的 65 Hz 源端真值替换错标。M 对照停在构想阶段。

## 审阅与复核

[文件清单及 SHA-256](ARCHIVE_MANIFEST.csv)记录本快照中的稿件、代码和归档文件。`output/` 沿用原目录结构，经过审阅的数值、审计表和冻结文件保持原始字节。部分历史文档和证据表中的运行目录、检查点地址指向本地完整归档。

`experiments/` 收录本轮试跑、源角色轮换、路径干预和 Oracle 的实现，供核对训练与评价口径。实际重跑还需要本地数据、已冻结的历史轨迹、模型依赖和运行环境。原始波形、模型权重、训练缓存和私有临时文件保留在本地。
