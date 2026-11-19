"""Verify all Oracle source runs before releasing the 80 Hz holdout.

Audit tables use 1-based optimizer steps and 0-based slot, order, and window
indices. The occurrence rows preserve repeated selections of the same window.
"""

import csv
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from . import oracle_archive


ROOT = Path(__file__).resolve().parents[2]
STEPS = 5000
BATCH = 64
CLASSES = 9
SEEDS = (0, 1, 2)
SOURCE_HZ = (20, 35, 65)
HEADS = ("common", "specific")
STEPWISE_NAME = "oracle_stepwise_mask_audit.csv"
CORRECTION_NAME = "oracle_label_correction_audit.csv"
UNCHANGED_FIELDS = ("indices", "raw_labels", "q_labels", "raw_mask", "q_mask", "actual_mask")
STEP_FIELDS = (
    "seed", "step", "sampled_20hz_indices", "sampled_35hz_indices", "sampled_65hz_indices",
    "ordered_35hz_slots", "ordered_65hz_slots", "ordered_35hz_indices", "ordered_65hz_indices",
    "selected_35hz", "selected_65hz", "unique_selected_65hz_windows",
    "original_correct_65hz", "corrected_65hz", "unselected_65hz_in_ce", "trace_sha256",
    "main_ramp", "consistency_denominator", "consistency_65hz_mean_contribution", "consistency_weight",
    *(f"{head}_{field}" for head in HEADS for field in (
        "ce65_count", "ce65_mean_denominator", "ce65_original_label_ce", "ce65_oracle_ce",
        "ce65_ramped_oracle_ce", "ce65_ramped_coefficient_per_occurrence",
    )),
)
CORRECTION_FIELDS = (
    "row_level", "seed", "step", "source_hz", "ce_input_order", "batch_slot",
    "source_window_index", "record_id", "window_start_sample",
    "original_A_label", "source_truth_label", "actual_oracle_label", "corrected",
    "occurrences", "unique_source_windows",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_manifest(info):
    path = ROOT / info["path"]
    require(sha256(path) == info["sha256"], "Source manifest checksum changed")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        used = [row for row in csv.DictReader(stream)
                if row["included"] == "1" and row["domain_id"] in ("0", "1", "2")]
    groups = [[row for row in used if int(row["domain_id"]) == domain]
              for domain in range(len(SOURCE_HZ))]
    for hz, records in zip(SOURCE_HZ, groups, strict=True):
        require(len(records) == CLASSES and {int(r["speed_hz"]) for r in records} == {hz},
                f"Unexpected source manifest records for {hz} Hz")
    truth, record_ids, offsets = [], [], []
    for row in groups[2]:
        count, stride = int(row["window_count"]), int(row["window_stride"])
        truth.extend([int(row["class_id"])] * count)
        record_ids.extend([row["record_id"]] * count)
        offsets.extend(np.arange(count, dtype=np.int64) * stride)
    require(len(truth) == info["65hz_windows"] and set(truth) == set(range(CLASSES)),
            "Unexpected 65 Hz source class/size inventory")
    source_records = [row["record_id"] for records in groups for row in records]
    return source_records, np.asarray(truth), record_ids, offsets


def open_receipts(seed, runs_dir, seed_basis, records, frozen_dir):
    a_info = seed_basis["source_archives"]["A"]
    a_dir = ROOT / a_info["directory"]
    a_receipt_path = a_dir / "source_complete.json"
    a_trace_path = a_dir / "training_predictions.npz"
    require(sha256(a_receipt_path) == a_info["receipt_sha256"], f"Seed {seed}: A receipt changed")
    require(sha256(a_trace_path) == a_info["training_predictions_sha256"], f"Seed {seed}: A trace changed")
    a_receipt = read_json(a_receipt_path)
    folder = runs_dir / f"hust-t3-L0-s{seed}-oracle"
    source_receipt_path = folder / "source_complete.json"
    receipt = read_json(source_receipt_path)
    expected = {
        "id": folder.name, "dataset": "hust", "target": 3, "labeled": 0,
        "seed": seed, "complete": True, "actual_updates": STEPS, "checkpoint_step": STEPS,
        "checkpoint_rule": "fixed_step_5000", "validation_records": 0,
        "target_arrays_loaded": False, "unlabeled_truth_used": True,
        "oracle_truth_domain_hz": 65, "oracle_truth_use": "selected_65hz_two_main_heads_only",
        "two_main_heads_using_identical_oracle_targets": True,
        "sources": [0, 1, 2], "source_records": records,
        "head_ce_rows": STEPS, "fixed_consistency_denominator": 192,
        "archive_sha256": oracle_archive.archive_sha256(seed, directory=frozen_dir),
        "archive_manifest_sha256": sha256(frozen_dir / "manifest.json"),
        "batch_digest": a_receipt["batch_digest"], "trajectory_digest": a_receipt["trajectory_digest"],
        "batch_initial": a_receipt["batch_initial"], "perturb_initial": a_receipt["perturb_initial"],
        "main_forward_calls": 2 * STEPS, "bn_restorations": STEPS,
        "initial": a_receipt["initial"],
    }
    for name, value in expected.items():
        require(receipt.get(name) == value, f"Seed {seed}: unexpected receipt field {name}")
    for key in ("aux_hash", "base_aux_hash", "queue_hash", "batch_generator_hash", "perturb_generator_hash"):
        require(receipt["final"].get(key) == a_receipt["final"][key],
                f"Seed {seed}: {key} differs from paired A")
    fingerprints = receipt["artifacts_sha256"]
    for name in ("config.json", "last.pt", "training_predictions.npz", "loss_history.json",
                 "head_ce_by_step.csv"):
        require(sha256(folder / name) == fingerprints[name],
                f"Seed {seed}: source artifact checksum changed for {name}")
    return a_trace_path, folder, source_receipt_path, fingerprints


def verify_trace(seed, a_trace_path, folder, frozen_dir, labels):
    frozen = oracle_archive.load_archive(seed, directory=frozen_dir)
    with (np.load(a_trace_path, allow_pickle=False) as original,
          np.load(folder / "training_predictions.npz", allow_pickle=False) as loaded):
        trace = {name: loaded[name] for name in (*UNCHANGED_FIELDS, "actual_labels", "consumed_order")}
        for name in UNCHANGED_FIELDS:
            require(np.array_equal(trace[name], original[name]) and np.array_equal(frozen[name], original[name]),
                    f"Seed {seed}: {name} differs from A")
        expected = original["actual_labels"].copy()
        require(np.array_equal(frozen["actual_labels"], expected), f"Seed {seed}: archived A labels differ")
    require(trace["indices"].shape == (STEPS, 3, BATCH), f"Seed {seed}: sampled shape changed")
    require((trace["indices"] >= 0).all() and (trace["indices"] < len(labels)).all(),
            f"Seed {seed}: source index outside manifest")
    order, mask = trace["consumed_order"], trace["actual_mask"]
    require(order.shape == mask.shape == (STEPS, 2, BATCH) and order.dtype == np.int64,
            f"Seed {seed}: unexpected selection order shape/type")
    require(mask.dtype == np.bool_ and np.array_equal(order, frozen["ordered_positions"]),
            f"Seed {seed}: CE slot order differs from the frozen archive")
    count = mask.sum(axis=2)
    require(np.array_equal(count, frozen["selected_count"]), f"Seed {seed}: selected count changed")
    within = np.arange(BATCH) < count[:, :, None]
    require((order[~within] == -1).all() and (order[within] >= 0).all() and (order[within] < BATCH).all(),
            f"Seed {seed}: invalid ordered slot or missing padding")
    steps, domains, _ = np.nonzero(within)
    entered = np.zeros_like(mask)
    entered[steps, domains, order[within]] = True
    require(np.array_equal(entered, mask), f"Seed {seed}: CE input order is not exactly the selected set")
    selected65 = mask[:, 1]
    independent = np.full((STEPS, BATCH), -1, dtype=np.int64)
    independent[selected65] = labels[trace["indices"][:, 2][selected65]]
    require(np.array_equal(oracle_archive.load_oracle_truth(seed, directory=frozen_dir), independent),
            f"Seed {seed}: frozen truth restricted to selected 65 Hz does not match the pinned manifest")
    original65 = expected[:, 1].copy()
    corrected = selected65 & (original65 != independent)
    expected[:, 1][corrected] = independent[corrected]
    require(np.array_equal(trace["actual_labels"], expected),
            f"Seed {seed}: actual labels differ from the selected-only correction")
    return trace, count, independent, original65, corrected


def verify_heads(seed, folder, counts, corrected):
    table = np.genfromtxt(folder / "head_ce_by_step.csv", delimiter=",", names=True, encoding="utf-8-sig")
    require(table.shape == (STEPS,), f"Seed {seed}: wrong number of per-step loss records")
    require(all(np.isfinite(table[name]).all() for name in table.dtype.names),
            f"Seed {seed}: nonfinite per-step loss record")
    expected = dict(step=np.arange(1, STEPS + 1), labeled_domain=0, unlabeled_domain_1=1,
                    unlabeled_domain_2=2, ce65=1, cons65=1, consistency_denominator=192)
    for name, value in expected.items():
        require((table[name] == value).all(), f"Seed {seed}: incorrect stepwise {name}")
    ramp = [2 / (1 + math.exp(-10 * (step / STEPS))) - 1 for step in expected["step"]]
    require(np.allclose(table["main_ramp"], ramp, rtol=0, atol=1e-12),
            f"Seed {seed}: inconsistent CE ramp")
    for head in HEADS:
        col = f"main_{head}_pseudo_ce_u2"
        require(np.array_equal(table[col + "_count"], counts[:, 1]),
                f"Seed {seed}: {head} CE input size differs from A")
        actual, original = table[col + "_raw"], table[col + "_original"]
        require((actual >= 0).all() and (original >= 0).all() and np.array_equal(table[col], actual),
                f"Seed {seed}: incorrect {head} CE loss values")
        empty = counts[:, 1] == 0
        require((actual[empty] == 0).all() and (original[empty] == 0).all(),
                f"Seed {seed}: nonzero empty-selection {head} CE")
        unchanged = ~corrected.any(axis=1)
        require(np.array_equal(actual[unchanged], original[unchanged]),
                f"Seed {seed}: {head} CE differed at a step with no corrected targets")
    for hz in SOURCE_HZ:
        distance = table[f"consistency_distance_sum_{hz}"]
        require((distance >= 0).all() and np.allclose(table[f"consistency_effective_{hz}"], distance / 192,
                                                    rtol=2e-6, atol=1e-9),
                f"Seed {seed}: incorrect {hz} Hz consistency contribution")
    require(np.allclose(table["consistency_total_effective"],
                        sum(table[f"consistency_effective_{hz}"] for hz in SOURCE_HZ),
                        rtol=2e-6, atol=1e-9), f"Seed {seed}: inconsistent aggregate consistency loss")
    snapshots = read_json(folder / "loss_history.json")
    require([s["step"] for s in snapshots] == [1, *range(250, STEPS + 1, 250)],
            f"Seed {seed}: incomplete loss snapshot record")
    for snapshot in snapshots:
        index = snapshot["step"] - 1
        ce, terms = table[index], snapshot["terms"]
        for head, key in (("common", "main_ce"), ("specific", "specific_ce")):
            values = [np.float32(ce[f"main_{head}_{loss_kind}"])
                      for loss_kind in ("labeled_ce", "pseudo_ce_u1", "pseudo_ce_u2")]
            require((values[0] + values[1]) + values[2] == np.float32(terms[key]),
                    f"Seed {seed}: snapshot {index + 1} {head} loss does not match its parts")
        require(counts[index].tolist() == [terms["selected_1"], terms["selected_2"]],
                f"Seed {seed}: snapshot {index + 1} selection counts differ")
    return table


def format_ids(indices):
    return "|".join(map(str, indices))


def write_seed_rows(step_writer, correction_writer, seed, trace, counts, truth, original65,
                    corrected, table, records, offsets, trace_hash):
    category_windows = {}
    for index, ce in enumerate(table):
        slots35 = trace["consumed_order"][index, 0, :counts[index, 0]]
        slots65 = trace["consumed_order"][index, 1, :counts[index, 1]]
        source20, source35, source65 = trace["indices"][index]
        ordered35, ordered65 = source35[slots35], source65[slots65]
        selected65 = len(slots65)
        ramp = float(ce["main_ramp"])
        changed = int(corrected[index].sum())
        step_writer.writerow({
            "seed": seed, "step": index + 1, "sampled_20hz_indices": format_ids(source20),
            "sampled_35hz_indices": format_ids(source35), "sampled_65hz_indices": format_ids(source65),
            "ordered_35hz_slots": format_ids(slots35), "ordered_65hz_slots": format_ids(slots65),
            "ordered_35hz_indices": format_ids(ordered35), "ordered_65hz_indices": format_ids(ordered65),
            "selected_35hz": len(slots35), "selected_65hz": selected65,
            "unique_selected_65hz_windows": len(np.unique(ordered65)),
            "original_correct_65hz": selected65 - changed, "corrected_65hz": changed,
            "unselected_65hz_in_ce": 0, "trace_sha256": trace_hash, "main_ramp": ramp,
            "consistency_denominator": int(ce["consistency_denominator"]),
            "consistency_65hz_mean_contribution": ce["consistency_effective_65"],
            "consistency_weight": 0.1 * ramp,
            **{f"{head}_{field}": value for head in HEADS for field, value in (
                ("ce65_count", selected65), ("ce65_mean_denominator", selected65),
                ("ce65_original_label_ce", ce[f"main_{head}_pseudo_ce_u2_original"]),
                ("ce65_oracle_ce", ce[f"main_{head}_pseudo_ce_u2_raw"]),
                ("ce65_ramped_oracle_ce", ramp * ce[f"main_{head}_pseudo_ce_u2"]),
                ("ce65_ramped_coefficient_per_occurrence", ramp / selected65 if selected65 else 0.0),
            )},
        })
        for position, (slot, window) in enumerate(zip(slots65, ordered65, strict=True)):
            original, expected = int(original65[index, slot]), int(truth[index, slot])
            changed = int(corrected[index, slot])
            category_windows.setdefault((original, expected), []).append(window)
            correction_writer.writerow({
                "row_level": "occurrence", "seed": seed, "step": index + 1, "source_hz": 65,
                "ce_input_order": position, "batch_slot": slot, "source_window_index": window,
                "record_id": records[window], "window_start_sample": offsets[window],
                "original_A_label": original, "source_truth_label": expected,
                "actual_oracle_label": trace["actual_labels"][index, 1, slot], "corrected": changed,
                "occurrences": 1, "unique_source_windows": 1,
            })
    for (original, actual), windows in sorted(category_windows.items()):
        correction_writer.writerow({
            "row_level": "seed_class_pair", "seed": seed, "source_hz": 65,
            "original_A_label": original, "source_truth_label": actual, "actual_oracle_label": actual,
            "corrected": int(original != actual), "occurrences": len(windows),
            "unique_source_windows": len(set(windows)),
        })


def verify_and_write(output_dir, runs_dir, frozen_dir):
    """Validate the source archives for the three fixed-step seeds and emit audit CSVs."""
    output_dir, runs_dir, frozen_dir = map(Path, (output_dir, runs_dir, frozen_dir))
    basis = read_json(output_dir / "oracle_implementation_audit.json")["archive_inspection"]
    source_records, labels, record_ids, offsets = source_manifest(basis["source_manifest"])
    training_rows = oracle_archive.training_rows(directory=frozen_dir)
    require([r["record_id"] for domain in ("0", "1", "2")
             for r in training_rows if r["domain_id"] == domain] == source_records,
            "Source-only training view differs from the pinned acquisition and window order")
    by_seed = {row["seed"]: row for row in basis["by_seed"]}
    summary = []
    with TemporaryDirectory(prefix=".oracle_source_audit_", dir=output_dir) as temp_dir:
        temp = Path(temp_dir)
        with ((temp / STEPWISE_NAME).open("w", newline="", encoding="utf-8-sig") as step_file,
              (temp / CORRECTION_NAME).open("w", newline="", encoding="utf-8-sig") as correction_file):
            step_writer = csv.DictWriter(step_file, fieldnames=STEP_FIELDS)
            correction_writer = csv.DictWriter(correction_file, fieldnames=CORRECTION_FIELDS)
            step_writer.writeheader()
            correction_writer.writeheader()
            for seed in SEEDS:
                a_path, folder, source_receipt, fingerprints = open_receipts(
                    seed, runs_dir, by_seed[seed], source_records, frozen_dir,
                )
                trace, counts, truth, original65, corrected = verify_trace(seed, a_path, folder, frozen_dir, labels)
                table = verify_heads(seed, folder, counts, corrected)
                total, corrections = int(counts[:, 1].sum()), int(corrected.sum())
                require(total == by_seed[seed]["historical_A_65hz_selected_occurrences"] and
                        corrections == by_seed[seed]["historical_A_65hz_incorrect_occurrences"],
                        f"Seed {seed}: selection or correction count differs from preregistration evidence")
                require(np.bincount(truth[corrected], minlength=CLASSES).tolist() ==
                        by_seed[seed]["historical_A_65hz_incorrect_by_true_class"],
                        f"Seed {seed}: per-class correction counts differ from preregistration evidence")
                trace_hash = fingerprints["training_predictions.npz"]
                write_seed_rows(step_writer, correction_writer, seed, trace, counts, truth,
                                original65, corrected, table, record_ids, offsets, trace_hash)
                summary.append({
                    "seed": seed, "steps": STEPS, "selected_65hz_occurrences": total,
                    "corrected_65hz_occurrences": corrections,
                    "retained_original_correct_65hz_occurrences": total - corrections,
                    "unselected_65hz_in_ce": 0,
                    "unique_selected_65hz_windows": int(np.unique(trace["indices"][:, 2][trace["actual_mask"][:, 1]]).size),
                    "source_receipt_sha256": sha256(source_receipt), "training_predictions_sha256": trace_hash,
                    "checkpoint_sha256": fingerprints["last.pt"],
                })
        for name in (STEPWISE_NAME, CORRECTION_NAME):
            (temp / name).replace(output_dir / name)
    return {
        "passed": True, "seeds": summary, "target_arrays_loaded": False,
        "total_selected_65hz_occurrences": sum(row["selected_65hz_occurrences"] for row in summary),
        "total_corrected_65hz_occurrences": sum(row["corrected_65hz_occurrences"] for row in summary),
        "artifacts_sha256": {name: sha256(output_dir / name) for name in (STEPWISE_NAME, CORRECTION_NAME)},
    }
