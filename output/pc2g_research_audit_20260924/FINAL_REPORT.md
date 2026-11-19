# PC²G 固定研究对象核查：结果报告

生成时间（UTC）：2026-09-26T05:24:36.986625+00:00。输入SHA-256：`b601d28ea5844c601965410e53fd33a65ba6673550685f8f43e7cd96d16e1994`。

**complete=true**；收到 440 行，有效且唯一 440/440 个配置—目标—种子条目。

complete 仅指计划结果矩阵完整且数值校验通过，不表示研究假说通过、数据采集独立、严格配对已审定或创新性得到证明。

## 固定统计口径与解释边界

主指标：干净Accuracy。次要指标：干净Macro-F1、2/4/6/8/10 dB的Accuracy与Macro-F1，及五档噪声等权均值。每类召回率与混淆矩阵完整保存在 summaries.json，召回率另有分种子描述。

每个数据集分开计算：同一优化种子先等权平均四个目标，再对seed 0–4计算均值及样本标准差（ddof=1）。差值在同一目标、同一种子内配对，再按上述顺序汇总。不能把四目标×五种子当成20次独立采集。

配对95%区间为 mean(d_s) ± 2.776445 × SD(d_s)/√5，df=4。这是固定数据、划分、实现和训练协议下的**优化种子描述区间**，不代替独立采集验证，不是经多重比较校正的正式显著性结论；不报告显著性星号或自动通过标志。

所有差值以百分点报告，顺序按预定配置固定，不按结果排名。覆盖范围差值为 all − selected，正值表示全部源样本版本分数较高。种子方向列按正/数值零/负计数，数值零容差为1e−12；它不构成通过门槛。

本轮interaction定义为同一B状态下 full − labels_only − selection_only + raw，区别于旧稿中的DA×B交互，不能混用。四组严格排序不作为pass gate，也不自动建议改参数。

本脚本只分析提交的结果；相同seed标签不等于初始化、数据顺序、辅助历史或扰动状态已核验。数据划分、采集来源、BN/前向一致性及历史复用资格需由主pipeline的独立审计确认。

## 完整性与数值校验

| 实验族 | 计划条目 | 收到行数 | 有效唯一条目 | 缺少条目 |
| --- | --- | --- | --- | --- |
| factorial | 320 | 320 | 320 | 0 |
| coverage | 80 | 80 | 80 | 0 |
| soft_weight | 40 | 40 | 40 | 0 |

统计不读取检查点、不执行训练或推理。仅校验结果字段及混淆矩阵与Accuracy、Macro-F1、召回率的一致性。重复ID或重复设计单元的所有副本均保留在原始行中，但从汇总排除，不择优选取。

## 配置描述：五种子均值 ± 样本标准差

分数单位为%。噪声均值是五档等权平均，不是额外独立样本。

| 数据集 | 配置 | 干净Accuracy | 干净Macro-F1 | 五档噪声Accuracy | 五档噪声Macro-F1 |
| --- | --- | --- | --- | --- | --- |
| PU | factorial/raw/B0/all | 72.571 ± 2.881 | 68.982 ± 2.461 | 60.035 ± 2.379 | 55.249 ± 2.319 |
| PU | factorial/labels_only/B0/all | 73.954 ± 3.577 | 70.565 ± 3.171 | 60.204 ± 3.653 | 55.924 ± 3.761 |
| PU | factorial/selection_only/B0/all | 73.396 ± 2.249 | 69.808 ± 2.308 | 60.335 ± 2.559 | 55.531 ± 2.707 |
| PU | factorial/full/B0/all | 74.523 ± 2.531 | 70.667 ± 2.495 | 60.656 ± 1.491 | 55.863 ± 1.330 |
| PU | factorial/raw/B0.1/all | 73.488 ± 1.869 | 69.960 ± 1.668 | 60.884 ± 2.415 | 55.957 ± 2.273 |
| PU | factorial/labels_only/B0.1/all | 73.633 ± 1.853 | 70.280 ± 1.634 | 60.829 ± 2.588 | 56.126 ± 3.081 |
| PU | factorial/selection_only/B0.1/all | 72.765 ± 3.198 | 69.078 ± 3.097 | 60.279 ± 3.412 | 55.609 ± 3.089 |
| PU | factorial/full/B0.1/all | 76.181 ± 1.109 | 72.542 ± 0.917 | 62.782 ± 2.183 | 58.056 ± 2.153 |
| PU | coverage/full/B0.1/selected_fixed | 74.504 ± 3.180 | 71.077 ± 2.954 | 62.420 ± 2.316 | 57.953 ± 2.203 |
| PU | coverage/full/B0.1/selected_domain_mean | 74.144 ± 0.734 | 70.733 ± 0.497 | 61.742 ± 2.064 | 57.168 ± 1.748 |
| PU | soft_weight/softmatch_weight/B0.1/all | 73.675 ± 1.479 | 70.508 ± 1.128 | 60.667 ± 1.608 | 56.118 ± 1.118 |
| DIRG | factorial/raw/B0/all | 50.304 ± 3.506 | 46.312 ± 3.485 | 36.387 ± 2.995 | 30.248 ± 2.913 |
| DIRG | factorial/labels_only/B0/all | 51.509 ± 2.683 | 47.590 ± 2.871 | 37.248 ± 2.017 | 30.967 ± 1.809 |
| DIRG | factorial/selection_only/B0/all | 50.960 ± 1.698 | 47.135 ± 1.973 | 36.760 ± 2.793 | 30.331 ± 3.277 |
| DIRG | factorial/full/B0/all | 51.388 ± 2.901 | 47.559 ± 3.104 | 36.340 ± 2.353 | 30.090 ± 3.119 |
| DIRG | factorial/raw/B0.1/all | 50.772 ± 2.320 | 46.923 ± 2.355 | 37.046 ± 2.262 | 30.918 ± 2.148 |
| DIRG | factorial/labels_only/B0.1/all | 52.263 ± 3.643 | 48.233 ± 3.722 | 37.107 ± 1.781 | 30.649 ± 1.438 |
| DIRG | factorial/selection_only/B0.1/all | 49.629 ± 2.851 | 45.444 ± 2.801 | 35.806 ± 3.302 | 29.461 ± 3.787 |
| DIRG | factorial/full/B0.1/all | 51.603 ± 1.974 | 47.909 ± 2.399 | 36.397 ± 2.813 | 29.895 ± 3.321 |
| DIRG | coverage/full/B0.1/selected_fixed | 51.205 ± 2.062 | 47.733 ± 2.275 | 36.097 ± 1.798 | 30.034 ± 2.147 |
| DIRG | coverage/full/B0.1/selected_domain_mean | 51.696 ± 2.233 | 47.735 ± 2.456 | 36.827 ± 2.222 | 30.254 ± 2.916 |
| DIRG | soft_weight/softmatch_weight/B0.1/all | 51.612 ± 1.995 | 47.620 ± 2.464 | 35.676 ± 2.453 | 29.852 ± 2.777 |


## 主指标：干净Accuracy的预定配对差

40个数据集内对比全部保留，包括负向结果与不确定区间。均值、SD及区间单位均为百分点。

| 数据集 | 对比（左减右） | 差值均值 ± SD | 种子t95描述区间 | 种子正/零/负 |
| --- | --- | --- | --- | --- |
| PU | B=0: full − labels_only | 0.569 ± 3.293 | [-3.520, 4.658] | 4/0/1 |
| PU | B=0: full − selection_only | 1.127 ± 1.593 | [-0.851, 3.105] | 3/0/2 |
| PU | B=0: full − raw | 1.952 ± 1.471 | [0.125, 3.779] | 4/0/1 |
| PU | B=0: labels_only − raw | 1.383 ± 2.271 | [-1.436, 4.203] | 4/0/1 |
| PU | B=0: selection_only − raw | 0.825 ± 1.620 | [-1.187, 2.837] | 4/0/1 |
| PU | B=0: full − labels_only − selection_only + raw | -0.256 ± 3.439 | [-4.526, 4.014] | 3/0/2 |
| PU | B=0.1: full − labels_only | 2.548 ± 1.347 | [0.875, 4.220] | 5/0/0 |
| PU | B=0.1: full − selection_only | 3.417 ± 2.377 | [0.465, 6.369] | 5/0/0 |
| PU | B=0.1: full − raw | 2.694 ± 1.504 | [0.826, 4.562] | 5/0/0 |
| PU | B=0.1: labels_only − raw | 0.146 ± 2.402 | [-2.836, 3.128] | 2/0/3 |
| PU | B=0.1: selection_only − raw | -0.723 ± 2.102 | [-3.333, 1.887] | 1/0/4 |
| PU | B=0.1: full − labels_only − selection_only + raw | 3.271 ± 3.199 | [-0.701, 7.243] | 4/0/1 |
| PU | raw: B=0.1 − B=0 | 0.917 ± 1.609 | [-1.081, 2.914] | 4/0/1 |
| PU | labels_only: B=0.1 − B=0 | -0.321 ± 3.289 | [-4.405, 3.763] | 4/0/1 |
| PU | selection_only: B=0.1 − B=0 | -0.631 ± 1.904 | [-2.996, 1.733] | 2/0/3 |
| PU | full: B=0.1 − B=0 | 1.658 ± 1.561 | [-0.279, 3.596] | 4/0/1 |
| PU | all − selected_fixed (full, B=0.1) | 1.677 ± 2.468 | [-1.387, 4.741] | 4/0/1 |
| PU | all − selected_domain_mean (full, B=0.1) | 2.037 ± 1.732 | [-0.113, 4.188] | 5/0/0 |
| PU | softmatch_weight − full (B=0.1) | -2.506 ± 0.763 | [-3.453, -1.559] | 0/0/5 |
| PU | softmatch_weight − selection_only (B=0.1) | 0.910 ± 1.748 | [-1.260, 3.080] | 2/0/3 |
| DIRG | B=0: full − labels_only | -0.121 ± 2.314 | [-2.994, 2.753] | 3/0/2 |
| DIRG | B=0: full − selection_only | 0.429 ± 2.085 | [-2.160, 3.017] | 4/0/1 |
| DIRG | B=0: full − raw | 1.085 ± 2.264 | [-1.727, 3.896] | 3/0/2 |
| DIRG | B=0: labels_only − raw | 1.205 ± 2.779 | [-2.245, 4.656] | 4/0/1 |
| DIRG | B=0: selection_only − raw | 0.656 ± 3.097 | [-3.189, 4.502] | 3/0/2 |
| DIRG | B=0: full − labels_only − selection_only + raw | -0.777 ± 4.436 | [-6.284, 4.731] | 3/0/2 |
| DIRG | B=0.1: full − labels_only | -0.661 ± 3.337 | [-4.804, 3.483] | 2/0/3 |
| DIRG | B=0.1: full − selection_only | 1.973 ± 2.938 | [-1.674, 5.621] | 4/0/1 |
| DIRG | B=0.1: full − raw | 0.830 ± 1.730 | [-1.318, 2.979] | 2/0/3 |
| DIRG | B=0.1: labels_only − raw | 1.491 ± 1.671 | [-0.584, 3.566] | 4/0/1 |
| DIRG | B=0.1: selection_only − raw | -1.143 ± 1.312 | [-2.771, 0.486] | 1/0/4 |
| DIRG | B=0.1: full − labels_only − selection_only + raw | 0.482 ± 4.462 | [-5.058, 6.022] | 2/0/3 |
| DIRG | raw: B=0.1 − B=0 | 0.469 ± 2.752 | [-2.948, 3.886] | 3/0/2 |
| DIRG | labels_only: B=0.1 − B=0 | 0.754 ± 1.304 | [-0.865, 2.374] | 3/0/2 |
| DIRG | selection_only: B=0.1 − B=0 | -1.330 ± 1.775 | [-3.534, 0.873] | 1/0/4 |
| DIRG | full: B=0.1 − B=0 | 0.214 ± 2.598 | [-3.012, 3.441] | 2/0/3 |
| DIRG | all − selected_fixed (full, B=0.1) | 0.397 ± 1.747 | [-1.772, 2.566] | 4/0/1 |
| DIRG | all − selected_domain_mean (full, B=0.1) | -0.094 ± 2.899 | [-3.693, 3.505] | 4/0/1 |
| DIRG | softmatch_weight − full (B=0.1) | 0.009 ± 2.022 | [-2.501, 2.519] | 1/0/4 |
| DIRG | softmatch_weight − selection_only (B=0.1) | 1.982 ± 1.641 | [-0.055, 4.019] | 5/0/0 |


## 次要指标：完整保留，不按结果选择噪声档位

<details>
<summary>PU：各配置的逐噪声分数</summary>

| 配置 | SNR/dB | Accuracy/% | Macro-F1/% |
| --- | --- | --- | --- |
| factorial/raw/B0/all | 2 | 48.429 ± 1.318 | 42.469 ± 1.378 |
| factorial/raw/B0/all | 4 | 56.333 ± 2.280 | 51.116 ± 2.292 |
| factorial/raw/B0/all | 6 | 62.096 ± 2.852 | 57.482 ± 2.733 |
| factorial/raw/B0/all | 8 | 65.519 ± 3.203 | 61.276 ± 3.235 |
| factorial/raw/B0/all | 10 | 67.796 ± 3.463 | 63.899 ± 3.471 |
| factorial/labels_only/B0/all | 2 | 47.135 ± 4.156 | 41.545 ± 4.650 |
| factorial/labels_only/B0/all | 4 | 55.319 ± 4.495 | 50.697 ± 4.974 |
| factorial/labels_only/B0/all | 6 | 62.131 ± 4.304 | 58.097 ± 4.492 |
| factorial/labels_only/B0/all | 8 | 66.825 ± 4.049 | 63.139 ± 4.085 |
| factorial/labels_only/B0/all | 10 | 69.610 ± 3.946 | 66.140 ± 3.839 |
| factorial/selection_only/B0/all | 2 | 48.585 ± 2.489 | 42.435 ± 2.911 |
| factorial/selection_only/B0/all | 4 | 56.015 ± 2.451 | 50.512 ± 2.674 |
| factorial/selection_only/B0/all | 6 | 62.019 ± 2.724 | 57.414 ± 2.849 |
| factorial/selection_only/B0/all | 8 | 66.244 ± 2.870 | 62.166 ± 2.908 |
| factorial/selection_only/B0/all | 10 | 68.810 ± 2.786 | 65.128 ± 2.755 |
| factorial/full/B0/all | 2 | 47.469 ± 2.800 | 41.590 ± 3.342 |
| factorial/full/B0/all | 4 | 56.135 ± 2.009 | 50.804 ± 2.065 |
| factorial/full/B0/all | 6 | 62.604 ± 1.286 | 57.915 ± 1.004 |
| factorial/full/B0/all | 8 | 67.102 ± 1.576 | 62.889 ± 1.200 |
| factorial/full/B0/all | 10 | 69.971 ± 1.989 | 66.118 ± 1.702 |
| factorial/raw/B0.1/all | 2 | 49.098 ± 2.675 | 42.969 ± 2.726 |
| factorial/raw/B0.1/all | 4 | 57.100 ± 2.596 | 51.783 ± 2.579 |
| factorial/raw/B0.1/all | 6 | 62.804 ± 2.899 | 57.946 ± 2.711 |
| factorial/raw/B0.1/all | 8 | 66.452 ± 2.842 | 62.071 ± 2.628 |
| factorial/raw/B0.1/all | 10 | 68.967 ± 2.617 | 65.013 ± 2.366 |
| factorial/labels_only/B0.1/all | 2 | 48.617 ± 3.562 | 42.338 ± 4.271 |
| factorial/labels_only/B0.1/all | 4 | 56.365 ± 3.448 | 51.207 ± 4.274 |
| factorial/labels_only/B0.1/all | 6 | 62.933 ± 2.683 | 58.489 ± 3.207 |
| factorial/labels_only/B0.1/all | 8 | 66.950 ± 2.418 | 62.966 ± 2.630 |
| factorial/labels_only/B0.1/all | 10 | 69.279 ± 2.286 | 65.632 ± 2.363 |
| factorial/selection_only/B0.1/all | 2 | 48.402 ± 3.633 | 42.420 ± 3.417 |
| factorial/selection_only/B0.1/all | 4 | 56.102 ± 3.663 | 50.984 ± 3.675 |
| factorial/selection_only/B0.1/all | 6 | 62.202 ± 3.862 | 57.783 ± 3.614 |
| factorial/selection_only/B0.1/all | 8 | 66.125 ± 3.601 | 62.108 ± 3.037 |
| factorial/selection_only/B0.1/all | 10 | 68.562 ± 3.311 | 64.750 ± 2.761 |
| factorial/full/B0.1/all | 2 | 49.681 ± 2.676 | 43.799 ± 3.099 |
| factorial/full/B0.1/all | 4 | 58.360 ± 2.722 | 53.088 ± 2.822 |
| factorial/full/B0.1/all | 6 | 64.929 ± 2.421 | 60.306 ± 2.297 |
| factorial/full/B0.1/all | 8 | 69.131 ± 2.065 | 65.061 ± 2.015 |
| factorial/full/B0.1/all | 10 | 71.810 ± 1.962 | 68.025 ± 1.775 |
| coverage/full/B0.1/selected_fixed | 2 | 49.938 ± 3.685 | 43.794 ± 3.959 |
| coverage/full/B0.1/selected_fixed | 4 | 57.700 ± 1.980 | 52.683 ± 2.050 |
| coverage/full/B0.1/selected_fixed | 6 | 64.571 ± 2.590 | 60.495 ± 2.423 |
| coverage/full/B0.1/selected_fixed | 8 | 68.783 ± 3.334 | 65.122 ± 3.207 |
| coverage/full/B0.1/selected_fixed | 10 | 71.106 ± 3.684 | 67.672 ± 3.496 |
| coverage/full/B0.1/selected_domain_mean | 2 | 48.977 ± 4.109 | 43.197 ± 4.234 |
| coverage/full/B0.1/selected_domain_mean | 4 | 57.258 ± 2.829 | 52.089 ± 2.429 |
| coverage/full/B0.1/selected_domain_mean | 6 | 63.852 ± 2.056 | 59.476 ± 1.980 |
| coverage/full/B0.1/selected_domain_mean | 8 | 68.133 ± 1.925 | 64.226 ± 1.889 |
| coverage/full/B0.1/selected_domain_mean | 10 | 70.487 ± 1.604 | 66.851 ± 1.529 |
| soft_weight/softmatch_weight/B0.1/all | 2 | 49.638 ± 2.299 | 43.510 ± 2.162 |
| soft_weight/softmatch_weight/B0.1/all | 4 | 56.867 ± 1.830 | 51.521 ± 1.520 |
| soft_weight/softmatch_weight/B0.1/all | 6 | 62.163 ± 2.004 | 57.798 ± 1.508 |
| soft_weight/softmatch_weight/B0.1/all | 8 | 65.971 ± 1.853 | 62.292 ± 1.172 |
| soft_weight/softmatch_weight/B0.1/all | 10 | 68.696 ± 1.756 | 65.470 ± 1.020 |

</details>

<details>
<summary>PU：Macro-F1与全部噪声的配对差</summary>

| 对比（左减右） | 条件 | 指标 | 差值均值 ± SD/pp | 种子t95区间/pp | 正/零/负 |
| --- | --- | --- | --- | --- | --- |
| B=0: full − labels_only | clean | macro_f1 | 0.103 ± 2.576 | [-3.096, 3.301] | 4/0/1 |
| B=0: full − labels_only | 2 | accuracy | 0.333 ± 3.876 | [-4.479, 5.146] | 3/0/2 |
| B=0: full − labels_only | 2 | macro_f1 | 0.044 ± 4.301 | [-5.296, 5.384] | 3/0/2 |
| B=0: full − labels_only | 4 | accuracy | 0.817 ± 4.320 | [-4.547, 6.181] | 3/0/2 |
| B=0: full − labels_only | 4 | macro_f1 | 0.107 ± 5.221 | [-6.375, 6.590] | 2/0/3 |
| B=0: full − labels_only | 6 | accuracy | 0.473 ± 3.997 | [-4.490, 5.436] | 2/0/3 |
| B=0: full − labels_only | 6 | macro_f1 | -0.181 ± 4.695 | [-6.011, 5.648] | 2/0/3 |
| B=0: full − labels_only | 8 | accuracy | 0.277 ± 3.802 | [-4.444, 4.998] | 4/0/1 |
| B=0: full − labels_only | 8 | macro_f1 | -0.250 ± 3.948 | [-5.153, 4.652] | 3/0/2 |
| B=0: full − labels_only | 10 | accuracy | 0.360 ± 3.862 | [-4.435, 5.156] | 4/0/1 |
| B=0: full − labels_only | 10 | macro_f1 | -0.022 ± 3.609 | [-4.504, 4.459] | 4/0/1 |
| B=0: full − labels_only | noise_mean | accuracy | 0.452 ± 3.177 | [-3.493, 4.397] | 2/0/3 |
| B=0: full − labels_only | noise_mean | macro_f1 | -0.060 ± 3.607 | [-4.540, 4.419] | 2/0/3 |
| B=0: full − selection_only | clean | macro_f1 | 0.859 ± 1.522 | [-1.031, 2.748] | 4/0/1 |
| B=0: full − selection_only | 2 | accuracy | -1.117 ± 2.529 | [-4.257, 2.024] | 1/0/4 |
| B=0: full − selection_only | 2 | macro_f1 | -0.846 ± 2.900 | [-4.447, 2.755] | 2/0/3 |
| B=0: full − selection_only | 4 | accuracy | 0.121 ± 2.648 | [-3.167, 3.409] | 3/0/2 |
| B=0: full − selection_only | 4 | macro_f1 | 0.292 ± 3.124 | [-3.587, 4.171] | 3/0/2 |
| B=0: full − selection_only | 6 | accuracy | 0.585 ± 2.148 | [-2.082, 3.252] | 3/0/2 |
| B=0: full − selection_only | 6 | macro_f1 | 0.502 ± 2.621 | [-2.753, 3.756] | 2/0/3 |
| B=0: full − selection_only | 8 | accuracy | 0.858 ± 1.834 | [-1.419, 3.135] | 3/0/2 |
| B=0: full − selection_only | 8 | macro_f1 | 0.722 ± 2.206 | [-2.017, 3.461] | 3/0/2 |
| B=0: full − selection_only | 10 | accuracy | 1.160 ± 1.778 | [-1.047, 3.368] | 4/0/1 |
| B=0: full − selection_only | 10 | macro_f1 | 0.990 ± 1.992 | [-1.483, 3.463] | 3/0/2 |
| B=0: full − selection_only | noise_mean | accuracy | 0.322 ± 1.950 | [-2.100, 2.743] | 3/0/2 |
| B=0: full − selection_only | noise_mean | macro_f1 | 0.332 ± 2.324 | [-2.554, 3.218] | 3/0/2 |
| B=0: full − raw | clean | macro_f1 | 1.686 ± 0.992 | [0.454, 2.917] | 5/0/0 |
| B=0: full − raw | 2 | accuracy | -0.960 ± 3.249 | [-4.994, 3.074] | 3/0/2 |
| B=0: full − raw | 2 | macro_f1 | -0.880 ± 3.639 | [-5.398, 3.639] | 2/0/3 |
| B=0: full − raw | 4 | accuracy | -0.198 ± 3.602 | [-4.670, 4.274] | 1/0/4 |
| B=0: full − raw | 4 | macro_f1 | -0.312 ± 3.946 | [-5.212, 4.588] | 1/0/4 |
| B=0: full − raw | 6 | accuracy | 0.508 ± 2.838 | [-3.016, 4.032] | 2/0/3 |
| B=0: full − raw | 6 | macro_f1 | 0.433 ± 3.068 | [-3.376, 4.243] | 2/0/3 |
| B=0: full − raw | 8 | accuracy | 1.583 ± 2.404 | [-1.401, 4.568] | 4/0/1 |
| B=0: full − raw | 8 | macro_f1 | 1.612 ± 2.585 | [-1.598, 4.823] | 4/0/1 |
| B=0: full − raw | 10 | accuracy | 2.175 ± 2.288 | [-0.667, 5.017] | 4/0/1 |
| B=0: full − raw | 10 | macro_f1 | 2.219 ± 2.226 | [-0.545, 4.983] | 4/0/1 |
| B=0: full − raw | noise_mean | accuracy | 0.622 ± 2.417 | [-2.380, 3.623] | 3/0/2 |
| B=0: full − raw | noise_mean | macro_f1 | 0.615 ± 2.603 | [-2.617, 3.846] | 3/0/2 |
| B=0: labels_only − raw | clean | macro_f1 | 1.583 ± 2.068 | [-0.985, 4.151] | 3/0/2 |
| B=0: labels_only − raw | 2 | accuracy | -1.294 ± 3.728 | [-5.922, 3.335] | 2/0/3 |
| B=0: labels_only − raw | 2 | macro_f1 | -0.924 ± 4.120 | [-6.039, 4.192] | 3/0/2 |
| B=0: labels_only − raw | 4 | accuracy | -1.015 ± 3.217 | [-5.009, 2.979] | 3/0/2 |
| B=0: labels_only − raw | 4 | macro_f1 | -0.420 ± 3.897 | [-5.259, 4.420] | 3/0/2 |
| B=0: labels_only − raw | 6 | accuracy | 0.035 ± 2.049 | [-2.508, 2.579] | 4/0/1 |
| B=0: labels_only − raw | 6 | macro_f1 | 0.615 ± 2.334 | [-2.283, 3.512] | 4/0/1 |
| B=0: labels_only − raw | 8 | accuracy | 1.306 ± 1.861 | [-1.004, 3.617] | 5/0/0 |
| B=0: labels_only − raw | 8 | macro_f1 | 1.863 ± 1.986 | [-0.604, 4.329] | 5/0/0 |
| B=0: labels_only − raw | 10 | accuracy | 1.815 ± 2.241 | [-0.968, 4.597] | 4/0/1 |
| B=0: labels_only − raw | 10 | macro_f1 | 2.242 ± 2.367 | [-0.697, 5.180] | 4/0/1 |
| B=0: labels_only − raw | noise_mean | accuracy | 0.170 ± 1.827 | [-2.100, 2.439] | 4/0/1 |
| B=0: labels_only − raw | noise_mean | macro_f1 | 0.675 ± 2.059 | [-1.882, 3.232] | 4/0/1 |
| B=0: selection_only − raw | clean | macro_f1 | 0.827 ± 1.874 | [-1.501, 3.154] | 4/0/1 |
| B=0: selection_only − raw | 2 | accuracy | 0.156 ± 2.462 | [-2.901, 3.214] | 4/0/1 |
| B=0: selection_only − raw | 2 | macro_f1 | -0.034 ± 2.693 | [-3.378, 3.310] | 4/0/1 |
| B=0: selection_only − raw | 4 | accuracy | -0.319 ± 1.931 | [-2.717, 2.079] | 2/0/3 |
| B=0: selection_only − raw | 4 | macro_f1 | -0.605 ± 2.364 | [-3.540, 2.331] | 2/0/3 |
| B=0: selection_only − raw | 6 | accuracy | -0.077 ± 1.442 | [-1.867, 1.713] | 2/0/3 |
| B=0: selection_only − raw | 6 | macro_f1 | -0.068 ± 1.831 | [-2.342, 2.205] | 2/0/3 |
| B=0: selection_only − raw | 8 | accuracy | 0.725 ± 1.251 | [-0.828, 2.278] | 4/0/1 |
| B=0: selection_only − raw | 8 | macro_f1 | 0.890 ± 1.651 | [-1.160, 2.940] | 3/0/2 |
| B=0: selection_only − raw | 10 | accuracy | 1.015 ± 1.491 | [-0.836, 2.865] | 4/0/1 |
| B=0: selection_only − raw | 10 | macro_f1 | 1.229 ± 1.864 | [-1.086, 3.544] | 4/0/1 |
| B=0: selection_only − raw | noise_mean | accuracy | 0.300 ± 1.380 | [-1.414, 2.014] | 3/0/2 |
| B=0: selection_only − raw | noise_mean | macro_f1 | 0.282 ± 1.784 | [-1.933, 2.498] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | clean | macro_f1 | -0.724 ± 3.075 | [-4.542, 3.094] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 2 | accuracy | 0.177 ± 5.253 | [-6.345, 6.699] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 2 | macro_f1 | 0.078 ± 5.850 | [-7.185, 7.341] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 4 | accuracy | 1.135 ± 4.645 | [-4.633, 6.904] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 4 | macro_f1 | 0.712 ± 5.916 | [-6.634, 8.058] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 6 | accuracy | 0.550 ± 3.734 | [-4.086, 5.186] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 6 | macro_f1 | -0.113 ± 4.676 | [-5.919, 5.692] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 8 | accuracy | -0.448 ± 3.321 | [-4.572, 3.676] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 8 | macro_f1 | -1.140 ± 3.608 | [-5.621, 3.340] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 10 | accuracy | -0.654 ± 3.477 | [-4.971, 3.663] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 10 | macro_f1 | -1.251 ± 3.530 | [-5.634, 3.132] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | noise_mean | accuracy | 0.152 ± 3.281 | [-3.922, 4.226] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | noise_mean | macro_f1 | -0.343 ± 3.989 | [-5.296, 4.611] | 2/0/3 |
| B=0.1: full − labels_only | clean | macro_f1 | 2.262 ± 1.262 | [0.696, 3.829] | 5/0/0 |
| B=0.1: full − labels_only | 2 | accuracy | 1.065 ± 2.546 | [-2.097, 4.226] | 4/0/1 |
| B=0.1: full − labels_only | 2 | macro_f1 | 1.461 ± 2.554 | [-1.710, 4.632] | 4/0/1 |
| B=0.1: full − labels_only | 4 | accuracy | 1.996 ± 2.626 | [-1.265, 5.256] | 4/0/1 |
| B=0.1: full − labels_only | 4 | macro_f1 | 1.881 ± 2.840 | [-1.646, 5.407] | 4/0/1 |
| B=0.1: full − labels_only | 6 | accuracy | 1.996 ± 2.121 | [-0.637, 4.629] | 4/0/1 |
| B=0.1: full − labels_only | 6 | macro_f1 | 1.817 ± 2.392 | [-1.153, 4.787] | 4/0/1 |
| B=0.1: full − labels_only | 8 | accuracy | 2.181 ± 1.347 | [0.509, 3.853] | 5/0/0 |
| B=0.1: full − labels_only | 8 | macro_f1 | 2.095 ± 1.477 | [0.261, 3.930] | 4/0/1 |
| B=0.1: full − labels_only | 10 | accuracy | 2.531 ± 1.229 | [1.006, 4.057] | 5/0/0 |
| B=0.1: full − labels_only | 10 | macro_f1 | 2.392 ± 1.196 | [0.908, 3.877] | 5/0/0 |
| B=0.1: full − labels_only | noise_mean | accuracy | 1.954 ± 1.867 | [-0.365, 4.272] | 4/0/1 |
| B=0.1: full − labels_only | noise_mean | macro_f1 | 1.929 ± 1.928 | [-0.465, 4.323] | 4/0/1 |
| B=0.1: full − selection_only | clean | macro_f1 | 3.464 ± 2.494 | [0.367, 6.561] | 5/0/0 |
| B=0.1: full − selection_only | 2 | accuracy | 1.279 ± 2.460 | [-1.776, 4.334] | 3/0/2 |
| B=0.1: full − selection_only | 2 | macro_f1 | 1.379 ± 2.700 | [-1.974, 4.731] | 3/0/2 |
| B=0.1: full − selection_only | 4 | accuracy | 2.258 ± 2.802 | [-1.221, 5.737] | 3/0/2 |
| B=0.1: full − selection_only | 4 | macro_f1 | 2.104 ± 3.524 | [-2.271, 6.479] | 3/0/2 |
| B=0.1: full − selection_only | 6 | accuracy | 2.727 ± 2.853 | [-0.816, 6.270] | 4/0/1 |
| B=0.1: full − selection_only | 6 | macro_f1 | 2.523 ± 3.162 | [-1.404, 6.449] | 4/0/1 |
| B=0.1: full − selection_only | 8 | accuracy | 3.006 ± 2.372 | [0.061, 5.952] | 5/0/0 |
| B=0.1: full − selection_only | 8 | macro_f1 | 2.953 ± 2.276 | [0.127, 5.779] | 5/0/0 |
| B=0.1: full − selection_only | 10 | accuracy | 3.248 ± 1.822 | [0.986, 5.510] | 5/0/0 |
| B=0.1: full − selection_only | 10 | macro_f1 | 3.275 ± 1.566 | [1.331, 5.219] | 5/0/0 |
| B=0.1: full − selection_only | noise_mean | accuracy | 2.504 ± 2.392 | [-0.466, 5.474] | 4/0/1 |
| B=0.1: full − selection_only | noise_mean | macro_f1 | 2.447 ± 2.568 | [-0.742, 5.635] | 4/0/1 |
| B=0.1: full − raw | clean | macro_f1 | 2.582 ± 1.382 | [0.866, 4.298] | 5/0/0 |
| B=0.1: full − raw | 2 | accuracy | 0.583 ± 0.719 | [-0.310, 1.476] | 4/0/1 |
| B=0.1: full − raw | 2 | macro_f1 | 0.830 ± 1.220 | [-0.685, 2.344] | 3/0/2 |
| B=0.1: full − raw | 4 | accuracy | 1.260 ± 1.027 | [-0.015, 2.536] | 5/0/0 |
| B=0.1: full − raw | 4 | macro_f1 | 1.304 ± 1.549 | [-0.620, 3.228] | 4/0/1 |
| B=0.1: full − raw | 6 | accuracy | 2.125 ± 1.096 | [0.764, 3.486] | 5/0/0 |
| B=0.1: full − raw | 6 | macro_f1 | 2.359 ± 1.211 | [0.855, 3.863] | 5/0/0 |
| B=0.1: full − raw | 8 | accuracy | 2.679 ± 1.393 | [0.950, 4.409] | 5/0/0 |
| B=0.1: full − raw | 8 | macro_f1 | 2.990 ± 1.479 | [1.154, 4.827] | 5/0/0 |
| B=0.1: full − raw | 10 | accuracy | 2.844 ± 1.538 | [0.933, 4.754] | 5/0/0 |
| B=0.1: full − raw | 10 | macro_f1 | 3.012 ± 1.458 | [1.201, 4.823] | 5/0/0 |
| B=0.1: full − raw | noise_mean | accuracy | 1.898 ± 1.060 | [0.582, 3.215] | 5/0/0 |
| B=0.1: full − raw | noise_mean | macro_f1 | 2.099 ± 1.277 | [0.514, 3.685] | 5/0/0 |
| B=0.1: labels_only − raw | clean | macro_f1 | 0.320 ± 2.175 | [-2.381, 3.021] | 2/0/3 |
| B=0.1: labels_only − raw | 2 | accuracy | -0.481 ± 3.074 | [-4.298, 3.335] | 1/0/4 |
| B=0.1: labels_only − raw | 2 | macro_f1 | -0.631 ± 3.565 | [-5.058, 3.796] | 1/0/4 |
| B=0.1: labels_only − raw | 4 | accuracy | -0.735 ± 3.299 | [-4.832, 3.361] | 1/0/4 |
| B=0.1: labels_only − raw | 4 | macro_f1 | -0.576 ± 3.874 | [-5.387, 4.234] | 1/0/4 |
| B=0.1: labels_only − raw | 6 | accuracy | 0.129 ± 2.551 | [-3.038, 3.297] | 2/0/3 |
| B=0.1: labels_only − raw | 6 | macro_f1 | 0.542 ± 2.960 | [-3.133, 4.218] | 2/0/3 |
| B=0.1: labels_only − raw | 8 | accuracy | 0.498 ± 2.089 | [-2.096, 3.092] | 2/0/3 |
| B=0.1: labels_only − raw | 8 | macro_f1 | 0.895 ± 2.547 | [-2.268, 4.057] | 2/0/3 |
| B=0.1: labels_only − raw | 10 | accuracy | 0.313 ± 2.191 | [-2.408, 3.033] | 2/0/3 |
| B=0.1: labels_only − raw | 10 | macro_f1 | 0.620 ± 2.410 | [-2.373, 3.612] | 2/0/3 |
| B=0.1: labels_only − raw | noise_mean | accuracy | -0.055 ± 2.453 | [-3.101, 2.990] | 2/0/3 |
| B=0.1: labels_only − raw | noise_mean | macro_f1 | 0.170 ± 2.888 | [-3.416, 3.756] | 2/0/3 |
| B=0.1: selection_only − raw | clean | macro_f1 | -0.882 ± 1.956 | [-3.311, 1.547] | 1/0/4 |
| B=0.1: selection_only − raw | 2 | accuracy | -0.696 ± 1.826 | [-2.963, 1.572] | 2/0/3 |
| B=0.1: selection_only − raw | 2 | macro_f1 | -0.549 ± 1.724 | [-2.690, 1.591] | 2/0/3 |
| B=0.1: selection_only − raw | 4 | accuracy | -0.998 ± 1.944 | [-3.412, 1.416] | 2/0/3 |
| B=0.1: selection_only − raw | 4 | macro_f1 | -0.799 ± 2.357 | [-3.726, 2.127] | 2/0/3 |
| B=0.1: selection_only − raw | 6 | accuracy | -0.602 ± 1.919 | [-2.985, 1.780] | 2/0/3 |
| B=0.1: selection_only − raw | 6 | macro_f1 | -0.163 ± 2.176 | [-2.865, 2.538] | 2/0/3 |
| B=0.1: selection_only − raw | 8 | accuracy | -0.327 ± 1.027 | [-1.602, 0.948] | 2/0/3 |
| B=0.1: selection_only − raw | 8 | macro_f1 | 0.037 ± 0.861 | [-1.033, 1.107] | 2/0/3 |
| B=0.1: selection_only − raw | 10 | accuracy | -0.404 ± 0.870 | [-1.485, 0.676] | 2/0/3 |
| B=0.1: selection_only − raw | 10 | macro_f1 | -0.263 ± 0.619 | [-1.032, 0.505] | 2/0/3 |
| B=0.1: selection_only − raw | noise_mean | accuracy | -0.605 ± 1.349 | [-2.280, 1.070] | 2/0/3 |
| B=0.1: selection_only − raw | noise_mean | macro_f1 | -0.348 ± 1.376 | [-2.057, 1.362] | 2/0/3 |
| B=0.1: full − labels_only − selection_only + raw | clean | macro_f1 | 3.144 ± 2.962 | [-0.534, 6.822] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 2 | accuracy | 1.760 ± 2.636 | [-1.512, 5.033] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 2 | macro_f1 | 2.010 ± 2.879 | [-1.565, 5.585] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 4 | accuracy | 2.994 ± 2.988 | [-0.717, 6.704] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 4 | macro_f1 | 2.680 ± 3.736 | [-1.959, 7.319] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 6 | accuracy | 2.598 ± 2.389 | [-0.369, 5.565] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 6 | macro_f1 | 1.980 ± 2.915 | [-1.639, 5.600] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 8 | accuracy | 2.508 ± 1.176 | [1.048, 3.969] | 5/0/0 |
| B=0.1: full − labels_only − selection_only + raw | 8 | macro_f1 | 2.058 ± 1.493 | [0.204, 3.913] | 5/0/0 |
| B=0.1: full − labels_only − selection_only + raw | 10 | accuracy | 2.935 ± 1.221 | [1.419, 4.451] | 5/0/0 |
| B=0.1: full − labels_only − selection_only + raw | 10 | macro_f1 | 2.655 ± 1.373 | [0.951, 4.360] | 5/0/0 |
| B=0.1: full − labels_only − selection_only + raw | noise_mean | accuracy | 2.559 ± 1.861 | [0.249, 4.870] | 5/0/0 |
| B=0.1: full − labels_only − selection_only + raw | noise_mean | macro_f1 | 2.277 ± 2.181 | [-0.432, 4.985] | 4/0/1 |
| raw: B=0.1 − B=0 | clean | macro_f1 | 0.979 ± 1.214 | [-0.529, 2.486] | 4/0/1 |
| raw: B=0.1 − B=0 | 2 | accuracy | 0.669 ± 2.162 | [-2.016, 3.353] | 4/0/1 |
| raw: B=0.1 − B=0 | 2 | macro_f1 | 0.500 ± 2.249 | [-2.293, 3.293] | 4/0/1 |
| raw: B=0.1 − B=0 | 4 | accuracy | 0.767 ± 1.505 | [-1.101, 2.635] | 3/0/2 |
| raw: B=0.1 − B=0 | 4 | macro_f1 | 0.667 ± 1.650 | [-1.382, 2.716] | 3/0/2 |
| raw: B=0.1 − B=0 | 6 | accuracy | 0.708 ± 0.726 | [-0.193, 1.610] | 3/0/2 |
| raw: B=0.1 − B=0 | 6 | macro_f1 | 0.464 ± 0.693 | [-0.397, 1.325] | 4/0/1 |
| raw: B=0.1 − B=0 | 8 | accuracy | 0.933 ± 0.585 | [0.207, 1.659] | 4/0/1 |
| raw: B=0.1 − B=0 | 8 | macro_f1 | 0.795 ± 0.829 | [-0.235, 1.824] | 4/0/1 |
| raw: B=0.1 − B=0 | 10 | accuracy | 1.171 ± 1.295 | [-0.437, 2.779] | 4/0/1 |
| raw: B=0.1 − B=0 | 10 | macro_f1 | 1.114 ± 1.495 | [-0.743, 2.971] | 4/0/1 |
| raw: B=0.1 − B=0 | noise_mean | accuracy | 0.850 ± 0.662 | [0.027, 1.672] | 4/0/1 |
| raw: B=0.1 − B=0 | noise_mean | macro_f1 | 0.708 ± 0.628 | [-0.072, 1.488] | 5/0/0 |
| labels_only: B=0.1 − B=0 | clean | macro_f1 | -0.285 ± 3.215 | [-4.277, 3.708] | 4/0/1 |
| labels_only: B=0.1 − B=0 | 2 | accuracy | 1.481 ± 3.944 | [-3.416, 6.379] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 2 | macro_f1 | 0.793 ± 4.150 | [-4.360, 5.946] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 4 | accuracy | 1.046 ± 3.912 | [-3.812, 5.903] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 4 | macro_f1 | 0.510 ± 4.254 | [-4.771, 5.792] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 6 | accuracy | 0.802 ± 3.401 | [-3.421, 5.025] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 6 | macro_f1 | 0.392 ± 3.890 | [-4.439, 5.222] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 8 | accuracy | 0.125 ± 3.080 | [-3.699, 3.949] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 8 | macro_f1 | -0.173 ± 3.623 | [-4.671, 4.325] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 10 | accuracy | -0.331 ± 3.174 | [-4.272, 3.610] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 10 | macro_f1 | -0.508 ± 3.509 | [-4.865, 3.849] | 2/0/3 |
| labels_only: B=0.1 − B=0 | noise_mean | accuracy | 0.625 ± 3.082 | [-3.202, 4.451] | 3/0/2 |
| labels_only: B=0.1 − B=0 | noise_mean | macro_f1 | 0.203 ± 3.423 | [-4.047, 4.453] | 3/0/2 |
| selection_only: B=0.1 − B=0 | clean | macro_f1 | -0.730 ± 2.221 | [-3.488, 2.028] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 2 | accuracy | -0.183 ± 1.457 | [-1.992, 1.625] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 2 | macro_f1 | -0.015 ± 1.400 | [-1.753, 1.723] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 4 | accuracy | 0.087 ± 1.572 | [-1.864, 2.039] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 4 | macro_f1 | 0.472 ± 1.716 | [-1.658, 2.603] | 4/0/1 |
| selection_only: B=0.1 − B=0 | 6 | accuracy | 0.183 ± 1.838 | [-2.099, 2.466] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 6 | macro_f1 | 0.369 ± 2.092 | [-2.228, 2.967] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 8 | accuracy | -0.119 ± 1.570 | [-2.068, 1.830] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 8 | macro_f1 | -0.058 ± 1.588 | [-2.031, 1.914] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 10 | accuracy | -0.248 ± 1.271 | [-1.826, 1.330] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 10 | macro_f1 | -0.378 ± 1.317 | [-2.013, 1.257] | 2/0/3 |
| selection_only: B=0.1 − B=0 | noise_mean | accuracy | -0.056 ± 1.359 | [-1.743, 1.632] | 3/0/2 |
| selection_only: B=0.1 − B=0 | noise_mean | macro_f1 | 0.078 ± 1.438 | [-1.707, 1.863] | 3/0/2 |
| full: B=0.1 − B=0 | clean | macro_f1 | 1.875 ± 1.799 | [-0.358, 4.108] | 4/0/1 |
| full: B=0.1 − B=0 | 2 | accuracy | 2.213 ± 2.273 | [-0.610, 5.035] | 4/0/1 |
| full: B=0.1 − B=0 | 2 | macro_f1 | 2.210 ± 2.168 | [-0.483, 4.902] | 4/0/1 |
| full: B=0.1 − B=0 | 4 | accuracy | 2.225 ± 2.600 | [-1.004, 5.454] | 4/0/1 |
| full: B=0.1 − B=0 | 4 | macro_f1 | 2.283 ± 2.697 | [-1.066, 5.633] | 4/0/1 |
| full: B=0.1 − B=0 | 6 | accuracy | 2.325 ± 2.232 | [-0.446, 5.096] | 4/0/1 |
| full: B=0.1 − B=0 | 6 | macro_f1 | 2.390 ± 2.471 | [-0.678, 5.458] | 4/0/1 |
| full: B=0.1 − B=0 | 8 | accuracy | 2.029 ± 1.467 | [0.207, 3.851] | 5/0/0 |
| full: B=0.1 − B=0 | 8 | macro_f1 | 2.172 ± 1.460 | [0.359, 3.986] | 5/0/0 |
| full: B=0.1 − B=0 | 10 | accuracy | 1.840 ± 0.956 | [0.653, 3.026] | 5/0/0 |
| full: B=0.1 − B=0 | 10 | macro_f1 | 1.907 ± 0.795 | [0.919, 2.894] | 5/0/0 |
| full: B=0.1 − B=0 | noise_mean | accuracy | 2.126 ± 1.587 | [0.156, 4.097] | 4/0/1 |
| full: B=0.1 − B=0 | noise_mean | macro_f1 | 2.192 ± 1.524 | [0.300, 4.085] | 5/0/0 |
| all − selected_fixed (full, B=0.1) | clean | macro_f1 | 1.465 ± 2.415 | [-1.534, 4.464] | 4/0/1 |
| all − selected_fixed (full, B=0.1) | 2 | accuracy | -0.256 ± 2.185 | [-2.969, 2.457] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 2 | macro_f1 | 0.005 ± 2.117 | [-2.624, 2.634] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 4 | accuracy | 0.660 ± 1.513 | [-1.218, 2.539] | 4/0/1 |
| all − selected_fixed (full, B=0.1) | 4 | macro_f1 | 0.404 ± 1.418 | [-1.357, 2.165] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 6 | accuracy | 0.358 ± 1.372 | [-1.346, 2.062] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 6 | macro_f1 | -0.189 ± 0.804 | [-1.188, 0.809] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 8 | accuracy | 0.348 ± 1.649 | [-1.699, 2.395] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 8 | macro_f1 | -0.061 ± 1.322 | [-1.702, 1.580] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 10 | accuracy | 0.704 ± 2.010 | [-1.792, 3.200] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 10 | macro_f1 | 0.353 ± 1.858 | [-1.954, 2.660] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | noise_mean | accuracy | 0.363 ± 0.966 | [-0.837, 1.563] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | noise_mean | macro_f1 | 0.102 ± 0.377 | [-0.366, 0.571] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | clean | macro_f1 | 1.809 ± 1.060 | [0.493, 3.125] | 5/0/0 |
| all − selected_domain_mean (full, B=0.1) | 2 | accuracy | 0.704 ± 1.958 | [-1.727, 3.136] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 2 | macro_f1 | 0.602 ± 1.405 | [-1.142, 2.347] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 4 | accuracy | 1.102 ± 1.614 | [-0.901, 3.106] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 4 | macro_f1 | 0.999 ± 1.079 | [-0.341, 2.339] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 6 | accuracy | 1.077 ± 1.424 | [-0.691, 2.846] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 6 | macro_f1 | 0.830 ± 1.260 | [-0.734, 2.394] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 8 | accuracy | 0.998 ± 1.524 | [-0.894, 2.890] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 8 | macro_f1 | 0.835 ± 1.610 | [-1.164, 2.834] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 10 | accuracy | 1.323 ± 1.809 | [-0.923, 3.569] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 10 | macro_f1 | 1.174 ± 1.518 | [-0.710, 3.058] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | noise_mean | accuracy | 1.041 ± 1.468 | [-0.782, 2.864] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | noise_mean | macro_f1 | 0.888 ± 1.072 | [-0.443, 2.219] | 4/0/1 |
| softmatch_weight − full (B=0.1) | clean | macro_f1 | -2.034 ± 0.519 | [-2.678, -1.390] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 2 | accuracy | -0.044 ± 1.751 | [-2.218, 2.130] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 2 | macro_f1 | -0.289 ± 2.165 | [-2.977, 2.399] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 4 | accuracy | -1.494 ± 1.417 | [-3.253, 0.265] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 4 | macro_f1 | -1.567 ± 1.764 | [-3.758, 0.624] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 6 | accuracy | -2.767 ± 0.880 | [-3.860, -1.674] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 6 | macro_f1 | -2.508 ± 1.317 | [-4.143, -0.873] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 8 | accuracy | -3.160 ± 0.907 | [-4.286, -2.035] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 8 | macro_f1 | -2.769 ± 1.295 | [-4.377, -1.162] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 10 | accuracy | -3.115 ± 0.814 | [-4.126, -2.104] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 10 | macro_f1 | -2.555 ± 1.039 | [-3.846, -1.264] | 0/0/5 |
| softmatch_weight − full (B=0.1) | noise_mean | accuracy | -2.116 ± 1.050 | [-3.420, -0.812] | 0/0/5 |
| softmatch_weight − full (B=0.1) | noise_mean | macro_f1 | -1.938 ± 1.325 | [-3.582, -0.293] | 1/0/4 |
| softmatch_weight − selection_only (B=0.1) | clean | macro_f1 | 1.430 ± 2.118 | [-1.200, 4.060] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 2 | accuracy | 1.235 ± 3.665 | [-3.316, 5.786] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 2 | macro_f1 | 1.090 ± 3.719 | [-3.527, 5.707] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 4 | accuracy | 0.765 ± 2.807 | [-2.720, 4.250] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 4 | macro_f1 | 0.537 ± 3.176 | [-3.407, 4.480] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 6 | accuracy | -0.040 ± 2.408 | [-3.029, 2.950] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 6 | macro_f1 | 0.015 ± 2.564 | [-3.169, 3.199] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 8 | accuracy | -0.154 ± 2.071 | [-2.726, 2.418] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 8 | macro_f1 | 0.184 ± 2.079 | [-2.398, 2.766] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 10 | accuracy | 0.133 ± 1.863 | [-2.180, 2.447] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 10 | macro_f1 | 0.720 ± 1.920 | [-1.664, 3.104] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | noise_mean | accuracy | 0.388 ± 2.494 | [-2.709, 3.485] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | noise_mean | macro_f1 | 0.509 ± 2.614 | [-2.737, 3.755] | 3/0/2 |

</details>


<details>
<summary>DIRG：各配置的逐噪声分数</summary>

| 配置 | SNR/dB | Accuracy/% | Macro-F1/% |
| --- | --- | --- | --- |
| factorial/raw/B0/all | 2 | 25.196 ± 2.332 | 16.594 ± 3.347 |
| factorial/raw/B0/all | 4 | 30.205 ± 3.071 | 22.617 ± 3.469 |
| factorial/raw/B0/all | 6 | 36.513 ± 3.704 | 30.673 ± 3.655 |
| factorial/raw/B0/all | 8 | 42.719 ± 3.570 | 38.131 ± 3.179 |
| factorial/raw/B0/all | 10 | 47.299 ± 2.844 | 43.227 ± 2.400 |
| factorial/labels_only/B0/all | 2 | 26.223 ± 0.805 | 17.186 ± 1.393 |
| factorial/labels_only/B0/all | 4 | 30.402 ± 2.147 | 22.563 ± 2.447 |
| factorial/labels_only/B0/all | 6 | 37.259 ± 2.886 | 31.389 ± 2.678 |
| factorial/labels_only/B0/all | 8 | 43.987 ± 2.860 | 39.408 ± 2.844 |
| factorial/labels_only/B0/all | 10 | 48.371 ± 2.620 | 44.291 ± 2.646 |
| factorial/selection_only/B0/all | 2 | 26.161 ± 1.958 | 17.163 ± 2.984 |
| factorial/selection_only/B0/all | 4 | 30.125 ± 2.628 | 22.299 ± 3.357 |
| factorial/selection_only/B0/all | 6 | 37.165 ± 3.519 | 31.044 ± 4.260 |
| factorial/selection_only/B0/all | 8 | 43.112 ± 3.594 | 38.202 ± 4.256 |
| factorial/selection_only/B0/all | 10 | 47.237 ± 3.348 | 42.949 ± 3.538 |
| factorial/full/B0/all | 2 | 25.134 ± 1.736 | 17.119 ± 2.965 |
| factorial/full/B0/all | 4 | 29.607 ± 2.221 | 22.222 ± 3.214 |
| factorial/full/B0/all | 6 | 36.696 ± 2.666 | 30.684 ± 3.584 |
| factorial/full/B0/all | 8 | 43.018 ± 3.980 | 37.726 ± 4.705 |
| factorial/full/B0/all | 10 | 47.246 ± 3.689 | 42.697 ± 4.036 |
| factorial/raw/B0.1/all | 2 | 25.683 ± 2.147 | 16.867 ± 2.674 |
| factorial/raw/B0.1/all | 4 | 30.188 ± 1.984 | 22.584 ± 2.581 |
| factorial/raw/B0.1/all | 6 | 37.344 ± 2.353 | 31.512 ± 2.260 |
| factorial/raw/B0.1/all | 8 | 43.973 ± 3.369 | 39.523 ± 3.301 |
| factorial/raw/B0.1/all | 10 | 48.045 ± 3.421 | 44.106 ± 3.282 |
| factorial/labels_only/B0.1/all | 2 | 25.402 ± 1.952 | 16.758 ± 2.969 |
| factorial/labels_only/B0.1/all | 4 | 30.174 ± 2.223 | 22.082 ± 2.008 |
| factorial/labels_only/B0.1/all | 6 | 37.335 ± 1.862 | 31.129 ± 1.805 |
| factorial/labels_only/B0.1/all | 8 | 44.018 ± 2.693 | 39.024 ± 2.893 |
| factorial/labels_only/B0.1/all | 10 | 48.607 ± 3.443 | 44.252 ± 3.594 |
| factorial/selection_only/B0.1/all | 2 | 25.054 ± 2.203 | 16.548 ± 3.475 |
| factorial/selection_only/B0.1/all | 4 | 29.063 ± 3.166 | 21.058 ± 3.989 |
| factorial/selection_only/B0.1/all | 6 | 35.969 ± 4.044 | 30.011 ± 4.810 |
| factorial/selection_only/B0.1/all | 8 | 42.272 ± 4.179 | 37.353 ± 4.675 |
| factorial/selection_only/B0.1/all | 10 | 46.674 ± 3.508 | 42.333 ± 3.751 |
| factorial/full/B0.1/all | 2 | 25.304 ± 1.600 | 16.712 ± 2.613 |
| factorial/full/B0.1/all | 4 | 29.906 ± 2.131 | 21.886 ± 2.469 |
| factorial/full/B0.1/all | 6 | 36.603 ± 2.919 | 30.241 ± 3.711 |
| factorial/full/B0.1/all | 8 | 42.888 ± 4.043 | 37.742 ± 4.918 |
| factorial/full/B0.1/all | 10 | 47.286 ± 3.799 | 42.893 ± 4.377 |
| coverage/full/B0.1/selected_fixed | 2 | 25.268 ± 1.584 | 16.972 ± 2.562 |
| coverage/full/B0.1/selected_fixed | 4 | 29.616 ± 1.497 | 22.082 ± 2.299 |
| coverage/full/B0.1/selected_fixed | 6 | 36.286 ± 1.757 | 30.393 ± 2.392 |
| coverage/full/B0.1/selected_fixed | 8 | 42.268 ± 2.707 | 37.578 ± 3.118 |
| coverage/full/B0.1/selected_fixed | 10 | 47.049 ± 2.784 | 43.143 ± 2.734 |
| coverage/full/B0.1/selected_domain_mean | 2 | 25.688 ± 1.551 | 16.781 ± 3.159 |
| coverage/full/B0.1/selected_domain_mean | 4 | 30.040 ± 2.350 | 21.929 ± 3.553 |
| coverage/full/B0.1/selected_domain_mean | 6 | 37.103 ± 2.587 | 30.755 ± 3.501 |
| coverage/full/B0.1/selected_domain_mean | 8 | 43.388 ± 2.985 | 38.190 ± 3.408 |
| coverage/full/B0.1/selected_domain_mean | 10 | 47.915 ± 2.936 | 43.617 ± 2.835 |
| soft_weight/softmatch_weight/B0.1/all | 2 | 23.808 ± 3.001 | 15.842 ± 3.545 |
| soft_weight/softmatch_weight/B0.1/all | 4 | 28.737 ± 3.055 | 21.547 ± 3.575 |
| soft_weight/softmatch_weight/B0.1/all | 6 | 35.250 ± 2.903 | 29.902 ± 3.684 |
| soft_weight/softmatch_weight/B0.1/all | 8 | 42.830 ± 2.750 | 38.416 ± 3.281 |
| soft_weight/softmatch_weight/B0.1/all | 10 | 47.754 ± 2.253 | 43.553 ± 2.170 |

</details>

<details>
<summary>DIRG：Macro-F1与全部噪声的配对差</summary>

| 对比（左减右） | 条件 | 指标 | 差值均值 ± SD/pp | 种子t95区间/pp | 正/零/负 |
| --- | --- | --- | --- | --- | --- |
| B=0: full − labels_only | clean | macro_f1 | -0.031 ± 2.557 | [-3.206, 3.144] | 3/0/2 |
| B=0: full − labels_only | 2 | accuracy | -1.089 ± 1.961 | [-3.525, 1.346] | 1/0/4 |
| B=0: full − labels_only | 2 | macro_f1 | -0.067 ± 1.765 | [-2.258, 2.124] | 3/0/2 |
| B=0: full − labels_only | 4 | accuracy | -0.795 ± 1.775 | [-2.999, 1.410] | 2/0/3 |
| B=0: full − labels_only | 4 | macro_f1 | -0.341 ± 1.546 | [-2.261, 1.578] | 2/0/3 |
| B=0: full − labels_only | 6 | accuracy | -0.563 ± 1.751 | [-2.736, 1.611] | 2/0/3 |
| B=0: full − labels_only | 6 | macro_f1 | -0.705 ± 1.983 | [-3.167, 1.758] | 2/0/3 |
| B=0: full − labels_only | 8 | accuracy | -0.969 ± 2.004 | [-3.458, 1.520] | 2/0/3 |
| B=0: full − labels_only | 8 | macro_f1 | -1.682 ± 2.796 | [-5.153, 1.790] | 2/0/3 |
| B=0: full − labels_only | 10 | accuracy | -1.125 ± 2.059 | [-3.682, 1.432] | 2/0/3 |
| B=0: full − labels_only | 10 | macro_f1 | -1.595 ± 2.810 | [-5.084, 1.895] | 2/0/3 |
| B=0: full − labels_only | noise_mean | accuracy | -0.908 ± 1.501 | [-2.772, 0.956] | 1/0/4 |
| B=0: full − labels_only | noise_mean | macro_f1 | -0.878 ± 1.877 | [-3.209, 1.453] | 2/0/3 |
| B=0: full − selection_only | clean | macro_f1 | 0.424 ± 2.822 | [-3.080, 3.928] | 4/0/1 |
| B=0: full − selection_only | 2 | accuracy | -1.027 ± 0.953 | [-2.210, 0.157] | 0/0/5 |
| B=0: full − selection_only | 2 | macro_f1 | -0.043 ± 0.510 | [-0.677, 0.590] | 3/0/2 |
| B=0: full − selection_only | 4 | accuracy | -0.518 ± 1.372 | [-2.221, 1.186] | 2/0/3 |
| B=0: full − selection_only | 4 | macro_f1 | -0.077 ± 0.704 | [-0.951, 0.798] | 2/0/3 |
| B=0: full − selection_only | 6 | accuracy | -0.469 ± 1.550 | [-2.394, 1.456] | 2/0/3 |
| B=0: full − selection_only | 6 | macro_f1 | -0.360 ± 2.194 | [-3.085, 2.364] | 3/0/2 |
| B=0: full − selection_only | 8 | accuracy | -0.094 ± 2.071 | [-2.665, 2.477] | 3/0/2 |
| B=0: full − selection_only | 8 | macro_f1 | -0.476 ± 2.863 | [-4.031, 3.079] | 3/0/2 |
| B=0: full − selection_only | 10 | accuracy | 0.009 ± 1.776 | [-2.196, 2.214] | 4/0/1 |
| B=0: full − selection_only | 10 | macro_f1 | -0.252 ± 2.629 | [-3.516, 3.013] | 4/0/1 |
| B=0: full − selection_only | noise_mean | accuracy | -0.420 ± 0.889 | [-1.524, 0.685] | 2/0/3 |
| B=0: full − selection_only | noise_mean | macro_f1 | -0.242 ± 1.445 | [-2.036, 1.553] | 3/0/2 |
| B=0: full − raw | clean | macro_f1 | 1.247 ± 2.335 | [-1.652, 4.146] | 3/0/2 |
| B=0: full − raw | 2 | accuracy | -0.062 ± 2.451 | [-3.106, 2.981] | 3/0/2 |
| B=0: full − raw | 2 | macro_f1 | 0.525 ± 2.540 | [-2.629, 3.679] | 3/0/2 |
| B=0: full − raw | 4 | accuracy | -0.598 ± 2.829 | [-4.110, 2.914] | 2/0/3 |
| B=0: full − raw | 4 | macro_f1 | -0.395 ± 2.412 | [-3.390, 2.599] | 1/0/4 |
| B=0: full − raw | 6 | accuracy | 0.183 ± 1.931 | [-2.215, 2.581] | 2/0/3 |
| B=0: full − raw | 6 | macro_f1 | 0.011 ± 1.705 | [-2.105, 2.127] | 2/0/3 |
| B=0: full − raw | 8 | accuracy | 0.299 ± 1.451 | [-1.502, 2.101] | 3/0/2 |
| B=0: full − raw | 8 | macro_f1 | -0.405 ± 2.093 | [-3.003, 2.194] | 2/0/3 |
| B=0: full − raw | 10 | accuracy | -0.054 ± 2.204 | [-2.790, 2.683] | 3/0/2 |
| B=0: full − raw | 10 | macro_f1 | -0.530 ± 2.846 | [-4.064, 3.003] | 2/0/3 |
| B=0: full − raw | noise_mean | accuracy | -0.046 ± 1.786 | [-2.264, 2.171] | 2/0/3 |
| B=0: full − raw | noise_mean | macro_f1 | -0.159 ± 1.875 | [-2.487, 2.170] | 2/0/3 |
| B=0: labels_only − raw | clean | macro_f1 | 1.278 ± 2.795 | [-2.193, 4.749] | 3/0/2 |
| B=0: labels_only − raw | 2 | accuracy | 1.027 ± 2.064 | [-1.536, 3.590] | 3/0/2 |
| B=0: labels_only − raw | 2 | macro_f1 | 0.592 ± 2.425 | [-2.419, 3.603] | 4/0/1 |
| B=0: labels_only − raw | 4 | accuracy | 0.196 ± 2.124 | [-2.441, 2.834] | 2/0/3 |
| B=0: labels_only − raw | 4 | macro_f1 | -0.054 ± 2.572 | [-3.248, 3.140] | 2/0/3 |
| B=0: labels_only − raw | 6 | accuracy | 0.746 ± 2.862 | [-2.808, 4.299] | 3/0/2 |
| B=0: labels_only − raw | 6 | macro_f1 | 0.715 ± 3.057 | [-3.081, 4.512] | 3/0/2 |
| B=0: labels_only − raw | 8 | accuracy | 1.268 ± 2.508 | [-1.847, 4.382] | 4/0/1 |
| B=0: labels_only − raw | 8 | macro_f1 | 1.277 ± 2.424 | [-1.732, 4.287] | 4/0/1 |
| B=0: labels_only − raw | 10 | accuracy | 1.071 ± 2.317 | [-1.805, 3.948] | 3/0/2 |
| B=0: labels_only − raw | 10 | macro_f1 | 1.064 ± 2.401 | [-1.916, 4.045] | 3/0/2 |
| B=0: labels_only − raw | noise_mean | accuracy | 0.862 ± 2.283 | [-1.973, 3.696] | 3/0/2 |
| B=0: labels_only − raw | noise_mean | macro_f1 | 0.719 ± 2.411 | [-2.274, 3.712] | 4/0/1 |
| B=0: selection_only − raw | clean | macro_f1 | 0.823 ± 3.462 | [-3.476, 5.121] | 3/0/2 |
| B=0: selection_only − raw | 2 | accuracy | 0.964 ± 1.830 | [-1.309, 3.237] | 4/0/1 |
| B=0: selection_only − raw | 2 | macro_f1 | 0.568 ± 2.346 | [-2.345, 3.482] | 3/0/2 |
| B=0: selection_only − raw | 4 | accuracy | -0.080 ± 2.307 | [-2.945, 2.784] | 3/0/2 |
| B=0: selection_only − raw | 4 | macro_f1 | -0.318 ± 2.756 | [-3.741, 3.104] | 1/0/4 |
| B=0: selection_only − raw | 6 | accuracy | 0.652 ± 3.226 | [-3.354, 4.657] | 3/0/2 |
| B=0: selection_only − raw | 6 | macro_f1 | 0.371 ± 3.567 | [-4.058, 4.801] | 2/0/3 |
| B=0: selection_only − raw | 8 | accuracy | 0.393 ± 3.072 | [-3.422, 4.207] | 3/0/2 |
| B=0: selection_only − raw | 8 | macro_f1 | 0.072 ± 3.685 | [-4.504, 4.648] | 2/0/3 |
| B=0: selection_only − raw | 10 | accuracy | -0.062 ± 3.132 | [-3.951, 3.826] | 2/0/3 |
| B=0: selection_only − raw | 10 | macro_f1 | -0.279 ± 3.921 | [-5.148, 4.590] | 2/0/3 |
| B=0: selection_only − raw | noise_mean | accuracy | 0.373 ± 2.586 | [-2.837, 3.584] | 3/0/2 |
| B=0: selection_only − raw | noise_mean | macro_f1 | 0.083 ± 3.187 | [-3.874, 4.040] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | clean | macro_f1 | -0.853 ± 5.215 | [-7.329, 5.622] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 2 | accuracy | -2.054 ± 1.754 | [-4.232, 0.124] | 1/0/4 |
| B=0: full − labels_only − selection_only + raw | 2 | macro_f1 | -0.635 ± 2.343 | [-3.545, 2.274] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 4 | accuracy | -0.714 ± 2.262 | [-3.523, 2.094] | 1/0/4 |
| B=0: full − labels_only − selection_only + raw | 4 | macro_f1 | -0.023 ± 2.988 | [-3.733, 3.687] | 4/0/1 |
| B=0: full − labels_only − selection_only + raw | 6 | accuracy | -1.214 ± 3.622 | [-5.712, 3.283] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 6 | macro_f1 | -1.076 ± 4.422 | [-6.566, 4.414] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 8 | accuracy | -1.362 ± 4.125 | [-6.483, 3.760] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 8 | macro_f1 | -1.753 ± 4.741 | [-7.640, 4.133] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 10 | accuracy | -1.063 ± 3.514 | [-5.426, 3.301] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 10 | macro_f1 | -1.316 ± 4.193 | [-6.522, 3.890] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | noise_mean | accuracy | -1.281 ± 2.941 | [-4.933, 2.371] | 1/0/4 |
| B=0: full − labels_only − selection_only + raw | noise_mean | macro_f1 | -0.961 ± 3.669 | [-5.516, 3.595] | 3/0/2 |
| B=0.1: full − labels_only | clean | macro_f1 | -0.323 ± 3.237 | [-4.342, 3.695] | 2/0/3 |
| B=0.1: full − labels_only | 2 | accuracy | -0.098 ± 1.901 | [-2.458, 2.262] | 2/0/3 |
| B=0.1: full − labels_only | 2 | macro_f1 | -0.046 ± 1.986 | [-2.512, 2.420] | 2/0/3 |
| B=0.1: full − labels_only | 4 | accuracy | -0.268 ± 2.340 | [-3.174, 2.638] | 2/0/3 |
| B=0.1: full − labels_only | 4 | macro_f1 | -0.196 ± 2.007 | [-2.688, 2.296] | 1/0/4 |
| B=0.1: full − labels_only | 6 | accuracy | -0.732 ± 1.688 | [-2.828, 1.364] | 1/0/4 |
| B=0.1: full − labels_only | 6 | macro_f1 | -0.888 ± 2.427 | [-3.902, 2.126] | 1/0/4 |
| B=0.1: full − labels_only | 8 | accuracy | -1.129 ± 1.370 | [-2.831, 0.572] | 1/0/4 |
| B=0.1: full − labels_only | 8 | macro_f1 | -1.282 ± 2.462 | [-4.339, 1.775] | 1/0/4 |
| B=0.1: full − labels_only | 10 | accuracy | -1.321 ± 0.475 | [-1.911, -0.732] | 0/0/5 |
| B=0.1: full − labels_only | 10 | macro_f1 | -1.359 ± 1.882 | [-3.696, 0.977] | 2/0/3 |
| B=0.1: full − labels_only | noise_mean | accuracy | -0.710 ± 1.430 | [-2.485, 1.066] | 1/0/4 |
| B=0.1: full − labels_only | noise_mean | macro_f1 | -0.754 ± 1.908 | [-3.123, 1.614] | 1/0/4 |
| B=0.1: full − selection_only | clean | macro_f1 | 2.465 ± 3.157 | [-1.455, 6.386] | 4/0/1 |
| B=0.1: full − selection_only | 2 | accuracy | 0.250 ± 0.916 | [-0.888, 1.388] | 3/0/2 |
| B=0.1: full − selection_only | 2 | macro_f1 | 0.164 ± 1.737 | [-1.993, 2.320] | 1/0/4 |
| B=0.1: full − selection_only | 4 | accuracy | 0.844 ± 1.587 | [-1.126, 2.814] | 3/0/2 |
| B=0.1: full − selection_only | 4 | macro_f1 | 0.828 ± 1.875 | [-1.499, 3.156] | 4/0/1 |
| B=0.1: full − selection_only | 6 | accuracy | 0.634 ± 1.906 | [-1.732, 3.000] | 2/0/3 |
| B=0.1: full − selection_only | 6 | macro_f1 | 0.230 ± 1.932 | [-2.169, 2.629] | 2/0/3 |
| B=0.1: full − selection_only | 8 | accuracy | 0.616 ± 2.022 | [-1.895, 3.127] | 3/0/2 |
| B=0.1: full − selection_only | 8 | macro_f1 | 0.389 ± 1.722 | [-1.749, 2.526] | 3/0/2 |
| B=0.1: full − selection_only | 10 | accuracy | 0.612 ± 1.398 | [-1.125, 2.348] | 3/0/2 |
| B=0.1: full − selection_only | 10 | macro_f1 | 0.560 ± 1.159 | [-0.879, 1.998] | 3/0/2 |
| B=0.1: full − selection_only | noise_mean | accuracy | 0.591 ± 1.476 | [-1.241, 2.423] | 3/0/2 |
| B=0.1: full − selection_only | noise_mean | macro_f1 | 0.434 ± 1.529 | [-1.465, 2.333] | 3/0/2 |
| B=0.1: full − raw | clean | macro_f1 | 0.986 ± 1.637 | [-1.046, 3.018] | 3/0/2 |
| B=0.1: full − raw | 2 | accuracy | -0.379 ± 1.981 | [-2.840, 2.081] | 2/0/3 |
| B=0.1: full − raw | 2 | macro_f1 | -0.156 ± 1.334 | [-1.812, 1.501] | 2/0/3 |
| B=0.1: full − raw | 4 | accuracy | -0.281 ± 1.471 | [-2.108, 1.546] | 2/0/3 |
| B=0.1: full − raw | 4 | macro_f1 | -0.698 ± 1.296 | [-2.307, 0.912] | 2/0/3 |
| B=0.1: full − raw | 6 | accuracy | -0.741 ± 1.418 | [-2.502, 1.020] | 2/0/3 |
| B=0.1: full − raw | 6 | macro_f1 | -1.271 ± 1.841 | [-3.558, 1.015] | 1/0/4 |
| B=0.1: full − raw | 8 | accuracy | -1.085 ± 1.984 | [-3.548, 1.378] | 2/0/3 |
| B=0.1: full − raw | 8 | macro_f1 | -1.781 ± 3.047 | [-5.565, 2.002] | 1/0/4 |
| B=0.1: full − raw | 10 | accuracy | -0.759 ± 1.783 | [-2.972, 1.454] | 3/0/2 |
| B=0.1: full − raw | 10 | macro_f1 | -1.213 ± 2.599 | [-4.440, 2.015] | 1/0/4 |
| B=0.1: full − raw | noise_mean | accuracy | -0.649 ± 1.521 | [-2.537, 1.239] | 2/0/3 |
| B=0.1: full − raw | noise_mean | macro_f1 | -1.024 ± 1.804 | [-3.264, 1.216] | 1/0/4 |
| B=0.1: labels_only − raw | clean | macro_f1 | 1.310 ± 1.713 | [-0.817, 3.436] | 4/0/1 |
| B=0.1: labels_only − raw | 2 | accuracy | -0.281 ± 1.105 | [-1.654, 1.091] | 2/0/3 |
| B=0.1: labels_only − raw | 2 | macro_f1 | -0.110 ± 1.338 | [-1.771, 1.551] | 2/0/3 |
| B=0.1: labels_only − raw | 4 | accuracy | -0.013 ± 1.116 | [-1.399, 1.372] | 2/0/3 |
| B=0.1: labels_only − raw | 4 | macro_f1 | -0.502 ± 1.500 | [-2.364, 1.361] | 2/0/3 |
| B=0.1: labels_only − raw | 6 | accuracy | -0.009 ± 1.453 | [-1.813, 1.795] | 3/0/2 |
| B=0.1: labels_only − raw | 6 | macro_f1 | -0.383 ± 1.859 | [-2.691, 1.925] | 2/0/3 |
| B=0.1: labels_only − raw | 8 | accuracy | 0.045 ± 1.843 | [-2.244, 2.333] | 2/0/3 |
| B=0.1: labels_only − raw | 8 | macro_f1 | -0.499 ± 1.760 | [-2.684, 1.686] | 2/0/3 |
| B=0.1: labels_only − raw | 10 | accuracy | 0.562 ± 1.374 | [-1.143, 2.268] | 3/0/2 |
| B=0.1: labels_only − raw | 10 | macro_f1 | 0.147 ± 1.034 | [-1.137, 1.430] | 2/0/3 |
| B=0.1: labels_only − raw | noise_mean | accuracy | 0.061 ± 1.034 | [-1.223, 1.345] | 2/0/3 |
| B=0.1: labels_only − raw | noise_mean | macro_f1 | -0.269 ± 1.136 | [-1.680, 1.141] | 2/0/3 |
| B=0.1: selection_only − raw | clean | macro_f1 | -1.479 ± 1.578 | [-3.438, 0.481] | 1/0/4 |
| B=0.1: selection_only − raw | 2 | accuracy | -0.629 ± 2.619 | [-3.882, 2.623] | 2/1/2 |
| B=0.1: selection_only − raw | 2 | macro_f1 | -0.319 ± 2.490 | [-3.411, 2.773] | 3/0/2 |
| B=0.1: selection_only − raw | 4 | accuracy | -1.125 ± 2.004 | [-3.614, 1.364] | 2/0/3 |
| B=0.1: selection_only − raw | 4 | macro_f1 | -1.526 ± 2.334 | [-4.424, 1.372] | 2/0/3 |
| B=0.1: selection_only − raw | 6 | accuracy | -1.375 ± 2.718 | [-4.750, 2.000] | 2/0/3 |
| B=0.1: selection_only − raw | 6 | macro_f1 | -1.501 ± 3.283 | [-5.577, 2.575] | 2/0/3 |
| B=0.1: selection_only − raw | 8 | accuracy | -1.701 ± 3.647 | [-6.229, 2.827] | 2/0/3 |
| B=0.1: selection_only − raw | 8 | macro_f1 | -2.170 ± 4.040 | [-7.186, 2.846] | 2/0/3 |
| B=0.1: selection_only − raw | 10 | accuracy | -1.371 ± 2.484 | [-4.455, 1.714] | 2/1/2 |
| B=0.1: selection_only − raw | 10 | macro_f1 | -1.772 ± 2.712 | [-5.140, 1.596] | 2/0/3 |
| B=0.1: selection_only − raw | noise_mean | accuracy | -1.240 ± 2.615 | [-4.487, 2.007] | 2/0/3 |
| B=0.1: selection_only − raw | noise_mean | macro_f1 | -1.458 ± 2.908 | [-5.069, 2.153] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | clean | macro_f1 | 1.155 ± 4.646 | [-4.613, 6.924] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 2 | accuracy | 0.531 ± 1.868 | [-1.788, 2.850] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 2 | macro_f1 | 0.273 ± 2.639 | [-3.003, 3.550] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 4 | accuracy | 0.857 ± 2.075 | [-1.719, 3.433] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 4 | macro_f1 | 1.330 ± 2.370 | [-1.612, 4.273] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 6 | accuracy | 0.643 ± 2.826 | [-2.866, 4.152] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 6 | macro_f1 | 0.613 ± 3.255 | [-3.429, 4.655] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 8 | accuracy | 0.571 ± 3.781 | [-4.123, 5.266] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 8 | macro_f1 | 0.888 ± 3.327 | [-3.243, 5.019] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 10 | accuracy | 0.049 ± 2.248 | [-2.743, 2.841] | 2/0/3 |
| B=0.1: full − labels_only − selection_only + raw | 10 | macro_f1 | 0.413 ± 1.452 | [-1.390, 2.215] | 2/0/3 |
| B=0.1: full − labels_only − selection_only + raw | noise_mean | accuracy | 0.530 ± 2.441 | [-2.501, 3.561] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | noise_mean | macro_f1 | 0.703 ± 2.482 | [-2.378, 3.785] | 3/0/2 |
| raw: B=0.1 − B=0 | clean | macro_f1 | 0.611 ± 3.028 | [-3.149, 4.371] | 3/0/2 |
| raw: B=0.1 − B=0 | 2 | accuracy | 0.487 ± 1.647 | [-1.559, 2.532] | 2/0/3 |
| raw: B=0.1 − B=0 | 2 | macro_f1 | 0.273 ± 1.161 | [-1.168, 1.714] | 4/0/1 |
| raw: B=0.1 − B=0 | 4 | accuracy | -0.018 ± 1.252 | [-1.573, 1.537] | 3/0/2 |
| raw: B=0.1 − B=0 | 4 | macro_f1 | -0.033 ± 1.159 | [-1.472, 1.406] | 2/0/3 |
| raw: B=0.1 − B=0 | 6 | accuracy | 0.830 ± 1.611 | [-1.170, 2.831] | 3/0/2 |
| raw: B=0.1 − B=0 | 6 | macro_f1 | 0.839 ± 1.646 | [-1.205, 2.883] | 3/0/2 |
| raw: B=0.1 − B=0 | 8 | accuracy | 1.254 ± 2.490 | [-1.837, 4.346] | 4/0/1 |
| raw: B=0.1 − B=0 | 8 | macro_f1 | 1.392 ± 2.738 | [-2.008, 4.792] | 4/0/1 |
| raw: B=0.1 − B=0 | 10 | accuracy | 0.746 ± 2.164 | [-1.942, 3.433] | 4/0/1 |
| raw: B=0.1 − B=0 | 10 | macro_f1 | 0.878 ± 2.434 | [-2.144, 3.901] | 3/0/2 |
| raw: B=0.1 − B=0 | noise_mean | accuracy | 0.660 ± 1.622 | [-1.354, 2.674] | 3/0/2 |
| raw: B=0.1 − B=0 | noise_mean | macro_f1 | 0.670 ± 1.661 | [-1.392, 2.732] | 4/0/1 |
| labels_only: B=0.1 − B=0 | clean | macro_f1 | 0.643 ± 1.236 | [-0.892, 2.178] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 2 | accuracy | -0.821 ± 2.175 | [-3.522, 1.879] | 1/0/4 |
| labels_only: B=0.1 − B=0 | 2 | macro_f1 | -0.428 ± 2.333 | [-3.326, 2.469] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 4 | accuracy | -0.228 ± 2.620 | [-3.481, 3.025] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 4 | macro_f1 | -0.481 ± 2.339 | [-3.385, 2.423] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 6 | accuracy | 0.076 ± 1.666 | [-1.992, 2.144] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 6 | macro_f1 | -0.260 ± 1.284 | [-1.854, 1.335] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 8 | accuracy | 0.031 ± 1.180 | [-1.434, 1.496] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 8 | macro_f1 | -0.384 ± 0.631 | [-1.168, 0.400] | 1/0/4 |
| labels_only: B=0.1 − B=0 | 10 | accuracy | 0.237 ± 1.559 | [-1.699, 2.172] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 10 | macro_f1 | -0.039 ± 1.625 | [-2.057, 1.979] | 2/0/3 |
| labels_only: B=0.1 − B=0 | noise_mean | accuracy | -0.141 ± 1.324 | [-1.785, 1.503] | 1/0/4 |
| labels_only: B=0.1 − B=0 | noise_mean | macro_f1 | -0.318 ± 0.868 | [-1.396, 0.759] | 2/0/3 |
| selection_only: B=0.1 − B=0 | clean | macro_f1 | -1.690 ± 2.093 | [-4.290, 0.909] | 1/0/4 |
| selection_only: B=0.1 − B=0 | 2 | accuracy | -1.107 ± 1.347 | [-2.780, 0.566] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 2 | macro_f1 | -0.615 ± 1.782 | [-2.828, 1.598] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 4 | accuracy | -1.063 ± 1.713 | [-3.190, 1.065] | 1/0/4 |
| selection_only: B=0.1 − B=0 | 4 | macro_f1 | -1.241 ± 2.031 | [-3.763, 1.281] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 6 | accuracy | -1.196 ± 2.131 | [-3.842, 1.450] | 1/0/4 |
| selection_only: B=0.1 − B=0 | 6 | macro_f1 | -1.033 ± 2.573 | [-4.229, 2.162] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 8 | accuracy | -0.839 ± 1.970 | [-3.286, 1.607] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 8 | macro_f1 | -0.849 ± 2.630 | [-4.115, 2.416] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 10 | accuracy | -0.562 ± 1.440 | [-2.351, 1.226] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 10 | macro_f1 | -0.615 ± 2.298 | [-3.468, 2.238] | 3/0/2 |
| selection_only: B=0.1 − B=0 | noise_mean | accuracy | -0.954 ± 1.640 | [-2.989, 1.082] | 1/0/4 |
| selection_only: B=0.1 − B=0 | noise_mean | macro_f1 | -0.871 ± 2.194 | [-3.595, 1.853] | 3/0/2 |
| full: B=0.1 − B=0 | clean | macro_f1 | 0.350 ± 3.146 | [-3.556, 4.257] | 2/0/3 |
| full: B=0.1 − B=0 | 2 | accuracy | 0.170 ± 2.020 | [-2.338, 2.677] | 2/0/3 |
| full: B=0.1 − B=0 | 2 | macro_f1 | -0.407 ± 1.801 | [-2.644, 1.829] | 3/0/2 |
| full: B=0.1 − B=0 | 4 | accuracy | 0.299 ± 2.362 | [-2.634, 3.232] | 2/0/3 |
| full: B=0.1 − B=0 | 4 | macro_f1 | -0.336 ± 1.859 | [-2.644, 1.973] | 3/0/2 |
| full: B=0.1 − B=0 | 6 | accuracy | -0.094 ± 0.883 | [-1.190, 1.003] | 2/0/3 |
| full: B=0.1 − B=0 | 6 | macro_f1 | -0.443 ± 1.017 | [-1.706, 0.819] | 3/0/2 |
| full: B=0.1 − B=0 | 8 | accuracy | -0.129 ± 0.725 | [-1.030, 0.771] | 2/1/2 |
| full: B=0.1 − B=0 | 8 | macro_f1 | 0.015 ± 0.683 | [-0.832, 0.863] | 4/0/1 |
| full: B=0.1 − B=0 | 10 | accuracy | 0.040 ± 0.734 | [-0.871, 0.951] | 3/0/2 |
| full: B=0.1 − B=0 | 10 | macro_f1 | 0.196 ± 1.074 | [-1.138, 1.530] | 3/0/2 |
| full: B=0.1 − B=0 | noise_mean | accuracy | 0.057 ± 1.116 | [-1.328, 1.443] | 2/0/3 |
| full: B=0.1 − B=0 | noise_mean | macro_f1 | -0.195 ± 1.057 | [-1.507, 1.118] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | clean | macro_f1 | 0.176 ± 2.409 | [-2.815, 3.168] | 4/0/1 |
| all − selected_fixed (full, B=0.1) | 2 | accuracy | 0.036 ± 1.513 | [-1.842, 1.914] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 2 | macro_f1 | -0.261 ± 0.662 | [-1.082, 0.561] | 1/0/4 |
| all − selected_fixed (full, B=0.1) | 4 | accuracy | 0.290 ± 1.056 | [-1.021, 1.601] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 4 | macro_f1 | -0.196 ± 0.826 | [-1.221, 0.829] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 6 | accuracy | 0.317 ± 1.225 | [-1.204, 1.837] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 6 | macro_f1 | -0.152 ± 1.856 | [-2.456, 2.152] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 8 | accuracy | 0.621 ± 1.638 | [-1.413, 2.655] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 8 | macro_f1 | 0.163 ± 2.202 | [-2.571, 2.898] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 10 | accuracy | 0.237 ± 1.305 | [-1.383, 1.857] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 10 | macro_f1 | -0.250 ± 1.877 | [-2.580, 2.080] | 1/0/4 |
| all − selected_fixed (full, B=0.1) | noise_mean | accuracy | 0.300 ± 1.158 | [-1.138, 1.738] | 4/0/1 |
| all − selected_fixed (full, B=0.1) | noise_mean | macro_f1 | -0.139 ± 1.388 | [-1.862, 1.584] | 1/0/4 |
| all − selected_domain_mean (full, B=0.1) | clean | macro_f1 | 0.174 ± 3.346 | [-3.981, 4.329] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 2 | accuracy | -0.384 ± 1.507 | [-2.255, 1.487] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 2 | macro_f1 | -0.069 ± 1.264 | [-1.639, 1.500] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 4 | accuracy | -0.134 ± 2.168 | [-2.825, 2.558] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 4 | macro_f1 | -0.043 ± 1.887 | [-2.386, 2.300] | 4/0/1 |
| all − selected_domain_mean (full, B=0.1) | 6 | accuracy | -0.500 ± 1.956 | [-2.928, 1.928] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 6 | macro_f1 | -0.514 ± 1.690 | [-2.613, 1.585] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 8 | accuracy | -0.500 ± 1.914 | [-2.876, 1.876] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 8 | macro_f1 | -0.448 ± 2.150 | [-3.118, 2.222] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 10 | accuracy | -0.629 ± 2.136 | [-3.282, 2.023] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 10 | macro_f1 | -0.724 ± 2.532 | [-3.868, 2.419] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | noise_mean | accuracy | -0.429 ± 1.824 | [-2.694, 1.835] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | noise_mean | macro_f1 | -0.360 ± 1.741 | [-2.522, 1.802] | 2/0/3 |
| softmatch_weight − full (B=0.1) | clean | macro_f1 | -0.290 ± 2.729 | [-3.678, 3.099] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 2 | accuracy | -1.496 ± 1.845 | [-3.786, 0.795] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 2 | macro_f1 | -0.869 ± 2.408 | [-3.859, 2.121] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 4 | accuracy | -1.170 ± 1.281 | [-2.760, 0.421] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 4 | macro_f1 | -0.339 ± 1.321 | [-1.980, 1.301] | 3/0/2 |
| softmatch_weight − full (B=0.1) | 6 | accuracy | -1.353 ± 0.523 | [-2.002, -0.703] | 0/0/5 |
| softmatch_weight − full (B=0.1) | 6 | macro_f1 | -0.339 ± 0.812 | [-1.348, 0.669] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 8 | accuracy | -0.058 ± 1.447 | [-1.855, 1.739] | 3/0/2 |
| softmatch_weight − full (B=0.1) | 8 | macro_f1 | 0.675 ± 2.169 | [-2.019, 3.369] | 3/0/2 |
| softmatch_weight − full (B=0.1) | 10 | accuracy | 0.469 ± 1.899 | [-1.889, 2.827] | 4/0/1 |
| softmatch_weight − full (B=0.1) | 10 | macro_f1 | 0.660 ± 2.676 | [-2.663, 3.984] | 4/0/1 |
| softmatch_weight − full (B=0.1) | noise_mean | accuracy | -0.721 ± 0.680 | [-1.565, 0.122] | 1/0/4 |
| softmatch_weight − full (B=0.1) | noise_mean | macro_f1 | -0.043 ± 0.684 | [-0.892, 0.807] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | clean | macro_f1 | 2.175 ± 2.246 | [-0.613, 4.964] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 2 | accuracy | -1.246 ± 1.047 | [-2.546, 0.055] | 0/0/5 |
| softmatch_weight − selection_only (B=0.1) | 2 | macro_f1 | -0.706 ± 1.226 | [-2.227, 0.816] | 1/0/4 |
| softmatch_weight − selection_only (B=0.1) | 4 | accuracy | -0.326 ± 1.371 | [-2.028, 1.376] | 2/0/3 |
| softmatch_weight − selection_only (B=0.1) | 4 | macro_f1 | 0.489 ± 1.877 | [-1.842, 2.820] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 6 | accuracy | -0.719 ± 2.032 | [-3.242, 1.805] | 1/0/4 |
| softmatch_weight − selection_only (B=0.1) | 6 | macro_f1 | -0.109 ± 1.978 | [-2.565, 2.347] | 1/0/4 |
| softmatch_weight − selection_only (B=0.1) | 8 | accuracy | 0.558 ± 2.459 | [-2.495, 3.611] | 1/1/3 |
| softmatch_weight − selection_only (B=0.1) | 8 | macro_f1 | 1.063 ± 2.577 | [-2.137, 4.264] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 10 | accuracy | 1.080 ± 2.347 | [-1.834, 3.994] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 10 | macro_f1 | 1.220 ± 2.533 | [-1.926, 4.365] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | noise_mean | accuracy | -0.130 ± 1.355 | [-1.812, 1.552] | 2/0/3 |
| softmatch_weight − selection_only (B=0.1) | noise_mean | macro_f1 | 0.391 ± 1.455 | [-1.415, 2.198] | 2/0/3 |

</details>


## 逐目标配对差：保留异质性

以下展示干净Accuracy；每一目标的seed 0–4差值均保留。其它条件、指标的逐目标差值及种子描述区间见 summaries.json → paired_differences → by_condition → per_target。逐目标区间也只描述优化种子，不构成独立物理采集验证。

<details>
<summary>PU：全部逐目标主指标差值（百分点）</summary>

| 对比 | 目标 | seed0 | seed1 | seed2 | seed3 | seed4 | 均值 ± SD | t95区间 | 正/零/负 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B=0: full − labels_only | 6 | 7.458 | 1.792 | 5.875 | -0.208 | 0.542 | 3.092 ± 3.387 | [-1.114, 7.298] | 4/0/1 |
| B=0: full − labels_only | 7 | 1.375 | 3.583 | -0.417 | -1.250 | 5.625 | 1.783 ± 2.838 | [-1.740, 5.307] | 3/0/2 |
| B=0: full − labels_only | 8 | 0.042 | 2.125 | 0.667 | 0.417 | 0.042 | 0.658 ± 0.862 | [-0.412, 1.728] | 5/0/0 |
| B=0: full − labels_only | 9 | 3.667 | -1.500 | -0.208 | -19.750 | 1.500 | -3.258 ± 9.420 | [-14.955, 8.438] | 2/0/3 |
| B=0: full − selection_only | 6 | 5.542 | 2.375 | 7.875 | 0.458 | 0.167 | 3.283 ± 3.343 | [-0.868, 7.434] | 5/0/0 |
| B=0: full − selection_only | 7 | -0.875 | 4.000 | -1.167 | 2.042 | 8.000 | 2.400 ± 3.791 | [-2.307, 7.107] | 3/0/2 |
| B=0: full − selection_only | 8 | -0.208 | 0.333 | 2.833 | 0.125 | 0.125 | 0.642 ± 1.240 | [-0.899, 2.182] | 4/0/1 |
| B=0: full − selection_only | 9 | -0.708 | -7.208 | 0.250 | -5.250 | 3.833 | -1.817 ± 4.424 | [-7.310, 3.676] | 2/0/3 |
| B=0: full − raw | 6 | 6.542 | 2.792 | 7.208 | 1.958 | -0.208 | 3.658 ± 3.143 | [-0.244, 7.561] | 4/0/1 |
| B=0: full − raw | 7 | 1.875 | 7.333 | -6.917 | -0.167 | 7.500 | 1.925 ± 5.977 | [-5.496, 9.346] | 3/0/2 |
| B=0: full − raw | 8 | 0.000 | 1.458 | 0.083 | 0.292 | -0.167 | 0.333 ± 0.650 | [-0.474, 1.141] | 3/1/1 |
| B=0: full − raw | 9 | -0.708 | 1.875 | 6.250 | -3.375 | 5.417 | 1.892 ± 4.060 | [-3.149, 6.932] | 3/0/2 |
| B=0: labels_only − raw | 6 | -0.917 | 1.000 | 1.333 | 2.167 | -0.750 | 0.567 ± 1.348 | [-1.107, 2.241] | 3/0/2 |
| B=0: labels_only − raw | 7 | 0.500 | 3.750 | -6.500 | 1.083 | 1.875 | 0.142 ± 3.910 | [-4.713, 4.997] | 4/0/1 |
| B=0: labels_only − raw | 8 | -0.042 | -0.667 | -0.583 | -0.125 | -0.208 | -0.325 ± 0.282 | [-0.675, 0.025] | 0/0/5 |
| B=0: labels_only − raw | 9 | -4.375 | 3.375 | 6.458 | 16.375 | 3.917 | 5.150 ± 7.468 | [-4.123, 14.423] | 4/0/1 |
| B=0: selection_only − raw | 6 | 1.000 | 0.417 | -0.667 | 1.500 | -0.375 | 0.375 ± 0.909 | [-0.754, 1.504] | 3/0/2 |
| B=0: selection_only − raw | 7 | 2.750 | 3.333 | -5.750 | -2.208 | -0.500 | -0.475 ± 3.733 | [-5.110, 4.160] | 2/0/3 |
| B=0: selection_only − raw | 8 | 0.208 | 1.125 | -2.750 | 0.167 | -0.292 | -0.308 ± 1.459 | [-2.119, 1.503] | 3/0/2 |
| B=0: selection_only − raw | 9 | 0.000 | 9.083 | 6.000 | 1.875 | 1.583 | 3.708 ± 3.734 | [-0.928, 8.345] | 4/1/0 |
| B=0: full − labels_only − selection_only + raw | 6 | 6.458 | 1.375 | 6.542 | -1.708 | 0.917 | 2.717 ± 3.649 | [-1.814, 7.247] | 4/0/1 |
| B=0: full − labels_only − selection_only + raw | 7 | -1.375 | 0.250 | 5.333 | 0.958 | 6.125 | 2.258 ± 3.291 | [-1.828, 6.345] | 4/0/1 |
| B=0: full − labels_only − selection_only + raw | 8 | -0.167 | 1.000 | 3.417 | 0.250 | 0.333 | 0.967 ± 1.432 | [-0.811, 2.745] | 4/0/1 |
| B=0: full − labels_only − selection_only + raw | 9 | 3.667 | -10.583 | -6.208 | -21.625 | -0.083 | -6.967 ± 9.861 | [-19.211, 5.278] | 1/0/4 |
| B=0.1: full − labels_only | 6 | 6.625 | 1.333 | 4.875 | 1.958 | 0.667 | 3.092 ± 2.546 | [-0.069, 6.253] | 5/0/0 |
| B=0.1: full − labels_only | 7 | 6.417 | 8.792 | -1.583 | 1.333 | -5.625 | 1.867 ± 5.852 | [-5.399, 9.133] | 3/0/2 |
| B=0.1: full − labels_only | 8 | -0.167 | -2.333 | 0.958 | 0.250 | 0.417 | -0.175 ± 1.272 | [-1.755, 1.405] | 3/0/2 |
| B=0.1: full − labels_only | 9 | 1.667 | 3.833 | 8.917 | 7.167 | 5.458 | 5.408 ± 2.823 | [1.903, 8.914] | 5/0/0 |
| B=0.1: full − selection_only | 6 | 7.083 | 0.375 | 5.083 | 4.292 | -2.958 | 2.775 ± 4.026 | [-2.223, 7.773] | 4/0/1 |
| B=0.1: full − selection_only | 7 | -0.417 | 19.083 | -5.792 | -0.042 | 4.125 | 3.392 ± 9.452 | [-8.345, 15.128] | 2/0/3 |
| B=0.1: full − selection_only | 8 | -0.500 | 3.417 | 1.917 | 0.083 | -0.042 | 0.975 ± 1.647 | [-1.070, 3.020] | 3/0/2 |
| B=0.1: full − selection_only | 9 | 3.667 | 6.417 | 14.667 | 2.375 | 5.500 | 6.525 ± 4.815 | [0.546, 12.504] | 5/0/0 |
| B=0.1: full − raw | 6 | 8.417 | 0.083 | 4.292 | 3.875 | -2.000 | 2.933 ± 4.039 | [-2.082, 7.949] | 4/0/1 |
| B=0.1: full − raw | 7 | -0.333 | 11.583 | -5.292 | 1.000 | 2.208 | 1.833 ± 6.151 | [-5.805, 9.471] | 3/0/2 |
| B=0.1: full − raw | 8 | -0.500 | -0.500 | 1.833 | 0.292 | 0.083 | 0.242 ± 0.957 | [-0.946, 1.430] | 3/0/2 |
| B=0.1: full − raw | 9 | 2.083 | 4.917 | 9.500 | -3.625 | 15.958 | 5.767 ± 7.421 | [-3.448, 14.981] | 4/0/1 |
| B=0.1: labels_only − raw | 6 | 1.792 | -1.250 | -0.583 | 1.917 | -2.667 | -0.158 ± 1.986 | [-2.624, 2.307] | 2/0/3 |
| B=0.1: labels_only − raw | 7 | -6.750 | 2.792 | -3.708 | -0.333 | 7.833 | -0.033 ± 5.670 | [-7.073, 7.006] | 2/0/3 |
| B=0.1: labels_only − raw | 8 | -0.333 | 1.833 | 0.875 | 0.042 | -0.333 | 0.417 ± 0.933 | [-0.742, 1.575] | 3/0/2 |
| B=0.1: labels_only − raw | 9 | 0.417 | 1.083 | 0.583 | -10.792 | 10.500 | 0.358 ± 7.546 | [-9.011, 9.728] | 4/0/1 |
| B=0.1: selection_only − raw | 6 | 1.333 | -0.292 | -0.792 | -0.417 | 0.958 | 0.158 ± 0.930 | [-0.996, 1.313] | 2/0/3 |
| B=0.1: selection_only − raw | 7 | 0.083 | -7.500 | 0.500 | 1.042 | -1.917 | -1.558 ± 3.504 | [-5.910, 2.793] | 3/0/2 |
| B=0.1: selection_only − raw | 8 | 0.000 | -3.917 | -0.083 | 0.208 | 0.125 | -0.733 ± 1.783 | [-2.947, 1.481] | 2/1/2 |
| B=0.1: selection_only − raw | 9 | -1.583 | -1.500 | -5.167 | -6.000 | 10.458 | -0.758 ± 6.595 | [-8.947, 7.430] | 1/0/4 |
| B=0.1: full − labels_only − selection_only + raw | 6 | 5.292 | 1.625 | 5.667 | 2.375 | -0.292 | 2.933 ± 2.523 | [-0.199, 6.066] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 7 | 6.333 | 16.292 | -2.083 | 0.292 | -3.708 | 3.425 ± 8.140 | [-6.682, 13.532] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 8 | -0.167 | 1.583 | 1.042 | 0.042 | 0.292 | 0.558 ± 0.733 | [-0.352, 1.468] | 4/0/1 |
| B=0.1: full − labels_only − selection_only + raw | 9 | 3.250 | 5.333 | 14.083 | 13.167 | -5.000 | 6.167 ± 7.835 | [-3.562, 15.896] | 4/0/1 |
| raw: B=0.1 − B=0 | 6 | -1.375 | 0.333 | 1.250 | 0.542 | -0.292 | 0.092 ± 0.988 | [-1.134, 1.318] | 3/0/2 |
| raw: B=0.1 − B=0 | 7 | 3.958 | 3.208 | -0.708 | 1.208 | 4.583 | 2.450 ± 2.175 | [-0.250, 5.150] | 4/0/1 |
| raw: B=0.1 − B=0 | 8 | 0.167 | 0.250 | -1.042 | 0.000 | -0.042 | -0.133 ± 0.522 | [-0.781, 0.514] | 2/1/2 |
| raw: B=0.1 − B=0 | 9 | -1.250 | 8.292 | 6.333 | 2.708 | -9.792 | 1.258 ± 7.171 | [-7.646, 10.163] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 6 | 1.333 | -1.917 | -0.667 | 0.292 | -2.208 | -0.633 ± 1.488 | [-2.480, 1.214] | 2/0/3 |
| labels_only: B=0.1 − B=0 | 7 | -3.292 | 2.250 | 2.083 | -0.208 | 10.542 | 2.275 ± 5.136 | [-4.103, 8.653] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 8 | -0.125 | 2.750 | 0.417 | 0.167 | -0.167 | 0.608 ± 1.220 | [-0.907, 2.124] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 9 | 3.542 | 6.000 | 0.458 | -24.458 | -3.208 | -3.533 ± 12.195 | [-18.675, 11.608] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 6 | -1.042 | -0.375 | 1.125 | -1.375 | 1.042 | -0.125 ± 1.161 | [-1.566, 1.316] | 2/0/3 |
| selection_only: B=0.1 − B=0 | 7 | 1.292 | -7.625 | 5.542 | 4.458 | 3.167 | 1.367 ± 5.270 | [-5.177, 7.910] | 4/0/1 |
| selection_only: B=0.1 − B=0 | 8 | -0.042 | -4.792 | 1.625 | 0.042 | 0.375 | -0.558 ± 2.459 | [-3.612, 2.495] | 3/0/2 |
| selection_only: B=0.1 − B=0 | 9 | -2.833 | -2.292 | -4.833 | -5.167 | -0.917 | -3.208 ± 1.782 | [-5.422, -0.995] | 0/0/5 |
| full: B=0.1 − B=0 | 6 | 0.500 | -2.375 | -1.667 | 2.458 | -2.083 | -0.633 ± 2.064 | [-3.197, 1.930] | 2/0/3 |
| full: B=0.1 − B=0 | 7 | 1.750 | 7.458 | 0.917 | 2.375 | -0.708 | 2.358 ± 3.077 | [-1.462, 6.179] | 4/0/1 |
| full: B=0.1 − B=0 | 8 | -0.333 | -1.708 | 0.708 | 0.000 | 0.208 | -0.225 ± 0.911 | [-1.356, 0.906] | 2/1/2 |
| full: B=0.1 − B=0 | 9 | 1.542 | 11.333 | 9.583 | 2.458 | 0.750 | 5.133 ± 4.937 | [-0.997, 11.264] | 5/0/0 |
| all − selected_fixed (full, B=0.1) | 6 | 1.708 | -0.250 | -1.000 | 0.417 | -1.083 | -0.042 ± 1.153 | [-1.474, 1.390] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 7 | 3.250 | 8.667 | -0.667 | -0.208 | 0.375 | 2.283 ± 3.881 | [-2.535, 7.102] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 8 | -0.333 | -2.250 | 0.125 | 0.292 | 0.208 | -0.392 ± 1.067 | [-1.716, 0.933] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 9 | -2.083 | 11.375 | 17.375 | -6.542 | 4.167 | 4.858 ± 9.718 | [-7.208, 16.925] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 6 | 1.458 | -0.917 | -1.500 | 2.750 | -1.583 | 0.042 ± 1.954 | [-2.385, 2.468] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 7 | 9.083 | 6.667 | -0.208 | -0.083 | 0.542 | 3.200 ± 4.362 | [-2.216, 8.616] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 8 | -0.250 | -2.333 | -0.125 | 0.333 | 0.333 | -0.408 ± 1.108 | [-1.784, 0.967] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 9 | 8.208 | -0.708 | 6.958 | -0.500 | 12.625 | 5.317 ± 5.801 | [-1.886, 12.519] | 3/0/2 |
| softmatch_weight − full (B=0.1) | 6 | -8.458 | 0.875 | -3.750 | -3.542 | 3.333 | -2.308 ± 4.566 | [-7.977, 3.361] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 7 | -3.208 | -18.333 | 1.708 | -7.583 | -9.083 | -7.300 ± 7.465 | [-16.569, 1.969] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 8 | 0.375 | 1.167 | -0.375 | -0.208 | -0.125 | 0.167 ± 0.625 | [-0.609, 0.943] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 9 | 0.542 | 1.333 | -6.292 | 4.250 | -2.750 | -0.583 ± 4.049 | [-5.611, 4.444] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 6 | -1.375 | 1.250 | 1.333 | 0.750 | 0.375 | 0.467 ± 1.101 | [-0.900, 1.833] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 7 | -3.625 | 0.750 | -4.083 | -7.625 | -4.958 | -3.908 ± 3.030 | [-7.671, -0.146] | 1/0/4 |
| softmatch_weight − selection_only (B=0.1) | 8 | -0.125 | 4.583 | 1.542 | -0.125 | -0.167 | 1.142 ± 2.057 | [-1.412, 3.696] | 2/0/3 |
| softmatch_weight − selection_only (B=0.1) | 9 | 4.208 | 7.750 | 8.375 | 6.625 | 2.750 | 5.942 ± 2.390 | [2.974, 8.909] | 5/0/0 |

</details>


<details>
<summary>DIRG：全部逐目标主指标差值（百分点）</summary>

| 对比 | 目标 | seed0 | seed1 | seed2 | seed3 | seed4 | 均值 ± SD | t95区间 | 正/零/负 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B=0: full − labels_only | 0 | 2.768 | -4.464 | 0.089 | -1.161 | 2.411 | -0.071 ± 2.947 | [-3.730, 3.587] | 3/0/2 |
| B=0: full − labels_only | 1 | 0.357 | -5.536 | 2.321 | 4.375 | -1.786 | -0.054 ± 3.823 | [-4.801, 4.694] | 3/0/2 |
| B=0: full − labels_only | 2 | 1.518 | -4.732 | 3.125 | -5.357 | -0.982 | -1.286 ± 3.737 | [-5.926, 3.354] | 2/0/3 |
| B=0: full − labels_only | 3 | -2.321 | 1.250 | 6.429 | 2.589 | -3.304 | 0.929 ± 3.924 | [-3.943, 5.801] | 3/0/2 |
| B=0: full − selection_only | 0 | -1.250 | -2.232 | -5.268 | -0.357 | -0.625 | -1.946 ± 1.992 | [-4.420, 0.527] | 0/0/5 |
| B=0: full − selection_only | 1 | -1.786 | -12.857 | 3.125 | 3.839 | 8.304 | 0.125 ± 8.091 | [-9.922, 10.172] | 3/0/2 |
| B=0: full − selection_only | 2 | 4.375 | 1.161 | 1.071 | -2.321 | 2.321 | 1.321 ± 2.433 | [-1.700, 4.343] | 4/0/1 |
| B=0: full − selection_only | 3 | 0.089 | 1.339 | 8.304 | 4.107 | -2.768 | 2.214 ± 4.206 | [-3.008, 7.437] | 4/0/1 |
| B=0: full − raw | 0 | -3.393 | -0.982 | 1.518 | -0.982 | -3.304 | -1.429 ± 2.028 | [-3.947, 1.090] | 1/0/4 |
| B=0: full − raw | 1 | -3.839 | 1.875 | 4.107 | 8.393 | 1.339 | 2.375 ± 4.448 | [-3.148, 7.898] | 4/0/1 |
| B=0: full − raw | 2 | 3.393 | -1.696 | -0.982 | -2.232 | 2.589 | 0.214 ± 2.589 | [-3.000, 3.429] | 2/0/3 |
| B=0: full − raw | 3 | -3.125 | 8.125 | 10.179 | 4.375 | -3.661 | 3.179 ± 6.352 | [-4.709, 11.066] | 3/0/2 |
| B=0: labels_only − raw | 0 | -6.161 | 3.482 | 1.429 | 0.179 | -5.714 | -1.357 ± 4.347 | [-6.755, 4.041] | 3/0/2 |
| B=0: labels_only − raw | 1 | -4.196 | 7.411 | 1.786 | 4.018 | 3.125 | 2.429 ± 4.247 | [-2.844, 7.701] | 4/0/1 |
| B=0: labels_only − raw | 2 | 1.875 | 3.036 | -4.107 | 3.125 | 3.571 | 1.500 ± 3.197 | [-2.469, 5.469] | 4/0/1 |
| B=0: labels_only − raw | 3 | -0.804 | 6.875 | 3.750 | 1.786 | -0.357 | 2.250 ± 3.161 | [-1.675, 6.175] | 3/0/2 |
| B=0: selection_only − raw | 0 | -2.143 | 1.250 | 6.786 | -0.625 | -2.679 | 0.518 ± 3.822 | [-4.228, 5.263] | 2/0/3 |
| B=0: selection_only − raw | 1 | -2.054 | 14.732 | 0.982 | 4.554 | -6.964 | 2.250 ± 8.157 | [-7.878, 12.378] | 3/0/2 |
| B=0: selection_only − raw | 2 | -0.982 | -2.857 | -2.054 | 0.089 | 0.268 | -1.107 ± 1.351 | [-2.784, 0.570] | 2/0/3 |
| B=0: selection_only − raw | 3 | -3.214 | 6.786 | 1.875 | 0.268 | -0.893 | 0.964 ± 3.745 | [-3.686, 5.615] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 0 | 4.911 | -5.714 | -6.696 | -0.536 | 5.089 | -0.589 ± 5.614 | [-7.560, 6.381] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 1 | 2.411 | -20.268 | 1.339 | -0.179 | 5.179 | -2.304 ± 10.231 | [-15.007, 10.400] | 3/0/2 |
| B=0: full − labels_only − selection_only + raw | 2 | 2.500 | -1.875 | 5.179 | -5.446 | -1.250 | -0.179 ± 4.112 | [-5.285, 4.928] | 2/0/3 |
| B=0: full − labels_only − selection_only + raw | 3 | 0.893 | -5.536 | 4.554 | 2.321 | -2.411 | -0.036 ± 3.980 | [-4.978, 4.906] | 3/0/2 |
| B=0.1: full − labels_only | 0 | 0.179 | -1.696 | 10.804 | 4.464 | 0.000 | 2.750 ± 5.043 | [-3.512, 9.012] | 3/1/1 |
| B=0.1: full − labels_only | 1 | 0.089 | 2.679 | -0.446 | -8.393 | -8.750 | -2.964 ± 5.255 | [-9.489, 3.560] | 2/0/3 |
| B=0.1: full − labels_only | 2 | 0.982 | 2.857 | -2.143 | -2.321 | -2.411 | -0.607 ± 2.402 | [-3.590, 2.375] | 2/0/3 |
| B=0.1: full − labels_only | 3 | -7.054 | 0.714 | 8.304 | -5.268 | -5.804 | -1.821 ± 6.404 | [-9.773, 6.130] | 2/0/3 |
| B=0.1: full − selection_only | 0 | 0.625 | -2.857 | 12.946 | 3.214 | -3.214 | 2.143 ± 6.593 | [-6.043, 10.329] | 3/0/2 |
| B=0.1: full − selection_only | 1 | -0.893 | 17.857 | 5.000 | 5.000 | 2.232 | 5.839 ± 7.144 | [-3.032, 14.710] | 4/0/1 |
| B=0.1: full − selection_only | 2 | 0.714 | 2.054 | -1.071 | -0.625 | -3.482 | -0.482 ± 2.075 | [-3.059, 2.095] | 2/0/3 |
| B=0.1: full − selection_only | 3 | 1.696 | 1.071 | 4.375 | -2.411 | -2.768 | 0.393 ± 2.994 | [-3.325, 4.111] | 3/0/2 |
| B=0.1: full − raw | 0 | 4.018 | -3.304 | 5.714 | 1.518 | 0.089 | 1.607 ± 3.504 | [-2.743, 5.958] | 4/0/1 |
| B=0.1: full − raw | 1 | 0.536 | 11.518 | 3.304 | 3.304 | 1.607 | 4.054 ± 4.336 | [-1.330, 9.437] | 5/0/0 |
| B=0.1: full − raw | 2 | 0.804 | -0.893 | -6.071 | 1.161 | -2.857 | -1.571 ± 2.978 | [-5.269, 2.126] | 2/0/3 |
| B=0.1: full − raw | 3 | -5.625 | 1.071 | 9.732 | -6.250 | -2.768 | -0.768 ± 6.544 | [-8.893, 7.357] | 2/0/3 |
| B=0.1: labels_only − raw | 0 | 3.839 | -1.607 | -5.089 | -2.946 | 0.089 | -1.143 ± 3.368 | [-5.325, 3.039] | 2/0/3 |
| B=0.1: labels_only − raw | 1 | 0.446 | 8.839 | 3.750 | 11.696 | 10.357 | 7.018 ± 4.749 | [1.121, 12.915] | 5/0/0 |
| B=0.1: labels_only − raw | 2 | -0.179 | -3.750 | -3.929 | 3.482 | -0.446 | -0.964 ± 3.050 | [-4.751, 2.822] | 1/0/4 |
| B=0.1: labels_only − raw | 3 | 1.429 | 0.357 | 1.429 | -0.982 | 3.036 | 1.054 ± 1.487 | [-0.792, 2.899] | 4/0/1 |
| B=0.1: selection_only − raw | 0 | 3.393 | -0.446 | -7.232 | -1.696 | 3.304 | -0.536 ± 4.370 | [-5.961, 4.890] | 2/0/3 |
| B=0.1: selection_only − raw | 1 | 1.429 | -6.339 | -1.696 | -1.696 | -0.625 | -1.786 ± 2.847 | [-5.321, 1.750] | 1/0/4 |
| B=0.1: selection_only − raw | 2 | 0.089 | -2.946 | -5.000 | 1.786 | 0.625 | -1.089 ± 2.799 | [-4.565, 2.386] | 3/0/2 |
| B=0.1: selection_only − raw | 3 | -7.321 | 0.000 | 5.357 | -3.839 | 0.000 | -1.161 ± 4.751 | [-7.060, 4.739] | 1/2/2 |
| B=0.1: full − labels_only − selection_only + raw | 0 | -3.214 | -1.250 | 18.036 | 6.161 | -3.304 | 3.286 ± 9.111 | [-8.028, 14.599] | 2/0/3 |
| B=0.1: full − labels_only − selection_only + raw | 1 | -1.339 | 9.018 | 1.250 | -6.696 | -8.125 | -1.179 ± 6.866 | [-9.704, 7.347] | 2/0/3 |
| B=0.1: full − labels_only − selection_only + raw | 2 | 0.893 | 5.804 | 2.857 | -4.107 | -3.036 | 0.482 ± 4.110 | [-4.621, 5.585] | 3/0/2 |
| B=0.1: full − labels_only − selection_only + raw | 3 | 0.268 | 0.714 | 2.946 | -1.429 | -5.804 | -0.661 ± 3.271 | [-4.722, 3.401] | 3/0/2 |
| raw: B=0.1 − B=0 | 0 | -5.536 | 3.393 | 5.536 | 0.893 | -6.339 | -0.411 ± 5.314 | [-7.008, 6.187] | 3/0/2 |
| raw: B=0.1 − B=0 | 1 | -2.232 | 0.268 | -1.875 | 2.768 | -6.696 | -1.554 ± 3.500 | [-5.900, 2.792] | 2/0/3 |
| raw: B=0.1 − B=0 | 2 | -0.893 | 2.143 | 1.071 | -1.339 | 2.946 | 0.786 ± 1.866 | [-1.531, 3.102] | 3/0/2 |
| raw: B=0.1 − B=0 | 3 | 1.071 | 10.089 | -0.357 | 5.179 | -0.714 | 3.054 ± 4.576 | [-2.629, 8.736] | 3/0/2 |
| labels_only: B=0.1 − B=0 | 0 | 4.464 | -1.696 | -0.982 | -2.232 | -0.536 | -0.196 ± 2.686 | [-3.531, 3.138] | 1/0/4 |
| labels_only: B=0.1 − B=0 | 1 | 2.411 | 1.696 | 0.089 | 10.446 | 0.536 | 3.036 ± 4.244 | [-2.233, 8.305] | 5/0/0 |
| labels_only: B=0.1 − B=0 | 2 | -2.946 | -4.643 | 1.250 | -0.982 | -1.071 | -1.679 ± 2.226 | [-4.443, 1.086] | 1/0/4 |
| labels_only: B=0.1 − B=0 | 3 | 3.304 | 3.571 | -2.679 | 2.411 | 2.679 | 1.857 ± 2.578 | [-1.344, 5.058] | 4/0/1 |
| selection_only: B=0.1 − B=0 | 0 | 0.000 | 1.696 | -8.482 | -0.179 | -0.357 | -1.464 ± 4.008 | [-6.441, 3.513] | 1/1/3 |
| selection_only: B=0.1 − B=0 | 1 | 1.250 | -20.804 | -4.554 | -3.482 | -0.357 | -5.589 ± 8.820 | [-16.540, 5.362] | 1/0/4 |
| selection_only: B=0.1 − B=0 | 2 | 0.179 | 2.054 | -1.875 | 0.357 | 3.304 | 0.804 ± 1.973 | [-1.647, 3.254] | 4/0/1 |
| selection_only: B=0.1 − B=0 | 3 | -3.036 | 3.304 | 3.125 | 1.071 | 0.179 | 0.929 ± 2.587 | [-2.283, 4.140] | 4/0/1 |
| full: B=0.1 − B=0 | 0 | 1.875 | 1.071 | 9.732 | 3.393 | -2.946 | 2.625 ± 4.613 | [-3.103, 8.353] | 4/0/1 |
| full: B=0.1 − B=0 | 1 | 2.143 | 9.911 | -2.679 | -2.321 | -6.429 | 0.125 ± 6.258 | [-7.645, 7.895] | 2/0/3 |
| full: B=0.1 − B=0 | 2 | -3.482 | 2.946 | -4.018 | 2.054 | -2.500 | -1.000 ± 3.256 | [-5.043, 3.043] | 2/0/3 |
| full: B=0.1 − B=0 | 3 | -1.429 | 3.036 | -0.804 | -5.446 | 0.179 | -0.893 ± 3.066 | [-4.700, 2.915] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 0 | 0.804 | -1.786 | 6.607 | 3.036 | -3.304 | 1.071 ± 3.933 | [-3.812, 5.955] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 1 | 2.411 | 2.946 | -0.446 | 6.964 | -5.089 | 1.357 ± 4.469 | [-4.192, 6.906] | 3/0/2 |
| all − selected_fixed (full, B=0.1) | 2 | 2.232 | 2.679 | -2.054 | -0.714 | -2.054 | 0.018 ± 2.297 | [-2.834, 2.870] | 2/0/3 |
| all − selected_fixed (full, B=0.1) | 3 | 0.804 | 2.768 | -0.714 | -7.143 | 0.000 | -0.857 ± 3.747 | [-5.510, 3.796] | 2/1/2 |
| all − selected_domain_mean (full, B=0.1) | 0 | -0.357 | -2.679 | 4.464 | 3.125 | -2.321 | 0.446 ± 3.217 | [-3.548, 4.441] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 1 | 2.411 | 3.482 | -1.607 | 8.750 | -10.804 | 0.446 ± 7.294 | [-8.610, 9.503] | 3/0/2 |
| all − selected_domain_mean (full, B=0.1) | 2 | 2.232 | 3.036 | -1.071 | -1.786 | -2.946 | -0.107 ± 2.606 | [-3.343, 3.128] | 2/0/3 |
| all − selected_domain_mean (full, B=0.1) | 3 | -4.107 | 7.232 | -1.518 | -4.018 | -3.393 | -1.161 ± 4.806 | [-7.128, 4.807] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 0 | -2.232 | 5.000 | -1.161 | 0.179 | 3.661 | 1.089 ± 3.116 | [-2.779, 4.958] | 3/0/2 |
| softmatch_weight − full (B=0.1) | 1 | -4.286 | -10.536 | -3.750 | -11.071 | 10.357 | -3.857 ± 8.644 | [-14.590, 6.876] | 1/0/4 |
| softmatch_weight − full (B=0.1) | 2 | -3.661 | -3.482 | 4.018 | 1.071 | -2.143 | -0.839 ± 3.312 | [-4.952, 3.274] | 2/0/3 |
| softmatch_weight − full (B=0.1) | 3 | 9.643 | 0.536 | -1.964 | 8.482 | 1.518 | 3.643 ± 5.124 | [-2.720, 10.005] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 0 | -1.607 | 2.143 | 11.786 | 3.393 | 0.446 | 3.232 ± 5.137 | [-3.146, 9.611] | 4/0/1 |
| softmatch_weight − selection_only (B=0.1) | 1 | -5.179 | 7.321 | 1.250 | -6.071 | 12.589 | 1.982 ± 8.026 | [-7.984, 11.948] | 3/0/2 |
| softmatch_weight − selection_only (B=0.1) | 2 | -2.946 | -1.429 | 2.946 | 0.446 | -5.625 | -1.321 ± 3.260 | [-5.369, 2.727] | 2/0/3 |
| softmatch_weight − selection_only (B=0.1) | 3 | 11.339 | 1.607 | 2.411 | 6.071 | -1.250 | 4.036 ± 4.847 | [-1.982, 10.054] | 4/0/1 |

</details>


## 本轮能回答什么、仍不能排除什么

因素干预：可描述在当前流程下标签/集合联合改变的收益方向、大小及种子重复性。仅有这些目标分数不能区分监督数量、类别构成、成员身份、优化轨迹等解释；需结合主pipeline的集合轨迹诊断。

覆盖范围：selected_fixed是固定分母下删除部分显式一致性项；selected_domain_mean提供分域尺度控制。前向批次、扰动安排、BN及缓冲恢复若未保持一致，不能把差值单独归于覆盖范围。即使掩码去掉某些显式损失，这些样本仍可能经共享BN统计影响计算。

软权重：这是固定骨架与B状态下借鉴SoftMatch的机制适配对照，不是完整复现SoftMatch论文，不能与旧主表的一维CNN适配混为一谈。

完成这一轮用于判断现象是否重复及哪些解释尚未排除；不自动完成因果归因、不自动解释DIRG差异、不把已有模块变为原创算法，也不保证录用。不因某个区间或平均排名自动改参数、换对照或扩大研究范围。

## 原始结果与溯源

summaries.json 的 rows 原样保留全部输入行，包括每类召回率、混淆矩阵、source_folder和额外审计字段。分组与配对统计通过row_id关联原始行；不合格或重复行也保留并单列原因。

<details>
<summary>收到的全部行（不排序、不排名；单目标单种子值）</summary>

| 行索引 | ID | 数据集 | 目标 | 种子 | 状态 | 干净Acc/% | 干净F1/% | source_folder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | PU-t6-s0-factorial-full-B0-all | PU | 6 | 0 | 可用 | 93.500 | 93.409 | runs/pu_distribution_v1/t6-s0-distribution |
| 1 | PU-t6-s0-factorial-labels_only-B0-all | PU | 6 | 0 | 可用 | 86.042 | 83.475 | runs/da_b_factorial_v1/cases/PU-t6-s0/labels_only |
| 2 | PU-t6-s0-factorial-raw-B0-all | PU | 6 | 0 | 可用 | 86.958 | 84.109 | runs/pu_v1/t6-s0-baseline |
| 3 | PU-t6-s0-factorial-selection_only-B0-all | PU | 6 | 0 | 可用 | 87.958 | 85.177 | runs/da_b_factorial_v1/cases/PU-t6-s0/selection_only |
| 4 | PU-t6-s0-factorial-full-B1-all | PU | 6 | 0 | 可用 | 94.000 | 93.919 | runs/pu_distribution_v1/t6-s0-distribution_consistency |
| 5 | PU-t6-s0-factorial-labels_only-B1-all | PU | 6 | 0 | 可用 | 87.375 | 84.892 | runs/da_component_intervention_v1/cases/PU-t6-s0/labels_only |
| 6 | PU-t6-s0-factorial-raw-B1-all | PU | 6 | 0 | 可用 | 85.583 | 82.651 | runs/pu_v1/t6-s0-stat_consistency |
| 7 | PU-t6-s0-factorial-selection_only-B1-all | PU | 6 | 0 | 可用 | 86.917 | 84.066 | runs/da_component_intervention_v1/cases/PU-t6-s0/selection_only |
| 8 | PU-t6-s0-coverage-full-B1-selected_domain_mean | PU | 6 | 0 | 可用 | 92.542 | 92.490 | runs/pc2g_research_audit_20260924/cells/PU-t6-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 9 | PU-t6-s0-coverage-full-B1-selected_fixed | PU | 6 | 0 | 可用 | 92.292 | 92.088 | runs/pc2g_research_audit_20260924/cells/PU-t6-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 10 | PU-t6-s0-soft_weight-softmatch_weight-B1-all | PU | 6 | 0 | 可用 | 85.542 | 82.776 | runs/pc2g_research_audit_20260924/cells/PU-t6-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 11 | DIRG-t0-s0-factorial-full-B0-all | DIRG | 0 | 0 | 可用 | 64.196 | 55.785 | runs/dirg_da_b_v1/cases/t0-s0-DA |
| 12 | DIRG-t0-s0-factorial-labels_only-B0-all | DIRG | 0 | 0 | 可用 | 61.429 | 53.589 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-factorial-labels_only-B0-all/attempt_01 |
| 13 | DIRG-t0-s0-factorial-raw-B0-all | DIRG | 0 | 0 | 可用 | 67.589 | 60.235 | runs/dirg_da_b_v1/cases/t0-s0-baseline |
| 14 | DIRG-t0-s0-factorial-selection_only-B0-all | DIRG | 0 | 0 | 可用 | 65.446 | 57.384 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-factorial-selection_only-B0-all/attempt_01 |
| 15 | DIRG-t0-s0-factorial-full-B1-all | DIRG | 0 | 0 | 可用 | 66.071 | 58.116 | runs/dirg_da_b_v1/cases/t0-s0-DA_B |
| 16 | DIRG-t0-s0-factorial-labels_only-B1-all | DIRG | 0 | 0 | 可用 | 65.893 | 57.552 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-factorial-labels_only-B1-all/attempt_01 |
| 17 | DIRG-t0-s0-factorial-raw-B1-all | DIRG | 0 | 0 | 可用 | 62.054 | 54.045 | runs/dirg_da_b_v1/cases/t0-s0-B |
| 18 | DIRG-t0-s0-factorial-selection_only-B1-all | DIRG | 0 | 0 | 可用 | 65.446 | 56.998 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-factorial-selection_only-B1-all/attempt_01 |
| 19 | DIRG-t0-s0-coverage-full-B1-selected_domain_mean | DIRG | 0 | 0 | 可用 | 66.429 | 58.741 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 20 | DIRG-t0-s0-coverage-full-B1-selected_fixed | DIRG | 0 | 0 | 可用 | 65.268 | 57.158 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 21 | DIRG-t0-s0-soft_weight-softmatch_weight-B1-all | DIRG | 0 | 0 | 可用 | 63.839 | 54.915 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 22 | PU-t7-s0-factorial-full-B0-all | PU | 7 | 0 | 可用 | 69.542 | 61.655 | runs/pu_distribution_v1/t7-s0-distribution |
| 23 | PU-t7-s0-factorial-labels_only-B0-all | PU | 7 | 0 | 可用 | 68.167 | 63.468 | runs/da_b_factorial_v1/cases/PU-t7-s0/labels_only |
| 24 | PU-t7-s0-factorial-raw-B0-all | PU | 7 | 0 | 可用 | 67.667 | 61.210 | runs/pu_v1/t7-s0-baseline |
| 25 | PU-t7-s0-factorial-selection_only-B0-all | PU | 7 | 0 | 可用 | 70.417 | 64.963 | runs/da_b_factorial_v1/cases/PU-t7-s0/selection_only |
| 26 | PU-t7-s0-factorial-full-B1-all | PU | 7 | 0 | 可用 | 71.292 | 64.839 | runs/pu_distribution_v1/t7-s0-distribution_consistency |
| 27 | PU-t7-s0-factorial-labels_only-B1-all | PU | 7 | 0 | 可用 | 64.875 | 60.331 | runs/da_component_intervention_v1/cases/PU-t7-s0/labels_only |
| 28 | PU-t7-s0-factorial-raw-B1-all | PU | 7 | 0 | 可用 | 71.625 | 64.307 | runs/pu_v1/t7-s0-stat_consistency |
| 29 | PU-t7-s0-factorial-selection_only-B1-all | PU | 7 | 0 | 可用 | 71.708 | 63.442 | runs/da_component_intervention_v1/cases/PU-t7-s0/selection_only |
| 30 | PU-t7-s0-coverage-full-B1-selected_domain_mean | PU | 7 | 0 | 可用 | 62.208 | 58.234 | runs/pc2g_research_audit_20260924/cells/PU-t7-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 31 | PU-t7-s0-coverage-full-B1-selected_fixed | PU | 7 | 0 | 可用 | 68.042 | 60.958 | runs/pc2g_research_audit_20260924/cells/PU-t7-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 32 | PU-t7-s0-soft_weight-softmatch_weight-B1-all | PU | 7 | 0 | 可用 | 68.083 | 63.385 | runs/pc2g_research_audit_20260924/cells/PU-t7-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 33 | DIRG-t1-s0-factorial-full-B0-all | DIRG | 1 | 0 | 可用 | 32.589 | 25.156 | runs/dirg_da_b_v1/cases/t1-s0-DA |
| 34 | DIRG-t1-s0-factorial-labels_only-B0-all | DIRG | 1 | 0 | 可用 | 32.232 | 25.741 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-factorial-labels_only-B0-all/attempt_01 |
| 35 | DIRG-t1-s0-factorial-raw-B0-all | DIRG | 1 | 0 | 可用 | 36.429 | 29.591 | runs/dirg_da_b_v1/cases/t1-s0-baseline |
| 36 | DIRG-t1-s0-factorial-selection_only-B0-all | DIRG | 1 | 0 | 可用 | 34.375 | 26.553 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-factorial-selection_only-B0-all/attempt_01 |
| 37 | DIRG-t1-s0-factorial-full-B1-all | DIRG | 1 | 0 | 可用 | 34.732 | 26.509 | runs/dirg_da_b_v1/cases/t1-s0-DA_B |
| 38 | DIRG-t1-s0-factorial-labels_only-B1-all | DIRG | 1 | 0 | 可用 | 34.643 | 27.939 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-factorial-labels_only-B1-all/attempt_01 |
| 39 | DIRG-t1-s0-factorial-raw-B1-all | DIRG | 1 | 0 | 可用 | 34.196 | 27.861 | runs/dirg_da_b_v1/cases/t1-s0-B |
| 40 | DIRG-t1-s0-factorial-selection_only-B1-all | DIRG | 1 | 0 | 可用 | 35.625 | 28.368 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-factorial-selection_only-B1-all/attempt_01 |
| 41 | DIRG-t1-s0-coverage-full-B1-selected_domain_mean | DIRG | 1 | 0 | 可用 | 32.321 | 25.074 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 42 | DIRG-t1-s0-coverage-full-B1-selected_fixed | DIRG | 1 | 0 | 可用 | 32.321 | 25.000 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 43 | DIRG-t1-s0-soft_weight-softmatch_weight-B1-all | DIRG | 1 | 0 | 可用 | 30.446 | 22.443 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 44 | PU-t8-s0-factorial-full-B0-all | PU | 8 | 0 | 可用 | 99.667 | 99.667 | runs/pu_distribution_v1/t8-s0-distribution |
| 45 | PU-t8-s0-factorial-labels_only-B0-all | PU | 8 | 0 | 可用 | 99.625 | 99.625 | runs/da_b_factorial_v1/cases/PU-t8-s0/labels_only |
| 46 | PU-t8-s0-factorial-raw-B0-all | PU | 8 | 0 | 可用 | 99.667 | 99.668 | runs/pu_v1/t8-s0-baseline |
| 47 | PU-t8-s0-factorial-selection_only-B0-all | PU | 8 | 0 | 可用 | 99.875 | 99.875 | runs/da_b_factorial_v1/cases/PU-t8-s0/selection_only |
| 48 | PU-t8-s0-factorial-full-B1-all | PU | 8 | 0 | 可用 | 99.333 | 99.334 | runs/pu_distribution_v1/t8-s0-distribution_consistency |
| 49 | PU-t8-s0-factorial-labels_only-B1-all | PU | 8 | 0 | 可用 | 99.500 | 99.500 | runs/da_component_intervention_v1/cases/PU-t8-s0/labels_only |
| 50 | PU-t8-s0-factorial-raw-B1-all | PU | 8 | 0 | 可用 | 99.833 | 99.833 | runs/pu_v1/t8-s0-stat_consistency |
| 51 | PU-t8-s0-factorial-selection_only-B1-all | PU | 8 | 0 | 可用 | 99.833 | 99.833 | runs/da_component_intervention_v1/cases/PU-t8-s0/selection_only |
| 52 | PU-t8-s0-coverage-full-B1-selected_domain_mean | PU | 8 | 0 | 可用 | 99.583 | 99.584 | runs/pc2g_research_audit_20260924/cells/PU-t8-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 53 | PU-t8-s0-coverage-full-B1-selected_fixed | PU | 8 | 0 | 可用 | 99.667 | 99.666 | runs/pc2g_research_audit_20260924/cells/PU-t8-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 54 | PU-t8-s0-soft_weight-softmatch_weight-B1-all | PU | 8 | 0 | 可用 | 99.708 | 99.709 | runs/pc2g_research_audit_20260924/cells/PU-t8-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 55 | DIRG-t2-s0-factorial-full-B0-all | DIRG | 2 | 0 | 可用 | 42.054 | 38.599 | runs/dirg_da_b_v1/cases/t2-s0-DA |
| 56 | DIRG-t2-s0-factorial-labels_only-B0-all | DIRG | 2 | 0 | 可用 | 40.536 | 38.026 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-factorial-labels_only-B0-all/attempt_01 |
| 57 | DIRG-t2-s0-factorial-raw-B0-all | DIRG | 2 | 0 | 可用 | 38.661 | 35.085 | runs/dirg_da_b_v1/cases/t2-s0-baseline |
| 58 | DIRG-t2-s0-factorial-selection_only-B0-all | DIRG | 2 | 0 | 可用 | 37.679 | 35.238 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-factorial-selection_only-B0-all/attempt_01 |
| 59 | DIRG-t2-s0-factorial-full-B1-all | DIRG | 2 | 0 | 可用 | 38.571 | 35.223 | runs/dirg_da_b_v1/cases/t2-s0-DA_B |
| 60 | DIRG-t2-s0-factorial-labels_only-B1-all | DIRG | 2 | 0 | 可用 | 37.589 | 35.197 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-factorial-labels_only-B1-all/attempt_01 |
| 61 | DIRG-t2-s0-factorial-raw-B1-all | DIRG | 2 | 0 | 可用 | 37.768 | 34.667 | runs/dirg_da_b_v1/cases/t2-s0-B |
| 62 | DIRG-t2-s0-factorial-selection_only-B1-all | DIRG | 2 | 0 | 可用 | 37.857 | 34.051 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-factorial-selection_only-B1-all/attempt_01 |
| 63 | DIRG-t2-s0-coverage-full-B1-selected_domain_mean | DIRG | 2 | 0 | 可用 | 36.339 | 33.555 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 64 | DIRG-t2-s0-coverage-full-B1-selected_fixed | DIRG | 2 | 0 | 可用 | 36.339 | 33.906 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 65 | DIRG-t2-s0-soft_weight-softmatch_weight-B1-all | DIRG | 2 | 0 | 可用 | 34.911 | 31.379 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 66 | PU-t9-s0-factorial-full-B0-all | PU | 9 | 0 | 可用 | 44.958 | 35.599 | runs/pu_distribution_v1/t9-s0-distribution |
| 67 | PU-t9-s0-factorial-labels_only-B0-all | PU | 9 | 0 | 可用 | 41.292 | 34.968 | runs/da_b_factorial_v1/cases/PU-t9-s0/labels_only |
| 68 | PU-t9-s0-factorial-raw-B0-all | PU | 9 | 0 | 可用 | 45.667 | 37.153 | runs/pu_v1/t9-s0-baseline |
| 69 | PU-t9-s0-factorial-selection_only-B0-all | PU | 9 | 0 | 可用 | 45.667 | 39.744 | runs/da_b_factorial_v1/cases/PU-t9-s0/selection_only |
| 70 | PU-t9-s0-factorial-full-B1-all | PU | 9 | 0 | 可用 | 46.500 | 37.574 | runs/pu_distribution_v1/t9-s0-distribution_consistency |
| 71 | PU-t9-s0-factorial-labels_only-B1-all | PU | 9 | 0 | 可用 | 44.833 | 38.403 | runs/da_component_intervention_v1/cases/PU-t9-s0/labels_only |
| 72 | PU-t9-s0-factorial-raw-B1-all | PU | 9 | 0 | 可用 | 44.417 | 38.017 | runs/pu_v1/t9-s0-stat_consistency |
| 73 | PU-t9-s0-factorial-selection_only-B1-all | PU | 9 | 0 | 可用 | 42.833 | 37.196 | runs/da_component_intervention_v1/cases/PU-t9-s0/selection_only |
| 74 | PU-t9-s0-coverage-full-B1-selected_domain_mean | PU | 9 | 0 | 可用 | 38.292 | 32.823 | runs/pc2g_research_audit_20260924/cells/PU-t9-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 75 | PU-t9-s0-coverage-full-B1-selected_fixed | PU | 9 | 0 | 可用 | 48.583 | 38.697 | runs/pc2g_research_audit_20260924/cells/PU-t9-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 76 | PU-t9-s0-soft_weight-softmatch_weight-B1-all | PU | 9 | 0 | 可用 | 47.042 | 41.637 | runs/pc2g_research_audit_20260924/cells/PU-t9-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 77 | DIRG-t3-s0-factorial-full-B0-all | DIRG | 3 | 0 | 可用 | 63.482 | 64.516 | runs/dirg_da_b_v1/cases/t3-s0-DA |
| 78 | DIRG-t3-s0-factorial-labels_only-B0-all | DIRG | 3 | 0 | 可用 | 65.804 | 64.729 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-factorial-labels_only-B0-all/attempt_01 |
| 79 | DIRG-t3-s0-factorial-raw-B0-all | DIRG | 3 | 0 | 可用 | 66.607 | 63.798 | runs/dirg_da_b_v1/cases/t3-s0-baseline |
| 80 | DIRG-t3-s0-factorial-selection_only-B0-all | DIRG | 3 | 0 | 可用 | 63.393 | 60.512 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-factorial-selection_only-B0-all/attempt_01 |
| 81 | DIRG-t3-s0-factorial-full-B1-all | DIRG | 3 | 0 | 可用 | 62.054 | 61.471 | runs/dirg_da_b_v1/cases/t3-s0-DA_B |
| 82 | DIRG-t3-s0-factorial-labels_only-B1-all | DIRG | 3 | 0 | 可用 | 69.107 | 66.943 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-factorial-labels_only-B1-all/attempt_01 |
| 83 | DIRG-t3-s0-factorial-raw-B1-all | DIRG | 3 | 0 | 可用 | 67.679 | 64.837 | runs/dirg_da_b_v1/cases/t3-s0-B |
| 84 | DIRG-t3-s0-factorial-selection_only-B1-all | DIRG | 3 | 0 | 可用 | 60.357 | 61.590 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-factorial-selection_only-B1-all/attempt_01 |
| 85 | DIRG-t3-s0-coverage-full-B1-selected_domain_mean | DIRG | 3 | 0 | 可用 | 66.161 | 63.884 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-coverage-full-B1-selected_domain_mean/attempt_01 |
| 86 | DIRG-t3-s0-coverage-full-B1-selected_fixed | DIRG | 3 | 0 | 可用 | 61.250 | 63.453 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-coverage-full-B1-selected_fixed/attempt_01 |
| 87 | DIRG-t3-s0-soft_weight-softmatch_weight-B1-all | DIRG | 3 | 0 | 可用 | 71.696 | 69.404 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s0-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 88 | PU-t6-s1-factorial-full-B0-all | PU | 6 | 1 | 可用 | 92.542 | 91.895 | runs/pu_distribution_seeds12/t6-s1-distribution |
| 89 | PU-t6-s1-factorial-labels_only-B0-all | PU | 6 | 1 | 可用 | 90.750 | 88.235 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-factorial-labels_only-B0-all/attempt_01 |
| 90 | PU-t6-s1-factorial-raw-B0-all | PU | 6 | 1 | 可用 | 89.750 | 86.965 | runs/pu_b_seeds12/t6-s1-baseline |
| 91 | PU-t6-s1-factorial-selection_only-B0-all | PU | 6 | 1 | 可用 | 90.167 | 87.624 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-factorial-selection_only-B0-all/attempt_01 |
| 92 | PU-t6-s1-factorial-full-B1-all | PU | 6 | 1 | 可用 | 90.167 | 88.276 | runs/pu_distribution_seeds12/t6-s1-distribution_consistency |
| 93 | PU-t6-s1-factorial-labels_only-B1-all | PU | 6 | 1 | 可用 | 88.833 | 86.154 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-factorial-labels_only-B1-all/attempt_01 |
| 94 | PU-t6-s1-factorial-raw-B1-all | PU | 6 | 1 | 可用 | 90.083 | 87.299 | runs/pu_b_seeds12/t6-s1-stat_consistency |
| 95 | PU-t6-s1-factorial-selection_only-B1-all | PU | 6 | 1 | 可用 | 89.792 | 86.998 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-factorial-selection_only-B1-all/attempt_01 |
| 96 | PU-t6-s1-coverage-full-B1-selected_domain_mean | PU | 6 | 1 | 可用 | 91.083 | 89.315 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 97 | PU-t6-s1-coverage-full-B1-selected_fixed | PU | 6 | 1 | 可用 | 90.417 | 88.671 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 98 | PU-t6-s1-soft_weight-softmatch_weight-B1-all | PU | 6 | 1 | 可用 | 91.042 | 88.315 | runs/pc2g_research_audit_20260924/cells/PU-t6-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 99 | DIRG-t0-s1-factorial-full-B0-all | DIRG | 0 | 1 | 可用 | 66.071 | 59.818 | runs/dirg_da_b_v1/cases/t0-s1-DA |
| 100 | DIRG-t0-s1-factorial-labels_only-B0-all | DIRG | 0 | 1 | 可用 | 70.536 | 63.964 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-factorial-labels_only-B0-all/attempt_01 |
| 101 | DIRG-t0-s1-factorial-raw-B0-all | DIRG | 0 | 1 | 可用 | 67.054 | 62.792 | runs/dirg_da_b_v1/cases/t0-s1-baseline |
| 102 | DIRG-t0-s1-factorial-selection_only-B0-all | DIRG | 0 | 1 | 可用 | 68.304 | 63.513 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-factorial-selection_only-B0-all/attempt_01 |
| 103 | DIRG-t0-s1-factorial-full-B1-all | DIRG | 0 | 1 | 可用 | 67.143 | 60.402 | runs/dirg_da_b_v1/cases/t0-s1-DA_B |
| 104 | DIRG-t0-s1-factorial-labels_only-B1-all | DIRG | 0 | 1 | 可用 | 68.839 | 62.766 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-factorial-labels_only-B1-all/attempt_01 |
| 105 | DIRG-t0-s1-factorial-raw-B1-all | DIRG | 0 | 1 | 可用 | 70.446 | 65.468 | runs/dirg_da_b_v1/cases/t0-s1-B |
| 106 | DIRG-t0-s1-factorial-selection_only-B1-all | DIRG | 0 | 1 | 可用 | 70.000 | 64.087 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-factorial-selection_only-B1-all/attempt_01 |
| 107 | DIRG-t0-s1-coverage-full-B1-selected_domain_mean | DIRG | 0 | 1 | 可用 | 69.821 | 63.684 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 108 | DIRG-t0-s1-coverage-full-B1-selected_fixed | DIRG | 0 | 1 | 可用 | 68.929 | 63.988 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 109 | DIRG-t0-s1-soft_weight-softmatch_weight-B1-all | DIRG | 0 | 1 | 可用 | 72.143 | 65.988 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 110 | PU-t7-s1-factorial-full-B0-all | PU | 7 | 1 | 可用 | 61.500 | 53.231 | runs/pu_distribution_seeds12/t7-s1-distribution |
| 111 | PU-t7-s1-factorial-labels_only-B0-all | PU | 7 | 1 | 可用 | 57.917 | 53.118 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-factorial-labels_only-B0-all/attempt_01 |
| 112 | PU-t7-s1-factorial-raw-B0-all | PU | 7 | 1 | 可用 | 54.167 | 49.040 | runs/pu_b_seeds12/t7-s1-baseline |
| 113 | PU-t7-s1-factorial-selection_only-B0-all | PU | 7 | 1 | 可用 | 57.500 | 53.575 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-factorial-selection_only-B0-all/attempt_01 |
| 114 | PU-t7-s1-factorial-full-B1-all | PU | 7 | 1 | 可用 | 68.958 | 63.610 | runs/pu_distribution_seeds12/t7-s1-distribution_consistency |
| 115 | PU-t7-s1-factorial-labels_only-B1-all | PU | 7 | 1 | 可用 | 60.167 | 55.034 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-factorial-labels_only-B1-all/attempt_01 |
| 116 | PU-t7-s1-factorial-raw-B1-all | PU | 7 | 1 | 可用 | 57.375 | 51.942 | runs/pu_b_seeds12/t7-s1-stat_consistency |
| 117 | PU-t7-s1-factorial-selection_only-B1-all | PU | 7 | 1 | 可用 | 49.875 | 46.235 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-factorial-selection_only-B1-all/attempt_01 |
| 118 | PU-t7-s1-coverage-full-B1-selected_domain_mean | PU | 7 | 1 | 可用 | 62.292 | 54.691 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 119 | PU-t7-s1-coverage-full-B1-selected_fixed | PU | 7 | 1 | 可用 | 60.292 | 54.582 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 120 | PU-t7-s1-soft_weight-softmatch_weight-B1-all | PU | 7 | 1 | 可用 | 50.625 | 46.826 | runs/pc2g_research_audit_20260924/cells/PU-t7-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 121 | DIRG-t1-s1-factorial-full-B0-all | DIRG | 1 | 1 | 可用 | 40.536 | 37.723 | runs/dirg_da_b_v1/cases/t1-s1-DA |
| 122 | DIRG-t1-s1-factorial-labels_only-B0-all | DIRG | 1 | 1 | 可用 | 46.071 | 47.380 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-factorial-labels_only-B0-all/attempt_01 |
| 123 | DIRG-t1-s1-factorial-raw-B0-all | DIRG | 1 | 1 | 可用 | 38.661 | 36.434 | runs/dirg_da_b_v1/cases/t1-s1-baseline |
| 124 | DIRG-t1-s1-factorial-selection_only-B0-all | DIRG | 1 | 1 | 可用 | 53.393 | 54.640 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-factorial-selection_only-B0-all/attempt_01 |
| 125 | DIRG-t1-s1-factorial-full-B1-all | DIRG | 1 | 1 | 可用 | 50.446 | 49.666 | runs/dirg_da_b_v1/cases/t1-s1-DA_B |
| 126 | DIRG-t1-s1-factorial-labels_only-B1-all | DIRG | 1 | 1 | 可用 | 47.768 | 46.954 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-factorial-labels_only-B1-all/attempt_01 |
| 127 | DIRG-t1-s1-factorial-raw-B1-all | DIRG | 1 | 1 | 可用 | 38.929 | 38.050 | runs/dirg_da_b_v1/cases/t1-s1-B |
| 128 | DIRG-t1-s1-factorial-selection_only-B1-all | DIRG | 1 | 1 | 可用 | 32.589 | 31.741 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-factorial-selection_only-B1-all/attempt_01 |
| 129 | DIRG-t1-s1-coverage-full-B1-selected_domain_mean | DIRG | 1 | 1 | 可用 | 46.964 | 43.514 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 130 | DIRG-t1-s1-coverage-full-B1-selected_fixed | DIRG | 1 | 1 | 可用 | 47.500 | 45.833 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 131 | DIRG-t1-s1-soft_weight-softmatch_weight-B1-all | DIRG | 1 | 1 | 可用 | 39.911 | 38.798 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 132 | PU-t8-s1-factorial-full-B0-all | PU | 8 | 1 | 可用 | 98.875 | 98.874 | runs/pu_distribution_seeds12/t8-s1-distribution |
| 133 | PU-t8-s1-factorial-labels_only-B0-all | PU | 8 | 1 | 可用 | 96.750 | 96.682 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-factorial-labels_only-B0-all/attempt_01 |
| 134 | PU-t8-s1-factorial-raw-B0-all | PU | 8 | 1 | 可用 | 97.417 | 97.386 | runs/pu_b_seeds12/t8-s1-baseline |
| 135 | PU-t8-s1-factorial-selection_only-B0-all | PU | 8 | 1 | 可用 | 98.542 | 98.539 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-factorial-selection_only-B0-all/attempt_01 |
| 136 | PU-t8-s1-factorial-full-B1-all | PU | 8 | 1 | 可用 | 97.167 | 97.122 | runs/pu_distribution_seeds12/t8-s1-distribution_consistency |
| 137 | PU-t8-s1-factorial-labels_only-B1-all | PU | 8 | 1 | 可用 | 99.500 | 99.499 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-factorial-labels_only-B1-all/attempt_01 |
| 138 | PU-t8-s1-factorial-raw-B1-all | PU | 8 | 1 | 可用 | 97.667 | 97.642 | runs/pu_b_seeds12/t8-s1-stat_consistency |
| 139 | PU-t8-s1-factorial-selection_only-B1-all | PU | 8 | 1 | 可用 | 93.750 | 92.815 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-factorial-selection_only-B1-all/attempt_01 |
| 140 | PU-t8-s1-coverage-full-B1-selected_domain_mean | PU | 8 | 1 | 可用 | 99.500 | 99.501 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 141 | PU-t8-s1-coverage-full-B1-selected_fixed | PU | 8 | 1 | 可用 | 99.417 | 99.417 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 142 | PU-t8-s1-soft_weight-softmatch_weight-B1-all | PU | 8 | 1 | 可用 | 98.333 | 98.327 | runs/pc2g_research_audit_20260924/cells/PU-t8-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 143 | DIRG-t2-s1-factorial-full-B0-all | DIRG | 2 | 1 | 可用 | 31.339 | 30.330 | runs/dirg_da_b_v1/cases/t2-s1-DA |
| 144 | DIRG-t2-s1-factorial-labels_only-B0-all | DIRG | 2 | 1 | 可用 | 36.071 | 33.814 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-factorial-labels_only-B0-all/attempt_01 |
| 145 | DIRG-t2-s1-factorial-raw-B0-all | DIRG | 2 | 1 | 可用 | 33.036 | 32.764 | runs/dirg_da_b_v1/cases/t2-s1-baseline |
| 146 | DIRG-t2-s1-factorial-selection_only-B0-all | DIRG | 2 | 1 | 可用 | 30.179 | 29.816 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-factorial-selection_only-B0-all/attempt_01 |
| 147 | DIRG-t2-s1-factorial-full-B1-all | DIRG | 2 | 1 | 可用 | 34.286 | 32.631 | runs/dirg_da_b_v1/cases/t2-s1-DA_B |
| 148 | DIRG-t2-s1-factorial-labels_only-B1-all | DIRG | 2 | 1 | 可用 | 31.429 | 30.549 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-factorial-labels_only-B1-all/attempt_01 |
| 149 | DIRG-t2-s1-factorial-raw-B1-all | DIRG | 2 | 1 | 可用 | 35.179 | 33.469 | runs/dirg_da_b_v1/cases/t2-s1-B |
| 150 | DIRG-t2-s1-factorial-selection_only-B1-all | DIRG | 2 | 1 | 可用 | 32.232 | 31.640 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-factorial-selection_only-B1-all/attempt_01 |
| 151 | DIRG-t2-s1-coverage-full-B1-selected_domain_mean | DIRG | 2 | 1 | 可用 | 31.250 | 31.027 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 152 | DIRG-t2-s1-coverage-full-B1-selected_fixed | DIRG | 2 | 1 | 可用 | 31.607 | 30.630 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 153 | DIRG-t2-s1-soft_weight-softmatch_weight-B1-all | DIRG | 2 | 1 | 可用 | 30.804 | 29.951 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 154 | PU-t9-s1-factorial-full-B0-all | PU | 9 | 1 | 可用 | 32.708 | 25.209 | runs/pu_distribution_seeds12/t9-s1-distribution |
| 155 | PU-t9-s1-factorial-labels_only-B0-all | PU | 9 | 1 | 可用 | 34.208 | 31.042 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-factorial-labels_only-B0-all/attempt_01 |
| 156 | PU-t9-s1-factorial-raw-B0-all | PU | 9 | 1 | 可用 | 30.833 | 26.337 | runs/pu_b_seeds12/t9-s1-baseline |
| 157 | PU-t9-s1-factorial-selection_only-B0-all | PU | 9 | 1 | 可用 | 39.917 | 33.239 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-factorial-selection_only-B0-all/attempt_01 |
| 158 | PU-t9-s1-factorial-full-B1-all | PU | 9 | 1 | 可用 | 44.042 | 37.880 | runs/pu_distribution_seeds12/t9-s1-distribution_consistency |
| 159 | PU-t9-s1-factorial-labels_only-B1-all | PU | 9 | 1 | 可用 | 40.208 | 36.272 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-factorial-labels_only-B1-all/attempt_01 |
| 160 | PU-t9-s1-factorial-raw-B1-all | PU | 9 | 1 | 可用 | 39.125 | 32.765 | runs/pu_b_seeds12/t9-s1-stat_consistency |
| 161 | PU-t9-s1-factorial-selection_only-B1-all | PU | 9 | 1 | 可用 | 37.625 | 30.264 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-factorial-selection_only-B1-all/attempt_01 |
| 162 | PU-t9-s1-coverage-full-B1-selected_domain_mean | PU | 9 | 1 | 可用 | 44.750 | 37.783 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 163 | PU-t9-s1-coverage-full-B1-selected_fixed | PU | 9 | 1 | 可用 | 32.667 | 25.522 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 164 | PU-t9-s1-soft_weight-softmatch_weight-B1-all | PU | 9 | 1 | 可用 | 45.375 | 41.896 | runs/pc2g_research_audit_20260924/cells/PU-t9-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 165 | DIRG-t3-s1-factorial-full-B0-all | DIRG | 3 | 1 | 可用 | 51.071 | 46.540 | runs/dirg_da_b_v1/cases/t3-s1-DA |
| 166 | DIRG-t3-s1-factorial-labels_only-B0-all | DIRG | 3 | 1 | 可用 | 49.821 | 45.693 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-factorial-labels_only-B0-all/attempt_01 |
| 167 | DIRG-t3-s1-factorial-raw-B0-all | DIRG | 3 | 1 | 可用 | 42.946 | 37.848 | runs/dirg_da_b_v1/cases/t3-s1-baseline |
| 168 | DIRG-t3-s1-factorial-selection_only-B0-all | DIRG | 3 | 1 | 可用 | 49.732 | 44.772 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-factorial-selection_only-B0-all/attempt_01 |
| 169 | DIRG-t3-s1-factorial-full-B1-all | DIRG | 3 | 1 | 可用 | 54.107 | 52.886 | runs/dirg_da_b_v1/cases/t3-s1-DA_B |
| 170 | DIRG-t3-s1-factorial-labels_only-B1-all | DIRG | 3 | 1 | 可用 | 53.393 | 48.162 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-factorial-labels_only-B1-all/attempt_01 |
| 171 | DIRG-t3-s1-factorial-raw-B1-all | DIRG | 3 | 1 | 可用 | 53.036 | 48.578 | runs/dirg_da_b_v1/cases/t3-s1-B |
| 172 | DIRG-t3-s1-factorial-selection_only-B1-all | DIRG | 3 | 1 | 可用 | 53.036 | 47.921 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-factorial-selection_only-B1-all/attempt_01 |
| 173 | DIRG-t3-s1-coverage-full-B1-selected_domain_mean | DIRG | 3 | 1 | 可用 | 46.875 | 45.227 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-coverage-full-B1-selected_domain_mean/attempt_01 |
| 174 | DIRG-t3-s1-coverage-full-B1-selected_fixed | DIRG | 3 | 1 | 可用 | 51.339 | 46.989 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-coverage-full-B1-selected_fixed/attempt_01 |
| 175 | DIRG-t3-s1-soft_weight-softmatch_weight-B1-all | DIRG | 3 | 1 | 可用 | 54.643 | 50.445 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s1-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 176 | PU-t6-s2-factorial-full-B0-all | PU | 6 | 2 | 可用 | 94.167 | 94.035 | runs/pu_distribution_seeds12/t6-s2-distribution |
| 177 | PU-t6-s2-factorial-labels_only-B0-all | PU | 6 | 2 | 可用 | 88.292 | 85.535 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-factorial-labels_only-B0-all/attempt_01 |
| 178 | PU-t6-s2-factorial-raw-B0-all | PU | 6 | 2 | 可用 | 86.958 | 83.800 | runs/pu_b_seeds12/t6-s2-baseline |
| 179 | PU-t6-s2-factorial-selection_only-B0-all | PU | 6 | 2 | 可用 | 86.292 | 83.391 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-factorial-selection_only-B0-all/attempt_01 |
| 180 | PU-t6-s2-factorial-full-B1-all | PU | 6 | 2 | 可用 | 92.500 | 92.156 | runs/pu_distribution_seeds12/t6-s2-distribution_consistency |
| 181 | PU-t6-s2-factorial-labels_only-B1-all | PU | 6 | 2 | 可用 | 87.625 | 84.754 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-factorial-labels_only-B1-all/attempt_01 |
| 182 | PU-t6-s2-factorial-raw-B1-all | PU | 6 | 2 | 可用 | 88.208 | 85.296 | runs/pu_b_seeds12/t6-s2-stat_consistency |
| 183 | PU-t6-s2-factorial-selection_only-B1-all | PU | 6 | 2 | 可用 | 87.417 | 84.580 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-factorial-selection_only-B1-all/attempt_01 |
| 184 | PU-t6-s2-coverage-full-B1-selected_domain_mean | PU | 6 | 2 | 可用 | 94.000 | 93.848 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 185 | PU-t6-s2-coverage-full-B1-selected_fixed | PU | 6 | 2 | 可用 | 93.500 | 93.324 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 186 | PU-t6-s2-soft_weight-softmatch_weight-B1-all | PU | 6 | 2 | 可用 | 88.750 | 85.938 | runs/pc2g_research_audit_20260924/cells/PU-t6-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 187 | DIRG-t0-s2-factorial-full-B0-all | DIRG | 0 | 2 | 可用 | 59.107 | 54.004 | runs/dirg_da_b_v1/cases/t0-s2-DA |
| 188 | DIRG-t0-s2-factorial-labels_only-B0-all | DIRG | 0 | 2 | 可用 | 59.018 | 53.380 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-factorial-labels_only-B0-all/attempt_01 |
| 189 | DIRG-t0-s2-factorial-raw-B0-all | DIRG | 0 | 2 | 可用 | 57.589 | 51.201 | runs/dirg_da_b_v1/cases/t0-s2-baseline |
| 190 | DIRG-t0-s2-factorial-selection_only-B0-all | DIRG | 0 | 2 | 可用 | 64.375 | 59.496 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-factorial-selection_only-B0-all/attempt_01 |
| 191 | DIRG-t0-s2-factorial-full-B1-all | DIRG | 0 | 2 | 可用 | 68.839 | 64.705 | runs/dirg_da_b_v1/cases/t0-s2-DA_B |
| 192 | DIRG-t0-s2-factorial-labels_only-B1-all | DIRG | 0 | 2 | 可用 | 58.036 | 51.915 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-factorial-labels_only-B1-all/attempt_01 |
| 193 | DIRG-t0-s2-factorial-raw-B1-all | DIRG | 0 | 2 | 可用 | 63.125 | 58.100 | runs/dirg_da_b_v1/cases/t0-s2-B |
| 194 | DIRG-t0-s2-factorial-selection_only-B1-all | DIRG | 0 | 2 | 可用 | 55.893 | 48.144 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-factorial-selection_only-B1-all/attempt_01 |
| 195 | DIRG-t0-s2-coverage-full-B1-selected_domain_mean | DIRG | 0 | 2 | 可用 | 64.375 | 58.926 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 196 | DIRG-t0-s2-coverage-full-B1-selected_fixed | DIRG | 0 | 2 | 可用 | 62.232 | 57.162 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 197 | DIRG-t0-s2-soft_weight-softmatch_weight-B1-all | DIRG | 0 | 2 | 可用 | 67.679 | 63.092 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 198 | PU-t7-s2-factorial-full-B0-all | PU | 7 | 2 | 可用 | 61.375 | 51.284 | runs/pu_distribution_seeds12/t7-s2-distribution |
| 199 | PU-t7-s2-factorial-labels_only-B0-all | PU | 7 | 2 | 可用 | 61.792 | 56.135 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-factorial-labels_only-B0-all/attempt_01 |
| 200 | PU-t7-s2-factorial-raw-B0-all | PU | 7 | 2 | 可用 | 68.292 | 63.635 | runs/pu_b_seeds12/t7-s2-baseline |
| 201 | PU-t7-s2-factorial-selection_only-B0-all | PU | 7 | 2 | 可用 | 62.542 | 55.023 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-factorial-selection_only-B0-all/attempt_01 |
| 202 | PU-t7-s2-factorial-full-B1-all | PU | 7 | 2 | 可用 | 62.292 | 54.134 | runs/pu_distribution_seeds12/t7-s2-distribution_consistency |
| 203 | PU-t7-s2-factorial-labels_only-B1-all | PU | 7 | 2 | 可用 | 63.875 | 58.559 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-factorial-labels_only-B1-all/attempt_01 |
| 204 | PU-t7-s2-factorial-raw-B1-all | PU | 7 | 2 | 可用 | 67.583 | 62.704 | runs/pu_b_seeds12/t7-s2-stat_consistency |
| 205 | PU-t7-s2-factorial-selection_only-B1-all | PU | 7 | 2 | 可用 | 68.083 | 61.288 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-factorial-selection_only-B1-all/attempt_01 |
| 206 | PU-t7-s2-coverage-full-B1-selected_domain_mean | PU | 7 | 2 | 可用 | 62.500 | 54.560 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 207 | PU-t7-s2-coverage-full-B1-selected_fixed | PU | 7 | 2 | 可用 | 62.958 | 56.555 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 208 | PU-t7-s2-soft_weight-softmatch_weight-B1-all | PU | 7 | 2 | 可用 | 64.000 | 59.597 | runs/pc2g_research_audit_20260924/cells/PU-t7-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 209 | DIRG-t1-s2-factorial-full-B0-all | DIRG | 1 | 2 | 可用 | 52.946 | 49.376 | runs/dirg_da_b_v1/cases/t1-s2-DA |
| 210 | DIRG-t1-s2-factorial-labels_only-B0-all | DIRG | 1 | 2 | 可用 | 50.625 | 47.858 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-factorial-labels_only-B0-all/attempt_01 |
| 211 | DIRG-t1-s2-factorial-raw-B0-all | DIRG | 1 | 2 | 可用 | 48.839 | 45.752 | runs/dirg_da_b_v1/cases/t1-s2-baseline |
| 212 | DIRG-t1-s2-factorial-selection_only-B0-all | DIRG | 1 | 2 | 可用 | 49.821 | 45.121 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-factorial-selection_only-B0-all/attempt_01 |
| 213 | DIRG-t1-s2-factorial-full-B1-all | DIRG | 1 | 2 | 可用 | 50.268 | 45.840 | runs/dirg_da_b_v1/cases/t1-s2-DA_B |
| 214 | DIRG-t1-s2-factorial-labels_only-B1-all | DIRG | 1 | 2 | 可用 | 50.714 | 46.494 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-factorial-labels_only-B1-all/attempt_01 |
| 215 | DIRG-t1-s2-factorial-raw-B1-all | DIRG | 1 | 2 | 可用 | 46.964 | 43.808 | runs/dirg_da_b_v1/cases/t1-s2-B |
| 216 | DIRG-t1-s2-factorial-selection_only-B1-all | DIRG | 1 | 2 | 可用 | 45.268 | 41.221 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-factorial-selection_only-B1-all/attempt_01 |
| 217 | DIRG-t1-s2-coverage-full-B1-selected_domain_mean | DIRG | 1 | 2 | 可用 | 51.875 | 48.742 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 218 | DIRG-t1-s2-coverage-full-B1-selected_fixed | DIRG | 1 | 2 | 可用 | 50.714 | 47.892 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 219 | DIRG-t1-s2-soft_weight-softmatch_weight-B1-all | DIRG | 1 | 2 | 可用 | 46.518 | 42.699 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 220 | PU-t8-s2-factorial-full-B0-all | PU | 8 | 2 | 可用 | 97.708 | 97.690 | runs/pu_distribution_seeds12/t8-s2-distribution |
| 221 | PU-t8-s2-factorial-labels_only-B0-all | PU | 8 | 2 | 可用 | 97.042 | 97.027 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-factorial-labels_only-B0-all/attempt_01 |
| 222 | PU-t8-s2-factorial-raw-B0-all | PU | 8 | 2 | 可用 | 97.625 | 97.576 | runs/pu_b_seeds12/t8-s2-baseline |
| 223 | PU-t8-s2-factorial-selection_only-B0-all | PU | 8 | 2 | 可用 | 94.875 | 94.448 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-factorial-selection_only-B0-all/attempt_01 |
| 224 | PU-t8-s2-factorial-full-B1-all | PU | 8 | 2 | 可用 | 98.417 | 98.414 | runs/pu_distribution_seeds12/t8-s2-distribution_consistency |
| 225 | PU-t8-s2-factorial-labels_only-B1-all | PU | 8 | 2 | 可用 | 97.458 | 97.434 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-factorial-labels_only-B1-all/attempt_01 |
| 226 | PU-t8-s2-factorial-raw-B1-all | PU | 8 | 2 | 可用 | 96.583 | 96.455 | runs/pu_b_seeds12/t8-s2-stat_consistency |
| 227 | PU-t8-s2-factorial-selection_only-B1-all | PU | 8 | 2 | 可用 | 96.500 | 96.409 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-factorial-selection_only-B1-all/attempt_01 |
| 228 | PU-t8-s2-coverage-full-B1-selected_domain_mean | PU | 8 | 2 | 可用 | 98.542 | 98.540 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 229 | PU-t8-s2-coverage-full-B1-selected_fixed | PU | 8 | 2 | 可用 | 98.292 | 98.291 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 230 | PU-t8-s2-soft_weight-softmatch_weight-B1-all | PU | 8 | 2 | 可用 | 98.042 | 98.015 | runs/pc2g_research_audit_20260924/cells/PU-t8-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 231 | DIRG-t2-s2-factorial-full-B0-all | DIRG | 2 | 2 | 可用 | 41.339 | 34.916 | runs/dirg_da_b_v1/cases/t2-s2-DA |
| 232 | DIRG-t2-s2-factorial-labels_only-B0-all | DIRG | 2 | 2 | 可用 | 38.214 | 32.407 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-factorial-labels_only-B0-all/attempt_01 |
| 233 | DIRG-t2-s2-factorial-raw-B0-all | DIRG | 2 | 2 | 可用 | 42.321 | 36.308 | runs/dirg_da_b_v1/cases/t2-s2-baseline |
| 234 | DIRG-t2-s2-factorial-selection_only-B0-all | DIRG | 2 | 2 | 可用 | 40.268 | 33.303 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-factorial-selection_only-B0-all/attempt_01 |
| 235 | DIRG-t2-s2-factorial-full-B1-all | DIRG | 2 | 2 | 可用 | 37.321 | 30.682 | runs/dirg_da_b_v1/cases/t2-s2-DA_B |
| 236 | DIRG-t2-s2-factorial-labels_only-B1-all | DIRG | 2 | 2 | 可用 | 39.464 | 33.646 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-factorial-labels_only-B1-all/attempt_01 |
| 237 | DIRG-t2-s2-factorial-raw-B1-all | DIRG | 2 | 2 | 可用 | 43.393 | 37.301 | runs/dirg_da_b_v1/cases/t2-s2-B |
| 238 | DIRG-t2-s2-factorial-selection_only-B1-all | DIRG | 2 | 2 | 可用 | 38.393 | 31.716 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-factorial-selection_only-B1-all/attempt_01 |
| 239 | DIRG-t2-s2-coverage-full-B1-selected_domain_mean | DIRG | 2 | 2 | 可用 | 38.393 | 32.138 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 240 | DIRG-t2-s2-coverage-full-B1-selected_fixed | DIRG | 2 | 2 | 可用 | 39.375 | 32.471 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 241 | DIRG-t2-s2-soft_weight-softmatch_weight-B1-all | DIRG | 2 | 2 | 可用 | 41.339 | 34.145 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 242 | PU-t9-s2-factorial-full-B0-all | PU | 9 | 2 | 可用 | 38.917 | 33.003 | runs/pu_distribution_seeds12/t9-s2-distribution |
| 243 | PU-t9-s2-factorial-labels_only-B0-all | PU | 9 | 2 | 可用 | 39.125 | 34.485 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-factorial-labels_only-B0-all/attempt_01 |
| 244 | PU-t9-s2-factorial-raw-B0-all | PU | 9 | 2 | 可用 | 32.667 | 28.276 | runs/pu_b_seeds12/t9-s2-baseline |
| 245 | PU-t9-s2-factorial-selection_only-B0-all | PU | 9 | 2 | 可用 | 38.667 | 33.858 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-factorial-selection_only-B0-all/attempt_01 |
| 246 | PU-t9-s2-factorial-full-B1-all | PU | 9 | 2 | 可用 | 48.500 | 42.451 | runs/pu_distribution_seeds12/t9-s2-distribution_consistency |
| 247 | PU-t9-s2-factorial-labels_only-B1-all | PU | 9 | 2 | 可用 | 39.583 | 35.192 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-factorial-labels_only-B1-all/attempt_01 |
| 248 | PU-t9-s2-factorial-raw-B1-all | PU | 9 | 2 | 可用 | 39.000 | 34.663 | runs/pu_b_seeds12/t9-s2-stat_consistency |
| 249 | PU-t9-s2-factorial-selection_only-B1-all | PU | 9 | 2 | 可用 | 33.833 | 30.337 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-factorial-selection_only-B1-all/attempt_01 |
| 250 | PU-t9-s2-coverage-full-B1-selected_domain_mean | PU | 9 | 2 | 可用 | 41.542 | 36.453 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 251 | PU-t9-s2-coverage-full-B1-selected_fixed | PU | 9 | 2 | 可用 | 31.125 | 27.307 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 252 | PU-t9-s2-soft_weight-softmatch_weight-B1-all | PU | 9 | 2 | 可用 | 42.208 | 37.703 | runs/pc2g_research_audit_20260924/cells/PU-t9-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 253 | DIRG-t3-s2-factorial-full-B0-all | DIRG | 3 | 2 | 可用 | 52.411 | 49.644 | runs/dirg_da_b_v1/cases/t3-s2-DA |
| 254 | DIRG-t3-s2-factorial-labels_only-B0-all | DIRG | 3 | 2 | 可用 | 45.982 | 42.470 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-factorial-labels_only-B0-all/attempt_01 |
| 255 | DIRG-t3-s2-factorial-raw-B0-all | DIRG | 3 | 2 | 可用 | 42.232 | 38.890 | runs/dirg_da_b_v1/cases/t3-s2-baseline |
| 256 | DIRG-t3-s2-factorial-selection_only-B0-all | DIRG | 3 | 2 | 可用 | 44.107 | 42.984 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-factorial-selection_only-B0-all/attempt_01 |
| 257 | DIRG-t3-s2-factorial-full-B1-all | DIRG | 3 | 2 | 可用 | 51.607 | 49.015 | runs/dirg_da_b_v1/cases/t3-s2-DA_B |
| 258 | DIRG-t3-s2-factorial-labels_only-B1-all | DIRG | 3 | 2 | 可用 | 43.304 | 41.899 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-factorial-labels_only-B1-all/attempt_01 |
| 259 | DIRG-t3-s2-factorial-raw-B1-all | DIRG | 3 | 2 | 可用 | 41.875 | 39.924 | runs/dirg_da_b_v1/cases/t3-s2-B |
| 260 | DIRG-t3-s2-factorial-selection_only-B1-all | DIRG | 3 | 2 | 可用 | 47.232 | 45.957 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-factorial-selection_only-B1-all/attempt_01 |
| 261 | DIRG-t3-s2-coverage-full-B1-selected_domain_mean | DIRG | 3 | 2 | 可用 | 53.125 | 50.183 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-coverage-full-B1-selected_domain_mean/attempt_01 |
| 262 | DIRG-t3-s2-coverage-full-B1-selected_fixed | DIRG | 3 | 2 | 可用 | 52.321 | 49.680 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-coverage-full-B1-selected_fixed/attempt_01 |
| 263 | DIRG-t3-s2-soft_weight-softmatch_weight-B1-all | DIRG | 3 | 2 | 可用 | 49.643 | 48.459 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s2-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 264 | PU-t6-s3-factorial-full-B0-all | PU | 6 | 3 | 可用 | 89.000 | 88.021 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-DA |
| 265 | PU-t6-s3-factorial-labels_only-B0-all | PU | 6 | 3 | 可用 | 89.208 | 86.879 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-factorial-labels_only-B0-all/attempt_01 |
| 266 | PU-t6-s3-factorial-raw-B0-all | PU | 6 | 3 | 可用 | 87.042 | 84.332 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-baseline |
| 267 | PU-t6-s3-factorial-selection_only-B0-all | PU | 6 | 3 | 可用 | 88.542 | 85.919 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-factorial-selection_only-B0-all/attempt_01 |
| 268 | PU-t6-s3-factorial-full-B1-all | PU | 6 | 3 | 可用 | 91.458 | 91.186 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-DA_B |
| 269 | PU-t6-s3-factorial-labels_only-B1-all | PU | 6 | 3 | 可用 | 89.500 | 87.182 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-factorial-labels_only-B1-all/attempt_01 |
| 270 | PU-t6-s3-factorial-raw-B1-all | PU | 6 | 3 | 可用 | 87.583 | 84.843 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s3-B |
| 271 | PU-t6-s3-factorial-selection_only-B1-all | PU | 6 | 3 | 可用 | 87.167 | 84.478 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-factorial-selection_only-B1-all/attempt_01 |
| 272 | PU-t6-s3-coverage-full-B1-selected_domain_mean | PU | 6 | 3 | 可用 | 88.708 | 87.651 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 273 | PU-t6-s3-coverage-full-B1-selected_fixed | PU | 6 | 3 | 可用 | 91.042 | 90.785 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 274 | PU-t6-s3-soft_weight-softmatch_weight-B1-all | PU | 6 | 3 | 可用 | 87.917 | 85.092 | runs/pc2g_research_audit_20260924/cells/PU-t6-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 275 | DIRG-t0-s3-factorial-full-B0-all | DIRG | 0 | 3 | 可用 | 63.661 | 56.689 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-DA |
| 276 | DIRG-t0-s3-factorial-labels_only-B0-all | DIRG | 0 | 3 | 可用 | 64.821 | 56.657 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-factorial-labels_only-B0-all/attempt_01 |
| 277 | DIRG-t0-s3-factorial-raw-B0-all | DIRG | 0 | 3 | 可用 | 64.643 | 56.691 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-baseline |
| 278 | DIRG-t0-s3-factorial-selection_only-B0-all | DIRG | 0 | 3 | 可用 | 64.018 | 56.288 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-factorial-selection_only-B0-all/attempt_01 |
| 279 | DIRG-t0-s3-factorial-full-B1-all | DIRG | 0 | 3 | 可用 | 67.054 | 60.671 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-DA_B |
| 280 | DIRG-t0-s3-factorial-labels_only-B1-all | DIRG | 0 | 3 | 可用 | 62.589 | 56.057 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-factorial-labels_only-B1-all/attempt_01 |
| 281 | DIRG-t0-s3-factorial-raw-B1-all | DIRG | 0 | 3 | 可用 | 65.536 | 57.377 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s3-B |
| 282 | DIRG-t0-s3-factorial-selection_only-B1-all | DIRG | 0 | 3 | 可用 | 63.839 | 56.153 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-factorial-selection_only-B1-all/attempt_01 |
| 283 | DIRG-t0-s3-coverage-full-B1-selected_domain_mean | DIRG | 0 | 3 | 可用 | 63.929 | 56.745 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 284 | DIRG-t0-s3-coverage-full-B1-selected_fixed | DIRG | 0 | 3 | 可用 | 64.018 | 56.635 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 285 | DIRG-t0-s3-soft_weight-softmatch_weight-B1-all | DIRG | 0 | 3 | 可用 | 67.232 | 58.200 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 286 | PU-t7-s3-factorial-full-B0-all | PU | 7 | 3 | 可用 | 70.250 | 64.809 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-DA |
| 287 | PU-t7-s3-factorial-labels_only-B0-all | PU | 7 | 3 | 可用 | 71.500 | 65.384 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-factorial-labels_only-B0-all/attempt_01 |
| 288 | PU-t7-s3-factorial-raw-B0-all | PU | 7 | 3 | 可用 | 70.417 | 63.792 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-baseline |
| 289 | PU-t7-s3-factorial-selection_only-B0-all | PU | 7 | 3 | 可用 | 68.208 | 63.137 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-factorial-selection_only-B0-all/attempt_01 |
| 290 | PU-t7-s3-factorial-full-B1-all | PU | 7 | 3 | 可用 | 72.625 | 65.852 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-DA_B |
| 291 | PU-t7-s3-factorial-labels_only-B1-all | PU | 7 | 3 | 可用 | 71.292 | 64.953 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-factorial-labels_only-B1-all/attempt_01 |
| 292 | PU-t7-s3-factorial-raw-B1-all | PU | 7 | 3 | 可用 | 71.625 | 65.433 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s3-B |
| 293 | PU-t7-s3-factorial-selection_only-B1-all | PU | 7 | 3 | 可用 | 72.667 | 66.029 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-factorial-selection_only-B1-all/attempt_01 |
| 294 | PU-t7-s3-coverage-full-B1-selected_domain_mean | PU | 7 | 3 | 可用 | 72.708 | 66.475 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 295 | PU-t7-s3-coverage-full-B1-selected_fixed | PU | 7 | 3 | 可用 | 72.833 | 66.534 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 296 | PU-t7-s3-soft_weight-softmatch_weight-B1-all | PU | 7 | 3 | 可用 | 65.042 | 59.276 | runs/pc2g_research_audit_20260924/cells/PU-t7-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 297 | DIRG-t1-s3-factorial-full-B0-all | DIRG | 1 | 3 | 可用 | 55.625 | 54.072 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-DA |
| 298 | DIRG-t1-s3-factorial-labels_only-B0-all | DIRG | 1 | 3 | 可用 | 51.250 | 49.857 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-factorial-labels_only-B0-all/attempt_01 |
| 299 | DIRG-t1-s3-factorial-raw-B0-all | DIRG | 1 | 3 | 可用 | 47.232 | 44.331 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-baseline |
| 300 | DIRG-t1-s3-factorial-selection_only-B0-all | DIRG | 1 | 3 | 可用 | 51.786 | 49.525 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-factorial-selection_only-B0-all/attempt_01 |
| 301 | DIRG-t1-s3-factorial-full-B1-all | DIRG | 1 | 3 | 可用 | 53.304 | 53.227 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-DA_B |
| 302 | DIRG-t1-s3-factorial-labels_only-B1-all | DIRG | 1 | 3 | 可用 | 61.696 | 59.669 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-factorial-labels_only-B1-all/attempt_01 |
| 303 | DIRG-t1-s3-factorial-raw-B1-all | DIRG | 1 | 3 | 可用 | 50.000 | 48.100 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s3-B |
| 304 | DIRG-t1-s3-factorial-selection_only-B1-all | DIRG | 1 | 3 | 可用 | 48.304 | 46.409 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-factorial-selection_only-B1-all/attempt_01 |
| 305 | DIRG-t1-s3-coverage-full-B1-selected_domain_mean | DIRG | 1 | 3 | 可用 | 44.554 | 40.613 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 306 | DIRG-t1-s3-coverage-full-B1-selected_fixed | DIRG | 1 | 3 | 可用 | 46.339 | 43.964 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 307 | DIRG-t1-s3-soft_weight-softmatch_weight-B1-all | DIRG | 1 | 3 | 可用 | 42.232 | 40.028 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 308 | PU-t8-s3-factorial-full-B0-all | PU | 8 | 3 | 可用 | 99.875 | 99.875 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-DA |
| 309 | PU-t8-s3-factorial-labels_only-B0-all | PU | 8 | 3 | 可用 | 99.458 | 99.458 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-factorial-labels_only-B0-all/attempt_01 |
| 310 | PU-t8-s3-factorial-raw-B0-all | PU | 8 | 3 | 可用 | 99.583 | 99.583 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-baseline |
| 311 | PU-t8-s3-factorial-selection_only-B0-all | PU | 8 | 3 | 可用 | 99.750 | 99.750 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-factorial-selection_only-B0-all/attempt_01 |
| 312 | PU-t8-s3-factorial-full-B1-all | PU | 8 | 3 | 可用 | 99.875 | 99.875 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-DA_B |
| 313 | PU-t8-s3-factorial-labels_only-B1-all | PU | 8 | 3 | 可用 | 99.625 | 99.626 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-factorial-labels_only-B1-all/attempt_01 |
| 314 | PU-t8-s3-factorial-raw-B1-all | PU | 8 | 3 | 可用 | 99.583 | 99.582 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s3-B |
| 315 | PU-t8-s3-factorial-selection_only-B1-all | PU | 8 | 3 | 可用 | 99.792 | 99.791 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-factorial-selection_only-B1-all/attempt_01 |
| 316 | PU-t8-s3-coverage-full-B1-selected_domain_mean | PU | 8 | 3 | 可用 | 99.542 | 99.542 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 317 | PU-t8-s3-coverage-full-B1-selected_fixed | PU | 8 | 3 | 可用 | 99.583 | 99.584 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 318 | PU-t8-s3-soft_weight-softmatch_weight-B1-all | PU | 8 | 3 | 可用 | 99.667 | 99.667 | runs/pc2g_research_audit_20260924/cells/PU-t8-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 319 | DIRG-t2-s3-factorial-full-B0-all | DIRG | 2 | 3 | 可用 | 52.589 | 47.639 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-DA |
| 320 | DIRG-t2-s3-factorial-labels_only-B0-all | DIRG | 2 | 3 | 可用 | 57.946 | 52.170 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-factorial-labels_only-B0-all/attempt_01 |
| 321 | DIRG-t2-s3-factorial-raw-B0-all | DIRG | 2 | 3 | 可用 | 54.821 | 49.944 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-baseline |
| 322 | DIRG-t2-s3-factorial-selection_only-B0-all | DIRG | 2 | 3 | 可用 | 54.911 | 50.156 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-factorial-selection_only-B0-all/attempt_01 |
| 323 | DIRG-t2-s3-factorial-full-B1-all | DIRG | 2 | 3 | 可用 | 54.643 | 50.270 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-DA_B |
| 324 | DIRG-t2-s3-factorial-labels_only-B1-all | DIRG | 2 | 3 | 可用 | 56.964 | 50.462 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-factorial-labels_only-B1-all/attempt_01 |
| 325 | DIRG-t2-s3-factorial-raw-B1-all | DIRG | 2 | 3 | 可用 | 53.482 | 48.206 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s3-B |
| 326 | DIRG-t2-s3-factorial-selection_only-B1-all | DIRG | 2 | 3 | 可用 | 55.268 | 49.794 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-factorial-selection_only-B1-all/attempt_01 |
| 327 | DIRG-t2-s3-coverage-full-B1-selected_domain_mean | DIRG | 2 | 3 | 可用 | 56.429 | 51.347 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 328 | DIRG-t2-s3-coverage-full-B1-selected_fixed | DIRG | 2 | 3 | 可用 | 55.357 | 49.116 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 329 | DIRG-t2-s3-soft_weight-softmatch_weight-B1-all | DIRG | 2 | 3 | 可用 | 55.714 | 50.856 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 330 | PU-t9-s3-factorial-full-B0-all | PU | 9 | 3 | 可用 | 36.708 | 31.922 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-DA |
| 331 | PU-t9-s3-factorial-labels_only-B0-all | PU | 9 | 3 | 可用 | 56.458 | 49.860 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-factorial-labels_only-B0-all/attempt_01 |
| 332 | PU-t9-s3-factorial-raw-B0-all | PU | 9 | 3 | 可用 | 40.083 | 34.573 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-baseline |
| 333 | PU-t9-s3-factorial-selection_only-B0-all | PU | 9 | 3 | 可用 | 41.958 | 35.017 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-factorial-selection_only-B0-all/attempt_01 |
| 334 | PU-t9-s3-factorial-full-B1-all | PU | 9 | 3 | 可用 | 39.167 | 32.338 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-DA_B |
| 335 | PU-t9-s3-factorial-labels_only-B1-all | PU | 9 | 3 | 可用 | 32.000 | 26.107 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-factorial-labels_only-B1-all/attempt_01 |
| 336 | PU-t9-s3-factorial-raw-B1-all | PU | 9 | 3 | 可用 | 42.792 | 36.915 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s3-B |
| 337 | PU-t9-s3-factorial-selection_only-B1-all | PU | 9 | 3 | 可用 | 36.792 | 31.239 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-factorial-selection_only-B1-all/attempt_01 |
| 338 | PU-t9-s3-coverage-full-B1-selected_domain_mean | PU | 9 | 3 | 可用 | 39.667 | 32.240 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 339 | PU-t9-s3-coverage-full-B1-selected_fixed | PU | 9 | 3 | 可用 | 45.708 | 38.679 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 340 | PU-t9-s3-soft_weight-softmatch_weight-B1-all | PU | 9 | 3 | 可用 | 43.417 | 37.508 | runs/pc2g_research_audit_20260924/cells/PU-t9-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 341 | DIRG-t3-s3-factorial-full-B0-all | DIRG | 3 | 3 | 可用 | 49.107 | 47.707 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-DA |
| 342 | DIRG-t3-s3-factorial-labels_only-B0-all | DIRG | 3 | 3 | 可用 | 46.518 | 45.277 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-factorial-labels_only-B0-all/attempt_01 |
| 343 | DIRG-t3-s3-factorial-raw-B0-all | DIRG | 3 | 3 | 可用 | 44.732 | 42.198 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-baseline |
| 344 | DIRG-t3-s3-factorial-selection_only-B0-all | DIRG | 3 | 3 | 可用 | 45.000 | 41.835 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-factorial-selection_only-B0-all/attempt_01 |
| 345 | DIRG-t3-s3-factorial-full-B1-all | DIRG | 3 | 3 | 可用 | 43.661 | 41.703 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-DA_B |
| 346 | DIRG-t3-s3-factorial-labels_only-B1-all | DIRG | 3 | 3 | 可用 | 48.929 | 46.792 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-factorial-labels_only-B1-all/attempt_01 |
| 347 | DIRG-t3-s3-factorial-raw-B1-all | DIRG | 3 | 3 | 可用 | 49.911 | 49.339 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s3-B |
| 348 | DIRG-t3-s3-factorial-selection_only-B1-all | DIRG | 3 | 3 | 可用 | 46.071 | 41.715 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-factorial-selection_only-B1-all/attempt_01 |
| 349 | DIRG-t3-s3-coverage-full-B1-selected_domain_mean | DIRG | 3 | 3 | 可用 | 47.679 | 45.348 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-coverage-full-B1-selected_domain_mean/attempt_01 |
| 350 | DIRG-t3-s3-coverage-full-B1-selected_fixed | DIRG | 3 | 3 | 可用 | 50.804 | 49.695 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-coverage-full-B1-selected_fixed/attempt_01 |
| 351 | DIRG-t3-s3-soft_weight-softmatch_weight-B1-all | DIRG | 3 | 3 | 可用 | 52.143 | 49.050 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s3-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 352 | PU-t6-s4-factorial-full-B0-all | PU | 6 | 4 | 可用 | 97.250 | 97.241 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-DA |
| 353 | PU-t6-s4-factorial-labels_only-B0-all | PU | 6 | 4 | 可用 | 96.708 | 96.699 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-factorial-labels_only-B0-all/attempt_01 |
| 354 | PU-t6-s4-factorial-raw-B0-all | PU | 6 | 4 | 可用 | 97.458 | 97.452 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-baseline |
| 355 | PU-t6-s4-factorial-selection_only-B0-all | PU | 6 | 4 | 可用 | 97.083 | 97.077 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-factorial-selection_only-B0-all/attempt_01 |
| 356 | PU-t6-s4-factorial-full-B1-all | PU | 6 | 4 | 可用 | 95.167 | 95.163 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-DA_B |
| 357 | PU-t6-s4-factorial-labels_only-B1-all | PU | 6 | 4 | 可用 | 94.500 | 94.390 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-factorial-labels_only-B1-all/attempt_01 |
| 358 | PU-t6-s4-factorial-raw-B1-all | PU | 6 | 4 | 可用 | 97.167 | 97.157 | runs/da_b_five_seed_followup_v1/cases/PU-t6-s4-B |
| 359 | PU-t6-s4-factorial-selection_only-B1-all | PU | 6 | 4 | 可用 | 98.125 | 98.119 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-factorial-selection_only-B1-all/attempt_01 |
| 360 | PU-t6-s4-coverage-full-B1-selected_domain_mean | PU | 6 | 4 | 可用 | 96.750 | 96.740 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 361 | PU-t6-s4-coverage-full-B1-selected_fixed | PU | 6 | 4 | 可用 | 96.250 | 96.235 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 362 | PU-t6-s4-soft_weight-softmatch_weight-B1-all | PU | 6 | 4 | 可用 | 98.500 | 98.495 | runs/pc2g_research_audit_20260924/cells/PU-t6-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 363 | DIRG-t0-s4-factorial-full-B0-all | DIRG | 0 | 4 | 可用 | 72.768 | 68.211 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-DA |
| 364 | DIRG-t0-s4-factorial-labels_only-B0-all | DIRG | 0 | 4 | 可用 | 70.357 | 64.307 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-factorial-labels_only-B0-all/attempt_01 |
| 365 | DIRG-t0-s4-factorial-raw-B0-all | DIRG | 0 | 4 | 可用 | 76.071 | 72.878 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-baseline |
| 366 | DIRG-t0-s4-factorial-selection_only-B0-all | DIRG | 0 | 4 | 可用 | 73.393 | 69.593 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-factorial-selection_only-B0-all/attempt_01 |
| 367 | DIRG-t0-s4-factorial-full-B1-all | DIRG | 0 | 4 | 可用 | 69.821 | 64.784 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-DA_B |
| 368 | DIRG-t0-s4-factorial-labels_only-B1-all | DIRG | 0 | 4 | 可用 | 69.821 | 64.379 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-factorial-labels_only-B1-all/attempt_01 |
| 369 | DIRG-t0-s4-factorial-raw-B1-all | DIRG | 0 | 4 | 可用 | 69.732 | 65.189 | runs/da_b_five_seed_followup_v1/cases/DIRG-t0-s4-B |
| 370 | DIRG-t0-s4-factorial-selection_only-B1-all | DIRG | 0 | 4 | 可用 | 73.036 | 69.339 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-factorial-selection_only-B1-all/attempt_01 |
| 371 | DIRG-t0-s4-coverage-full-B1-selected_domain_mean | DIRG | 0 | 4 | 可用 | 72.143 | 67.824 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 372 | DIRG-t0-s4-coverage-full-B1-selected_fixed | DIRG | 0 | 4 | 可用 | 73.125 | 69.266 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 373 | DIRG-t0-s4-soft_weight-softmatch_weight-B1-all | DIRG | 0 | 4 | 可用 | 73.482 | 69.905 | runs/pc2g_research_audit_20260924/cells/DIRG-t0-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 374 | PU-t7-s4-factorial-full-B0-all | PU | 7 | 4 | 可用 | 64.583 | 57.764 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-DA |
| 375 | PU-t7-s4-factorial-labels_only-B0-all | PU | 7 | 4 | 可用 | 58.958 | 50.803 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-factorial-labels_only-B0-all/attempt_01 |
| 376 | PU-t7-s4-factorial-raw-B0-all | PU | 7 | 4 | 可用 | 57.083 | 48.885 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-baseline |
| 377 | PU-t7-s4-factorial-selection_only-B0-all | PU | 7 | 4 | 可用 | 56.583 | 49.138 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-factorial-selection_only-B0-all/attempt_01 |
| 378 | PU-t7-s4-factorial-full-B1-all | PU | 7 | 4 | 可用 | 63.875 | 58.510 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-DA_B |
| 379 | PU-t7-s4-factorial-labels_only-B1-all | PU | 7 | 4 | 可用 | 69.500 | 62.318 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-factorial-labels_only-B1-all/attempt_01 |
| 380 | PU-t7-s4-factorial-raw-B1-all | PU | 7 | 4 | 可用 | 61.667 | 54.856 | runs/da_b_five_seed_followup_v1/cases/PU-t7-s4-B |
| 381 | PU-t7-s4-factorial-selection_only-B1-all | PU | 7 | 4 | 可用 | 59.750 | 51.805 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-factorial-selection_only-B1-all/attempt_01 |
| 382 | PU-t7-s4-coverage-full-B1-selected_domain_mean | PU | 7 | 4 | 可用 | 63.333 | 54.852 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 383 | PU-t7-s4-coverage-full-B1-selected_fixed | PU | 7 | 4 | 可用 | 63.500 | 59.302 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 384 | PU-t7-s4-soft_weight-softmatch_weight-B1-all | PU | 7 | 4 | 可用 | 54.792 | 48.366 | runs/pc2g_research_audit_20260924/cells/PU-t7-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 385 | DIRG-t1-s4-factorial-full-B0-all | DIRG | 1 | 4 | 可用 | 49.464 | 46.869 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-DA |
| 386 | DIRG-t1-s4-factorial-labels_only-B0-all | DIRG | 1 | 4 | 可用 | 51.250 | 48.377 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-factorial-labels_only-B0-all/attempt_01 |
| 387 | DIRG-t1-s4-factorial-raw-B0-all | DIRG | 1 | 4 | 可用 | 48.125 | 46.980 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-baseline |
| 388 | DIRG-t1-s4-factorial-selection_only-B0-all | DIRG | 1 | 4 | 可用 | 41.161 | 38.430 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-factorial-selection_only-B0-all/attempt_01 |
| 389 | DIRG-t1-s4-factorial-full-B1-all | DIRG | 1 | 4 | 可用 | 43.036 | 39.623 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-DA_B |
| 390 | DIRG-t1-s4-factorial-labels_only-B1-all | DIRG | 1 | 4 | 可用 | 51.786 | 48.725 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-factorial-labels_only-B1-all/attempt_01 |
| 391 | DIRG-t1-s4-factorial-raw-B1-all | DIRG | 1 | 4 | 可用 | 41.429 | 38.332 | runs/da_b_five_seed_followup_v1/cases/DIRG-t1-s4-B |
| 392 | DIRG-t1-s4-factorial-selection_only-B1-all | DIRG | 1 | 4 | 可用 | 40.804 | 35.847 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-factorial-selection_only-B1-all/attempt_01 |
| 393 | DIRG-t1-s4-coverage-full-B1-selected_domain_mean | DIRG | 1 | 4 | 可用 | 53.839 | 50.970 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 394 | DIRG-t1-s4-coverage-full-B1-selected_fixed | DIRG | 1 | 4 | 可用 | 48.125 | 46.425 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 395 | DIRG-t1-s4-soft_weight-softmatch_weight-B1-all | DIRG | 1 | 4 | 可用 | 53.393 | 50.927 | runs/pc2g_research_audit_20260924/cells/DIRG-t1-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 396 | PU-t8-s4-factorial-full-B0-all | PU | 8 | 4 | 可用 | 99.625 | 99.625 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-DA |
| 397 | PU-t8-s4-factorial-labels_only-B0-all | PU | 8 | 4 | 可用 | 99.583 | 99.583 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-factorial-labels_only-B0-all/attempt_01 |
| 398 | PU-t8-s4-factorial-raw-B0-all | PU | 8 | 4 | 可用 | 99.792 | 99.792 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-baseline |
| 399 | PU-t8-s4-factorial-selection_only-B0-all | PU | 8 | 4 | 可用 | 99.500 | 99.500 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-factorial-selection_only-B0-all/attempt_01 |
| 400 | PU-t8-s4-factorial-full-B1-all | PU | 8 | 4 | 可用 | 99.833 | 99.833 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-DA_B |
| 401 | PU-t8-s4-factorial-labels_only-B1-all | PU | 8 | 4 | 可用 | 99.417 | 99.416 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-factorial-labels_only-B1-all/attempt_01 |
| 402 | PU-t8-s4-factorial-raw-B1-all | PU | 8 | 4 | 可用 | 99.750 | 99.750 | runs/da_b_five_seed_followup_v1/cases/PU-t8-s4-B |
| 403 | PU-t8-s4-factorial-selection_only-B1-all | PU | 8 | 4 | 可用 | 99.875 | 99.875 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-factorial-selection_only-B1-all/attempt_01 |
| 404 | PU-t8-s4-coverage-full-B1-selected_domain_mean | PU | 8 | 4 | 可用 | 99.500 | 99.500 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 405 | PU-t8-s4-coverage-full-B1-selected_fixed | PU | 8 | 4 | 可用 | 99.625 | 99.625 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 406 | PU-t8-s4-soft_weight-softmatch_weight-B1-all | PU | 8 | 4 | 可用 | 99.708 | 99.708 | runs/pc2g_research_audit_20260924/cells/PU-t8-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 407 | DIRG-t2-s4-factorial-full-B0-all | DIRG | 2 | 4 | 可用 | 38.839 | 36.586 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-DA |
| 408 | DIRG-t2-s4-factorial-labels_only-B0-all | DIRG | 2 | 4 | 可用 | 39.821 | 36.486 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-factorial-labels_only-B0-all/attempt_01 |
| 409 | DIRG-t2-s4-factorial-raw-B0-all | DIRG | 2 | 4 | 可用 | 36.250 | 33.573 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-baseline |
| 410 | DIRG-t2-s4-factorial-selection_only-B0-all | DIRG | 2 | 4 | 可用 | 36.518 | 33.784 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-factorial-selection_only-B0-all/attempt_01 |
| 411 | DIRG-t2-s4-factorial-full-B1-all | DIRG | 2 | 4 | 可用 | 36.339 | 34.690 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-DA_B |
| 412 | DIRG-t2-s4-factorial-labels_only-B1-all | DIRG | 2 | 4 | 可用 | 38.750 | 36.336 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-factorial-labels_only-B1-all/attempt_01 |
| 413 | DIRG-t2-s4-factorial-raw-B1-all | DIRG | 2 | 4 | 可用 | 39.196 | 35.773 | runs/da_b_five_seed_followup_v1/cases/DIRG-t2-s4-B |
| 414 | DIRG-t2-s4-factorial-selection_only-B1-all | DIRG | 2 | 4 | 可用 | 39.821 | 35.917 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-factorial-selection_only-B1-all/attempt_01 |
| 415 | DIRG-t2-s4-coverage-full-B1-selected_domain_mean | DIRG | 2 | 4 | 可用 | 39.286 | 37.527 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 416 | DIRG-t2-s4-coverage-full-B1-selected_fixed | DIRG | 2 | 4 | 可用 | 38.393 | 35.625 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 417 | DIRG-t2-s4-soft_weight-softmatch_weight-B1-all | DIRG | 2 | 4 | 可用 | 34.196 | 31.708 | runs/pc2g_research_audit_20260924/cells/DIRG-t2-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 418 | PU-t9-s4-factorial-full-B0-all | PU | 9 | 4 | 可用 | 47.708 | 38.540 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-DA |
| 419 | PU-t9-s4-factorial-labels_only-B0-all | PU | 9 | 4 | 可用 | 46.208 | 38.831 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-factorial-labels_only-B0-all/attempt_01 |
| 420 | PU-t9-s4-factorial-raw-B0-all | PU | 9 | 4 | 可用 | 42.292 | 36.068 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-baseline |
| 421 | PU-t9-s4-factorial-selection_only-B0-all | PU | 9 | 4 | 可用 | 43.875 | 37.175 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-factorial-selection_only-B0-all/attempt_01 |
| 422 | PU-t9-s4-factorial-full-B1-all | PU | 9 | 4 | 可用 | 48.458 | 38.380 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-DA_B |
| 423 | PU-t9-s4-factorial-labels_only-B1-all | PU | 9 | 4 | 可用 | 43.000 | 35.587 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-factorial-labels_only-B1-all/attempt_01 |
| 424 | PU-t9-s4-factorial-raw-B1-all | PU | 9 | 4 | 可用 | 32.500 | 27.092 | runs/da_b_five_seed_followup_v1/cases/PU-t9-s4-B |
| 425 | PU-t9-s4-factorial-selection_only-B1-all | PU | 9 | 4 | 可用 | 42.958 | 36.768 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-factorial-selection_only-B1-all/attempt_01 |
| 426 | PU-t9-s4-coverage-full-B1-selected_domain_mean | PU | 9 | 4 | 可用 | 35.833 | 29.840 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 427 | PU-t9-s4-coverage-full-B1-selected_fixed | PU | 9 | 4 | 可用 | 44.292 | 35.718 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 428 | PU-t9-s4-soft_weight-softmatch_weight-B1-all | PU | 9 | 4 | 可用 | 45.708 | 37.932 | runs/pc2g_research_audit_20260924/cells/PU-t9-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |
| 429 | DIRG-t3-s4-factorial-full-B0-all | DIRG | 3 | 4 | 可用 | 48.571 | 46.998 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-DA |
| 430 | DIRG-t3-s4-factorial-labels_only-B0-all | DIRG | 3 | 4 | 可用 | 51.875 | 49.614 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-factorial-labels_only-B0-all/attempt_01 |
| 431 | DIRG-t3-s4-factorial-raw-B0-all | DIRG | 3 | 4 | 可用 | 52.232 | 48.949 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-baseline |
| 432 | DIRG-t3-s4-factorial-selection_only-B0-all | DIRG | 3 | 4 | 可用 | 51.339 | 49.747 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-factorial-selection_only-B0-all/attempt_01 |
| 433 | DIRG-t3-s4-factorial-full-B1-all | DIRG | 3 | 4 | 可用 | 48.750 | 46.072 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-DA_B |
| 434 | DIRG-t3-s4-factorial-labels_only-B1-all | DIRG | 3 | 4 | 可用 | 54.554 | 52.218 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-factorial-labels_only-B1-all/attempt_01 |
| 435 | DIRG-t3-s4-factorial-raw-B1-all | DIRG | 3 | 4 | 可用 | 51.518 | 50.035 | runs/da_b_five_seed_followup_v1/cases/DIRG-t3-s4-B |
| 436 | DIRG-t3-s4-factorial-selection_only-B1-all | DIRG | 3 | 4 | 可用 | 51.518 | 50.275 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-factorial-selection_only-B1-all/attempt_01 |
| 437 | DIRG-t3-s4-coverage-full-B1-selected_domain_mean | DIRG | 3 | 4 | 可用 | 52.143 | 49.634 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-coverage-full-B1-selected_domain_mean/attempt_01 |
| 438 | DIRG-t3-s4-coverage-full-B1-selected_fixed | DIRG | 3 | 4 | 可用 | 48.750 | 49.768 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-coverage-full-B1-selected_fixed/attempt_01 |
| 439 | DIRG-t3-s4-soft_weight-softmatch_weight-B1-all | DIRG | 3 | 4 | 可用 | 50.268 | 49.999 | runs/pc2g_research_audit_20260924/cells/DIRG-t3-s4-soft_weight-softmatch_weight-B1-all/attempt_01 |

</details>

本报告不包含自动训练、目标分数选参或下一轮任务启动指令。
