"""Summarize the complete HUSTbearing labeled-source rotation."""

import argparse
import csv
import math
import statistics
from pathlib import Path

from .report_pilot import CLASS_NAMES, MODES, class_metrics, config_name, read_json, write_csv


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "output/pc2g_hust_role_rotation_20261118"
HZ = (20, 35, 65, 80)
ROLES = (0, 1, 2)
SEEDS = (0, 1, 2)
CONFIGS = tuple((mode, alternate) for alternate in (False, True) for mode in MODES)
CLASSES = CLASS_NAMES["hust"]
MODE_PAIRS = (
    ("Full−Select", (("full", 1), ("selection_only", -1))),
    ("Label−Raw", (("labels_only", 1), ("raw", -1))),
    ("Select−Raw", (("selection_only", 1), ("raw", -1))),
    ("标签×筛选", (("full", 1), ("labels_only", -1), ("selection_only", -1), ("raw", 1))),
)
RESULT_NAME = "HUST_role_rotation_results.csv"
CLASS_NAME = "HUST_role_rotation_class_metrics.csv"
PSEUDO_NAME = "HUST_role_rotation_pseudo_label.csv"
COMPARISON_NAME = "HUST_role_rotation_comparison.md"
REPORT_NAME = "PC2G_role_rotation_final_report.md"


def validate(data, protocol):
    if data.get("complete") is not True:
        raise ValueError("The aggregate run results must be complete")
    expected = {(role, mode, b_on, seed) for role in ROLES for mode, b_on in CONFIGS for seed in SEEDS}
    rows = data["rows"]
    if len(rows) != len(expected) or len({row["id"] for row in rows}) != len(expected):
        raise ValueError("Expected 72 unique HUSTbearing runs")
    by_key, metric_rows, result_rows = {}, [], {}
    for row in rows:
        role, mode, weight, seed = row["labeled"], row["mode"], row["B_weight"], row["seed"]
        key = (role, mode, bool(weight), seed)
        if key not in expected or key in by_key or row["target"] != 3 or row["dataset"] != "hust":
            raise ValueError(f"Unexpected experimental identity {row['id']}")
        if (weight not in (0, 0.1) or row["checkpoint_step"] != 5000
                or row["reused"] is not (role == 0) or not math.isfinite(row["training_seconds"])
                or row["training_seconds"] <= 0):
            raise ValueError(f"Unexpected checkpoint or training metadata {row['id']}")
        if row["id"] != f"hust-t3-L{role}-s{seed}-{mode}-B{int(bool(weight))}":
            raise ValueError(f"Run ID does not match row metadata: {row['id']}")
        metrics = row["metrics"]
        matrix = metrics["confusion_matrix"]
        parts = class_metrics(matrix)
        if tuple(part["support"] for part in parts) != (81,) * len(CLASSES):
            raise ValueError(f"Expected 81 windows from each target class in {row['id']}")
        total = sum(part["support"] for part in parts)
        correct = sum(matrix[i][i] for i in range(len(CLASSES)))
        recall = metrics["per_class_recall"]
        if (len(recall) != len(CLASSES)
                or not math.isclose(metrics["accuracy"], correct / total, abs_tol=1e-10)
                or not math.isclose(metrics["macro_f1"], statistics.mean(p["f1"] for p in parts), abs_tol=1e-10)
                or any(not math.isclose(a, p["recall"], abs_tol=1e-10) for a, p in zip(recall, parts))):
            raise ValueError(f"Saved results disagree with confusion matrix in {row['id']}")
        identity = dict(dataset="hust", target_hz=80, labeled_source_hz=HZ[role],
                        unlabeled_source_hz="|".join(str(HZ[u]) for u in ROLES if u != role),
                        labeled=role, target=3, seed=seed, mode=mode,
                        configuration=config_name(mode, bool(weight)), B_weight=weight,
                        run_id=row["id"], checkpoint_step=5000, reused=row["reused"])
        result_rows[key] = dict(
            **identity, accuracy_percent=100 * metrics["accuracy"], macro_f1_percent=100 * metrics["macro_f1"],
            evaluated_windows=total, correct_windows=correct, predicted_normal_windows=parts[0]["predicted"],
            predicted_normal_percent=100 * parts[0]["predicted"] / total,
            true_fault_predicted_normal_windows=sum(matrix[i][0] for i in range(1, len(CLASSES))),
            true_fault_windows=total - 81, training_seconds=row["training_seconds"],
        )
        for index, part in enumerate(parts):
            metric_rows.append(dict(
                **identity, class_id=index, class_name_cn=CLASSES[index], true_count=part["support"],
                predicted_count=part["predicted"], true_positive_count=matrix[index][index],
                precision_percent=100 * part["precision"], precision_defined=int(part["predicted"] > 0),
                recall_percent=100 * part["recall"], f1_percent=100 * part["f1"],
                predicted_as_normal_count=matrix[index][0],
            ))
        by_key[key] = row
    protocol_rows = protocol.get("rows")
    if protocol_rows is not None:
        fields = ("id", "dataset", "target", "labeled", "seed", "mode", "B_weight")
        recorded = {tuple(row[field] for field in fields) for row in protocol_rows}
        applicable = rows if len(protocol_rows) == 72 else [row for row in rows if not row["reused"]]
        if len(recorded) != len(protocol_rows) or recorded != {
            tuple(row[field] for field in fields) for row in applicable
        }:
            raise ValueError("Run identities differ from the frozen protocol")
        baseline = protocol.get("baseline_rows")
        if baseline is not None and (
                len(baseline) != 24 or {tuple(row[field] for field in fields) for row in baseline} != {
                    tuple(row[field] for field in fields) for row in rows if row["reused"]
                }):
            raise ValueError("Reused run identities differ from the frozen baseline")
    order = [(role, mode, b_on, seed) for role in ROLES for mode, b_on in CONFIGS for seed in SEEDS]
    ordered = [result_rows[key] for key in order]
    order_ids = {row["run_id"]: i for i, row in enumerate(ordered)}
    metric_rows.sort(key=lambda row: (order_ids[row["run_id"]], row["class_id"]))
    return by_key, result_rows, ordered, metric_rows


def read_supervision(path):
    class_rows = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            role, source, seed = (int(row[k]) for k in ("labeled", "unlabeled", "seed"))
            if role not in ROLES or source not in ROLES or role == source:
                raise ValueError("Pseudo-label rows must distinguish the labeled and unlabeled domains")
            if HZ[role] != int(row["labeled_source_hz"]) or HZ[source] != int(row["unlabeled_source_hz"]):
                raise ValueError("Pseudo-label frequency does not match domain index")
            weight = float(row["B_weight"])
            mode, phase, cls = row["mode"], row["phase"], int(row["class_id"])
            key = (role, source, mode, bool(weight), seed, phase, cls)
            if key in class_rows or weight not in (0, 0.1):
                raise ValueError(f"Duplicated or invalid pseudo-label identity {key}")
            if int(row["actual_ce_archive_available"]) != int(role != 0):
                raise ValueError("Actual cross-entropy evidence must agree with training provenance")
            class_rows[key] = row
    expected = {(role, source, mode, b_on, seed, phase, cls)
                for role in ROLES for source in ROLES if source != role
                for mode, b_on in CONFIGS for seed in SEEDS
                for phase in ("all", "early", "middle", "late") for cls in range(len(CLASSES))}
    if set(class_rows) != expected:
        raise ValueError("Incomplete class-wise pseudo-label records")
    for role, source, mode, b_on, seed, phase, cls in class_rows:
        if cls != 0:
            continue
        subset = [class_rows[role, source, mode, b_on, seed, phase, cls] for cls in range(len(CLASSES))]
        for total, per_class in (
                ("selected_occurrences", "selected_true_class_occurrences"),
                ("selected_error_occurrences", "selected_true_class_errors"),
                ("sampled_occurrences", "sampled_true_class_occurrences")):
            if (len({row[total] for row in subset}) != 1
                    or sum(int(row[per_class]) for row in subset) != int(subset[0][total])):
                raise ValueError(f"Pseudo-label counts do not reconcile in {subset[0]['configuration']}")
    return class_rows


def percent(numerator, denominator):
    return 100 * numerator / denominator if denominator else None


def shown(value):
    return "无入选" if value is None else f"{value:.3f}%"


def sign(value):
    return f"{value:+.3f}" if abs(value) >= 1e-12 else "0.000"


def paired_text(values):
    return f"{sign(statistics.mean(values))} ± {statistics.stdev(values):.3f}"


def concise_values(values):
    return " / ".join(sign(v) for v in values)


def grouped_text(values):
    return f"{statistics.mean(values):.3f} ± {statistics.stdev(values):.3f}"


def supervision_counts(table, role, source, mode="full", b_on=True, class_id=0, phase="all"):
    subset = [table[role, source, mode, b_on, seed, phase, class_id] for seed in SEEDS]
    fields = ("sampled_occurrences", "selected_occurrences", "selected_error_occurrences",
              "selected_true_class_occurrences", "selected_true_class_errors",
              "selected_true_class_as_normal_occurrences")
    return {field: sum(int(row[field]) for row in subset) for field in fields}


def role_table(results):
    lines = ["| 配置 | 20 Hz 有标签 | 35 Hz 有标签 | 65 Hz 有标签 |",
             "|---|---:|---:|---:|"]
    for mode, b_on in CONFIGS:
        cells = []
        for role in ROLES:
            rows = [results[role, mode, b_on, seed] for seed in SEEDS]
            cells.append("<br>".join(grouped_text([r[metric] for r in rows])
                                      for metric in ("accuracy_percent", "macro_f1_percent", "predicted_normal_percent")))
        lines.append(f"| {config_name(mode, b_on)} | " + " | ".join(cells) + " |")
    return lines


def contrast_table(results):
    lines = ["| 有标签源 | B | 对比 | Δ Accuracy，均值 ± SD（百分点） | 三个种子 Δ Accuracy | "
             "Δ Macro-F1，均值 ± SD（百分点） | 三个种子 Δ Macro-F1 |",
             "|---|---|---|---:|---:|---:|---:|"]
    for role in ROLES:
        for b_on in (False, True):
            for label, terms in MODE_PAIRS:
                values = [[math.fsum(results[role, mode, b_on, seed][metric] * k for mode, k in terms)
                           for seed in SEEDS] for metric in ("accuracy_percent", "macro_f1_percent")]
                lines.append(f"| {HZ[role]} Hz | {'开' if b_on else '关'} | {label} | "
                             f"{paired_text(values[0])} | {concise_values(values[0])} | "
                             f"{paired_text(values[1])} | {concise_values(values[1])} |")
    return lines


def cross_role_table(results):
    lines = ["| 角色对照 | 配置 | Δ Accuracy，均值 ± SD（百分点） | 三个种子 Δ Accuracy | "
             "Δ Macro-F1，均值 ± SD（百分点） | Δ 预测正常，均值 ± SD（百分点） |",
             "|---|---|---:|---:|---:|---:|"]
    for before, after in ((0, 1), (0, 2), (1, 2)):
        for mode, b_on in CONFIGS:
            values = [[results[after, mode, b_on, seed][metric] - results[before, mode, b_on, seed][metric]
                       for seed in SEEDS] for metric in (
                           "accuracy_percent", "macro_f1_percent", "predicted_normal_percent")]
            lines.append(f"| {HZ[after]}−{HZ[before]} Hz | {config_name(mode, b_on)} | "
                         f"{paired_text(values[0])} | {concise_values(values[0])} | "
                         f"{paired_text(values[1])} | {paired_text(values[2])} |")
    return lines


def quality_table(table):
    lines = ["| 有标签源 | 无标签源 | B | 配置 | 入选数 | 入选错误数 | 入选正确率 |",
             "|---:|---:|---|---|---:|---:|---:|"]
    for role in ROLES:
        for source in (source for source in ROLES if source != role):
            for mode, b_on in CONFIGS:
                row = supervision_counts(table, role, source, mode, b_on)
                selected, errors = row["selected_occurrences"], row["selected_error_occurrences"]
                lines.append(f"| {HZ[role]} Hz | {HZ[source]} Hz | {'开' if b_on else '关'} | "
                             f"{config_name(mode, b_on)} | {selected:,} | {errors:,} | "
                             f"{shown(percent(selected - errors, selected))} |")
    return lines


def calibration_table(table):
    lines = ["| 有标签源 | 无标签源 | B | Label−Raw 错误次数 | Select−Raw 错误次数 | "
             "Full−Select 错误次数 | Full−Select 入选错误率差（百分点） |",
             "|---:|---:|---|---:|---:|---:|---:|"]
    for role in ROLES:
        for source in (source for source in ROLES if source != role):
            for b_on in (False, True):
                counts = {mode: supervision_counts(table, role, source, mode, b_on) for mode in MODES}
                errors = {mode: row["selected_error_occurrences"] for mode, row in counts.items()}
                selected = {mode: row["selected_occurrences"] for mode, row in counts.items()}
                if selected["full"] != selected["selection_only"] or selected["labels_only"] != selected["raw"]:
                    raise ValueError("Fixed-selection comparisons have unequal decision denominators")
                diff = errors["full"] - errors["selection_only"]
                rate = percent(diff, selected["full"])
                rate_text = sign(rate) if rate is not None else "无入选"
                lines.append(f"| {HZ[role]} Hz | {HZ[source]} Hz | {'开' if b_on else '关'} | "
                             f"{errors['labels_only'] - errors['raw']:+,} | "
                             f"{errors['selection_only'] - errors['raw']:+,} | {diff:+,} | {rate_text} |")
    return lines


def recall_table(by_key, mode="full", b_on=True):
    lines = ["| 真实类别 | 20 Hz 有标签 | 35 Hz 有标签 | 65 Hz 有标签 |",
             "|---|---:|---:|---:|"]
    for i, label in enumerate(CLASSES):
        cells = [grouped_text([100 * by_key[role, mode, b_on, seed]["metrics"]["per_class_recall"][i]
                               for seed in SEEDS]) for role in ROLES]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def shared_source_tables(by_key, table):
    output = []
    for before, after, source in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
        output.extend([f"### 有标签源 {HZ[before]}→{HZ[after]} Hz，共享无标签源 {HZ[source]} Hz", "",
                       "| 真实类别 | 共享源入选错误率（前 → 后） | 80 Hz 召回变化（百分点） |",
                       "|---|---:|---:|"])
        for i, label in enumerate(CLASSES):
            old, new = (supervision_counts(table, role, source, class_id=i) for role in (before, after))
            rates = [shown(percent(x["selected_true_class_errors"], x["selected_true_class_occurrences"]))
                     for x in (old, new)]
            delta = statistics.mean(100 * (by_key[after, "full", True, seed]["metrics"]["per_class_recall"][i]
                                           - by_key[before, "full", True, seed]["metrics"]["per_class_recall"][i])
                                    for seed in SEEDS)
            output.append(f"| {label} | {' → '.join(rates)} | {sign(delta)} |")
        output.append("")
    return output


def loss_table(table):
    fields = ("mean_step_main_common_pseudo_ce", "mean_step_main_specific_pseudo_ce",
              "mean_step_aux_labeled_ce_1", "mean_step_aux_labeled_ce_2")
    lines = ["| 有标签源 | 无标签源 | 共同头伪标签 CE | 特定头伪标签 CE | 辅助头 1 有标签 CE | 辅助头 2 有标签 CE |",
             "|---|---|---:|---:|---:|---:|"]
    for role in (1, 2):
        for source in (source for source in ROLES if source != role):
            rows = [table[role, source, "full", True, seed, "all", 0] for seed in SEEDS]
            averages = [statistics.mean(float(row[field]) for row in rows) for field in fields]
            lines.append(f"| {HZ[role]} Hz | {HZ[source]} Hz | "
                         + " | ".join(f"{value:.5f}" for value in averages) + " |")
    return lines


def report_status(directory):
    audit_path = directory / "source_pairing_audit.json"
    return (" · [源端配对核验](source_pairing_audit.json)"
            if audit_path.is_file() else "")


def write_reports(directory, by_key, results, supervision):
    links = f"[冻结协议](protocol.json) · [逐模型指标]({RESULT_NAME}) · [逐类指标]({CLASS_NAME}) · [伪标签诊断]({PSEUDO_NAME})"
    comparison = [
        "# HUSTbearing 80 Hz 留出任务的有标签源角色对照", "",
        "三种角色均使用第 5 000 步检查点和种子 0、1、2。目标测试共有 729 个窗口，九类各 81 个。"
        "20 Hz 角色的 24 个模型来自既有试跑，另两角色各新增 24 个模型。目标性能均值和样本标准差"
        "在三个优化种子之间计算。", "",
        links + report_status(directory), "",
        "## 同配置下的角色表现", "",
        "表中每格依次为 Accuracy、Macro-F1、预测正常比例，单位为 %，均为三个种子的均值 ± 样本标准差。", "",
        *role_table(results), "",
        "## 同角色、同 B 水平内的条件对比", "",
        "同种子先作差，再计算三个种子的均值和样本标准差。"
        "Full−Select 固定校正筛选集合，Label−Raw 固定原筛选集合，Select−Raw 固定原标签。"
        "标签×筛选双差为 Full−Label−Select+Raw。", "",
        *contrast_table(results), "",
        "## 同配置在不同角色之间的配对差", "",
        *cross_role_table(results), "",
        "## 两个无标签源的监督质量", "",
        "三种子的计数单位为有放回采样出现次数。同一无标签源的入选准确率以该源所有入选出现次数为分母。", "",
        *quality_table(supervision), "",
        "负值表示该对比减少了错误出现次数。Select−Raw 改变入选集合，总数也可能变化。", "",
        *calibration_table(supervision), "",
        "## Full+B 的 80 Hz 逐类召回", "",
        "单位为 %，每格为均值 ± 样本标准差。", "",
        *recall_table(by_key), "",
        "## 共享无标签源与目标召回的并列观察", "",
        "以下只展示 Full+B。共享源的入选错误率以入选的真实类别采样出现为分母，召回变化按配对种子均值计算。"
        "有标签源、另一个无标签源以及对应的辅助分支输入也随角色改变。", "",
        *shared_source_tables(by_key, supervision),
        "既有 20 Hz 角色只有 21 次合计损失快照。新增模型在每步保存两个辅助头各自的有标签源交叉熵，"
        "以及共同头和域特定头在各无标签源上的伪标签交叉熵。逐类表保留采样次数和名义权重，"
        "另提供按源和阶段汇总的已存实际交叉熵。20 Hz 角色缺档的同口径实际交叉熵留空。", "",
        "下表选取 Full+B 的逐步交叉熵，先平均每个种子的 5 000 步，再等权平均三个种子。"
        "辅助头的有标签损失按同角色显示，两个无标签源行重复同一损失。", "",
        *loss_table(supervision), "",
    ]
    summary = [
        "# PC2G 角色轮换实验结果", "",
        "80 Hz 留出目标固定。20 Hz 角色复用已有的 24 个模型，35 与 65 Hz 角色各完成新增 24 个模型，"
        "共汇总 72 个第 5 000 步的检查点。八种配置沿用相同的网络、预处理及优化预算。"
        "三个种子用于描述训练随机性，本次覆盖同一个目标工况。", "",
        links + report_status(directory) + f" · [完整配对比较]({COMPARISON_NAME})", "",
        "## A. 65 Hz 提供标签后，原有错配怎样变化", "",
        build_a(supervision), "",
        "## B. 35 Hz 提供标签后，无标签源的质量怎样变化", "",
        build_b(supervision), "",
        "## C. 目标表现随角色怎样变化", "",
        *build_c(results), "",
        "## D. 校正标签的作用方向是否随组合变化", "",
        *build_d(supervision, results), "",
        "## E. 源端错误与目标逐类召回怎样对应", "",
        *build_e(supervision, by_key), "",
        "本次角色替换同时改变了有标签训练样本、无标签源组合和辅助预测分支的任务，"
        "只能描述角色敏感性。每个工况的每类窗口来自一份原始记录，"
        "种子和窗口重复只用于描述固定任务上的变化。CWRU 的现有结果保持探索性定位，同一子集内采样链与类别绑定。"
        "[CWRU 预处理核查](../pc2g_source_diagnostic_20261118/CWRU_preprocessing_audit.md)", "",
    ]
    for name, lines in ((COMPARISON_NAME, comparison), (REPORT_NAME, summary)):
        path = directory / name
        temp = path.with_suffix(".tmp")
        temp.write_text("\n".join(lines), encoding="utf-8")
        temp.replace(path)


def build_a(table):
    parts = []
    for role in (0, 1):
        row = supervision_counts(table, role, 2, class_id=5)
        wrong, selected = row["selected_true_class_as_normal_occurrences"], row["selected_true_class_occurrences"]
        parts.append(f"{HZ[role]} Hz 提供标签时，{wrong:,}/{selected:,}（{shown(percent(wrong, selected))}）")
    return ("Full+B 中，按真实中度滚动体的入选次数计算，65 Hz 上被标为正常的比例随有标签源而变。"
            + "。".join(parts) + "。65 Hz 提供标签后，该源的训练样本由真值监督，"
            "65 Hz 硬伪标签错配这条直接训练路径随角色变更而消失。该角色下仍可观察其他无标签源的错配和 80 Hz 召回。")


def build_b(table):
    result = []
    for source in (0, 2):
        row = supervision_counts(table, 1, source)
        selected, error = row["selected_occurrences"], row["selected_error_occurrences"]
        candidate = [(supervision_counts(table, 1, source, class_id=i), label) for i, label in enumerate(CLASSES)]
        covered = [(percent(part["selected_true_class_errors"], part["selected_true_class_occurrences"]), label)
                   for part, label in candidate if part["selected_true_class_occurrences"] > 0]
        worst, label = max(covered, default=(None, "无入选样本"))
        result.append(f"{HZ[source]} Hz 的入选错误为 {error:,}/{selected:,}（{shown(percent(error, selected))}），"
                      f"入选真实类别错误率最高者为{label}（{shown(worst)}）")
    before, after = (supervision_counts(table, role, 2) for role in (0, 1))
    previous, current = (percent(part["selected_error_occurrences"], part["selected_occurrences"])
                         for part in (before, after))
    shared = (f"共同保留为无标签源的 65 Hz 入选错误率较 20 Hz 有标签时变化 "
              f"{sign(current-previous)} 个百分点。" if previous is not None and current is not None else
              "共有的 65 Hz 无标签源至少有一个角色没有入选样本，错误率差无法计算。")
    return ("35 Hz 提供真值时，20 Hz 成为此前未参与伪标签监督的无标签源。Full+B 中，"
            + "。".join(result) + "。" + shared + "逐类表也保留覆盖率为零的类别。")


def build_c(results):
    lines = ["| 配置 | 20 Hz 有标签 | 35 Hz 有标签 | 65 Hz 有标签 |",
             "|---|---:|---:|---:|"]
    for mode, b_on in (("raw", False), ("full", False), ("full", True)):
        cells = []
        for role in ROLES:
            rows = [results[role, mode, b_on, seed] for seed in SEEDS]
            cells.append(" / ".join(f"{statistics.mean(r[metric] for r in rows):.3f}%"
                                    for metric in ("accuracy_percent", "macro_f1_percent", "predicted_normal_percent")))
        lines.append(f"| {config_name(mode, b_on)} | " + " | ".join(cells) + " |")
    mean_acc = {role: statistics.mean(results[role, "full", True, seed]["accuracy_percent"] for seed in SEEDS)
                for role in ROLES}
    best = "、".join(f"{HZ[role]} Hz" for role, value in mean_acc.items()
                    if math.isclose(value, max(mean_acc.values()), abs_tol=1e-10))
    lines.extend(["", f"每格依次为平均 Accuracy、Macro-F1 和预测正常比例。Full+B 的平均 Accuracy "
                      f"在 {best} 有标签时最高。"])
    all_means = {(role, mode, b_on): statistics.mean(results[role, mode, b_on, seed]["accuracy_percent"]
                                                    for seed in SEEDS)
                 for role in ROLES for mode, b_on in CONFIGS}
    top_accuracy = max(all_means.values())
    highest = "、".join(f"{HZ[role]} Hz 有标签的 {config_name(mode, b_on)}"
                       for (role, mode, b_on), value in all_means.items()
                       if math.isclose(value, top_accuracy, abs_tol=1e-10))
    lines.extend(["", f"全部角色与配置中，平均 Accuracy 最高的是{highest}（{top_accuracy:.3f}%）。"
                      f"Full+B 与同角色 Raw 相比，35 Hz 有标签时的平均差是 "
                      f"{sign(mean_acc[1]-all_means[1, 'raw', False])} 个百分点，65 Hz 有标签时是 "
                      f"{sign(mean_acc[2]-all_means[2, 'raw', False])} 个百分点。"])
    for after in (1, 2):
        auc = [results[after, "full", True, seed]["accuracy_percent"] -
               results[0, "full", True, seed]["accuracy_percent"] for seed in SEEDS]
        f1 = [results[after, "full", True, seed]["macro_f1_percent"] -
              results[0, "full", True, seed]["macro_f1_percent"] for seed in SEEDS]
        lines.extend(["", f"Full+B 的 {HZ[after]}−20 Hz 角色配对差为 Accuracy "
                           f"{paired_text(auc)} 个百分点，三个种子的差为 {concise_values(auc)}。"
                           f"Macro-F1 配对差为 {paired_text(f1)} 个百分点。"])
    adjacent = [results[2, "full", True, seed]["accuracy_percent"] -
                results[1, "full", True, seed]["accuracy_percent"] for seed in SEEDS]
    lines.extend(["", f"Full+B 的 65−35 Hz 角色 Accuracy 配对差为 {paired_text(adjacent)} 个百分点，"
                      f"三个种子分别为 {concise_values(adjacent)} 个百分点。"])
    return lines


def build_d(table, results):
    lines = ["| 有标签源 | B | 两个无标签源的 Full−Select 入选错误次数 | "
             "80 Hz Full−Select 平均 Accuracy 差（百分点） |",
             "|---:|---|---|---:|"]
    direction = {}
    for role in ROLES:
        for b_on in (False, True):
            source_cells = []
            for source in (source for source in ROLES if source != role):
                full, select = (supervision_counts(table, role, source, mode, b_on)
                                for mode in ("full", "selection_only"))
                change = full["selected_error_occurrences"] - select["selected_error_occurrences"]
                source_cells.append(f"{HZ[source]} Hz {change:+,}")
            delta = statistics.mean(results[role, "full", b_on, seed]["accuracy_percent"]
                                    - results[role, "selection_only", b_on, seed]["accuracy_percent"]
                                    for seed in SEEDS)
            direction[role, b_on] = 0 if abs(delta) < 1e-10 else (1 if delta > 0 else -1)
            lines.append(f"| {HZ[role]} Hz | {'开' if b_on else '关'} | {'，'.join(source_cells)} | {sign(delta)} |")
    for b_on in (False, True):
        directions = {direction[role, b_on] for role in ROLES}
        if directions == {0}:
            observation = "三个角色的均差都为零"
        elif {-1, 1} <= directions:
            observation = "角色之间出现正负方向相反的均差"
        elif 0 in directions:
            observation = "至少一个角色均差为零，其余非零均差方向一致"
        else:
            observation = "三个角色的均差均为正" if directions == {1} else "三个角色的均差均为负"
        lines.extend(["", f"B {'开' if b_on else '关'}时，目标 Accuracy 的 Full−Select 对比中{observation}。"])
    lines.extend(["", "源端比较固定校正集合，负数表示改用校正标签减少错误。"
                  "方向描述基于每个角色三个种子的均值，逐种子方向在对照表中列出。"
                  "完整报告同时保留 Label−Raw、Select−Raw 及标签×筛选双差。"])
    return lines


def build_e(table, by_key):
    recall = [[statistics.mean(100 * by_key[role, "full", True, seed]["metrics"]["per_class_recall"][i]
                               for seed in SEEDS) for role in ROLES] for i in (5, 0)]
    lines = [f"Full+B 的中度滚动体目标召回按 20、35、65 Hz 有标签角色依次为 "
             f"{'、'.join(shown(v) for v in recall[0])}，正常类依次为 "
             f"{'、'.join(shown(v) for v in recall[1])}。", "",
             "下面同时报告共享无标签源中度滚动体到正常类的错配及其目标召回变化。源端分母为该真实类"
             "被入选的有放回采样出现，目标端为 80 Hz 原始类别记录所对应窗口的召回。", "",
             "| 有标签角色变化 | 共享无标签源 | 中度滚动体入选后标正常（前 → 后） | 目标召回差（百分点） |",
             "|---|---:|---:|---:|"]
    direction = dict(same=0, opposite=0, flat=0, missing=0)
    for old, new, source in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
        counts = [supervision_counts(table, role, source, class_id=5) for role in (old, new)]
        rates = " → ".join(shown(percent(x["selected_true_class_as_normal_occurrences"],
                                         x["selected_true_class_occurrences"])) for x in counts)
        lines.append(f"| {HZ[old]}→{HZ[new]} Hz | {HZ[source]} Hz | {rates} | {sign(recall[0][new]-recall[0][old])} |")
        for i in range(len(CLASSES)):
            counts = [supervision_counts(table, role, source, class_id=i) for role in (old, new)]
            errors = [percent(x["selected_true_class_errors"], x["selected_true_class_occurrences"]) for x in counts]
            if None in errors:
                direction["missing"] += 1
                continue
            improvement = errors[0] - errors[1]
            delta = statistics.mean(
                by_key[new, "full", True, seed]["metrics"]["per_class_recall"][i]
                - by_key[old, "full", True, seed]["metrics"]["per_class_recall"][i] for seed in SEEDS
            )
            if abs(improvement) < 1e-10 or abs(delta) < 1e-10:
                direction["flat"] += 1
            else:
                direction["same" if improvement * delta > 0 else "opposite"] += 1
    lines.extend(["", f"以各类别总体入选错误率衡量共享源，三组角色对照涉及的类别比较中，"
                  f"源质量与目标召回同向 {direction['same']} 项、反向 {direction['opposite']} 项、"
                  f"至少一项不变 {direction['flat']} 项、源端无可比入选分母 {direction['missing']} 项。"
                  "这些对照共享同一目标窗及模型，计数为描述性。角色改变时多个源同时受影响，"
                  "现有档案无法量化某一条误标流向独立造成的目标召回变化。"])
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    directory = parser.parse_args().output
    data, protocol = (read_json(directory / name) for name in ("results.json", "protocol.json"))
    by_key, results, ordered, class_rows = validate(data, protocol)
    supervision = read_supervision(directory / PSEUDO_NAME)
    for filename, rows in ((RESULT_NAME, ordered), (CLASS_NAME, class_rows)):
        destination = directory / filename
        temp = destination.with_suffix(".tmp")
        write_csv(temp, rows)
        temp.replace(destination)
    write_reports(directory, by_key, results, supervision)
    print(f"Verified {len(ordered)} runs, {len(class_rows)} target class rows, "
          f"and {len(supervision)} source supervision rows")


if __name__ == "__main__":
    main()
