"""Independently audit saved fixed-step pilot evidence using CPU only."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from . import tasks


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pc2g_cross_dataset_pilot_20261117"
RUNS = ROOT / "runs/pc2g_cross_dataset_pilot_20261117"
STEPS = 5000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def state_hash(state, include):
    digest = hashlib.sha256()
    for name in sorted(state):
        if not include(name):
            continue
        value = state[name].detach().cpu().contiguous()
        header = json.dumps([name, str(value.dtype), list(value.shape)],
                            separators=(",", ":")).encode("utf-8")
        digest.update(len(header).to_bytes(8, "little"))
        digest.update(header)
        digest.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def validate_selection(logits, labels, mask):
    """Accept entropy ties within a fixed CPU/GPU arithmetic tolerance."""
    require(np.array_equal(logits.argmax(axis=-1), labels), "Labels differ from logit argmax")
    tensor = torch.from_numpy(logits)
    probabilities = tensor.softmax(dim=-1)
    entropy = -(probabilities * probabilities.clamp_min(1e-8).log()).sum(-1).numpy()
    for cls in range(logits.shape[-1]):
        predicted = labels == cls
        chosen = predicted & mask
        expected_count = np.floor(predicted.sum(-1) * 0.6).astype(int)
        require(np.array_equal(chosen.sum(-1), expected_count), "Per-predicted-class floor quota differs")
        chosen_max = np.max(np.where(chosen, entropy, -np.inf), axis=-1)
        excluded_min = np.min(np.where(predicted & ~mask, entropy, np.inf), axis=-1)
        require(bool(np.all(chosen_max <= excluded_min + 2e-6)), "Selection is not classwise low entropy")


def validate_alignment(raw, adjusted, class_counts):
    probabilities = torch.from_numpy(raw).softmax(dim=-1).numpy()
    means = probabilities.mean(axis=2, dtype=np.float64)
    classes = raw.shape[-1]
    padding = np.full((128, 2, classes), 1 / classes)
    padded = np.concatenate((padding, means))
    cumulative = np.concatenate((np.zeros((1, 2, classes)), padded.cumsum(axis=0)))
    marginal = (cumulative[128:128+STEPS] - cumulative[:STEPS]) / 128
    marginal /= marginal.sum(axis=-1, keepdims=True)
    prior = np.asarray(class_counts, dtype=np.float64)
    prior /= prior.sum()
    correction = np.log(prior + 1e-6) - np.log(marginal + 1e-6)
    expected = raw.astype(np.float64) + correction[:, :, None, :]
    error = float(np.max(np.abs(expected - adjusted)))
    require(error < 4e-6, f"DA old-history calibration differs, max error {error}")
    return error


def read_trace(folder):
    with np.load(folder / "training_predictions.npz", allow_pickle=False) as data:
        return {name: data[name] for name in data.files}


def audit_source(row):
    folder = RUNS / row["id"]
    receipt = read(folder / "source_complete.json")
    config = read(folder / "config.json")
    for name, expected in row.items():
        require(receipt[name] == expected and config[name] == expected, f"Identity mismatch {row['id']}.{name}")
    require(receipt["complete"] and receipt["actual_updates"] == receipt["checkpoint_step"] == STEPS,
            "Source run has not completed 5000 updates")
    require(receipt["checkpoint_rule"] == config["checkpoint_rule"] == "fixed_step_5000", "Checkpoint policy changed")
    require(receipt["target_arrays_loaded"] is False and config["target_arrays_loaded"] is False,
            "Source receipt reports target access")
    require(receipt["unlabeled_truth_used"] is False and receipt["validation_records"] == config["validation_records"] == 0,
            "Unexpected unlabeled supervision or validation")
    for name, expected in receipt["artifacts_sha256"].items():
        require(sha(folder / name) == expected, f"Artifact fingerprint mismatch {row['id']}/{name}")
    records = tasks.records(row["dataset"])
    source_domains = [row["labeled"], *(d for d in tasks.DOMAINS if d not in (row["target"], row["labeled"]))]
    expected_ids = [r["record_id"] for domain in source_domains for r in records if int(r["domain_id"]) == domain]
    target_ids = {r["record_id"] for r in records if int(r["domain_id"]) == row["target"]}
    require(receipt["source_records"] == config["source_records"] == expected_ids, "Source record membership changed")
    require(set(expected_ids).isdisjoint(target_ids), "Source/target record IDs intersect")
    source_counts = [sum(int(r["window_count"]) for r in records if int(r["domain_id"]) == d) for d in source_domains]
    require(config["source_counts"] == source_counts, "Source window counts differ from manifest")
    classes = config["classes"]
    class_counts = [sum(int(r["window_count"]) for r in records
                        if int(r["domain_id"]) == row["labeled"] and int(r["class_id"]) == c)
                    for c in range(classes)]
    require(all(class_counts), "Labeled source lost a class")
    checkpoint = torch.load(folder / "last.pt", map_location="cpu", weights_only=False)
    require(checkpoint["step"] == STEPS and checkpoint["config"] == config, "Checkpoint metadata differs")
    state = checkpoint["state_dict"]
    predicates = {"aux_hash": lambda key: not key.startswith(("sharedNet3.", "audit_soft_weights.")),
                  "base_aux_hash": lambda key: not key.startswith(("sharedNet3.", "audit_soft_weights.", "pseudo_alignment.")),
                  "queue_hash": lambda key: key.startswith("pseudo_alignment."),
                  "main_hash": lambda key: key.startswith("sharedNet3.")}
    for name, predicate in predicates.items():
        require(state_hash(state, predicate) == receipt["final"][name], f"Final state hash differs {name}")
    for branch in range(2):
        require(int(state[f"pseudo_alignment.{branch}.updates"]) == STEPS, "DA update count differs")
        actual_prior = state[f"pseudo_alignment.{branch}.prior"].numpy()
        require(np.allclose(actual_prior, np.asarray(class_counts) / sum(class_counts), atol=1e-7), "DA prior differs from L only")
    bon = int(row["B_weight"] > 0)
    require(receipt["main_forward_calls"] == STEPS * (1 + bon), "Main forward count differs")
    require(receipt["bn_restorations"] == STEPS * bon, "BN restoration count differs")
    if not bon:
        require(receipt["perturb_initial"] == receipt["final"]["perturb_generator_hash"], "B-off consumed perturbation RNG")
    history = read(folder / "loss_history.json")
    require([x["step"] for x in history] == [1, *range(250, STEPS+1, 250)], "Loss heartbeat steps differ")
    require(all(np.isfinite(x["loss"]) and all(np.isfinite(v) for v in x["terms"].values()) for x in history),
            "Loss history contains nonfinite numbers")
    trace = read_trace(folder)
    require(trace["indices"].shape == (STEPS, 3, 64), "Incorrect trace index shape")
    require(trace["indices"].dtype == np.int64, "Trace indices changed type")
    batch_bytes = np.ascontiguousarray(trace["indices"], dtype="<i8").tobytes()
    require(hashlib.sha256(batch_bytes).hexdigest() == receipt["batch_digest"], "Batch trajectory hash differs")
    for domain_index, count in enumerate(source_counts):
        idx = trace["indices"][:, domain_index]
        require(bool(np.all((idx >= 0) & (idx < count))), "Sample indices out of source range")
    for name in ("raw_labels", "q_labels", "actual_labels", "raw_mask", "q_mask", "actual_mask"):
        require(trace[name].shape == (STEPS, 2, 64), f"Unexpected trace shape {name}")
    for name in ("raw_mask", "q_mask", "actual_mask"):
        require(trace[name].dtype == np.bool_, f"Unexpected mask type {name}")
    label_key = "raw_labels" if row["mode"] in ("raw", "selection_only") else "q_labels"
    mask_key = "raw_mask" if row["mode"] in ("raw", "labels_only") else "q_mask"
    require(np.array_equal(trace["actual_labels"], trace[label_key]), "Actual label source differs from intervention")
    require(np.array_equal(trace["actual_mask"], trace[mask_key]), "Actual mask source differs from intervention")
    if "raw_logits" in trace:
        probabilities = torch.from_numpy(trace["raw_logits"][-128:]).softmax(dim=-1).mean(dim=2).numpy()
        for branch in range(2):
            actual_history = state[f"pseudo_alignment.{branch}.history"].numpy()
            require(np.allclose(actual_history, probabilities[:, branch], atol=2e-7), "Final FIFO differs from raw batch means")
    return receipt, trace, class_counts


def audit_result(row, receipt):
    folder = RUNS / row["id"]
    result = read(folder / "result.json")
    for name, value in row.items():
        require(result[name] == value, "Result identity differs")
    require(result["checkpoint_step"] == STEPS and result["checkpoint_sha256"] == receipt["artifacts_sha256"]["last.pt"],
            "Result checkpoint differs")
    require(result["prediction_sha256"] == sha(folder / "target_predictions.npz"), "Target prediction hash differs")
    with np.load(folder / "target_predictions.npz", allow_pickle=False) as data:
        logits, labels = data["logits"], data["labels"]
    classes = logits.shape[1]
    expected_labels = np.concatenate([np.full(int(r["window_count"]), int(r["class_id"]))
                                      for r in tasks.records(row["dataset"]) if int(r["domain_id"]) == row["target"]])
    require(np.array_equal(labels, expected_labels), "Target labels differ from frozen manifest order")
    require(logits.shape == (len(labels), classes) and bool(np.isfinite(logits).all()), "Target logits invalid")
    prediction = logits.argmax(-1)
    confusion = np.bincount(labels * classes + prediction, minlength=classes**2).reshape(classes, classes)
    truth_count, predicted_count = confusion.sum(1), confusion.sum(0)
    recall = np.divide(confusion.diagonal(), truth_count, out=np.zeros(classes), where=truth_count > 0)
    f1 = np.divide(2*confusion.diagonal(), truth_count+predicted_count,
                   out=np.zeros(classes), where=(truth_count+predicted_count) > 0)
    metrics = result["metrics"]
    require(confusion.tolist() == metrics["confusion_matrix"], "Target confusion matrix differs")
    require(abs(confusion.trace()/len(labels)-metrics["accuracy"]) < 1e-12, "Target Accuracy differs")
    require(abs(f1.mean()-metrics["macro_f1"]) < 1e-12, "Target Macro-F1 differs")
    require(np.allclose(recall, metrics["per_class_recall"], atol=1e-12), "Target class recall differs")
    return result


def audit(sources_only=False, partial=False):
    protocol = read(OUT / "protocol.json")
    require(protocol["checkpoint_rule"] == "fixed_step_5000" and protocol["steps"] == STEPS, "Incorrect frozen policy")
    require(len(protocol["rows"]) == 48 and len({row["id"] for row in protocol["rows"]}) == 48, "Incorrect matrix size")
    for name, value in protocol["input_sha256"].items():
        require(sha(ROOT / name) == value, f"Frozen input changed {name}")
    rows = [row for row in protocol["rows"] if (RUNS / row["id"] / "source_complete.json").exists()]
    require(partial or len(rows) == 48, f"Only {len(rows)}/48 source runs are complete")
    groups = defaultdict(list)
    for row in rows:
        groups[(row["dataset"], row["seed"])].append(row)
    group_checks, results = [], []
    latest_source = max((read(RUNS / row["id"] / "source_complete.json")["completed_utc"] for row in rows), default=None)
    for (dataset, seed), group in groups.items():
        reference_receipt = None
        reference_trace = None
        bon_perturb_final = None
        alignment_error = None
        for row in group:
            receipt, trace, class_counts = audit_source(row)
            if reference_receipt is None:
                require(row["mode"] == "raw" and row["B_weight"] == 0, "Missing raw-B0 trace anchor")
                reference_receipt, reference_trace = receipt, trace
                raw, adjusted = trace["raw_logits"], trace["adjusted_logits"]
                require(raw.shape == adjusted.shape == (STEPS, 2, 64, len(class_counts)), "Anchor logit shape differs")
                require(bool(np.isfinite(raw).all() and np.isfinite(adjusted).all()), "Anchor logits nonfinite")
                validate_selection(raw, trace["raw_labels"], trace["raw_mask"])
                validate_selection(adjusted, trace["q_labels"], trace["q_mask"])
                alignment_error = validate_alignment(raw, adjusted, class_counts)
                digest = hashlib.sha256()
                for step in range(STEPS):
                    for value, dtype in ((trace["indices"][step], "<i8"), (raw[step], "<f4"), (adjusted[step], "<f4")):
                        digest.update(np.ascontiguousarray(value, dtype=dtype).tobytes())
                require(digest.hexdigest() == receipt["trajectory_digest"], "Anchor trajectory digest differs")
            for field in ("batch_digest", "trajectory_digest", "batch_initial", "perturb_initial"):
                require(receipt[field] == reference_receipt[field], f"Paired {field} differs")
            require(receipt["initial"] == reference_receipt["initial"], "Paired initial model differs")
            for field in ("aux_hash", "base_aux_hash", "queue_hash", "batch_generator_hash"):
                require(receipt["final"][field] == reference_receipt["final"][field], f"Paired final {field} differs")
            if row["B_weight"]:
                final_rng = receipt["final"]["perturb_generator_hash"]
                if bon_perturb_final is None:
                    bon_perturb_final = final_rng
                require(final_rng == bon_perturb_final, "B-on final perturbation RNG differs")
            for field in ("indices", "raw_labels", "q_labels", "raw_mask", "q_mask"):
                require(np.array_equal(trace[field], reference_trace[field]), f"Saved paired {field} differs")
            if not sources_only:
                result = audit_result(row, receipt)
                require(latest_source is not None and result["evaluated_utc"] >= latest_source,
                        "Target result predates all source completion")
                results.append(result)
        group_checks.append(dict(dataset=dataset, seed=seed, completed_models=len(group),
                                 masks_labels_and_indices_verified=True,
                                 initial_and_final_rng_verified=True,
                                 calibration_max_abs_cpu_error=alignment_error))
    if not sources_only:
        combined = read(OUT / "results.json")
        require(combined["complete"] and combined["rows"] == results, "Combined result rows differ")
        require(read(OUT / "all_sources_complete.json")["complete"] is True, "Source completion gate absent")
    result = dict(checked_utc=datetime.now(timezone.utc).isoformat(), complete=len(rows) == 48,
                  source_models_verified=len(rows), expected_source_models=48, phase="sources" if sources_only else "results",
                  target_predictions_verified=len(results), groups=group_checks,
                  checked_on_cpu=True, trained_or_inferred_models=0,
                  limitations=["Data-access declarations are checked against the frozen runner and actual manifest groups; this audit does not add OS-level file interception.",
                               "Low-entropy checks allow 2e-6 CPU/GPU entropy differences at ordering boundaries."])
    destination = OUT / ("source_audit_checks.json" if sources_only else "audit_checks.json")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-only", action="store_true")
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(2)
    audit(sources_only=args.sources_only, partial=args.partial)
