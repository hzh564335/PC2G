"""Summarize completed HUSTbearing 65 Hz supervision-path runs from archives."""

import argparse
import csv
import math
import statistics
from pathlib import Path

from .report_pilot import CLASS_NAMES, class_metrics, read_json, relative_link, write_csv


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "output/pc2g_hust_65hz_path_20261119"
PREREG = ROOT / "output/pc2g_hust_65hz_path_preregistration_20261119/HUST_65Hz_supervision_path_preregistration.md"
ARMS = {"A": (True, True), "B": (False, True), "C": (True, False), "D": (False, False)}
SEEDS = (0, 1, 2)
CLASSES = CLASS_NAMES["hust"]
NORMAL, MEDIUM_BALL = 0, 5
PHASES = ("all", "early", "middle", "late")
SOURCES = (35, 65)
EXPECTED = {(arm, seed) for arm in ARMS for seed in SEEDS}
SOURCE_DOMAIN = "HUST_65Hz_path_source_domain.csv"
SOURCE_CLASS = "HUST_65Hz_path_source_supervision.csv"
TARGET_RESULTS = "HUST_65Hz_path_intervention_results.csv"
TARGET_CLASSES = "HUST_65Hz_path_intervention_class_metrics.csv"
CONTRAST_RESULTS = "HUST_65Hz_path_intervention_paired_contrasts.csv"
REPORT = "HUST_65Hz_path_intervention_report.md"
CONTRASTS = (
    ("B−A", {"B": 1, "A": -1}),
    ("D−C", {"D": 1, "C": -1}),
    ("C−A", {"C": 1, "A": -1}),
    ("D−B", {"D": 1, "B": -1}),
    ("(D−C)−(B−A)", {"D": 1, "C": -1, "B": -1, "A": 1}),
    ("D−A", {"D": 1, "A": -1}),
)


def validate_runs(data, protocol):
    if data.get("complete") is not True:
        raise ValueError("Twelve complete arm/seed results are required")
    rows = data["rows"]
    runs = {(r["arm"], r["seed"]): r for r in rows}
    if len(rows) != len(EXPECTED) or set(runs) != EXPECTED or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Expected exactly three unique runs per arm")
    fields = ("arm", "id", "dataset", "target", "labeled", "seed", "mode", "B_weight", "ce65", "cons65")
    for key, historical in (("rows", False), ("baseline_rows", True)):
        registered = {tuple(row[field] for field in fields) for row in protocol[key]}
        actual = {tuple(row[field] for field in fields) for row in rows if row["reused"] is historical}
        if len(protocol[key]) != (3 if historical else 9) or actual != registered:
            raise ValueError(f"Run identities differ from frozen {key}")
    overview, per_class = {}, {}
    for arm in ARMS:
        for seed in SEEDS:
            row = runs[arm, seed]
            ce, consistency = ARMS[arm]
            if (row["ce65"] is not ce or row["cons65"] is not consistency
                    or (row["dataset"], row["target"], row["labeled"], row["mode"], row["B_weight"])
                       != ("hust", 3, 0, "full", 0.1)
                    or isinstance(row["seed"], bool) or row["checkpoint_step"] != 5000
                    or row["reused"] is not (arm == "A") or not math.isfinite(row["training_seconds"])
                    or row["training_seconds"] <= 0):
                raise ValueError(f"Unexpected gate, task or checkpoint for {row['id']}")
            metrics = row["metrics"]
            matrix = metrics["confusion_matrix"]
            parts = class_metrics(matrix)
            if [p["support"] for p in parts] != [81] * len(CLASSES):
                raise ValueError(f"Wrong target class counts for {row['id']}")
            n = sum(p["support"] for p in parts)
            correct = sum(matrix[i][i] for i in range(len(parts)))
            accuracy = correct / n
            macro_f1 = statistics.mean(p["f1"] for p in parts)
            recall = metrics["per_class_recall"]
            if (not math.isclose(metrics["accuracy"], accuracy, abs_tol=1e-10)
                    or not math.isclose(metrics["macro_f1"], macro_f1, abs_tol=1e-10)
                    or len(recall) != len(parts)
                    or any(not math.isclose(v, part["recall"], abs_tol=1e-10)
                           for v, part in zip(recall, parts))):
                raise ValueError(f"Stored metrics differ from the confusion matrix for {row['id']}")
            predicted_normal = parts[NORMAL]["predicted"]
            fault_as_normal = predicted_normal - matrix[NORMAL][NORMAL]
            identity = dict(arm=arm, seed=seed, run_id=row["id"], reused=row["reused"],
                            labeled_hz=20, target_hz=80, checkpoint_step=5000, ce65=ce, cons65=consistency)
            overview[arm, seed] = dict(
                **identity, target_windows=n, correct_windows=correct,
                accuracy_percent=100 * accuracy, macro_f1_percent=100 * macro_f1,
                predicted_normal_windows=predicted_normal, predicted_normal_percent=100 * predicted_normal / n,
                true_fault_windows=n - parts[NORMAL]["support"], true_fault_as_normal_windows=fault_as_normal,
                true_fault_as_normal_percent=100 * fault_as_normal / (n - parts[NORMAL]["support"]),
                training_seconds=row["training_seconds"], run_dir=row["run_dir"],
            )
            for i, part in enumerate(parts):
                per_class[arm, seed, i] = dict(
                    **identity, class_id=i, class_name=CLASSES[i], support=part["support"],
                    correct_windows=matrix[i][i], predicted_count=part["predicted"],
                    precision_percent=100 * part["precision"], precision_defined=int(part["predicted"] > 0),
                    recall_percent=100 * part["recall"], f1_percent=100 * part["f1"],
                    predicted_as_normal_percent=100 * matrix[i][NORMAL] / part["support"],
                    **{f"predicted_as_class_{j}_count": matrix[i][j] for j in range(len(CLASSES))},
                )
    return overview, per_class


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def source_key(row):
    return row["arm"], int(row["seed"]), int(row["source_hz"]), row["phase"]


def read_source(output, overview):
    domain_rows = read_csv(output / SOURCE_DOMAIN)
    class_rows = read_csv(output / SOURCE_CLASS)
    domain = {source_key(row): row for row in domain_rows}
    per_class = {(*source_key(row), int(row["class_id"])): row for row in class_rows}
    expected = {(arm, seed, hz, phase) for arm, seed in EXPECTED for hz in SOURCES for phase in PHASES}
    expected_classes = {(*key, i) for key in expected for i in range(len(CLASSES))}
    if len(domain_rows) != len(expected) or set(domain) != expected:
        raise ValueError("Incomplete source-domain summary")
    if len(class_rows) != len(expected_classes) or set(per_class) != expected_classes:
        raise ValueError("Incomplete source class summary")
    for key, row in domain.items():
        arm, seed, hz, phase = key
        if row["run_id"] != overview[arm, seed]["run_id"]:
            raise ValueError(f"Wrong source-summary identity {key}")
        active = hz == 35 or ARMS[arm][0]
        consistency_active = hz == 35 or ARMS[arm][1]
        if (int(row["ce_active_for_source"]) != active or int(row["consistency_active_for_source"]) != consistency_active
                or int(row["consistency_denominator"]) != 192
                or int(row["consistency_pair_occurrences"]) != (int(row["sampled_occurrences"]) if consistency_active else 0)
                or int(row["actual_loss_archive_available"]) != (arm != "A")):
            raise ValueError(f"Wrong gate or fixed consistency denominator {key}")
        raw_distance = row["raw_consistency_distance_sum"]
        effective_distance = row["effective_consistency_contribution_sum"]
        if arm == "A":
            if raw_distance or effective_distance:
                raise ValueError("Historical A lacks separate actual consistency values")
        elif (not raw_distance or not effective_distance
              or any(not math.isfinite(float(v)) or float(v) < 0 for v in (raw_distance, effective_distance))
              or not math.isclose(float(effective_distance), float(raw_distance) / 192 if consistency_active else 0,
                                  rel_tol=2e-6, abs_tol=1e-9)):
            raise ValueError(f"Incorrect consistency gate or denominator in recorded loss {key}")
        selected, wrong, fed = (int(row[f]) for f in (
            "selected_count", "selected_error_count", "active_ce_error_occurrences_per_head"))
        nominal = float(row["active_ce_nominal_error_weight_sum_per_head"])
        if (not 0 <= wrong <= selected <= int(row["sampled_occurrences"]) or fed != (wrong if active else 0)
                or not math.isfinite(nominal) or nominal < 0 or (not active and nominal != 0)):
            raise ValueError(f"Wrong source loss exposure counts {key}")
        for head in ("common", "specific"):
            raw = row[f"raw_pseudo_ce_{head}_sum"]
            gated = row[f"gated_pseudo_ce_{head}_sum"]
            if arm == "A":
                if raw or gated:
                    raise ValueError("Historical A lacks separate actual cross-entropies")
            elif (not raw or not gated or any(not math.isfinite(float(v)) or float(v) < 0 for v in (raw, gated))
                  or not math.isclose(float(gated), float(raw) if active else 0, abs_tol=1e-9)):
                raise ValueError(f"Wrong observed gate for {key} {head}")
        class_group = [per_class[*key, i] for i in range(len(CLASSES))]
        if (any(item["run_id"] != row["run_id"] for item in class_group)
                or selected != sum(int(item["selected_true_class_count"]) for item in class_group)
                or wrong != sum(int(item["selected_true_class_error_count"]) for item in class_group)
                or fed != sum(int(item["active_ce_error_occurrences_per_head"]) for item in class_group)):
            raise ValueError(f"Source-class counts fail to reconcile {key}")
        candidate = ("selected_true_class_count", "selected_true_class_error_count", "selected_true_class_to_normal_count")
        if any(item[field] != per_class["A", seed, hz, phase, i][field]
               for i, item in enumerate(class_group) for field in candidate):
            raise ValueError(f"Candidate pseudo-label counts differ from the paired A archive {key}")
    return domain, per_class


def contrasts(overview, classes):
    metrics = [(f, None) for f in ("accuracy_percent", "macro_f1_percent",
                                  "predicted_normal_percent", "true_fault_as_normal_percent")]
    metrics += [("recall_percent", i) for i in range(len(CLASSES))]
    metrics += [("predicted_as_normal_percent", i) for i in range(1, len(CLASSES))]
    contrasts = {}
    for name, terms in CONTRASTS:
        for metric, cls in metrics:
            row = dict(contrast=name, priority="primary" if (name, metric) == ("B−A", "accuracy_percent")
                       else "supplementary" if name == "D−A" else "secondary",
                       metric=metric, class_id="" if cls is None else cls,
                       class_name="" if cls is None else CLASSES[cls])
            values = []
            for seed in SEEDS:
                scores = {arm: (overview[arm, seed] if cls is None else classes[arm, seed, cls])[metric]
                          for arm in ARMS}
                for arm, score in scores.items():
                    row[f"{arm}_seed_{seed}_percent"] = score
                delta = math.fsum(scores[arm] * weight for arm, weight in terms.items())
                # Exact count contrasts can leave minute binary floating-point remainders.
                values.append(0.0 if abs(delta) < 1e-12 else delta)
                row[f"delta_seed_{seed}_pp"] = values[-1]
            contrasts[name, metric, cls] = dict(
                **row, mean_pp=statistics.mean(values), sample_sd_pp=statistics.stdev(values),
                positive_seeds=sum(v > 0 for v in values), zero_seeds=sum(v == 0 for v in values),
                negative_seeds=sum(v < 0 for v in values))
    return contrasts


def group_summary(values):
    return f"{statistics.mean(values):.3f} ± {statistics.stdev(values):.3f}"


def signed_three(value):
    return "0.000" if abs(value) <= 0.0005 else f"{value:+.3f}"


def fault_flows(overview, classes, arm):
    runs = [overview[arm, seed] for seed in SEEDS]
    total = sum(row["true_fault_windows"] for row in runs)
    right = sum(row["correct_windows"] - classes[arm, row["seed"], NORMAL]["correct_windows"] for row in runs)
    as_normal = sum(row["true_fault_as_normal_windows"] for row in runs)
    return right, as_normal, total - right - as_normal


def sum_source(table, arm, hz, phase, field, *, cls=None):
    rows = [table[arm, seed, hz, phase] if cls is None else table[arm, seed, hz, phase, cls] for seed in SEEDS]
    values = [r[field] for r in rows]
    return sum(float(v) for v in values) if all(v != "" for v in values) else None


def source_report(domain, classes):
    lines = ["## 65 Hz 和 35 Hz 的伪标签与实际损失", "",
             "下表合计三个配对种子的全程采样出现次数。每个源的错误率以其入选数为分母。"
             "实际进入交叉熵的次数在两个主分类头相同。表中每头名义权重为将每步错误出现数除以该源当步入选数并乘原调度系数后，再按步与种子求和。"
             "实际 CE 两列是各头逐步按该源求均值，再按三个种子和 15 000 步求平均，列出门控前后，未乘训练调度系数。"
             "历史 A 只有合计损失快照，其逐头逐域实际 CE 没有归档。", "",
             "| 无标签源 | 臂 | 入选次数 | 错误入选次数（比例） | 错误实际进入每头次数 | 错误的每头名义权重和 | 共同头 CE 门控前→后 | 域特定头 CE 门控前→后 |",
             "|---:|:---:|---:|---:|---:|---:|---:|---:|"]
    for hz in SOURCES:
        for arm in ARMS:
            def aggregate(field):
                return sum_source(domain, arm, hz, "all", field)

            n, wrong = aggregate("selected_count"), aggregate("selected_error_count")
            fed = aggregate("active_ce_error_occurrences_per_head")
            weight = aggregate("active_ce_nominal_error_weight_sum_per_head")
            rate = f"{100 * wrong / n:.3f}%" if n else "无入选"
            ce = []
            for head in ("common", "specific"):
                raw = aggregate(f"raw_pseudo_ce_{head}_sum")
                gated = aggregate(f"gated_pseudo_ce_{head}_sum")
                ce.append(f"{raw / 15000:.5f} → {gated / 15000:.5f}" if raw is not None else "档案缺失")
            lines.append(f"| {hz} Hz | {arm} | {n:,.0f} | {wrong:,.0f}（{rate}） | {fed:,.0f} | {weight:,.3f} | "
                         + " | ".join(ce) + " |")
    lines.extend(["", "65 Hz 真值中度滚动体样本的候选错配沿用相同分母。关闭主 CE 时，候选掩码和伪标签仍继续记录。", "",
                  "| 臂 | 1–1 000 步入选后误标正常 | 1 001–2 500 步 | 2 501–5 000 步 |",
                  "|:---:|---:|---:|---:|"])
    for arm in ARMS:
        cells = []
        for phase in PHASES[1:]:
            n = sum_source(classes, arm, 65, phase, "selected_true_class_count", cls=MEDIUM_BALL)
            wrong = sum_source(classes, arm, 65, phase, "selected_true_class_to_normal_count", cls=MEDIUM_BALL)
            cells.append(f"{wrong:,.0f}/{n:,.0f}（{100 * wrong / n:.3f}%）" if n else "无入选")
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    return lines


def write_report(output, overview, classes, deltas, source, source_classes):
    primary = deltas["B−A", "accuracy_percent", None]
    prereg_link = relative_link(PREREG, output) if PREREG.anchor.casefold() == output.anchor.casefold() else PREREG.as_posix()
    if primary["positive_seeds"] == 3:
        direction = "三个种子一致改善，支持在这项固定任务中关闭整条 65 Hz 伪标签 CE 的预定方向。"
    elif primary["negative_seeds"] == 3:
        direction = "三个种子都下降，与预定的改善方向相反。"
    else:
        direction = "配对方向存在混合或零值，稳定改善未建立。"
    lines = ["# HUSTbearing 65 Hz 监督路径干预结果", "",
             "20 Hz 提供真值，35 和 65 Hz 提供无标签源，80 Hz 留出评价。"
             "三种子复用了 A 臂归档，B、C、D 共新增九次完整训练。每个模型在第 5 000 步评价相同的 729 窗，九类各 81 窗。", "",
             f"**预定主对比 B−A 的平均 Accuracy 差为 {signed_three(primary['mean_pp'])} 个百分点。** {direction}", "",
             f"[预注册方案]({prereg_link}) · [冻结协议](protocol.json) · [短检](preflight_complete.json)"
             " · [源轨迹配对核验](source_pairing_audit.json)", "",
             f"[逐模型目标结果]({TARGET_RESULTS}) · [逐类指标与混淆计数]({TARGET_CLASSES})"
             f" · [完整逐种子配对差]({CONTRAST_RESULTS}) · [源域汇总]({SOURCE_DOMAIN}) · [逐源逐类监督]({SOURCE_CLASS})", "",
             "## 80 Hz 目标结果", "", "表中百分数为三个种子的均值 ± 样本标准差。两个开关只针对 65 Hz。", "",
             "| 臂 | 主伪标签 CE | 一致性直接项 | Accuracy（%） | Macro-F1（%） | 预测正常（%） | 真实故障判正常（%） |",
             "|:---:|:---:|:---:|---:|---:|---:|---:|"]
    for arm, (ce, consistency) in ARMS.items():
        cells = [group_summary([overview[arm, seed][metric] for seed in SEEDS])
                 for metric in ("accuracy_percent", "macro_f1_percent", "predicted_normal_percent",
                                "true_fault_as_normal_percent")]
        lines.append(f"| {arm} | {'开' if ce else '关'} | {'开' if consistency else '关'} | " + " | ".join(cells) + " |")
    lines.extend(["", "| 种子 | A 正确窗 | B 正确窗 | B−A Accuracy（百分点） | B−A Macro-F1（百分点） |",
                  "|---:|---:|---:|---:|---:|"])
    primary_f1 = deltas["B−A", "macro_f1_percent", None]
    for seed in SEEDS:
        lines.append(f"| {seed} | {overview['A', seed]['correct_windows']}/729 | {overview['B', seed]['correct_windows']}/729 | "
                     f"{signed_three(primary[f'delta_seed_{seed}_pp'])} | {signed_three(primary_f1[f'delta_seed_{seed}_pp'])} |")
    lines.extend(["", "| 对比 | Accuracy 均差 ± SD（百分点） | 种子 0 / 1 / 2 的 Accuracy 差 | 正 / 零 / 负 | "
                  "Macro-F1 均差 ± SD（百分点） | 中度滚动体 Recall 均差 ± SD（百分点） |",
                  "|---|---:|---:|---:|---:|---:|"])
    for name, _ in CONTRASTS:
        acc = deltas[name, "accuracy_percent", None]
        f1 = deltas[name, "macro_f1_percent", None]
        ball = deltas[name, "recall_percent", MEDIUM_BALL]
        seeds = " / ".join(signed_three(acc[f'delta_seed_{seed}_pp']) for seed in SEEDS)
        lines.append(f"| {name} | {signed_three(acc['mean_pp'])} ± {acc['sample_sd_pp']:.3f} | {seeds} | "
                     f"{acc['positive_seeds']} / {acc['zero_seeds']} / {acc['negative_seeds']} | "
                     f"{signed_three(f1['mean_pp'])} ± {f1['sample_sd_pp']:.3f} | "
                     f"{signed_three(ball['mean_pp'])} ± {ball['sample_sd_pp']:.3f} |")
    lines.extend(["", "## 目标九类 Recall 和主对比", "",
                  "| 真实类 | A Recall（%） | B Recall（%） | C Recall（%） | D Recall（%） | B−A Recall（百分点） |",
                  "|---|---:|---:|---:|---:|---:|"])
    for i, label in enumerate(CLASSES):
        cells = [f"{statistics.mean(classes[arm, seed, i]['recall_percent'] for seed in SEEDS):.3f}" for arm in ARMS]
        lines.append(f"| {label} | " + " | ".join(cells) + f" | {signed_three(deltas['B−A', 'recall_percent', i]['mean_pp'])} |")
    lines.extend(["", "主对比 B−A 下，正常类 Recall 变化 "
                  f"{signed_three(deltas['B−A', 'recall_percent', NORMAL]['mean_pp'])} 个百分点，中度滚动体 Recall 变化 "
                  f"{signed_three(deltas['B−A', 'recall_percent', MEDIUM_BALL]['mean_pp'])} 个百分点，真实故障被判正常的比例变化 "
                  f"{signed_three(deltas['B−A', 'true_fault_as_normal_percent', None]['mean_pp'])} 个百分点。"
                  "逐类 CSV 的每行是混淆矩阵中的一个真实类，九个预测计数列按类编号排列。", ""])
    a_flows, b_flows = (fault_flows(overview, classes, arm) for arm in ("A", "B"))
    lines.extend([f"A、B 每臂各有 {sum(a_flows):,} 次真实故障评价，合计时每个目标窗在三个种子中各评价一次。",
                  "", "| 真实故障的预测去向 | A（次） | B（次） | B−A（次） |", "|---|---:|---:|---:|"])
    for label, before, after in zip(("判对具体故障", "判为正常", "判为其他故障"), a_flows, b_flows):
        lines.append(f"| {label} | {before:,} | {after:,} | {after - before:+,} |")
    lines.append("")
    lines.extend(source_report(source, source_classes))
    lines.extend(["", "## 解释范围", "",
                  "B−A 与 D−C 衡量整条 65 Hz 主伪标签交叉熵的净作用。该干预同时屏蔽正确和错误标签的损失，无法单独识别错标的因果贡献。"
                  "C−A 与 D−B 只改变 65 Hz 对一致性损失的直接项。一致性分母为 192，三域仍一起完成干净和扰动前向，65 Hz 仍可经共享批归一化与辅助分支影响模型。"
                  "固定分母和其余项的代数权重不能抵消总梯度随门控造成的变化。", "",
                  "本轮固定 20 Hz 提供真值。所得对比无法分解既往角色轮换差异。"
                  "三个种子描述同一批窗口上的优化波动。逐种子结果仅作描述性比较。", ""])
    (output / REPORT).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    output = parser.parse_args().output.resolve()
    ready = read_json(output / "all_sources_complete.json")
    preflight = read_json(output / "preflight_complete.json")
    if ready.get("complete") is not True or ready.get("models") != 9:
        raise ValueError("The nine source-only runs must pass pairing before target analysis")
    if preflight.get("complete") is not True or preflight.get("optimizer_updates") != 120:
        raise ValueError("The frozen 120-step equivalence and gate verification must be complete")
    overview, classes = validate_runs(read_json(output / "results.json"), read_json(output / "protocol.json"))
    source, source_classes = read_source(output, overview)
    deltas = contrasts(overview, classes)
    write_csv(output / TARGET_RESULTS, list(overview.values()))
    write_csv(output / TARGET_CLASSES, list(classes.values()))
    write_csv(output / CONTRAST_RESULTS, list(deltas.values()))
    write_report(output, overview, classes, deltas, source, source_classes)
    print(f"Verified {len(overview)} runs, {len(classes)} target-class rows, {len(deltas)} contrast summaries.")


if __name__ == "__main__":
    main()
