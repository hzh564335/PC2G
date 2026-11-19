"""Summarize completed fixed-step CWRU/HUST pilot results without model execution."""

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / "output/pc2g_cross_dataset_pilot_20261117/results.json"
DATASETS = ("cwru", "hust")
MODES = ("raw", "labels_only", "selection_only", "full")
NAMES = {"raw": "Raw", "labels_only": "Label", "selection_only": "Select", "full": "Full"}
CLASS_NAMES = {
    "cwru": ("正常", "内圈", "滚动体", "外圈"),
    "hust": ("正常", "内圈中度", "内圈重度", "外圈中度", "外圈重度",
             "滚动体中度", "滚动体重度", "复合中度", "复合重度"),
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def config_name(mode, b_on):
    return NAMES[mode] + ("+B" if b_on else "")


def class_metrics(matrix):
    count = len(matrix)
    if any(len(row) != count for row in matrix):
        raise ValueError("The confusion matrix must be square")
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for row in matrix for v in row):
        raise ValueError("Confusion counts must be nonnegative integers")
    output = []
    for cls in range(count):
        support = sum(matrix[cls])
        predicted = sum(row[cls] for row in matrix)
        tp = matrix[cls][cls]
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * tp / (support + predicted) if support + predicted else 0.0
        output.append({"class_id": cls, "support": support, "predicted": predicted,
                       "precision": precision, "recall": recall, "f1": f1})
    return output


def validate(results):
    if results.get("complete") is not True or results.get("scope") != "pilot":
        raise ValueError("Only a completed pilot result can be summarized")
    rows = results["rows"]
    if len(rows) != 48 or len({r["id"] for r in rows}) != 48:
        raise ValueError("Expected 48 uniquely identified runs")
    lookup = {}
    class_rows = []
    for row in rows:
        dataset, mode, seed = row["dataset"], row["mode"], row["seed"]
        weight = row["B_weight"]
        if dataset not in DATASETS or mode not in MODES or seed not in (0, 1, 2):
            raise ValueError(f"Unexpected run identity {row['id']}")
        if weight not in (0, 0.1) or row["checkpoint_step"] != 5000:
            raise ValueError(f"Unexpected B weight or checkpoint step in {row['id']}")
        if row["target"] == row["labeled"]:
            raise ValueError(f"Target and labeled source coincide in {row['id']}")
        key = (dataset, mode, bool(weight), seed)
        if key in lookup:
            raise ValueError(f"Duplicated experiment cell {key}")
        metrics = row["metrics"]
        matrix = metrics["confusion_matrix"]
        if len(matrix) != len(CLASS_NAMES[dataset]):
            raise ValueError(f"Unexpected class count in {row['id']}")
        per_class = class_metrics(matrix)
        total = sum(c["support"] for c in per_class)
        if total == 0:
            raise ValueError(f"Empty target evaluation in {row['id']}")
        accuracy = sum(matrix[c][c] for c in range(len(matrix))) / total
        macro_f1 = statistics.mean(c["f1"] for c in per_class)
        for field, calculated in (("accuracy", accuracy), ("macro_f1", macro_f1)):
            value = metrics[field]
            if not math.isfinite(value) or not math.isclose(value, calculated, abs_tol=1e-10):
                raise ValueError(f"Confusion matrix disagrees with {field} in {row['id']}")
        recall = metrics["per_class_recall"]
        if len(recall) != len(matrix) or any(
            not math.isclose(a, b["recall"], abs_tol=1e-10) for a, b in zip(recall, per_class)
        ):
            raise ValueError(f"Confusion matrix disagrees with recall in {row['id']}")
        if not math.isfinite(row["training_seconds"]) or row["training_seconds"] <= 0:
            raise ValueError(f"Invalid training duration in {row['id']}")
        lookup[key] = row
        for cls in per_class:
            class_rows.append({"dataset": dataset, "target": row["target"], "labeled": row["labeled"],
                               "configuration": config_name(mode, bool(weight)), "seed": seed,
                               "run_id": row["id"], "class_name": CLASS_NAMES[dataset][cls["class_id"]],
                               **cls})
    expected = {(d, m, b, s) for d in DATASETS for m in MODES for b in (False, True) for s in (0, 1, 2)}
    if set(lookup) != expected:
        raise ValueError("The eight configurations by three seeds are incomplete")
    for dataset in DATASETS:
        same_data = [r for r in rows if r["dataset"] == dataset]
        if len({(r["target"], r["labeled"]) for r in same_data}) != 1:
            raise ValueError(f"Pilot {dataset} contains multiple target/source roles")
        supports = {tuple(sum(r) for r in row["metrics"]["confusion_matrix"]) for row in same_data}
        if len(supports) != 1:
            raise ValueError(f"Target label distribution differs across runs of {dataset}")
    return lookup, class_rows


def summaries(lookup):
    output = []
    for dataset in DATASETS:
        for b_on in (False, True):
            for mode in MODES:
                runs = [lookup[dataset, mode, b_on, seed] for seed in (0, 1, 2)]
                row = {"dataset": dataset, "target": runs[0]["target"], "labeled": runs[0]["labeled"],
                       "configuration": config_name(mode, b_on), "mode": mode,
                       "B_weight": 0.1 if b_on else 0.0, "n_optimization_seeds": 3,
                       "checkpoint_step": 5000}
                for metric in ("accuracy", "macro_f1"):
                    values = [r["metrics"][metric] * 100 for r in runs]
                    row[f"{metric}_mean_percent"] = statistics.mean(values)
                    row[f"{metric}_sd_percent"] = statistics.stdev(values)
                row["training_seconds_total"] = sum(r["training_seconds"] for r in runs)
                output.append(row)
    return output


def contrasts():
    output = []
    for b_on in (False, True):
        suffix = "B开" if b_on else "B关"
        output.extend([
            (f"固定原始集合，{suffix}，Label−Raw", [("labels_only", b_on, 1), ("raw", b_on, -1)]),
            (f"固定校正集合，{suffix}，Full−Select", [("full", b_on, 1), ("selection_only", b_on, -1)]),
            (f"固定原始标签，{suffix}，Select−Raw", [("selection_only", b_on, 1), ("raw", b_on, -1)]),
            (f"固定校正标签，{suffix}，Full−Label", [("full", b_on, 1), ("labels_only", b_on, -1)]),
            (f"标签×筛选双差，{suffix}", [("full", b_on, 1), ("labels_only", b_on, -1),
                                               ("selection_only", b_on, -1), ("raw", b_on, 1)]),
        ])
    for mode in MODES:
        output.append((f"固定{NAMES[mode]}，B开−B关", [(mode, True, 1), (mode, False, -1)]))
    output.append(("三阶双差，B开时标签×筛选减B关时标签×筛选",
                   [("full", True, 1), ("labels_only", True, -1), ("selection_only", True, -1),
                    ("raw", True, 1), ("full", False, -1), ("labels_only", False, 1),
                    ("selection_only", False, 1), ("raw", False, -1)]))
    output.append(("整体方案，Full+B−Raw", [("full", True, 1), ("raw", False, -1)]))
    return output


def paired_differences(lookup):
    output = []
    for dataset in DATASETS:
        for name, weights in contrasts():
            row = {"dataset": dataset, "contrast": name, "n_optimization_seeds": 3,
                   "target": lookup[dataset, "raw", False, 0]["target"],
                   "labeled": lookup[dataset, "raw", False, 0]["labeled"]}
            for metric in ("accuracy", "macro_f1"):
                values = [sum(lookup[dataset, mode, b_on, seed]["metrics"][metric] * weight * 100
                              for mode, b_on, weight in weights) for seed in (0, 1, 2)]
                row[f"{metric}_mean_pp"] = statistics.mean(values)
                row[f"{metric}_sd_pp"] = statistics.stdev(values)
                row[f"{metric}_positive_seeds"] = sum(v > 1e-12 for v in values)
                row[f"{metric}_zero_seeds"] = sum(abs(v) <= 1e-12 for v in values)
                row[f"{metric}_negative_seeds"] = sum(v < -1e-12 for v in values)
                for seed, value in enumerate(values):
                    row[f"{metric}_seed_{seed}_pp"] = value
            output.append(row)
    return output


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def relative_link(path, directory):
    return Path(os.path.relpath(path, directory)).as_posix()


def write_report(directory, source, protocol, rows, summary, differences):
    protocol_link = relative_link(protocol, directory)
    source_link = relative_link(source, directory)
    lines = ["# CWRU 与 HUSTbearing 固定第 5 000 步试跑结果", "",
             "本轮完成两个数据集各 24 次训练，每库一个留出目标、一个有标签源角色、八种配置、三个配对优化种子。"
             "所有模型统一在第 5 000 步评价。均值与样本标准差以三个优化种子计算，描述这一任务内的训练随机性。"
             "这轮范围只覆盖所列目标与源角色。正式四折及源角色轮换还需另行执行。", "",
             f"[冻结协议]({protocol_link}) · [48 条原始结果]({source_link}) · "
             "[逐配置均值与标准差](configuration_summary.csv) · [逐种子成绩](seed_results.csv) · "
             "[逐类指标](class_results.csv) · [配对差](paired_differences.csv)", ""]
    for dataset in DATASETS:
        runs = [r for r in rows if r["dataset"] == dataset]
        target, labeled = runs[0]["target"], runs[0]["labeled"]
        title = "CWRU" if dataset == "cwru" else "HUSTbearing"
        domain_text = ("域 0/1/2/3 对应 0/1/2/3 HP。" if dataset == "cwru" else
                       "域 0/1/2/3 对应电机设定频率 20/35/65/80 Hz。")
        total = sum(sum(row) for row in runs[0]["metrics"]["confusion_matrix"])
        seconds = sum(r["training_seconds"] for r in runs)
        lines.extend([f"## {title}", "", f"{domain_text}本次留出域 {target}，有标签源为域 {labeled}，"
                      f"其他两个源仅提供无标签训练输入。每次最终测试 {total} 窗。"
                      f"24 次源训练累计 {seconds / 3600:.3f} 小时。", "",
                      "| 配置 | Accuracy / %，均值 ± SD | Macro-F1 / %，均值 ± SD |",
                      "|---|---:|---:|"])
        for row in summary:
            if row["dataset"] == dataset:
                lines.append(f"| {row['configuration']} | {row['accuracy_mean_percent']:.3f} ± "
                             f"{row['accuracy_sd_percent']:.3f} | {row['macro_f1_mean_percent']:.3f} ± "
                             f"{row['macro_f1_sd_percent']:.3f} |")
        lines.extend(["", "配对差在同一种子内相减，然后汇总三个种子。双差按表中算式计算，"
                      "正值指算式结果为正。该表保留正、零、负方向，不进行显著性判断。", "",
                      "| 条件对比 | Accuracy 差 / 百分点，均值 ± SD | Macro-F1 差 / 百分点，均值 ± SD | Accuracy 正/零/负种子 |",
                      "|---|---:|---:|---:|"])
        for row in differences:
            if row["dataset"] == dataset:
                lines.append(f"| {row['contrast']} | {row['accuracy_mean_pp']:+.3f} ± "
                             f"{row['accuracy_sd_pp']:.3f} | {row['macro_f1_mean_pp']:+.3f} ± "
                             f"{row['macro_f1_sd_pp']:.3f} | {row['accuracy_positive_seeds']}/"
                             f"{row['accuracy_zero_seeds']}/{row['accuracy_negative_seeds']} |")
        lines.append("")
    lines.extend(["## 复核及适用范围", "",
                  "本汇总核对了每库八配置、种子 0–2 的 24 个唯一单元，步数均为 5 000，同库目标角色与"
                  "目标类别支持数一致。所有 Accuracy、Macro-F1 和逐类召回均由保存的混淆矩阵独立复算。"
                  "初始化、采样顺序、监督路径和训练期文件访问的核验应结合运行回执及配对审计文件阅读。", "",
                  "两个新子集每个工况、每类只有一条采集，采用整记录分组和固定末步，源验证为零。"
                  "CWRU 正常驱动端信号先从 48 kHz 抗混叠降至 12 kHz，故障信号保持原 12 kHz。"
                  "HUST 保持 25.6 kHz。两库输入均为 3 200 点、无重叠窗口，每窗独立极值归一化。"
                  "HUST 同健康状态跨工况使用同一轴承，CWRU 也没有建立轴承身份隔离，因此任务范围是工况变化下的诊断。"
                  "三种子和多个信号窗不能代替独立轴承或设备的重复试验。", "",
                  "历史 CWRU10 和 HUST 20/40/60/80 Hz 的成绩已经查看过。该试跑使用冻结的新任务，"
                  "论文需要明确既有探索和本轮范围。", "",
                  f"结果文件 SHA-256 为 {hashlib.sha256(source.read_bytes()).hexdigest()}。", "",
                  f"冻结协议 SHA-256 为 {hashlib.sha256(protocol.read_bytes()).hexdigest()}。", ""])
    quality_path = directory / "pseudo_label_quality.csv"
    if quality_path.exists():
        with quality_path.open(encoding="utf-8-sig", newline="") as stream:
            quality = list(csv.DictReader(stream))
        lines.extend(["## 训练监督的离线核对", "",
                      "以下只在全部训练完成后使用无标签源真值，分母是训练中有放回采样的出现次数。"
                      "每个种子先合并两个无标签源的全程计数，再对三种子等权平均。"
                      "两种 B 水平共享辅助轨迹。完整分阶段和成员结果见"
                      "[伪标签质量](pseudo_label_quality.csv)与[成员变化](member_changes.csv)。", "",
                      "| 数据集 | 配置 | 入选正确率 / % | 实际入选率 / % |",
                      "|---|---|---:|---:|"])
        for dataset in DATASETS:
            for mode in MODES:
                selected = [r for r in quality if r["dataset"] == dataset and r["mode"] == mode
                            and r["phase"] == "all" and r["source_scope"] == "all_U"]
                if len(selected) != 3:
                    raise ValueError("Incomplete offline quality summary")
                accuracy = statistics.mean(float(r["selected_accuracy_percent"]) for r in selected)
                selection = statistics.mean(float(r["selection_rate_percent"]) for r in selected)
                lines.append(f"| {dataset} | {NAMES[mode]} | {accuracy:.3f} | {selection:.3f} |")
        lines.extend(["", "源端质量与目标表现采用不同的统计单位。CWRU 的 Full 与 Select 入选正确率均约 99.70%，"
                      "差值很小；HUST 的 Full 入选正确率约 71.15%，"
                      "与当前 80 Hz 目标的低准确率不能用同一个数字概括。", ""])
    source_fit = directory / "source_fit_diagnostic.json"
    if source_fit.exists():
        lines.extend(["## 源训练拟合复核", "",
                      "针对 Raw 与 Full+B 的三个种子，额外读取各自冻结末步模型，对有标签源训练集计算指标。"
                      "两库共 12 个模型的源训练 Accuracy 和 Macro-F1 均为 100%。"
                      "HUST 的低目标成绩发生在源训练已完全拟合的情况下。"
                      "此项检查训练集拟合情况，各窗已参与训练，不能视为独立源验证。"
                      "[逐模型复核值](source_fit_diagnostic.json)", ""])
    lines.extend(["## HUSTbearing 低分与执行记录", "",
                  "HUST 的九类目标支持数均为 81。当前 80 Hz 原始窗口按类别重排后，"
                  "与旧实验同工况的 729 个目标窗逐点一致，类别映射一致。"
                  "当前 Full+B 三种子分别把 523、520、530 个目标窗判为正常，占约 71%–73%，"
                  "正常类召回率均为 100%，故障类召回很低。旧 HUST 的四目标均分约 47%，"
                  "其中这个 80 Hz、20 Hz 有标签源任务的旧 Raw 与旧 Full+B 均分分别只有 15.958% 和 14.266%。"
                  "新旧训练源频率、训练窗数、选模规则同时变化，不能由两次成绩推出单一原因。"
                  "[旧实验原始结果](../hust_da_b_v1/results.json) · [本轮逐类指标](class_results.csv)", "",
                  "首个完整训练在第 286 步后因 Windows 进度文件被短暂占用而中断。"
                  "不完整记录保存在 interrupted_io_attempt，进度写入加入短重试后从头重跑，"
                  "该尝试未计入 48 个完成模型。protocol_initial.json 和 protocol.json 保存了执行修复的来源。"
                  "六组初始化、逐步采样和辅助轨迹配对以及全部 48 份目标预测指标通过"
                  "[独立审计](audit_checks.json)。", ""])
    (directory / "PILOT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    source = args.results.resolve()
    protocol = args.protocol.resolve() if args.protocol else source.parent / "protocol.json"
    if not protocol.is_file():
        raise FileNotFoundError(f"Missing frozen protocol {protocol}")
    data = read_json(source)
    frozen = read_json(protocol)
    fields = ("id", "dataset", "target", "labeled", "seed", "mode", "B_weight")
    frozen_rows = {tuple(row[field] for field in fields) for row in frozen["rows"]}
    actual_rows = {tuple(row[field] for field in fields) for row in data["rows"]}
    if len(frozen_rows) != 48 or frozen_rows != actual_rows:
        raise ValueError("Completed run identities differ from the frozen protocol")
    lookup, class_rows = validate(data)
    summary = summaries(lookup)
    differences = paired_differences(lookup)
    seed_rows = []
    for dataset in DATASETS:
        for b_on in (False, True):
            for mode in MODES:
                for seed in (0, 1, 2):
                    row = lookup[dataset, mode, b_on, seed]
                    seed_rows.append({"dataset": dataset, "target": row["target"], "labeled": row["labeled"],
                                      "configuration": config_name(mode, b_on), "mode": mode,
                                      "B_weight": row["B_weight"], "seed": seed, "run_id": row["id"],
                                      "checkpoint_step": row["checkpoint_step"],
                                      "accuracy_percent": row["metrics"]["accuracy"] * 100,
                                      "macro_f1_percent": row["metrics"]["macro_f1"] * 100,
                                      "training_seconds": row["training_seconds"]})
    directory = source.parent
    for name, values in (("configuration_summary.csv", summary), ("seed_results.csv", seed_rows),
                         ("class_results.csv", class_rows), ("paired_differences.csv", differences)):
        write_csv(directory / name, values)
    write_report(directory, source, protocol, data["rows"], summary, differences)
    print(json.dumps({"complete": True, "validated_runs": len(seed_rows),
                      "class_rows": len(class_rows), "report": str(directory / "PILOT_REPORT.md")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
