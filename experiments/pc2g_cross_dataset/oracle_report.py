"""Aggregate audited, completed 65 Hz Oracle and historical A/B evaluations."""

import argparse
import hashlib
import math
import statistics
from pathlib import Path

import numpy as np

from .report_path import group_summary, signed_three
from .report_pilot import CLASS_NAMES, class_metrics, read_json, relative_link, write_csv


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/pc2g_hust_65hz_oracle_preregistration_20261119"
ORACLE_RUNS = ROOT / "runs/pc2g_hust_65hz_oracle_20261119"
HISTORICAL = {
    "A": (ROOT / "runs/pc2g_cross_dataset_pilot_20261117", "full-B1"),
    "B": (ROOT / "runs/pc2g_hust_65hz_path_20261119", "path-B"),
}
ARMS = ("A", "B", "O")
SEEDS = (0, 1, 2)
CLASSES = CLASS_NAMES["hust"]
N_CLASSES = len(CLASSES)
SUPPORT, CHECKPOINT_STEP = 81, 5000
NORMAL, MEDIUM_BALL, SEVERE_COMBINED = 0, 5, 8
PAIRS = (("O−A", "O", "A"), ("O−B", "O", "B"), ("B−A", "B", "A"))
PRIMARY = (("accuracy_percent", "Accuracy"), ("macro_f1_percent", "Macro-F1"))
MECHANISM = (
    ("true_fault_as_normal_percent", "故障判正常比例"),
    ("predicted_normal_percent", "预测正常比例"),
)
FAULT_COUNTS = (
    ("true_fault_correct_windows", "判对具体故障"),
    ("true_fault_wrong_fault_windows", "判为其他故障"),
    ("true_fault_as_normal_windows", "判为正常"),
)
FILE_NAMES = {
    "seed": "oracle_seed_results.csv",
    "class": "oracle_class_metrics.csv",
    "paired": "oracle_paired_comparison.csv",
    "report": "oracle_final_report.md",
}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_release(output):
    preflight = read_json(output / "preflight_complete.json")
    release = read_json(output / "all_sources_complete.json")
    if preflight.get("complete") is not True or preflight.get("actual_updates") != 120:
        raise ValueError("A successful 120-update technical check is required")
    if (release.get("complete") is not True or release.get("models") != len(SEEDS)
            or release.get("checkpoint_step") != CHECKPOINT_STEP
            or set(release.get("by_seed", ())) != {str(seed) for seed in SEEDS}):
        raise ValueError("The three fixed-step source releases are required")
    return release["by_seed"]


def read_evaluation(arm, seed, runs, release):
    run_root, suffix = HISTORICAL.get(arm, (runs, "oracle"))
    run_id = f"hust-t3-L0-s{seed}-{suffix}"
    directory = run_root / run_id
    receipt_file = directory / "source_complete.json"
    receipt = read_json(receipt_file)
    result = read_json(directory / "result.json")
    expected = {
        "id": run_id, "dataset": "hust", "target": 3, "labeled": 0, "seed": seed,
        "checkpoint_step": CHECKPOINT_STEP,
    }
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Target result identity mismatch for {run_id}")
    if (receipt.get("complete") is not True or receipt.get("actual_updates") != CHECKPOINT_STEP
            or receipt.get("target_arrays_loaded") is not False):
        raise ValueError(f"Invalid fixed-step source receipt for {run_id}")
    checkpoint = result["checkpoint_sha256"]
    if checkpoint != receipt["artifacts_sha256"]["last.pt"] or checkpoint != sha256(directory / "last.pt"):
        raise ValueError(f"Checkpoint mismatch for {run_id}")
    if arm == "O":
        gate = release[str(seed)]
        if gate["source_receipt_sha256"] != sha256(receipt_file) or gate["checkpoint_sha256"] != checkpoint:
            raise ValueError(f"Oracle result differs from the audited source release for {run_id}")
    if arm == "B" and (result.get("ce65") is not False or result.get("cons65") is not True):
        raise ValueError(f"Historical B supervision switches differ for {run_id}")
    predictions = directory / "target_predictions.npz"
    if sha256(predictions) != result["prediction_sha256"]:
        raise ValueError(f"Prediction archive digest mismatch for {run_id}")
    with np.load(predictions, allow_pickle=False) as data:
        labels, logits = data["labels"], data["logits"]
    if (labels.shape != (SUPPORT * N_CLASSES,) or not np.issubdtype(labels.dtype, np.integer)
            or labels.min() < 0 or labels.max() >= N_CLASSES
            or np.bincount(labels, minlength=N_CLASSES).tolist() != [SUPPORT] * N_CLASSES
            or logits.shape != (len(labels), N_CLASSES) or not np.isfinite(logits).all()):
        raise ValueError(f"Frozen target population or logits mismatch for {run_id}")
    matrix = np.bincount(N_CLASSES * labels + logits.argmax(axis=1), minlength=N_CLASSES ** 2)
    matrix = matrix.reshape(N_CLASSES, N_CLASSES).tolist()
    metrics = result["metrics"]
    if metrics["confusion_matrix"] != matrix:
        raise ValueError(f"Prediction archive differs from the confusion matrix for {run_id}")
    return labels, directory, result, matrix


def summarize(arm, seed, directory, result, matrix):
    parts = class_metrics(matrix)
    metrics = result["metrics"]
    total = sum(part["support"] for part in parts)
    correct = sum(matrix[i][i] for i in range(N_CLASSES))
    accuracy = correct / total
    macro_f1 = statistics.mean(part["f1"] for part in parts)
    recall = metrics["per_class_recall"]
    if (not math.isclose(metrics["accuracy"], accuracy, abs_tol=1e-10)
            or not math.isclose(metrics["macro_f1"], macro_f1, abs_tol=1e-10)
            or len(recall) != N_CLASSES
            or any(not math.isclose(v, part["recall"], abs_tol=1e-10) for v, part in zip(recall, parts))):
        raise ValueError(f"Stored metrics disagree with the archived counts for {result['id']}")
    seconds = result["training_seconds"]
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(f"Invalid training duration for {result['id']}")
    predicted_normal = parts[NORMAL]["predicted"]
    faults = total - parts[NORMAL]["support"]
    fault_as_normal = predicted_normal - matrix[NORMAL][NORMAL]
    fault_correct = correct - matrix[NORMAL][NORMAL]
    identity = dict(arm=arm, seed=seed, run_id=result["id"], reused=arm != "O",
                    labeled_hz=20, target_hz=80, checkpoint_step=CHECKPOINT_STEP,
                    ce65=arm != "B", cons65=True)
    overview = dict(
        **identity, target_windows=total, correct_windows=correct,
        accuracy_percent=100 * accuracy, macro_f1_percent=100 * macro_f1,
        predicted_normal_windows=predicted_normal, predicted_normal_percent=100 * predicted_normal / total,
        true_fault_windows=faults, true_fault_as_normal_windows=fault_as_normal,
        true_fault_as_normal_percent=100 * fault_as_normal / faults,
        true_fault_correct_windows=fault_correct,
        true_fault_wrong_fault_windows=faults - fault_as_normal - fault_correct,
        checkpoint_sha256=result["checkpoint_sha256"], prediction_sha256=result["prediction_sha256"],
        training_seconds=seconds, run_dir=str(directory),
    )
    per_class = {}
    for i, part in enumerate(parts):
        per_class[arm, seed, i] = dict(
            **identity, class_id=i, class_name=CLASSES[i], support=part["support"],
            correct_windows=matrix[i][i], predicted_count=part["predicted"],
            precision_percent=100 * part["precision"], precision_defined=int(part["predicted"] > 0),
            recall_percent=100 * part["recall"], f1_percent=100 * part["f1"],
            predicted_as_normal_percent=100 * matrix[i][NORMAL] / part["support"],
            **{f"predicted_as_class_{j}_count": matrix[i][j] for j in range(N_CLASSES)},
        )
    return overview, per_class


def paired_comparisons(overview, classes):
    fields = [(metric, None, "percentage_points") for metric, _ in PRIMARY + MECHANISM]
    fields.extend((metric, None, "windows") for metric, _ in FAULT_COUNTS)
    fields.extend(("recall_percent", cls, "percentage_points") for cls in range(N_CLASSES))
    fields.extend(("predicted_count", cls, "windows") for cls in range(N_CLASSES))
    result = {}
    for contrast, first, second in PAIRS:
        for metric, cls, unit in fields:
            priority = "secondary"
            if contrast == "O−A":
                priority = "primary" if metric in dict(PRIMARY) else "mechanism"
            row = dict(contrast=contrast, priority=priority, metric=metric, delta_unit=unit,
                       class_id="" if cls is None else cls, class_name="" if cls is None else CLASSES[cls])
            deltas = []
            for seed in SEEDS:
                scores = {arm: (overview[arm, seed] if cls is None else classes[arm, seed, cls])[metric]
                          for arm in ARMS}
                for arm, score in scores.items():
                    row[f"{arm}_seed_{seed}"] = score
                delta = scores[first] - scores[second]
                deltas.append(0 if abs(delta) < 1e-12 else delta)
                row[f"delta_seed_{seed}"] = deltas[-1]
            result[contrast, metric, cls] = dict(
                **row, mean_delta=statistics.mean(deltas), sample_sd_delta=statistics.stdev(deltas),
                positive_seeds=sum(value > 0 for value in deltas),
                zero_seeds=sum(value == 0 for value in deltas),
                negative_seeds=sum(value < 0 for value in deltas),
            )
    return result


def headline(paired, contrast):
    rows = [paired[contrast, metric, None] for metric, _ in PRIMARY]
    if all(row["positive_seeds"] == len(SEEDS) for row in rows):
        return f"**{contrast} 的两项主指标在三个种子上均提高。**"
    if all(row["mean_delta"] > 0 for row in rows):
        return f"**{contrast} 的两项主指标平均提高，种子间方向有差异。**"
    changes = "、".join(f"{label} {signed_three(row['mean_delta'])}"
                        for (_, label), row in zip(PRIMARY, rows))
    return f"**{contrast} 的两项主指标未同时平均提高。** {changes} 个百分点。"


def report_text(output, overview, classes, paired):
    old_report = ROOT / "output/pc2g_hust_65hz_path_20261119/HUST_65Hz_path_intervention_report.md"
    historical_link = relative_link(old_report, output) if old_report.anchor == output.anchor else old_report.as_posix()
    lines = [
        "# HUSTbearing 65 Hz Oracle 伪标签纠错结果", "",
        headline(paired, "O−A"), "", headline(paired, "O−B"), "",
        "固定 20 Hz 有标签、35 Hz 和 65 Hz 源域、80 Hz 留出。120 步技术检查通过后，"
        "O 的三个种子分别训练 5,000 步。全部源端审计通过后评价 80 Hz，共 729 个窗口，每类 81 个。"
        "A 与 B 直接复用历史第 5,000 步评价。[预注册方案](oracle_preregistration.md) "
        f"[历史 A、B 报告]({historical_link})", "",
        "## 总体表现", "",
        "下表为种子 0、1、2 的均值 ± 样本标准差，单位为 %。", "",
        "| 实验臂 | Accuracy | Macro-F1 | 故障判正常比例 | 预测正常比例 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    arm_names = {"A": "A 原监督", "B": "B 屏蔽 65 Hz 分类监督", "O": "O 入选错标纠正"}
    for arm in ARMS:
        summaries = [group_summary([overview[arm, seed][metric] for seed in SEEDS])
                     for metric, _ in PRIMARY + MECHANISM]
        lines.append("| " + " | ".join([arm_names[arm], *summaries]) + " |")
    lines.extend([
        "", "## 同种子配对差", "", "差值单位为百分点。正召回差表示更多该类窗口被识别。",
        "故障判正常比例与故障预测去向一起解释。", "",
        "| 对比 | 指标 | 种子 0 | 种子 1 | 种子 2 | 均值 ± 样本标准差 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ])
    paired_fields = [(metric, label, None) for metric, label in PRIMARY + MECHANISM]
    paired_fields.extend(("recall_percent", f"{CLASSES[cls]} Recall", cls)
                         for cls in (MEDIUM_BALL, SEVERE_COMBINED))
    for contrast, _, _ in PAIRS:
        for metric, label, cls in paired_fields:
            row = paired[contrast, metric, cls]
            cells = [signed_three(row[f"delta_seed_{seed}"]) for seed in SEEDS]
            summary = f"{signed_three(row['mean_delta'])} ± {row['sample_sd_delta']:.3f}"
            lines.append("| " + " | ".join([contrast, label, *cells, summary]) + " |")
    lines.extend([
        "", "## 类别召回和故障预测去向", "",
        "| 真实类别 | A Recall (%) | B Recall (%) | O Recall (%) | O−A 平均 (pp) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for cls, label in enumerate(CLASSES):
        summaries = [group_summary([classes[arm, seed, cls]["recall_percent"] for seed in SEEDS]) for arm in ARMS]
        difference = signed_three(paired["O−A", "recall_percent", cls]["mean_delta"])
        lines.append("| " + " | ".join([label, *summaries, difference]) + " |")
    lines.extend([
        "", "下表合计三个种子的真实故障窗口预测去向。", "",
        "| 实验臂 | 判对具体故障 | 判为其他故障 | 判为正常 |",
        "| --- | ---: | ---: | ---: |",
    ])
    for arm in ARMS:
        counts = [f"{sum(overview[arm, seed][key] for seed in SEEDS):,}" for key, _ in FAULT_COUNTS]
        lines.append("| " + " | ".join([arm, *counts]) + " |")
    o_a_normal = paired["O−A", "true_fault_as_normal_percent", None]["mean_delta"]
    o_a_correct = paired["O−A", "true_fault_correct_windows", None]["mean_delta"]
    if o_a_normal < 0:
        message = ("O 相对 A 减少了故障判正常，也增加了判对具体故障的次数。"
                   if o_a_correct > 0 else
                   "O 相对 A 减少了故障判正常，但判对具体故障的次数并未增加。")
        lines.extend(["", message])
    lines.extend([
        "", "## 解释范围", "",
        "O−A 衡量固定入选集合和权重后替换错标的净效应。O−B 衡量整组正确监督相对关闭 "
        "65 Hz 分类监督的净效应。B−A 衡量移除原有整组监督的净效应。"
        "三个配对种子的差值用于描述方向与波动，推论限于当前 HUSTbearing 任务与固定入选轨迹。"
        "Oracle 使用额外的 65 Hz 真值，仅作机制对照。", "",
        "## 结果与审计文件", "",
        f"- [种子结果]({FILE_NAMES['seed']})",
        f"- [逐类指标与预测计数]({FILE_NAMES['class']})",
        f"- [全部配对差]({FILE_NAMES['paired']})",
        "- [技术审查](oracle_implementation_audit.json)",
        "- [正式源端放行记录](all_sources_complete.json)",
    ])
    for label, name in (("逐步入选审计", "oracle_stepwise_mask_audit.csv"),
                        ("标签纠正审计", "oracle_label_correction_audit.csv")):
        if (output / name).is_file():
            lines.append(f"- [{label}]({name})")
    return "\n".join(lines) + "\n"


def generate(output, runs):
    release = source_release(output)
    overview, per_class = {}, {}
    reference_labels = None
    for arm in ARMS:
        for seed in SEEDS:
            labels, directory, result, matrix = read_evaluation(arm, seed, runs, release)
            if reference_labels is None:
                reference_labels = labels
            elif not np.array_equal(labels, reference_labels):
                raise ValueError(f"Target row order differs for {result['id']}")
            overview[arm, seed], class_rows = summarize(arm, seed, directory, result, matrix)
            per_class.update(class_rows)
    paired = paired_comparisons(overview, per_class)
    report = report_text(output, overview, per_class, paired)
    write_csv(output / FILE_NAMES["seed"], list(overview.values()))
    write_csv(output / FILE_NAMES["class"], list(per_class.values()))
    write_csv(output / FILE_NAMES["paired"], list(paired.values()))
    (output / FILE_NAMES["report"]).write_text(report, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--runs-dir", type=Path, default=ORACLE_RUNS)
    args = parser.parse_args()
    generate(args.output.resolve(), args.runs_dir.resolve())


if __name__ == "__main__":
    main()
