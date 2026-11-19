"""Summarize archived HUST role-rotation supervision without opening target data.

Each row describes a class, a physical unlabeled source, a training stage, and
a run. Domain totals and logged losses repeat on its nine class rows. Filter
class_id == 0 before aggregating those fields across runs. Class rates based on
true labels and on assigned pseudo-labels have different denominators.
"""

import argparse
import csv
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

from . import offline_pilot_diagnostics as archive
from . import tasks


ROOT = tasks.ROOT
OUT = ROOT / "output/pc2g_hust_role_rotation_20261118"
RUNS = ROOT / "runs/pc2g_hust_role_rotation_20261118"
CSV_NAME = "HUST_role_rotation_pseudo_label.csv"
FREQUENCIES = {0: 20, 1: 35, 2: 65}
MODES = {"raw": "Raw", "labels_only": "Label", "selection_only": "Select", "full": "Full"}
CLASSES = ("正常", "中度内圈", "重度内圈", "中度外圈", "重度外圈",
           "中度滚动体", "重度滚动体", "中度复合", "重度复合")
N_CLASSES = len(CLASSES)
STEPS = 5000
RAMP = 2 / (1 + np.exp(-10 * np.arange(1, STEPS + 1) / STEPS)) - 1


def check(condition, description):
    if not condition:
        raise ValueError(description)


def folder_for(row, runs):
    default = archive.RUNS if row["labeled"] == 0 else runs
    configured = row.get("run_dir")
    folder = (ROOT / configured if configured else default / row["id"]).resolve()
    check(folder.name == row["id"] and folder.is_relative_to(default.resolve()),
          f"Run directory is outside the expected archive for {row['id']}")
    return folder


def frozen_runs(protocol_path, runs, archive_only):
    if archive_only:
        original = archive.read(archive.OUTPUT / "protocol.json")
        rows = [row for row in original["rows"] if row["dataset"] == "hust"]
        roles = (0,)
    else:
        protocol = archive.read(protocol_path)
        marker = archive.read(protocol_path.parent / "all_sources_complete.json")
        check(marker.get("complete") is True and marker.get("models") == 48
              and marker.get("total_with_baseline") == 72, "The 48 source runs must be finalized")
        rows = protocol["baseline_rows"] + protocol["rows"]
        roles = (0, 1, 2)
    identities = {(row["labeled"], row["seed"], row["mode"], row["B_weight"]) for row in rows}
    expected = set(product(roles, range(3), MODES, (0.0, 0.1)))
    check(len(rows) == len(expected) and expected == identities, "Incomplete rotation matrix")
    for row in rows:
        label, seed = row["labeled"], row["seed"]
        expected_id = f"hust-t3-L{label}-s{seed}-{row['mode']}-B{int(bool(row['B_weight']))}"
        check(row["dataset"] == "hust" and row["target"] == 3 and row["id"] == expected_id,
              f"Unexpected run identity: {row}")
        receipt = archive.read(folder_for(row, runs) / "source_complete.json")
        check(receipt.get("complete") is True and receipt.get("actual_updates") == STEPS,
              f"Run unfinished: {row['id']}")
    return rows


def source_files():
    original = archive.read(archive.OUTPUT / "protocol.json")
    manifest = tasks.OUTPUT / "hust_manifest.csv"
    key = manifest.relative_to(ROOT).as_posix()
    check(archive.sha(manifest) == original["input_sha256"][key],
          "The file manifest differs from the pilot training input")
    groups = defaultdict(list)
    for row in tasks.records("hust"):
        domain = int(row["domain_id"])
        if domain in FREQUENCIES:
            groups[domain].append(row)
    for domain, frequency in FREQUENCIES.items():
        records = groups[domain]
        check(len(records) == N_CLASSES and {int(r["class_id"]) for r in records} == set(range(N_CLASSES)),
              f"Invalid source coverage at {frequency} Hz")
        check({int(r["window_count"]) for r in records} == {81} and
              {int(r["speed_hz"]) for r in records} == {frequency}, "Invalid source window manifest")
    return groups


def load_run(row, folder, source_order, records):
    trace, receipt, digest = archive.load_trace(row, folder.parent)
    config_path = folder / "config.json"
    ce_path = folder / "head_ce_by_step.csv"
    check(archive.sha(config_path) == receipt["artifacts_sha256"]["config.json"],
          f"Configuration hash differs for {row['id']}")
    config = archive.read(config_path)
    expected_records = [record["record_id"] for domain in source_order for record in records[domain]]
    check(receipt.get("source_records") == expected_records and receipt.get("validation_records") == 0,
          f"The receipt does not establish source file order for {row['id']}")
    check(config["fixed"]["profile"] == "paper_objective" and config["source_counts"] == [729] * 3,
          f"Unexpected loss profile or window count for {row['id']}")
    for metadata in (receipt, config):
        check(metadata.get("sources", source_order) == source_order,
              f"Physical source order differs for {row['id']}")
    indices = trace["indices"]
    check(indices.min() >= 0 and indices.max() < 729, f"Out of range sampled index for {row['id']}")
    for name in ("raw_labels", "q_labels"):
        labels = trace[name]
        check(labels.min() >= 0 and labels.max() < N_CLASSES, f"Out of range labels for {row['id']}")
    if row["labeled"] == 0:
        return trace, receipt, digest, None
    check(archive.sha(ce_path) == receipt["artifacts_sha256"][ce_path.name],
          f"Per-head loss hash differs for {row['id']}")
    ce = np.genfromtxt(ce_path, delimiter=",", names=True, encoding="utf-8-sig")
    check(np.array_equal(ce["step"], np.arange(1, STEPS + 1)) and
          np.allclose(ce["main_ramp"], RAMP, rtol=0, atol=1e-7), f"Invalid loss step or ramp for {row['id']}")
    for name, domain in zip(("labeled_domain", "unlabeled_domain_1", "unlabeled_domain_2"), source_order):
        check(bool(np.all(ce[name] == domain)), f"Loss source axis differs for {row['id']}")
    for name in ce.dtype.names:
        check(np.isfinite(ce[name]).all(), f"Non-finite per-head loss for {row['id']}")
    history_path = folder / "loss_history.json"
    check(archive.sha(history_path) == receipt["artifacts_sha256"][history_path.name],
          f"Source history hash differs for {row['id']}")
    history = archive.read(history_path)
    check([snapshot["step"] for snapshot in history] == [1, *range(250, STEPS + 1, 250)],
          f"The source history does not contain the expected loss snapshots for {row['id']}")
    for snapshot in history:
        step = snapshot["step"] - 1
        names = (("aux_ce", ("aux_labeled_ce_1", "aux_labeled_ce_2")),
                 ("main_ce", ("main_common_labeled_ce", "main_common_pseudo_ce_u1",
                              "main_common_pseudo_ce_u2")),
                 ("specific_ce", ("main_specific_labeled_ce", "main_specific_pseudo_ce_u1",
                                  "main_specific_pseudo_ce_u2")))
        for reference, components in names:
            reconstructed = sum((np.float32(ce[name][step]) for name in components), np.float32(0))
            check(reconstructed == np.float32(snapshot["terms"][reference]),
                  f"Archived loss components do not match {reference} at step {step+1} for {row['id']}")
    return trace, receipt, digest, ce


def confusion(truth, pseudo, selected=None, weights=None):
    codes = truth * N_CLASSES + pseudo
    if selected is not None:
        codes = codes[selected]
        if weights is not None:
            weights = weights[selected]
    counts = np.bincount(codes.ravel(), weights=None if weights is None else weights.ravel(),
                         minlength=N_CLASSES ** 2)
    return counts.reshape(N_CLASSES, N_CLASSES)


def loss_columns(ce, take, branch):
    suffix = f"u{branch + 1}"
    names = ("aux_labeled_ce_1", "aux_labeled_ce_2", "main_common_labeled_ce",
             "main_specific_labeled_ce", "main_common_pseudo_ce", "main_specific_pseudo_ce")
    values = {"actual_ce_archive_available": int(ce is not None)}
    for name in names:
        key = name if not name.endswith("_pseudo_ce") else f"{name}_{suffix}"
        values[f"mean_step_{name}"] = float(ce[key][take].mean()) if ce is not None else None
    for head in ("common", "specific"):
        values[f"mean_step_ramped_main_{head}_pseudo_ce"] = (
            float((ce[f"main_{head}_pseudo_ce_{suffix}"][take] * RAMP[take]).mean()) if ce is not None else None)
    return values


def summarize_stage(key, trace, truth, indices, branch, phase, start, stop, records, ce):
    take = slice(start, stop)
    truth = truth[take]
    indices = indices[take]
    raw, q, actual, mask, raw_mask, q_mask = (
        trace[k][take, branch] for k in ("raw_labels", "q_labels", "actual_labels",
                                       "actual_mask", "raw_mask", "q_mask"))
    raw_matrix = confusion(truth, raw)
    q_matrix = confusion(truth, q)
    selected = confusion(truth, actual, mask)
    selected_count = int(selected.sum())
    good_count = int(np.trace(selected))
    wrong_count = selected_count - good_count
    missed = int(selected[1:, 0].sum())
    normal_mislabeled = int(selected[0, 1:].sum())
    counts = np.count_nonzero(mask, axis=1)
    coefficient = np.divide(RAMP[take], counts, out=np.zeros_like(RAMP[take]), where=counts > 0)
    weights = np.broadcast_to(coefficient[:, None], mask.shape)
    nominal = confusion(truth, actual, mask, weights)
    nominal_wrong = nominal.copy()
    np.fill_diagonal(nominal_wrong, 0)
    wrong = truth != actual
    raw_bad = truth != raw
    q_bad = truth != q
    shared = dict(
        **key, phase=phase, first_step=start + 1, last_step=stop,
        unit="sampled_occurrences_with_replacement",
        domain_totals_repeated_for_each_class=1,
        sampled_occurrences=truth.size,
        selected_occurrences=selected_count,
        selected_correct_occurrences=good_count,
        selected_error_occurrences=wrong_count,
        selected_accuracy_pct=archive.percent(good_count, selected_count),
        selected_error_pct=archive.percent(wrong_count, selected_count),
        selected_rate_pct=archive.percent(selected_count, truth.size),
        raw_error_occurrences=int(raw_bad.sum()),
        calibrated_error_occurrences=int(q_bad.sum()),
        selected_fault_as_normal_occurrences=missed,
        selected_fault_as_normal_pct=archive.percent(missed, int(selected[1:, :].sum())),
        selected_normal_as_fault_occurrences=normal_mislabeled,
        selected_normal_as_fault_pct=archive.percent(normal_mislabeled, int(selected[0, :].sum())),
        selected_raw_wrong_calibrated_right_occurrences=int((mask & raw_bad & ~q_bad).sum()),
        selected_raw_right_calibrated_wrong_occurrences=int((mask & ~raw_bad & q_bad).sum()),
        selected_error_retention_pct=archive.percent(wrong_count, int(wrong.sum())),
        selected_correct_retention_pct=archive.percent(good_count, int((~wrong).sum())),
        auxiliary_hard_pseudo_ce_occurrences=0,
        main_common_pseudo_ce_occurrences=selected_count,
        main_specific_pseudo_ce_occurrences=selected_count,
        main_common_error_ce_occurrences=wrong_count,
        main_specific_error_ce_occurrences=wrong_count,
        nominal_selected_weight_per_head_sum=float(nominal.sum()),
        nominal_error_weight_per_head_sum=float(nominal_wrong.sum()),
        **loss_columns(ce, take, branch),
    )
    output = []
    for class_id in range(N_CLASSES):
        true_count = int(raw_matrix[class_id, :].sum())
        raw_pseudo_count = int(raw_matrix[:, class_id].sum())
        q_pseudo_count = int(q_matrix[:, class_id].sum())
        selected_true = int(selected[class_id, :].sum())
        selected_pseudo = int(selected[:, class_id].sum())
        correct = int(selected[class_id, class_id])
        true_class = truth == class_id
        output.append(dict(
            **shared, class_id=class_id, class_name_cn=CLASSES[class_id],
            original_record_id=records[class_id]["record_id"],
            sampled_true_class_occurrences=true_count,
            raw_pseudo_class_occurrences=raw_pseudo_count,
            raw_pseudo_class_share_pct=archive.percent(raw_pseudo_count, truth.size),
            calibrated_pseudo_class_occurrences=q_pseudo_count,
            calibrated_pseudo_class_share_pct=archive.percent(q_pseudo_count, truth.size),
            calibrated_minus_raw_class_share_pp=archive.percent(q_pseudo_count-raw_pseudo_count, truth.size),
            raw_true_class_error_pct=archive.percent(true_count-int(raw_matrix[class_id, class_id]), true_count),
            calibrated_true_class_error_pct=archive.percent(true_count-int(q_matrix[class_id, class_id]), true_count),
            selected_true_class_occurrences=selected_true,
            selected_true_class_errors=selected_true-correct,
            selected_true_class_error_pct=archive.percent(selected_true-correct, selected_true),
            selected_true_class_retention_pct=archive.percent(selected_true, true_count),
            selected_true_class_as_normal_occurrences=int(selected[class_id, 0]),
            selected_true_class_as_normal_pct=archive.percent(int(selected[class_id, 0]), selected_true),
            selected_true_class_as_normal_unique_windows=int(
                np.unique(indices[true_class & mask & (actual == 0)]).size),
            selected_pseudo_class_occurrences=selected_pseudo,
            selected_pseudo_class_errors=selected_pseudo-correct,
            selected_correct_as_class_occurrences=correct,
            selected_pseudo_class_accuracy_pct=archive.percent(correct, selected_pseudo),
            selected_pseudo_class_share_pct=archive.percent(selected_pseudo, selected_count),
            common_true_class_occurrences=int((true_class & raw_mask & q_mask).sum()),
            added_true_class_occurrences=int((true_class & ~raw_mask & q_mask).sum()),
            removed_true_class_occurrences=int((true_class & raw_mask & ~q_mask).sum()),
            common_head_ce_occurrences_by_true_class=selected_true,
            specific_head_ce_occurrences_by_true_class=selected_true,
            common_head_ce_occurrences_by_pseudo_class=selected_pseudo,
            specific_head_ce_occurrences_by_pseudo_class=selected_pseudo,
            nominal_weight_per_head_by_true_class_sum=float(nominal[class_id, :].sum()),
            nominal_weight_per_head_by_pseudo_class_sum=float(nominal[:, class_id].sum()),
            nominal_error_weight_per_head_by_true_class_sum=float(nominal_wrong[class_id, :].sum()),
            nominal_error_weight_per_head_by_pseudo_class_sum=float(nominal_wrong[:, class_id].sum()),
            **{f"selected_true_class_assigned_to_class_{dest}_occurrences": int(selected[class_id, dest])
               for dest in range(N_CLASSES)},
            **{f"selected_pseudo_class_from_true_class_{origin}_occurrences": int(selected[origin, class_id])
               for origin in range(N_CLASSES)},
        ))
    check(sum(row["selected_true_class_errors"] for row in output) == wrong_count
          and sum(row["selected_pseudo_class_errors"] for row in output) == wrong_count,
          f"Class error margins differ from source total for {key['run_id']}")
    return output


def collect(rows, runs):
    records = source_files()
    label_arrays = {domain: np.concatenate([np.full(int(row["window_count"]), int(row["class_id"]))
                                            for row in files])
                    for domain, files in records.items()}
    groups = defaultdict(list)
    for row in rows:
        groups[row["labeled"], row["seed"]].append(row)
    output = []
    physical_anchor = {}
    physical_pairing = True
    for (labeled, seed), group in sorted(groups.items()):
        unlabeled = [domain for domain in FREQUENCIES if domain != labeled]
        source_order = [labeled, *unlabeled]
        indices_by_role = [source_order.index(domain) for domain in FREQUENCIES]
        by_class = {domain: {int(row["class_id"]): row for row in records[domain]} for domain in unlabeled}
        expected_trace = expected_digests = None
        for row in group:
            trace, receipt, digest, ce = load_run(row, folder_for(row, runs), source_order, records)
            pair_digests = tuple(receipt[k] for k in ("batch_digest", "trajectory_digest", "initial"))
            if expected_trace is None:
                expected_trace, expected_digests = trace, pair_digests
                physical = trace["indices"][:, indices_by_role, :]
                if labeled == 0:
                    physical_anchor[seed] = physical
                else:
                    physical_pairing &= np.array_equal(physical, physical_anchor[seed])
            else:
                check(expected_digests == pair_digests and
                      all(np.array_equal(trace[k], expected_trace[k]) for k in archive.TRACE_FIELDS),
                      f"Expected paired comparison within role and seed: {row['id']}")
            for branch, domain in enumerate(unlabeled):
                indices = trace["indices"][:, branch + 1]
                truth = label_arrays[domain][indices]
                key = dict(
                    dataset="hust", target=3, target_hz=80, labeled=labeled,
                    labeled_source_hz=FREQUENCIES[labeled], unlabeled=domain,
                    unlabeled_source_hz=FREQUENCIES[domain], unlabeled_branch=branch + 1,
                    run_id=row["id"], reused=int(labeled == 0), seed=seed, mode=row["mode"],
                    configuration=MODES[row["mode"]] + ("+B" if row["B_weight"] else ""),
                    B_weight=row["B_weight"], trace_sha256=digest)
                for phase, start, stop in archive.PHASES:
                    output.extend(summarize_stage(key, trace, truth, indices, branch, phase, start, stop,
                                                  by_class[domain], ce))
    check(len(output) == len(rows) * 2 * len(archive.PHASES) * N_CLASSES,
          "Unexpected number of pseudo-label analysis rows")
    check(physical_pairing, "Physical domain draws differ from the 20 Hz archive for a paired role")
    return output, bool(physical_pairing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=OUT / "protocol.json")
    parser.add_argument("--runs", type=Path, default=RUNS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive-only", action="store_true", help="Verify the 20 Hz archive only. Do not write the rotation CSV.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    protocol_path = args.protocol.resolve()
    rows = frozen_runs(protocol_path, args.runs, args.archive_only)
    output, physically_paired = collect(rows, args.runs)
    if not args.verify_only and not args.archive_only:
        directory = args.output or protocol_path.parent
        archive.write_csv(directory / CSV_NAME, output)
    print(f"Audited {len(rows)} source traces; {len(output)} class rows; "
          f"physical domain draws match the 20 Hz role: {physically_paired}")


if __name__ == "__main__":
    main()
