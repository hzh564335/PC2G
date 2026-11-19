# 历史结果严格复用核查

生成：2026-09-24T12:52:01.084088+00:00

总计320条：**reusable=176，missing=144，blocked_evidence=0，rejected_mismatch=0**。

440条总计划减去已核准复用为264条；其中确定缺失factor为144条，另有80条coverage与40条同骨架soft对照。没有启动训练、推理、模型构造或GPU。

## 接口与复用边界

主代理读取 `reuse_manifest.json` 顶层 `rows`。仅 `reuse_status == "reusable"` 可复用。每行包含用户要求的全部11字段，另有 `row_id/checks/blockers/readable_config/artifact_verification/checkpoint_inspection`。所有路径为工作区相对路径；无历史训练项的路径为null，另保留searched路径。`artifact_sha256` 是相对路径到当前SHA256的字典；历史预期与比较结果另列在 `artifact_verification`、`code_audit.json`。

复用判断针对原始数据矩阵和固定训练协议。数据哈希一致不证明无泄漏或原始记录独立；父任务的数据协议核查仍是批量开跑前置条件。176/144是待核验预期，并非强制凑齐目标。

## 核查内容

- 每条数据SHA、profile、5000步、batch64、persistent Adam lr=.001、weight_decay=.0005、inverse^.75、ratio=.6、DA128、B0/.1与源信息；21个验证点逐点检查学习率。
- 从history重新求LS验证CE最小项；验证source_complete/metrics与best检查点的step/config；last检查点必须5000步。只用CPU安全读取已存在的检查点。
- 检查B std=.1、clean stop-gradient、全192样本归一化、额外前向BN缓冲在backward后/optimizer前恢复；last的主分支BN计数必须均为5000。
- 数据、配置、日志、检查点、预测文件均计算SHA并与存在的历史声明比较。仅当前hash不冒充历史hash；原始PU未提供逐次访问守卫日志时，明确依赖冻结训练器静态访问检查。
- 每组同dataset/target/seed的辅助分支末态、DA末态与21个日志点辅助损失比较。末态和稀疏日志相等不等于5000步逐步轨迹证明；主网络末态不要求相等。
- seed3/4总表64条缺reference，通过冻结protocol的准确case身份恢复路径，再核对配置、checkpoint/hash和全部12个干净/噪声指标，未用分数就近匹配。

## 历史B范围实验

|系列|新训练条数|显式一致性范围|归一化|能替代LS+selected吗|
|---|---:|---|---|---|
|b_labeled_screen_v1|16（PU/CWRU10，各4目标，seed0，B/DA+B）|仅LS|LS sum/64|不能|
|b_scope_normalization_v1|16（同上）|仅LS|LS sum/192|不能|

两系列均保留全部源的干净/扰动前向、扰动随机过程和BN恢复。第一系列LS行的系数为原全批次B的3倍；第二系列维持原LS行系数、删除显式US项。US仍可能通过联合BN间接影响计算。它们不是LS+selected，不计入320 factor或80 coverage的复用。详见 `historical_B_scope.json`。

## 批量运行前需要处理的问题

- **data_protocol_gate / external_gate**：Hashes verify exact historical matrices, not acquisition independence or absence of leakage. Before batch training, parent data audit must resolve substantive validity defects; C-PU raw record identities are unavailable and DIRG reuses bearing identities across conditions.
- **new_trainer_equivalence / pre_run_required**：Reuse is conditional on preserving audited trainer semantics. Any changes to RNG order, selector, hard masks, loss normalization, BN restoration, ramp, source CE checkpointing or data hashes require a new compatibility assessment. Merely using seed0-4 does not establish pairing.
- **partial_runner_B0 / implementation**：experiments/da_component_intervention/train_components.py hard asserts B=.1; B0 must use experiments/da_b_factorial/train_bfactor.py or an audited equivalent. Do not bulk-call the B=.1 runner for all8 cells.
- **partial_DIRG_protocol / implementation**：Old partial suites predeclare only PU/CWRU10 seed0; DIRG and seeds1-4 need a new frozen protocol/config. Do not mutate original protocol files.
- **missing_dense_selection_records / diagnostic_gap**：Reusable metrics/checkpoints do not supply complete selected indices, logits, batch IDs and trajectories for all160 anchors. Paired endpoint agreement is not full5000-step trajectory evidence. New diagnostic replay needs independent authorization/execution outside this audit.
- **coverage_no_reuse / expected_new**：32 old scope cases are LS-only, not LS+selected. They supply contextual controls only; none fills the80 planned selected_fixed/selected_domain_mean rows.
- **soft_mechanism_no_reuse / expected_new**：Existing main-table SoftMatch uses another backbone; no equivalent same-MSDGN mechanism row accepted in this320-row audit.
- **new_training_count / planning**：factor definitely missing=144; blocked/rejected=0; total440 minus accepted reuse=264. Evidence blocks are not automatically a mandate to retrain.

## 可读配置及路径清单

公共完整参数见 `effective_protocol.json`；逐行实参在manifest的`readable_config`。下表列出全部320条；SHA及详细检查见JSON。

|dataset|target|seed|mode|B|reuse_status|source_folder|reference_result_path|
|---|---:|---:|---|---:|---|---|---|
|PU|6|0|raw|0.0|reusable|runs/pu_v1/t6-s0-baseline|runs/pu_v1/t6-s0-baseline/metrics.json|
|PU|6|0|raw|0.1|reusable|runs/pu_v1/t6-s0-stat_consistency|runs/pu_v1/t6-s0-stat_consistency/metrics.json|
|PU|6|0|labels_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t6-s0/labels_only|output/da_b_factorial_v1/target_cases/PU-t6-s0/labels_only/result.json|
|PU|6|0|labels_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t6-s0/labels_only|output/da_component_intervention_v1/target_cases/PU-t6-s0/labels_only/result.json|
|PU|6|0|selection_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t6-s0/selection_only|output/da_b_factorial_v1/target_cases/PU-t6-s0/selection_only/result.json|
|PU|6|0|selection_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t6-s0/selection_only|output/da_component_intervention_v1/target_cases/PU-t6-s0/selection_only/result.json|
|PU|6|0|full|0.0|reusable|runs/pu_distribution_v1/t6-s0-distribution|runs/pu_distribution_v1/t6-s0-distribution/metrics.json|
|PU|6|0|full|0.1|reusable|runs/pu_distribution_v1/t6-s0-distribution_consistency|runs/pu_distribution_v1/t6-s0-distribution_consistency/metrics.json|
|PU|6|1|raw|0.0|reusable|runs/pu_b_seeds12/t6-s1-baseline|runs/pu_b_seeds12/t6-s1-baseline/metrics.json|
|PU|6|1|raw|0.1|reusable|runs/pu_b_seeds12/t6-s1-stat_consistency|runs/pu_b_seeds12/t6-s1-stat_consistency/metrics.json|
|PU|6|1|labels_only|0.0|missing|—|—|
|PU|6|1|labels_only|0.1|missing|—|—|
|PU|6|1|selection_only|0.0|missing|—|—|
|PU|6|1|selection_only|0.1|missing|—|—|
|PU|6|1|full|0.0|reusable|runs/pu_distribution_seeds12/t6-s1-distribution|runs/pu_distribution_seeds12/t6-s1-distribution/metrics.json|
|PU|6|1|full|0.1|reusable|runs/pu_distribution_seeds12/t6-s1-distribution_consistency|runs/pu_distribution_seeds12/t6-s1-distribution_consistency/metrics.json|
|PU|6|2|raw|0.0|reusable|runs/pu_b_seeds12/t6-s2-baseline|runs/pu_b_seeds12/t6-s2-baseline/metrics.json|
|PU|6|2|raw|0.1|reusable|runs/pu_b_seeds12/t6-s2-stat_consistency|runs/pu_b_seeds12/t6-s2-stat_consistency/metrics.json|
|PU|6|2|labels_only|0.0|missing|—|—|
|PU|6|2|labels_only|0.1|missing|—|—|
|PU|6|2|selection_only|0.0|missing|—|—|
|PU|6|2|selection_only|0.1|missing|—|—|
|PU|6|2|full|0.0|reusable|runs/pu_distribution_seeds12/t6-s2-distribution|runs/pu_distribution_seeds12/t6-s2-distribution/metrics.json|
|PU|6|2|full|0.1|reusable|runs/pu_distribution_seeds12/t6-s2-distribution_consistency|runs/pu_distribution_seeds12/t6-s2-distribution_consistency/metrics.json|
|PU|6|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s3-baseline/result.json|
|PU|6|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-B|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s3-B/result.json|
|PU|6|3|labels_only|0.0|missing|—|—|
|PU|6|3|labels_only|0.1|missing|—|—|
|PU|6|3|selection_only|0.0|missing|—|—|
|PU|6|3|selection_only|0.1|missing|—|—|
|PU|6|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s3-DA/result.json|
|PU|6|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s3-DA_B/result.json|
|PU|6|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s4-baseline/result.json|
|PU|6|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-B|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s4-B/result.json|
|PU|6|4|labels_only|0.0|missing|—|—|
|PU|6|4|labels_only|0.1|missing|—|—|
|PU|6|4|selection_only|0.0|missing|—|—|
|PU|6|4|selection_only|0.1|missing|—|—|
|PU|6|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s4-DA/result.json|
|PU|6|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t6-s4-DA_B/result.json|
|PU|7|0|raw|0.0|reusable|runs/pu_v1/t7-s0-baseline|runs/pu_v1/t7-s0-baseline/metrics.json|
|PU|7|0|raw|0.1|reusable|runs/pu_v1/t7-s0-stat_consistency|runs/pu_v1/t7-s0-stat_consistency/metrics.json|
|PU|7|0|labels_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t7-s0/labels_only|output/da_b_factorial_v1/target_cases/PU-t7-s0/labels_only/result.json|
|PU|7|0|labels_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t7-s0/labels_only|output/da_component_intervention_v1/target_cases/PU-t7-s0/labels_only/result.json|
|PU|7|0|selection_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t7-s0/selection_only|output/da_b_factorial_v1/target_cases/PU-t7-s0/selection_only/result.json|
|PU|7|0|selection_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t7-s0/selection_only|output/da_component_intervention_v1/target_cases/PU-t7-s0/selection_only/result.json|
|PU|7|0|full|0.0|reusable|runs/pu_distribution_v1/t7-s0-distribution|runs/pu_distribution_v1/t7-s0-distribution/metrics.json|
|PU|7|0|full|0.1|reusable|runs/pu_distribution_v1/t7-s0-distribution_consistency|runs/pu_distribution_v1/t7-s0-distribution_consistency/metrics.json|
|PU|7|1|raw|0.0|reusable|runs/pu_b_seeds12/t7-s1-baseline|runs/pu_b_seeds12/t7-s1-baseline/metrics.json|
|PU|7|1|raw|0.1|reusable|runs/pu_b_seeds12/t7-s1-stat_consistency|runs/pu_b_seeds12/t7-s1-stat_consistency/metrics.json|
|PU|7|1|labels_only|0.0|missing|—|—|
|PU|7|1|labels_only|0.1|missing|—|—|
|PU|7|1|selection_only|0.0|missing|—|—|
|PU|7|1|selection_only|0.1|missing|—|—|
|PU|7|1|full|0.0|reusable|runs/pu_distribution_seeds12/t7-s1-distribution|runs/pu_distribution_seeds12/t7-s1-distribution/metrics.json|
|PU|7|1|full|0.1|reusable|runs/pu_distribution_seeds12/t7-s1-distribution_consistency|runs/pu_distribution_seeds12/t7-s1-distribution_consistency/metrics.json|
|PU|7|2|raw|0.0|reusable|runs/pu_b_seeds12/t7-s2-baseline|runs/pu_b_seeds12/t7-s2-baseline/metrics.json|
|PU|7|2|raw|0.1|reusable|runs/pu_b_seeds12/t7-s2-stat_consistency|runs/pu_b_seeds12/t7-s2-stat_consistency/metrics.json|
|PU|7|2|labels_only|0.0|missing|—|—|
|PU|7|2|labels_only|0.1|missing|—|—|
|PU|7|2|selection_only|0.0|missing|—|—|
|PU|7|2|selection_only|0.1|missing|—|—|
|PU|7|2|full|0.0|reusable|runs/pu_distribution_seeds12/t7-s2-distribution|runs/pu_distribution_seeds12/t7-s2-distribution/metrics.json|
|PU|7|2|full|0.1|reusable|runs/pu_distribution_seeds12/t7-s2-distribution_consistency|runs/pu_distribution_seeds12/t7-s2-distribution_consistency/metrics.json|
|PU|7|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s3-baseline/result.json|
|PU|7|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-B|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s3-B/result.json|
|PU|7|3|labels_only|0.0|missing|—|—|
|PU|7|3|labels_only|0.1|missing|—|—|
|PU|7|3|selection_only|0.0|missing|—|—|
|PU|7|3|selection_only|0.1|missing|—|—|
|PU|7|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s3-DA/result.json|
|PU|7|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s3-DA_B/result.json|
|PU|7|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s4-baseline/result.json|
|PU|7|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-B|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s4-B/result.json|
|PU|7|4|labels_only|0.0|missing|—|—|
|PU|7|4|labels_only|0.1|missing|—|—|
|PU|7|4|selection_only|0.0|missing|—|—|
|PU|7|4|selection_only|0.1|missing|—|—|
|PU|7|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s4-DA/result.json|
|PU|7|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t7-s4-DA_B/result.json|
|PU|8|0|raw|0.0|reusable|runs/pu_v1/t8-s0-baseline|runs/pu_v1/t8-s0-baseline/metrics.json|
|PU|8|0|raw|0.1|reusable|runs/pu_v1/t8-s0-stat_consistency|runs/pu_v1/t8-s0-stat_consistency/metrics.json|
|PU|8|0|labels_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t8-s0/labels_only|output/da_b_factorial_v1/target_cases/PU-t8-s0/labels_only/result.json|
|PU|8|0|labels_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t8-s0/labels_only|output/da_component_intervention_v1/target_cases/PU-t8-s0/labels_only/result.json|
|PU|8|0|selection_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t8-s0/selection_only|output/da_b_factorial_v1/target_cases/PU-t8-s0/selection_only/result.json|
|PU|8|0|selection_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t8-s0/selection_only|output/da_component_intervention_v1/target_cases/PU-t8-s0/selection_only/result.json|
|PU|8|0|full|0.0|reusable|runs/pu_distribution_v1/t8-s0-distribution|runs/pu_distribution_v1/t8-s0-distribution/metrics.json|
|PU|8|0|full|0.1|reusable|runs/pu_distribution_v1/t8-s0-distribution_consistency|runs/pu_distribution_v1/t8-s0-distribution_consistency/metrics.json|
|PU|8|1|raw|0.0|reusable|runs/pu_b_seeds12/t8-s1-baseline|runs/pu_b_seeds12/t8-s1-baseline/metrics.json|
|PU|8|1|raw|0.1|reusable|runs/pu_b_seeds12/t8-s1-stat_consistency|runs/pu_b_seeds12/t8-s1-stat_consistency/metrics.json|
|PU|8|1|labels_only|0.0|missing|—|—|
|PU|8|1|labels_only|0.1|missing|—|—|
|PU|8|1|selection_only|0.0|missing|—|—|
|PU|8|1|selection_only|0.1|missing|—|—|
|PU|8|1|full|0.0|reusable|runs/pu_distribution_seeds12/t8-s1-distribution|runs/pu_distribution_seeds12/t8-s1-distribution/metrics.json|
|PU|8|1|full|0.1|reusable|runs/pu_distribution_seeds12/t8-s1-distribution_consistency|runs/pu_distribution_seeds12/t8-s1-distribution_consistency/metrics.json|
|PU|8|2|raw|0.0|reusable|runs/pu_b_seeds12/t8-s2-baseline|runs/pu_b_seeds12/t8-s2-baseline/metrics.json|
|PU|8|2|raw|0.1|reusable|runs/pu_b_seeds12/t8-s2-stat_consistency|runs/pu_b_seeds12/t8-s2-stat_consistency/metrics.json|
|PU|8|2|labels_only|0.0|missing|—|—|
|PU|8|2|labels_only|0.1|missing|—|—|
|PU|8|2|selection_only|0.0|missing|—|—|
|PU|8|2|selection_only|0.1|missing|—|—|
|PU|8|2|full|0.0|reusable|runs/pu_distribution_seeds12/t8-s2-distribution|runs/pu_distribution_seeds12/t8-s2-distribution/metrics.json|
|PU|8|2|full|0.1|reusable|runs/pu_distribution_seeds12/t8-s2-distribution_consistency|runs/pu_distribution_seeds12/t8-s2-distribution_consistency/metrics.json|
|PU|8|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s3-baseline/result.json|
|PU|8|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-B|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s3-B/result.json|
|PU|8|3|labels_only|0.0|missing|—|—|
|PU|8|3|labels_only|0.1|missing|—|—|
|PU|8|3|selection_only|0.0|missing|—|—|
|PU|8|3|selection_only|0.1|missing|—|—|
|PU|8|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s3-DA/result.json|
|PU|8|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s3-DA_B/result.json|
|PU|8|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s4-baseline/result.json|
|PU|8|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-B|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s4-B/result.json|
|PU|8|4|labels_only|0.0|missing|—|—|
|PU|8|4|labels_only|0.1|missing|—|—|
|PU|8|4|selection_only|0.0|missing|—|—|
|PU|8|4|selection_only|0.1|missing|—|—|
|PU|8|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s4-DA/result.json|
|PU|8|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t8-s4-DA_B/result.json|
|PU|9|0|raw|0.0|reusable|runs/pu_v1/t9-s0-baseline|runs/pu_v1/t9-s0-baseline/metrics.json|
|PU|9|0|raw|0.1|reusable|runs/pu_v1/t9-s0-stat_consistency|runs/pu_v1/t9-s0-stat_consistency/metrics.json|
|PU|9|0|labels_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t9-s0/labels_only|output/da_b_factorial_v1/target_cases/PU-t9-s0/labels_only/result.json|
|PU|9|0|labels_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t9-s0/labels_only|output/da_component_intervention_v1/target_cases/PU-t9-s0/labels_only/result.json|
|PU|9|0|selection_only|0.0|reusable|runs/da_b_factorial_v1/cases/PU-t9-s0/selection_only|output/da_b_factorial_v1/target_cases/PU-t9-s0/selection_only/result.json|
|PU|9|0|selection_only|0.1|reusable|runs/da_component_intervention_v1/cases/PU-t9-s0/selection_only|output/da_component_intervention_v1/target_cases/PU-t9-s0/selection_only/result.json|
|PU|9|0|full|0.0|reusable|runs/pu_distribution_v1/t9-s0-distribution|runs/pu_distribution_v1/t9-s0-distribution/metrics.json|
|PU|9|0|full|0.1|reusable|runs/pu_distribution_v1/t9-s0-distribution_consistency|runs/pu_distribution_v1/t9-s0-distribution_consistency/metrics.json|
|PU|9|1|raw|0.0|reusable|runs/pu_b_seeds12/t9-s1-baseline|runs/pu_b_seeds12/t9-s1-baseline/metrics.json|
|PU|9|1|raw|0.1|reusable|runs/pu_b_seeds12/t9-s1-stat_consistency|runs/pu_b_seeds12/t9-s1-stat_consistency/metrics.json|
|PU|9|1|labels_only|0.0|missing|—|—|
|PU|9|1|labels_only|0.1|missing|—|—|
|PU|9|1|selection_only|0.0|missing|—|—|
|PU|9|1|selection_only|0.1|missing|—|—|
|PU|9|1|full|0.0|reusable|runs/pu_distribution_seeds12/t9-s1-distribution|runs/pu_distribution_seeds12/t9-s1-distribution/metrics.json|
|PU|9|1|full|0.1|reusable|runs/pu_distribution_seeds12/t9-s1-distribution_consistency|runs/pu_distribution_seeds12/t9-s1-distribution_consistency/metrics.json|
|PU|9|2|raw|0.0|reusable|runs/pu_b_seeds12/t9-s2-baseline|runs/pu_b_seeds12/t9-s2-baseline/metrics.json|
|PU|9|2|raw|0.1|reusable|runs/pu_b_seeds12/t9-s2-stat_consistency|runs/pu_b_seeds12/t9-s2-stat_consistency/metrics.json|
|PU|9|2|labels_only|0.0|missing|—|—|
|PU|9|2|labels_only|0.1|missing|—|—|
|PU|9|2|selection_only|0.0|missing|—|—|
|PU|9|2|selection_only|0.1|missing|—|—|
|PU|9|2|full|0.0|reusable|runs/pu_distribution_seeds12/t9-s2-distribution|runs/pu_distribution_seeds12/t9-s2-distribution/metrics.json|
|PU|9|2|full|0.1|reusable|runs/pu_distribution_seeds12/t9-s2-distribution_consistency|runs/pu_distribution_seeds12/t9-s2-distribution_consistency/metrics.json|
|PU|9|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s3-baseline/result.json|
|PU|9|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-B|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s3-B/result.json|
|PU|9|3|labels_only|0.0|missing|—|—|
|PU|9|3|labels_only|0.1|missing|—|—|
|PU|9|3|selection_only|0.0|missing|—|—|
|PU|9|3|selection_only|0.1|missing|—|—|
|PU|9|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s3-DA/result.json|
|PU|9|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s3-DA_B/result.json|
|PU|9|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s4-baseline/result.json|
|PU|9|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-B|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s4-B/result.json|
|PU|9|4|labels_only|0.0|missing|—|—|
|PU|9|4|labels_only|0.1|missing|—|—|
|PU|9|4|selection_only|0.0|missing|—|—|
|PU|9|4|selection_only|0.1|missing|—|—|
|PU|9|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-DA|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s4-DA/result.json|
|PU|9|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/PU-t9-s4-DA_B/result.json|
|DIRG|0|0|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s0-baseline|output/dirg_da_b_v1/target_cases/t0-s0-baseline/result.json|
|DIRG|0|0|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s0-B|output/dirg_da_b_v1/target_cases/t0-s0-B/result.json|
|DIRG|0|0|labels_only|0.0|missing|—|—|
|DIRG|0|0|labels_only|0.1|missing|—|—|
|DIRG|0|0|selection_only|0.0|missing|—|—|
|DIRG|0|0|selection_only|0.1|missing|—|—|
|DIRG|0|0|full|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s0-DA|output/dirg_da_b_v1/target_cases/t0-s0-DA/result.json|
|DIRG|0|0|full|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s0-DA_B|output/dirg_da_b_v1/target_cases/t0-s0-DA_B/result.json|
|DIRG|0|1|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s1-baseline|output/dirg_da_b_v1/target_cases/t0-s1-baseline/result.json|
|DIRG|0|1|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s1-B|output/dirg_da_b_v1/target_cases/t0-s1-B/result.json|
|DIRG|0|1|labels_only|0.0|missing|—|—|
|DIRG|0|1|labels_only|0.1|missing|—|—|
|DIRG|0|1|selection_only|0.0|missing|—|—|
|DIRG|0|1|selection_only|0.1|missing|—|—|
|DIRG|0|1|full|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s1-DA|output/dirg_da_b_v1/target_cases/t0-s1-DA/result.json|
|DIRG|0|1|full|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s1-DA_B|output/dirg_da_b_v1/target_cases/t0-s1-DA_B/result.json|
|DIRG|0|2|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s2-baseline|output/dirg_da_b_v1/target_cases/t0-s2-baseline/result.json|
|DIRG|0|2|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s2-B|output/dirg_da_b_v1/target_cases/t0-s2-B/result.json|
|DIRG|0|2|labels_only|0.0|missing|—|—|
|DIRG|0|2|labels_only|0.1|missing|—|—|
|DIRG|0|2|selection_only|0.0|missing|—|—|
|DIRG|0|2|selection_only|0.1|missing|—|—|
|DIRG|0|2|full|0.0|reusable|runs/dirg_da_b_v1/cases/t0-s2-DA|output/dirg_da_b_v1/target_cases/t0-s2-DA/result.json|
|DIRG|0|2|full|0.1|reusable|runs/dirg_da_b_v1/cases/t0-s2-DA_B|output/dirg_da_b_v1/target_cases/t0-s2-DA_B/result.json|
|DIRG|0|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s3-baseline/result.json|
|DIRG|0|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s3-B/result.json|
|DIRG|0|3|labels_only|0.0|missing|—|—|
|DIRG|0|3|labels_only|0.1|missing|—|—|
|DIRG|0|3|selection_only|0.0|missing|—|—|
|DIRG|0|3|selection_only|0.1|missing|—|—|
|DIRG|0|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s3-DA/result.json|
|DIRG|0|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s3-DA_B/result.json|
|DIRG|0|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s4-baseline/result.json|
|DIRG|0|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s4-B/result.json|
|DIRG|0|4|labels_only|0.0|missing|—|—|
|DIRG|0|4|labels_only|0.1|missing|—|—|
|DIRG|0|4|selection_only|0.0|missing|—|—|
|DIRG|0|4|selection_only|0.1|missing|—|—|
|DIRG|0|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s4-DA/result.json|
|DIRG|0|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t0-s4-DA_B/result.json|
|DIRG|1|0|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s0-baseline|output/dirg_da_b_v1/target_cases/t1-s0-baseline/result.json|
|DIRG|1|0|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s0-B|output/dirg_da_b_v1/target_cases/t1-s0-B/result.json|
|DIRG|1|0|labels_only|0.0|missing|—|—|
|DIRG|1|0|labels_only|0.1|missing|—|—|
|DIRG|1|0|selection_only|0.0|missing|—|—|
|DIRG|1|0|selection_only|0.1|missing|—|—|
|DIRG|1|0|full|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s0-DA|output/dirg_da_b_v1/target_cases/t1-s0-DA/result.json|
|DIRG|1|0|full|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s0-DA_B|output/dirg_da_b_v1/target_cases/t1-s0-DA_B/result.json|
|DIRG|1|1|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s1-baseline|output/dirg_da_b_v1/target_cases/t1-s1-baseline/result.json|
|DIRG|1|1|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s1-B|output/dirg_da_b_v1/target_cases/t1-s1-B/result.json|
|DIRG|1|1|labels_only|0.0|missing|—|—|
|DIRG|1|1|labels_only|0.1|missing|—|—|
|DIRG|1|1|selection_only|0.0|missing|—|—|
|DIRG|1|1|selection_only|0.1|missing|—|—|
|DIRG|1|1|full|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s1-DA|output/dirg_da_b_v1/target_cases/t1-s1-DA/result.json|
|DIRG|1|1|full|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s1-DA_B|output/dirg_da_b_v1/target_cases/t1-s1-DA_B/result.json|
|DIRG|1|2|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s2-baseline|output/dirg_da_b_v1/target_cases/t1-s2-baseline/result.json|
|DIRG|1|2|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s2-B|output/dirg_da_b_v1/target_cases/t1-s2-B/result.json|
|DIRG|1|2|labels_only|0.0|missing|—|—|
|DIRG|1|2|labels_only|0.1|missing|—|—|
|DIRG|1|2|selection_only|0.0|missing|—|—|
|DIRG|1|2|selection_only|0.1|missing|—|—|
|DIRG|1|2|full|0.0|reusable|runs/dirg_da_b_v1/cases/t1-s2-DA|output/dirg_da_b_v1/target_cases/t1-s2-DA/result.json|
|DIRG|1|2|full|0.1|reusable|runs/dirg_da_b_v1/cases/t1-s2-DA_B|output/dirg_da_b_v1/target_cases/t1-s2-DA_B/result.json|
|DIRG|1|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s3-baseline/result.json|
|DIRG|1|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s3-B/result.json|
|DIRG|1|3|labels_only|0.0|missing|—|—|
|DIRG|1|3|labels_only|0.1|missing|—|—|
|DIRG|1|3|selection_only|0.0|missing|—|—|
|DIRG|1|3|selection_only|0.1|missing|—|—|
|DIRG|1|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s3-DA/result.json|
|DIRG|1|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s3-DA_B/result.json|
|DIRG|1|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s4-baseline/result.json|
|DIRG|1|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s4-B/result.json|
|DIRG|1|4|labels_only|0.0|missing|—|—|
|DIRG|1|4|labels_only|0.1|missing|—|—|
|DIRG|1|4|selection_only|0.0|missing|—|—|
|DIRG|1|4|selection_only|0.1|missing|—|—|
|DIRG|1|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s4-DA/result.json|
|DIRG|1|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t1-s4-DA_B/result.json|
|DIRG|2|0|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s0-baseline|output/dirg_da_b_v1/target_cases/t2-s0-baseline/result.json|
|DIRG|2|0|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s0-B|output/dirg_da_b_v1/target_cases/t2-s0-B/result.json|
|DIRG|2|0|labels_only|0.0|missing|—|—|
|DIRG|2|0|labels_only|0.1|missing|—|—|
|DIRG|2|0|selection_only|0.0|missing|—|—|
|DIRG|2|0|selection_only|0.1|missing|—|—|
|DIRG|2|0|full|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s0-DA|output/dirg_da_b_v1/target_cases/t2-s0-DA/result.json|
|DIRG|2|0|full|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s0-DA_B|output/dirg_da_b_v1/target_cases/t2-s0-DA_B/result.json|
|DIRG|2|1|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s1-baseline|output/dirg_da_b_v1/target_cases/t2-s1-baseline/result.json|
|DIRG|2|1|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s1-B|output/dirg_da_b_v1/target_cases/t2-s1-B/result.json|
|DIRG|2|1|labels_only|0.0|missing|—|—|
|DIRG|2|1|labels_only|0.1|missing|—|—|
|DIRG|2|1|selection_only|0.0|missing|—|—|
|DIRG|2|1|selection_only|0.1|missing|—|—|
|DIRG|2|1|full|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s1-DA|output/dirg_da_b_v1/target_cases/t2-s1-DA/result.json|
|DIRG|2|1|full|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s1-DA_B|output/dirg_da_b_v1/target_cases/t2-s1-DA_B/result.json|
|DIRG|2|2|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s2-baseline|output/dirg_da_b_v1/target_cases/t2-s2-baseline/result.json|
|DIRG|2|2|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s2-B|output/dirg_da_b_v1/target_cases/t2-s2-B/result.json|
|DIRG|2|2|labels_only|0.0|missing|—|—|
|DIRG|2|2|labels_only|0.1|missing|—|—|
|DIRG|2|2|selection_only|0.0|missing|—|—|
|DIRG|2|2|selection_only|0.1|missing|—|—|
|DIRG|2|2|full|0.0|reusable|runs/dirg_da_b_v1/cases/t2-s2-DA|output/dirg_da_b_v1/target_cases/t2-s2-DA/result.json|
|DIRG|2|2|full|0.1|reusable|runs/dirg_da_b_v1/cases/t2-s2-DA_B|output/dirg_da_b_v1/target_cases/t2-s2-DA_B/result.json|
|DIRG|2|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s3-baseline/result.json|
|DIRG|2|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s3-B/result.json|
|DIRG|2|3|labels_only|0.0|missing|—|—|
|DIRG|2|3|labels_only|0.1|missing|—|—|
|DIRG|2|3|selection_only|0.0|missing|—|—|
|DIRG|2|3|selection_only|0.1|missing|—|—|
|DIRG|2|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s3-DA/result.json|
|DIRG|2|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s3-DA_B/result.json|
|DIRG|2|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s4-baseline/result.json|
|DIRG|2|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s4-B/result.json|
|DIRG|2|4|labels_only|0.0|missing|—|—|
|DIRG|2|4|labels_only|0.1|missing|—|—|
|DIRG|2|4|selection_only|0.0|missing|—|—|
|DIRG|2|4|selection_only|0.1|missing|—|—|
|DIRG|2|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s4-DA/result.json|
|DIRG|2|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t2-s4-DA_B/result.json|
|DIRG|3|0|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s0-baseline|output/dirg_da_b_v1/target_cases/t3-s0-baseline/result.json|
|DIRG|3|0|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s0-B|output/dirg_da_b_v1/target_cases/t3-s0-B/result.json|
|DIRG|3|0|labels_only|0.0|missing|—|—|
|DIRG|3|0|labels_only|0.1|missing|—|—|
|DIRG|3|0|selection_only|0.0|missing|—|—|
|DIRG|3|0|selection_only|0.1|missing|—|—|
|DIRG|3|0|full|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s0-DA|output/dirg_da_b_v1/target_cases/t3-s0-DA/result.json|
|DIRG|3|0|full|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s0-DA_B|output/dirg_da_b_v1/target_cases/t3-s0-DA_B/result.json|
|DIRG|3|1|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s1-baseline|output/dirg_da_b_v1/target_cases/t3-s1-baseline/result.json|
|DIRG|3|1|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s1-B|output/dirg_da_b_v1/target_cases/t3-s1-B/result.json|
|DIRG|3|1|labels_only|0.0|missing|—|—|
|DIRG|3|1|labels_only|0.1|missing|—|—|
|DIRG|3|1|selection_only|0.0|missing|—|—|
|DIRG|3|1|selection_only|0.1|missing|—|—|
|DIRG|3|1|full|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s1-DA|output/dirg_da_b_v1/target_cases/t3-s1-DA/result.json|
|DIRG|3|1|full|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s1-DA_B|output/dirg_da_b_v1/target_cases/t3-s1-DA_B/result.json|
|DIRG|3|2|raw|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s2-baseline|output/dirg_da_b_v1/target_cases/t3-s2-baseline/result.json|
|DIRG|3|2|raw|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s2-B|output/dirg_da_b_v1/target_cases/t3-s2-B/result.json|
|DIRG|3|2|labels_only|0.0|missing|—|—|
|DIRG|3|2|labels_only|0.1|missing|—|—|
|DIRG|3|2|selection_only|0.0|missing|—|—|
|DIRG|3|2|selection_only|0.1|missing|—|—|
|DIRG|3|2|full|0.0|reusable|runs/dirg_da_b_v1/cases/t3-s2-DA|output/dirg_da_b_v1/target_cases/t3-s2-DA/result.json|
|DIRG|3|2|full|0.1|reusable|runs/dirg_da_b_v1/cases/t3-s2-DA_B|output/dirg_da_b_v1/target_cases/t3-s2-DA_B/result.json|
|DIRG|3|3|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s3-baseline/result.json|
|DIRG|3|3|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s3-B/result.json|
|DIRG|3|3|labels_only|0.0|missing|—|—|
|DIRG|3|3|labels_only|0.1|missing|—|—|
|DIRG|3|3|selection_only|0.0|missing|—|—|
|DIRG|3|3|selection_only|0.1|missing|—|—|
|DIRG|3|3|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s3-DA/result.json|
|DIRG|3|3|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s3-DA_B/result.json|
|DIRG|3|4|raw|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-baseline|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s4-baseline/result.json|
|DIRG|3|4|raw|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s4-B/result.json|
|DIRG|3|4|labels_only|0.0|missing|—|—|
|DIRG|3|4|labels_only|0.1|missing|—|—|
|DIRG|3|4|selection_only|0.0|missing|—|—|
|DIRG|3|4|selection_only|0.1|missing|—|—|
|DIRG|3|4|full|0.0|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-DA|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s4-DA/result.json|
|DIRG|3|4|full|0.1|reusable|runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-DA_B|output/da_b_five_seed_followup_v1/target_cases/DIRG-t3-s4-DA_B/result.json|

## 运行与完整性

`D:/paper/.venv/Scripts/python.exe -B D:/paper/output/pc2g_research_audit_20260924/reuse/audit_reuse.py`

读取/校验的旧文件在本轮结束时size/mtime未变：True。脚本只在当前reuse目录写JSON/Markdown；CUDA_VISIBLE_DEVICES=-1；未导入任何训练入口，未调用模型forward、优化器或CUDA初始化。
