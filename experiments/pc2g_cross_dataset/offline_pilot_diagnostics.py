"""Audit saved pilot supervision traces after every source model has finished."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from . import tasks


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/pc2g_cross_dataset_pilot_20261117"
RUNS = ROOT / "runs/pc2g_cross_dataset_pilot_20261117"
PHASES = (("all", 0, 5000), ("early", 0, 1000),
          ("middle", 1000, 2500), ("late", 2500, 5000))
MODE_PATHS = {"raw": ("raw_mask", "raw_labels"),
              "labels_only": ("raw_mask", "q_labels"),
              "selection_only": ("q_mask", "raw_labels"),
              "full": ("q_mask", "q_labels")}
TRACE_FIELDS = ("indices", "raw_labels", "q_labels", "raw_mask", "q_mask")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def percent(numerator, denominator):
    return numerator * 100 / denominator if denominator else None


def load_trace(row, runs):
    folder = runs / row["id"]
    receipt = read(folder / "source_complete.json")
    if (receipt.get("complete") is not True or receipt["actual_updates"] != 5000 or
            receipt["checkpoint_step"] != 5000 or receipt["target_arrays_loaded"] is not False or
            receipt["unlabeled_truth_used"] is not False):
        raise ValueError(f"Incomplete source-only receipt for {row['id']}")
    for field in ("id", "dataset", "target", "labeled", "seed", "mode", "B_weight"):
        if receipt[field] != row[field]:
            raise ValueError(f"Receipt identity differs for {row['id']}")
    path = folder / "training_predictions.npz"
    digest = sha(path)
    if digest != receipt["artifacts_sha256"][path.name]:
        raise ValueError(f"Trace file hash differs for {row['id']}")
    with np.load(path, allow_pickle=False) as source:
        trace = {key: source[key] for key in (*TRACE_FIELDS, "actual_labels", "actual_mask")}
    if trace["indices"].shape != (5000, 3, 64) or not np.issubdtype(trace["indices"].dtype, np.integer):
        raise ValueError(f"Unexpected sampling indices in {row['id']}")
    for name in ("raw_labels", "q_labels", "actual_labels"):
        if trace[name].shape != (5000, 2, 64) or not np.issubdtype(trace[name].dtype, np.integer):
            raise ValueError(f"Unexpected label trace {name} in {row['id']}")
    for name in ("raw_mask", "q_mask", "actual_mask"):
        if trace[name].shape != (5000, 2, 64) or trace[name].dtype != np.bool_:
            raise ValueError(f"Unexpected mask trace {name} in {row['id']}")
    mask, labels = MODE_PATHS[row["mode"]]
    if not np.array_equal(trace["actual_mask"], trace[mask]):
        raise ValueError(f"Actual mask contradicts configured selection in {row['id']}")
    if not np.array_equal(trace["actual_labels"], trace[labels]):
        raise ValueError(f"Actual labels contradict configured assignment in {row['id']}")
    return trace, receipt, digest


def check_sources(output, runs):
    marker = read(output / "all_sources_complete.json")
    if marker.get("complete") is not True or marker.get("models") != 48:
        raise ValueError("The source-completion gate must contain all 48 completed models")
    protocol = read(output / "protocol.json")
    rows = protocol["rows"]
    expected = {(dataset, seed, mode, weight) for dataset in ("cwru", "hust")
                for seed in range(3) for mode in MODE_PATHS for weight in (0.0, 0.1)}
    actual = {(row["dataset"], row["seed"], row["mode"], row["B_weight"]) for row in rows}
    if len(rows) != 48 or len({row["id"] for row in rows}) != 48 or actual != expected:
        raise ValueError("The frozen pilot matrix is incomplete")
    # Verify the existence of all source receipts before reading any hidden labels.
    for row in rows:
        receipt = read(runs / row["id"] / "source_complete.json")
        if receipt.get("complete") is not True or receipt["actual_updates"] != 5000:
            raise ValueError(f"Source training unfinished for {row['id']}")
    return rows


def hidden_source_truth(dataset, rows):
    labeled = {row["labeled"] for row in rows}
    target = {row["target"] for row in rows}
    if len(labeled) != 1 or len(target) != 1 or labeled == target:
        raise ValueError(f"Expected one task for {dataset}")
    source_domains = [domain for domain in tasks.DOMAINS if domain not in labeled | target]
    records = tasks.records(dataset)
    source_records = [r for r in records if int(r["domain_id"]) in source_domains]
    truths = []
    for domain in source_domains:
        signals, truth = tasks.load_domain(dataset, source_records, domain, True, ROOT)
        if len(signals) != len(truth):
            raise ValueError("Source-window label count differs from signal count")
        truths.append(truth)
        del signals
    return source_domains, truths


def quality_rows(common, trace, truth, domains):
    output = []
    for phase, first, end in PHASES:
        for mode, (mask_key, label_key) in MODE_PATHS.items():
            masks = trace[mask_key][first:end]
            correct = trace[label_key][first:end] == truth[first:end]
            for name, index in (("U1", 0), ("U2", 1), ("all_U", None)):
                selected = masks if index is None else masks[:, index]
                correctness = correct if index is None else correct[:, index]
                denominator = selected.size
                count = int(selected.sum())
                correct_count = int((selected & correctness).sum())
                output.append({**common, "phase": phase, "first_step": first + 1, "last_step": end,
                               "mode": mode, "source_scope": name,
                               "source_domain": "|".join(map(str, domains)) if index is None else domains[index],
                               "sampled_occurrences": denominator, "selected_occurrences": count,
                               "selected_correct_occurrences": correct_count,
                               "selection_rate_percent": percent(count, denominator),
                               "selected_accuracy_percent": percent(correct_count, count)})
    return output


def member_rows(common, trace, truth, domains):
    output = []
    raw_mask, q_mask = trace["raw_mask"], trace["q_mask"]
    groups = {"common": raw_mask & q_mask, "added": ~raw_mask & q_mask,
              "removed": raw_mask & ~q_mask}
    raw_correct = trace["raw_labels"] == truth
    q_correct = trace["q_labels"] == truth
    label_changed = trace["raw_labels"] != trace["q_labels"]
    events = {"wrong_to_right": ~raw_correct & q_correct,
              "right_to_wrong": raw_correct & ~q_correct,
              "wrong_to_different_wrong": ~raw_correct & ~q_correct & label_changed,
              "unchanged_correct": raw_correct & q_correct,
              "unchanged_wrong": ~raw_correct & ~q_correct & ~label_changed}
    for phase, first, end in PHASES:
        for group, mask in groups.items():
            part = mask[first:end]
            for name, index in (("U1", 0), ("U2", 1), ("all_U", None)):
                selected = part if index is None else part[:, index]
                raw = raw_correct[first:end] if index is None else raw_correct[first:end, index]
                q = q_correct[first:end] if index is None else q_correct[first:end, index]
                count = int(selected.sum())
                raw_count, q_count = int((selected & raw).sum()), int((selected & q).sum())
                result = {**common, "phase": phase, "first_step": first + 1, "last_step": end,
                          "member_group": group, "source_scope": name,
                          "source_domain": "|".join(map(str, domains)) if index is None else domains[index],
                          "sampled_occurrences": selected.size, "member_occurrences": count,
                          "member_share_percent": percent(count, selected.size),
                          "raw_correct_occurrences": raw_count, "corrected_correct_occurrences": q_count,
                          "raw_accuracy_percent": percent(raw_count, count),
                          "corrected_accuracy_percent": percent(q_count, count)}
                event_total = 0
                for event, all_events in events.items():
                    event_part = all_events[first:end] if index is None else all_events[first:end, index]
                    event_count = int((selected & event_part).sum())
                    result[f"{event}_occurrences"] = event_count
                    result[f"{event}_per_100_member_occurrences"] = percent(event_count, count)
                    event_total += event_count
                if event_total != count:
                    raise ValueError("Member correction events fail to partition member occurrences")
                if (result["wrong_to_right_occurrences"] - result["right_to_wrong_occurrences"] !=
                        q_count - raw_count):
                    raise ValueError("Correction events disagree with net correct-label change")
                output.append(result)
    return output


def write_csv(path, rows):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--runs", type=Path, default=RUNS)
    args = parser.parse_args()
    output, runs = args.output.resolve(), args.runs.resolve()
    rows = check_sources(output, runs)
    quality, members = [], []
    for dataset in ("cwru", "hust"):
        dataset_rows = [row for row in rows if row["dataset"] == dataset]
        domains, labels = hidden_source_truth(dataset, dataset_rows)
        for seed in range(3):
            paired = [row for row in dataset_rows if row["seed"] == seed]
            anchor = next(row for row in paired if row["mode"] == "raw" and row["B_weight"] == 0)
            trace, receipt, digest = load_trace(anchor, runs)
            for row in paired:
                comparison, paired_receipt, _ = load_trace(row, runs)
                if any(not np.array_equal(trace[field], comparison[field]) for field in TRACE_FIELDS):
                    raise ValueError(f"Saved auxiliary traces differ for {row['id']}")
                for key in ("batch_digest", "trajectory_digest"):
                    if receipt[key] != paired_receipt[key]:
                        raise ValueError(f"Saved trajectory digest differs for {row['id']}")
                del comparison
            source_indices = trace["indices"][:, 1:]
            for branch, truth in enumerate(labels):
                indices = source_indices[:, branch]
                if indices.min() < 0 or indices.max() >= len(truth):
                    raise ValueError(f"Sampled index exceeds source-domain rows for {anchor['id']}")
            truth = np.stack([labels[branch][source_indices[:, branch]] for branch in range(2)], axis=1)
            classes = 4 if dataset == "cwru" else 9
            for field in ("raw_labels", "q_labels"):
                if trace[field].min() < 0 or trace[field].max() >= classes:
                    raise ValueError(f"Pseudo-label range differs from class map for {anchor['id']}")
            common = {"dataset": dataset, "target": anchor["target"], "labeled": anchor["labeled"],
                      "seed": seed, "anchor_id": anchor["id"], "anchor_trace_sha256": digest,
                      "B_scope": "shared_auxiliary_trace_B0_and_B0.1",
                      "count_unit": "sampled_occurrence_with_replacement"}
            quality.extend(quality_rows(common, trace, truth, domains))
            members.extend(member_rows(common, trace, truth, domains))
    write_csv(output / "pseudo_label_quality.csv", quality)
    write_csv(output / "member_changes.csv", members)
    print(json.dumps({"complete": True, "models_verified": 48, "anchor_groups": 6,
                      "quality_rows": len(quality), "member_rows": len(members),
                      "target_data_access": False, "unit": "sampled_occurrences_with_replacement"}))


if __name__ == "__main__":
    main()
