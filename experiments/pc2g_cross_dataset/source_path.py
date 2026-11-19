"""Audit four-arm HUST supervision from source archives.

The class file separates the selected candidates from the hard labels entering
the loss. An archived A arm has complete candidate traces but lacks per-domain
CE and distance observations. The analyzer opens no target inputs or results.
"""

import argparse
from itertools import product
from pathlib import Path

import numpy as np

from . import offline_pilot_diagnostics as archive
from . import pseudo_rotation as pseudo


ROOT = pseudo.ROOT
OUT = ROOT / "output/pc2g_hust_65hz_path_20261119"
DOMAIN_NAME = "HUST_65Hz_path_source_domain.csv"
CLASS_NAME = "HUST_65Hz_path_source_supervision.csv"
ARM_GATES = {"A": (True, True), "B": (False, True), "C": (True, False), "D": (False, False)}
STEPS = pseudo.STEPS
CLASSES = pseudo.CLASSES
FREQUENCIES = {1: 35, 2: 65}


def verify(condition, message):
    if not condition:
        raise ValueError(message)


def frozen_rows(protocol, archive_only):
    if archive_only:
        old = archive.read(archive.OUTPUT / "protocol.json")
        rows = [dict(row, arm="A", ce65=True, cons65=True)
                for row in old["rows"] if row["dataset"] == "hust" and row["mode"] == "full"
                and row["B_weight"] == 0.1]
        baseline_root = archive.RUNS
        runs_root = None
        arms = ("A",)
    else:
        marker = archive.read(protocol.parent / "all_sources_complete.json")
        verify(marker.get("complete") is True and marker.get("models") == 9
               and marker.get("total_with_baseline") == 12, "All nine new source runs must be complete")
        new = archive.read(protocol)
        rows = new["baseline_rows"] + new["rows"]
        baseline_root = (ROOT / new["baseline_runs_dir"]).resolve()
        runs_root = (ROOT / new["runs_dir"]).resolve()
        arms = tuple(ARM_GATES)
    expected = set(product(arms, range(3)))
    verify(len(rows) == len(expected) and {(r["arm"], r["seed"]) for r in rows} == expected,
           "Frozen matrix must contain one row per arm and seed")
    verify(len({r["id"] for r in rows}) == len(rows), "Duplicated frozen run ID")
    for row in rows:
        arm = row["arm"]
        verify(tuple(row[k] for k in ("dataset", "target", "labeled", "mode", "B_weight"))
               == ("hust", 3, 0, "full", 0.1), f"Unexpected task identity {row['id']}")
        verify((row["ce65"], row["cons65"]) == ARM_GATES[arm], f"Incorrect gate identity {row['id']}")
        expected_id = (
            f"hust-t3-L0-s{row['seed']}-full-B1" if arm == "A"
            else f"hust-t3-L0-s{row['seed']}-path-{arm}"
        )
        verify(row["id"] == expected_id, f"Unexpected run name {row['id']}")
    return sorted(rows, key=lambda row: (row["seed"], row["arm"])), baseline_root, runs_root


def load_losses(folder, row, receipt):
    ce_file = folder / "head_ce_by_step.csv"
    verify(archive.sha(ce_file) == receipt["artifacts_sha256"][ce_file.name],
           f"Recorded loss archive checksum differs for {row['id']}")
    ce = np.genfromtxt(ce_file, delimiter=",", names=True, encoding="utf-8-sig")
    verify(np.array_equal(ce["step"], np.arange(1, STEPS + 1)) and
           np.allclose(ce["main_ramp"], pseudo.RAMP, rtol=0, atol=1e-7),
           f"Unexpected loss step or ramp for {row['id']}")
    verify(all(np.isfinite(ce[name]).all() for name in ce.dtype.names), f"Non-finite loss in {row['id']}")
    for column, value in (
        ("labeled_domain", 0), ("unlabeled_domain_1", 1), ("unlabeled_domain_2", 2),
        ("ce65", row["ce65"]), ("cons65", row["cons65"]), ("consistency_denominator", 192),
    ):
        verify(bool(np.all(ce[column] == value)), f"Invalid {column} in {row['id']}")
    for head in ("common", "specific"):
        field = f"main_{head}_pseudo_ce_u2"
        raw, gated = ce[field + "_raw"], ce[field]
        verify((raw >= 0).all() and np.array_equal(gated, raw * int(row["ce65"])),
               f"Incorrect CE gate for {head} head in {row['id']}")
    for source in (20, 35, 65):
        raw = ce[f"consistency_distance_sum_{source}"]
        expected = raw * int(source != 65 or row["cons65"]) / 192
        verify((raw >= 0).all() and np.allclose(ce[f"consistency_effective_{source}"], expected,
                                              rtol=2e-6, atol=1e-9),
               f"Invalid consistency gate for source {source} Hz in {row['id']}")
    effective = sum(ce[f"consistency_effective_{source}"] for source in (20, 35, 65))
    verify(np.allclose(ce["consistency_total_effective"], effective, rtol=2e-6, atol=1e-9),
           f"Per-source consistency distances do not recover the total in {row['id']}")
    return ce


def verify_heartbeats(folder, row, receipt, trace, ce):
    path = folder / "loss_history.json"
    verify(archive.sha(path) == receipt["artifacts_sha256"][path.name],
           f"Heartbeat archive checksum differs for {row['id']}")
    snapshots = archive.read(path)
    verify([s["step"] for s in snapshots] == [1, *range(250, STEPS + 1, 250)],
           f"Invalid source snapshot coverage in {row['id']}")
    for snapshot in snapshots:
        position = snapshot["step"] - 1
        terms = snapshot["terms"]
        verify(trace["actual_mask"][position].sum(axis=1).tolist() ==
               [terms["selected_1"], terms["selected_2"]], f"Snapshot mask counts differ for {row['id']}")
        if ce is None:
            continue
        c = ce[position]
        aux = np.float32(c["aux_labeled_ce_1"]) + np.float32(c["aux_labeled_ce_2"])
        common = sum((np.float32(c[f"main_common_{key}"]) for key in
                      ("labeled_ce", "pseudo_ce_u1", "pseudo_ce_u2")), np.float32(0))
        specific = sum((np.float32(c[f"main_specific_{key}"]) for key in
                        ("labeled_ce", "pseudo_ce_u1", "pseudo_ce_u2")), np.float32(0))
        verify(np.allclose([aux, common, specific, c["consistency_total_effective"]],
                           [terms["aux_ce"], terms["main_ce"], terms["specific_ce"], terms["consistency"]],
                           rtol=2e-6, atol=1e-8),
               f"Per-head reconstruction failed at step {position + 1} for {row['id']}")


def verify_source_archive(row, folder, records):
    trace, receipt, digest = archive.load_trace(row, folder.parent)
    verify(receipt.get("validation_records") == 0 and receipt.get("checkpoint_rule") == "fixed_step_5000",
           f"Source receipt does not confirm fixed-step selection for {row['id']}")
    verify(receipt.get("main_forward_calls") == 10000 and receipt.get("bn_restorations") == STEPS,
           f"Main forward or BN restoration count differs for {row['id']}")
    config_path = folder / "config.json"
    verify(archive.sha(config_path) == receipt["artifacts_sha256"][config_path.name],
           f"Configuration checksum differs for {row['id']}")
    verify(archive.sha(folder / "last.pt") == receipt["artifacts_sha256"]["last.pt"],
           f"Last checkpoint checksum differs for {row['id']}")
    config = archive.read(config_path)
    expected_records = [r["record_id"] for domain in (0, 1, 2) for r in records[domain]]
    verify(receipt.get("source_records") == expected_records and
           config["fixed"]["profile"] == "paper_objective" and config["source_counts"] == [729] * 3,
           f"Inconsistent source record order, count, or profile for {row['id']}")
    for metadata in (config, receipt):
        verify(metadata.get("sources", [0, 1, 2]) == [0, 1, 2],
               f"Incorrect role order for {row['id']}")
        if row["arm"] != "A":
            verify(all(metadata.get(k) == row[k] for k in ("arm", "ce65", "cons65")),
                   f"Incorrect gate metadata for {row['id']}")
    for name, limit in (("indices", 729), ("raw_labels", 9), ("q_labels", 9)):
        data = trace[name]
        verify(int(data.min()) >= 0 and int(data.max()) < limit, f"Invalid {name} for {row['id']}")
    ce = None if row["arm"] == "A" else load_losses(folder, row, receipt)
    verify_heartbeats(folder, row, receipt, trace, ce)
    return trace, receipt, digest, ce


def actual_loss_fields(ce, take, source):
    fields = {"actual_loss_archive_available": int(ce is not None)}
    for head in ("common", "specific"):
        gated_name = f"main_{head}_pseudo_ce_u{1 if source == 35 else 2}"
        raw_name = gated_name if source == 35 else gated_name + "_raw"
        for gate_status, name in (("raw", raw_name), ("gated", gated_name)):
            values = None if ce is None else ce[name][take]
            fields[f"{gate_status}_pseudo_ce_{head}_sum"] = None if values is None else float(values.sum())
            fields[f"{gate_status}_ramped_pseudo_ce_{head}_sum"] = (
                None if values is None else float(np.dot(values, pseudo.RAMP[take])))
    fields["raw_consistency_distance_sum"] = (
        None if ce is None else float(ce[f"consistency_distance_sum_{source}"][take].sum()))
    effective = None if ce is None else ce[f"consistency_effective_{source}"][take]
    fields["effective_consistency_contribution_sum"] = (
        None if effective is None else float(effective.sum()))
    fields["weighted_ramped_consistency_contribution_sum"] = (
        None if effective is None else float(np.dot(effective, pseudo.RAMP[take]) * 0.1))
    # Shared terms are shown once per run and phase, on the 35 Hz row.
    for name in ("aux_labeled_ce_1", "aux_labeled_ce_2", "main_common_labeled_ce", "main_specific_labeled_ce",
                 "consistency_effective_20", "consistency_total_effective"):
        fields[f"shared_{name}_sum"] = None if ce is None or source != 35 else float(ce[name][take].sum())
    return fields


def phase_summary(row, trace, ce, digest, labels, files, domain, phase, start, stop):
    branch = domain - 1
    source = FREQUENCIES[domain]
    take = slice(start, stop)
    indices = trace["indices"][take, domain]
    truth = labels[indices]
    raw, corrected, used_label, mask, raw_mask, q_mask = (
        trace[name][take, branch] for name in
        ("raw_labels", "q_labels", "actual_labels", "actual_mask", "raw_mask", "q_mask"))
    effective_ce = domain != 2 or row["ce65"]
    effective_cons = domain != 2 or row["cons65"]
    common = dict(run_id=row["id"], arm=row["arm"], seed=row["seed"], labeled_source_hz=20, source_hz=source,
                  phase=phase, first_step=start + 1, last_step=stop, trace_sha256=digest,
                  ce_active_for_source=int(effective_ce), consistency_active_for_source=int(effective_cons),
                  unit="sampled_occurrences_with_replacement")

    raw_counts = pseudo.confusion(truth, raw)
    corrected_counts = pseudo.confusion(truth, corrected)
    selected = pseudo.confusion(truth, used_label, mask)
    selected_count = int(selected.sum())
    selected_error_count = selected_count - int(np.trace(selected))
    batch_count = mask.sum(axis=1)
    nominal = np.divide(pseudo.RAMP[take], batch_count, out=np.zeros_like(pseudo.RAMP[take]), where=batch_count > 0)
    weight_matrix = pseudo.confusion(truth, used_label, mask, np.broadcast_to(nominal[:, None], mask.shape))
    error_weights = weight_matrix.copy()
    np.fill_diagonal(error_weights, 0)
    candidate_error_weight = float(error_weights.sum())

    domain_result = dict(
        **common, sampled_occurrences=int(truth.size), consistency_denominator=192,
        consistency_pair_occurrences=truth.size if effective_cons else 0,
        raw_error_occurrences=int(truth.size - np.trace(raw_counts)),
        calibrated_error_occurrences=int(truth.size - np.trace(corrected_counts)),
        selected_count=selected_count, selected_error_count=selected_error_count,
        selected_error_pct=archive.percent(selected_error_count, selected_count),
        selected_true_fault_to_normal_count=int(selected[1:, 0].sum()),
        selected_true_fault_count=int(selected[1:].sum()),
        selected_true_normal_to_fault_count=int(selected[0, 1:].sum()),
        selected_true_normal_count=int(selected[0].sum()),
        active_ce_occurrences_per_head=selected_count * int(effective_ce),
        active_ce_error_occurrences_per_head=selected_error_count * int(effective_ce),
        auxiliary_hard_pseudo_ce_occurrences=0,
        candidate_ce_nominal_weight_sum_per_head=float(weight_matrix.sum()),
        candidate_ce_nominal_error_weight_sum_per_head=candidate_error_weight,
        active_ce_nominal_weight_sum_per_head=float(weight_matrix.sum()) * int(effective_ce),
        active_ce_nominal_error_weight_sum_per_head=candidate_error_weight * int(effective_ce),
        **actual_loss_fields(ce, take, source),
    )
    class_results = []
    for code, name in enumerate(CLASSES):
        selected_true = int(selected[code].sum())
        selected_pseudo = int(selected[:, code].sum())
        correct = int(selected[code, code])
        true_class_error_count = selected_true - correct
        pseudo_class_error_count = selected_pseudo - correct
        candidate_class_error_weight = float(error_weights[code].sum())
        class_results.append(dict(
            **common, class_id=code, class_name=name, original_record_id=files[code]["record_id"],
            sampled_true_class_count=int(raw_counts[code].sum()),
            raw_pseudo_class_count=int(raw_counts[:, code].sum()),
            raw_pseudo_class_share_pct=archive.percent(int(raw_counts[:, code].sum()), truth.size),
            calibrated_pseudo_class_count=int(corrected_counts[:, code].sum()),
            calibrated_pseudo_class_share_pct=archive.percent(int(corrected_counts[:, code].sum()), truth.size),
            raw_true_class_error_count=int(raw_counts[code].sum() - raw_counts[code, code]),
            calibrated_true_class_error_count=int(corrected_counts[code].sum() - corrected_counts[code, code]),
            selected_true_class_count=selected_true,
            selected_true_class_correct_count=correct,
            selected_true_class_error_count=true_class_error_count,
            selected_true_class_error_pct=archive.percent(true_class_error_count, selected_true),
            selected_true_class_to_normal_count=int(selected[code, 0]),
            selected_true_class_to_normal_pct=archive.percent(int(selected[code, 0]), selected_true),
            selected_pseudo_class_count=selected_pseudo, selected_pseudo_class_error_count=pseudo_class_error_count,
            common_true_class_count=int(((truth == code) & raw_mask & q_mask).sum()),
            added_true_class_count=int(((truth == code) & ~raw_mask & q_mask).sum()),
            removed_true_class_count=int(((truth == code) & raw_mask & ~q_mask).sum()),
            active_ce_true_class_occurrences_per_head=selected_true * int(effective_ce),
            active_ce_error_occurrences_per_head=true_class_error_count * int(effective_ce),
            active_ce_pseudo_class_occurrences_per_head=selected_pseudo * int(effective_ce),
            active_ce_pseudo_class_error_occurrences_per_head=pseudo_class_error_count * int(effective_ce),
            candidate_ce_nominal_error_weight_sum_per_head=candidate_class_error_weight,
            active_ce_nominal_error_weight_sum_per_head=candidate_class_error_weight * int(effective_ce),
            active_ce_nominal_pseudo_class_weight_sum_per_head=float(weight_matrix[:, code].sum()) * int(effective_ce),
            active_ce_nominal_true_class_weight_sum_per_head=float(weight_matrix[code].sum()) * int(effective_ce),
            active_ce_nominal_pseudo_class_error_weight_sum_per_head=float(error_weights[:, code].sum()) * int(effective_ce),
            **{f"selected_as_class_{dest}_count": int(selected[code, dest]) for dest in range(len(CLASSES))},
        ))
    verify(sum(r["selected_true_class_count"] for r in class_results) == selected_count and
           sum(r["selected_true_class_error_count"] for r in class_results) == selected_error_count,
           f"Source class count margins differ in {row['id']}")
    return domain_result, class_results


def summarize(rows, baseline_root, runs_root):
    records = pseudo.source_files()
    record_by_class = {d: {int(r["class_id"]): r for r in records[d]} for d in FREQUENCIES}
    label_arrays = {d: np.concatenate([np.full(int(r["window_count"]), int(r["class_id"]))
                                        for r in records[d]]) for d in FREQUENCIES}
    domains, classes = [], []
    reference_by_seed = {}
    for row in rows:
        root = baseline_root if row["arm"] == "A" else runs_root
        folder = root / row["id"]
        trace, receipt, digest, ce = verify_source_archive(row, folder, records)
        if row["arm"] == "A":
            reference_by_seed[row["seed"]] = (trace, receipt)
        else:
            ref_trace, ref_receipt = reference_by_seed[row["seed"]]
            verify(all(np.array_equal(trace[k], ref_trace[k]) for k in archive.TRACE_FIELDS)
                   and all(receipt[k] == ref_receipt[k] for k in
                           ("batch_digest", "trajectory_digest", "initial")),
                   f"Unpaired candidate or sampling trace in {row['id']}")
            for key in ("aux_hash", "queue_hash", "batch_generator_hash", "perturb_generator_hash"):
                verify(receipt["final"][key] == ref_receipt["final"][key],
                       f"Unpaired auxiliary state or random stream {key} in {row['id']}")
        for domain in FREQUENCIES:
            for phase, start, stop in archive.PHASES:
                domain_row, class_rows = phase_summary(row, trace, ce, digest, label_arrays[domain],
                                                       record_by_class[domain], domain, phase, start, stop)
                domains.append(domain_row)
                classes.extend(class_rows)
    verify(len(domains) == len(rows) * 2 * len(archive.PHASES) and len(classes) == len(domains) * len(CLASSES),
           "Incomplete source domain or class summaries")
    return domains, classes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=OUT / "protocol.json")
    parser.add_argument("--archive-only", action="store_true", help="Verify the three archived A runs without writing reports.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    protocol = args.protocol.resolve()
    rows, baseline_root, runs_root = frozen_rows(protocol, args.archive_only)
    domains, classes = summarize(rows, baseline_root, runs_root)
    if not args.archive_only and not args.verify_only:
        archive.write_csv(protocol.parent / DOMAIN_NAME, domains)
        archive.write_csv(protocol.parent / CLASS_NAME, classes)
    print(f"Verified {len(rows)} source archives, {len(domains)} arm/seed/domain/stage rows "
          f"and {len(classes)} class rows. No target results were read.")


if __name__ == "__main__":
    main()
