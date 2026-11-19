"""Freeze historical A's ordered occurrences for the 65 Hz Oracle experiment."""

import csv
from pathlib import Path

from . import run_pilot as pilot


ROOT = pilot.ROOT
OUT = ROOT / "output/pc2g_hust_65hz_oracle_preregistration_20261119"
FROZEN_DIR = OUT / "frozen_archive"
SEEDS = (0, 1, 2)
STEPS = pilot.STEPS
SLOT_COUNT = 64
RUN_RATIO = 0.6
SOURCE_HZ = ("20", "35", "65")
ARCHIVE_KEYS = ("indices", "raw_labels", "q_labels", "actual_labels",
                "raw_mask", "q_mask", "actual_mask")
RECORD_FIELDS = ("dataset", "record_id", "relative_path", "raw_sha256", "payload_title",
                 "class_id", "domain_id", "speed_hz", "input_axis", "fs_hz", "signal_sha256",
                 "included", "status", "window_length", "window_stride", "window_count")
MANIFEST_NAME = "manifest.json"
TRAINING_SOURCES = "training_sources.csv"
np = pilot.np
torch = pilot.torch


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_hash(path, expected):
    require(pilot.sha(path) == expected, f"Frozen input changed: {path}")


def replay_name(seed):
    require(seed in SEEDS, f"Unregistered seed: {seed}")
    return f"seed{seed}_replay.npz"


def truth_name(seed):
    require(seed in SEEDS, f"Unregistered seed: {seed}")
    return f"seed{seed}_truth65.npy"


def verified_artifact(directory, name):
    directory = Path(directory)
    lock = pilot.read(directory / MANIFEST_NAME)
    path = directory / name
    verify_hash(path, lock["artifacts_sha256"][name])
    return path


def archive_sha256(seed, directory=FROZEN_DIR):
    path = verified_artifact(directory, replay_name(seed))
    return pilot.sha(path)


def load_archive(seed, directory=FROZEN_DIR):
    """Load frozen A positions and labels with the paired auxiliary logit anchors."""
    with np.load(verified_artifact(directory, replay_name(seed)), allow_pickle=False) as handle:
        return {name: handle[name] for name in handle.files}


def load_oracle_truth(seed, directory=FROZEN_DIR):
    """Load 65 Hz truth exclusively for O's selected batch positions."""
    return np.load(verified_artifact(directory, truth_name(seed)), allow_pickle=False)


def training_rows(directory=FROZEN_DIR):
    """Read the source-only signal manifest, with truth only for 20 Hz."""
    source = verified_artifact(directory, TRAINING_SOURCES)
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 27, "Training manifest must contain 27 source records")
    for row in rows:
        domain = SOURCE_HZ.index(row["speed_hz"])
        require(row["domain_id"] == str(domain), f"Unexpected source mapping: {row['record_id']}")
        require(bool(row["class_id"]) == (domain == 0), f"Unexpected source truth: {row['record_id']}")
    return rows


def read_pinned_input(record):
    path = ROOT / record["path"]
    verify_hash(path, record["sha256"])
    return path


def prepare_sources(inspection, directory):
    path = read_pinned_input(inspection["source_manifest"])
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle)
                if row["included"] == "1" and row["speed_hz"] in SOURCE_HZ]

    for domain, hz in enumerate(SOURCE_HZ):
        group = [row for row in rows if row["speed_hz"] == hz]
        require(len(group) == 9, f"Unexpected record count at {hz} Hz")
        require(all(row["domain_id"] == str(domain) and row["window_count"] == "81" for row in group),
                f"Unexpected window mapping at {hz} Hz")
        require({int(row["class_id"]) for row in group} == set(range(9)),
                f"Unexpected class coverage at {hz} Hz")

    source_coords = [row["record_id"] for hz in SOURCE_HZ for row in rows if row["speed_hz"] == hz]
    truth_65 = np.repeat([int(row["class_id"]) for row in rows if row["speed_hz"] == "65"], 81)
    output = directory / TRAINING_SOURCES
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS)
        writer.writeheader()
        for row in rows:
            training_record = {key: row[key] for key in RECORD_FIELDS}
            if row["speed_hz"] != "20":
                training_record["class_id"] = ""
            writer.writerow(training_record)
    return truth_65, source_coords


def historical_receipt(source, seed, source_coords):
    directory = ROOT / source["directory"]
    receipt_path = directory / "source_complete.json"
    trace_path = directory / "training_predictions.npz"
    verify_hash(receipt_path, source["receipt_sha256"])
    verify_hash(trace_path, source["training_predictions_sha256"])
    receipt = pilot.read(receipt_path)
    require(receipt["complete"] and receipt["seed"] == seed and receipt["dataset"] == "hust" and
            receipt["labeled"] == 0 and receipt["target"] == 3 and
            receipt["actual_updates"] == receipt["checkpoint_step"] == STEPS and
            receipt["source_records"] == source_coords and
            not receipt["target_arrays_loaded"] and not receipt["unlabeled_truth_used"],
            f"Unexpected historical source receipt: {receipt_path}")
    require(receipt["artifacts_sha256"][trace_path.name] == source["training_predictions_sha256"],
            f"Trace differs from historical receipt: {trace_path}")
    return receipt, trace_path


def load_pinned_pair(seed_row, source_coords):
    seed = seed_row["seed"]
    receipts = {
        role: historical_receipt(source, seed, source_coords)
        for role, source in seed_row["source_archives"].items()
    }
    for field, expected in (("batch_digest", seed_row["shared_batch_digest"]),
                            ("trajectory_digest", seed_row["shared_trajectory_digest"])):
        require(all(receipt[field] == expected for receipt, _ in receipts.values()),
                f"Seed {seed}: archived {field} differs")
    a_receipt, a_path = receipts["A"]
    b_receipt, b_path = receipts["B"]
    anchor_receipt, anchor_path = receipts["order_anchor"]
    require(a_receipt["mode"] == b_receipt["mode"] == "full" and
            a_receipt["B_weight"] == b_receipt["B_weight"] == 0.1 and
            b_receipt["ce65"] is False and b_receipt["cons65"] is True and
            anchor_receipt["mode"] == "raw" and anchor_receipt["B_weight"] == 0,
            f"Seed {seed}: archived arm definitions differ")
    with (np.load(a_path, allow_pickle=False) as original,
          np.load(b_path, allow_pickle=False) as removed,
          np.load(anchor_path, allow_pickle=False) as anchor):
        frozen = {key: original[key] for key in ARCHIVE_KEYS}
        require(all(np.array_equal(frozen[key], removed[key]) for key in ARCHIVE_KEYS),
                f"Seed {seed}: archived A/B sampling and labels differ")
        for key in ("indices", "raw_mask", "q_mask", "raw_labels", "q_labels"):
            require(np.array_equal(frozen[key], anchor[key]),
                    f"Seed {seed}: historical anchor q/p differs in {key}")
        for key in ("raw_logits", "adjusted_logits"):
            logits = anchor[key]
            require(logits.shape == (STEPS, 2, SLOT_COUNT, 9) and logits.dtype == np.float32 and
                    np.isfinite(logits).all(), f"Seed {seed}: invalid anchor {key}")
            frozen[f"anchor_{key}"] = np.ascontiguousarray(logits)
    require(frozen["indices"].shape == (STEPS, 3, SLOT_COUNT) and
            (frozen["indices"] >= 0).all() and (frozen["indices"] < 729).all() and
            frozen["actual_mask"].shape == (STEPS, 2, SLOT_COUNT) and
            frozen["actual_mask"].dtype == np.bool_ and
            np.array_equal(frozen["actual_mask"], frozen["q_mask"]) and
            np.array_equal(frozen["actual_labels"], frozen["q_labels"]),
            f"Seed {seed}: invalid Full+B source archive")
    return frozen


def configure_cuda(inspection):
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    require(torch.cuda.is_available(), "Historical CUDA sorting backend is required")
    environment = {"torch": str(torch.__version__), "gpu": torch.cuda.get_device_name()}
    require(all(row["historical_A_runtime"] == environment for row in inspection["by_seed"]),
            f"CUDA environment differs from the historical A archive: {environment}")
    return {
        **environment, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
        "device_capability": list(torch.cuda.get_device_capability()),
    }


def entropy_ties(steps_entropy, labels, selection):
    """Count steps with same predicted class and equal FP32 entropy."""
    left, right = np.triu_indices(SLOT_COUNT, k=1)
    internal = boundary = 0
    for start in range(0, STEPS, 128):
        block = slice(start, start + 128)
        h = steps_entropy[block]
        predicted = labels[block]
        mask = selection[block]
        tie = (h[:, left] == h[:, right]) & (predicted[:, left] == predicted[:, right])
        internal += int(np.count_nonzero((tie & mask[:, left] & mask[:, right]).any(axis=1)))
        boundary += int(np.count_nonzero((tie & (mask[:, left] != mask[:, right])).any(axis=1)))
    return {"inside_selection": internal, "across_selection_boundary": boundary}


@torch.no_grad()
def rebuild_order(seed, frozen):
    q = torch.from_numpy(frozen["anchor_adjusted_logits"]).cuda()
    ordered = np.full((STEPS, 2, SLOT_COUNT), -1, dtype=np.int64)
    entropy = torch.empty((STEPS, 2, SLOT_COUNT), dtype=torch.float32, device=q.device)
    counts = frozen["actual_mask"].sum(axis=-1, dtype=np.int64)
    selector = pilot.core.base.selected_indices
    for step in range(STEPS):
        for branch in range(2):
            logits = q[step, branch]
            idx, labels = selector(logits, RUN_RATIO, classwise=True)
            p = logits.softmax(1)
            entropy[step, branch] = -(p * p.clamp_min(1e-8).log()).sum(1)
            selected = idx.cpu().numpy()
            expected = np.flatnonzero(frozen["actual_mask"][step, branch])
            location = f"seed {seed}, step {step + 1}, {SOURCE_HZ[branch + 1]} Hz"
            require(np.array_equal(np.sort(selected), expected),
                    f"{location}: CUDA replay has different A membership, "
                    f"historical slots={expected.tolist()}, rebuilt slots={selected.tolist()}")
            require(np.array_equal(labels.cpu().numpy(), frozen["actual_labels"][step, branch]),
                    f"{location}: CUDA replay has different historical A pseudo labels")
            ordered[step, branch, :len(selected)] = selected
        if (step + 1) % 1000 == 0:
            print(f"seed {seed}: matched A positions through step {step + 1}", flush=True)

    frozen["ordered_positions"] = ordered
    frozen["selected_count"] = counts
    entropy = entropy.cpu().numpy()
    return {
        SOURCE_HZ[branch + 1]: entropy_ties(entropy[:, branch], frozen["actual_labels"][:, branch],
                                            frozen["actual_mask"][:, branch])
        for branch in range(2)
    }


def prepare(directory=FROZEN_DIR):
    directory = Path(directory)
    if (directory / MANIFEST_NAME).exists():
        lock = pilot.read(directory / MANIFEST_NAME)
        for name, expected in lock["artifacts_sha256"].items():
            verify_hash(directory / name, expected)
        print(f"Verified existing frozen archive: {directory}", flush=True)
        return lock

    directory.mkdir(parents=True, exist_ok=True)
    plan = OUT / "oracle_implementation_audit.json"
    inspection = pilot.read(plan)["archive_inspection"]
    try:
        read_pinned_input(inspection["historical_protocol"])
        for name, digest in inspection["historically_pinned_source_sha256"].items():
            verify_hash(ROOT / name, digest)
        cuda = configure_cuda(inspection)
        truth, source_coords = prepare_sources(inspection, directory)
        output = {TRAINING_SOURCES: pilot.sha(directory / TRAINING_SOURCES)}
        summaries = []
        require(tuple(row["seed"] for row in inspection["by_seed"]) == SEEDS, "Unregistered seed list")
        for seed_row in inspection["by_seed"]:
            seed = seed_row["seed"]
            frozen = load_pinned_pair(seed_row, source_coords)
            ties = rebuild_order(seed, frozen)
            np.savez(directory / replay_name(seed), **frozen)

            mask = frozen["actual_mask"][:, 1]
            row_truth = np.full(mask.shape, -1, dtype=np.int64)
            row_truth[mask] = truth[frozen["indices"][:, 2][mask]]
            incorrect = int(np.count_nonzero(mask & (frozen["actual_labels"][:, 1] != row_truth)))
            require(int(mask.sum()) == seed_row["historical_A_65hz_selected_occurrences"] and
                    incorrect == seed_row["historical_A_65hz_incorrect_occurrences"],
                    f"Seed {seed}: selected source-truth mapping differs from preregistration")
            np.save(directory / truth_name(seed), row_truth, allow_pickle=False)
            for name in (replay_name(seed), truth_name(seed)):
                output[name] = pilot.sha(directory / name)
            summaries.append({
                "seed": seed, "archived_steps_per_branch": STEPS,
                "selected_occurrences_65hz": int(mask.sum()), "invalid_original_65hz": incorrect,
                "steps_with_same_predicted_class_and_equal_fp32_entropy": ties,
                "historical_archives": seed_row["source_archives"],
            })
        lock = {
            "status": "order_rebuilt_and_membership_matched",
            "created_utc": pilot.now(), "cuda": cuda, "source_hz": SOURCE_HZ,
            "selector": "historical per-step, per-branch FP32 CUDA, original selected_indices",
            "sort_scope": "Full candidate groups. The A mask is the reference for selected occurrences.",
            "historical_order_independently_archived": False,
            "by_seed": summaries, "artifacts_sha256": output,
            "target_arrays_loaded": False, "optimizer_updates": 0,
        }
        pilot.write(directory / MANIFEST_NAME, lock)
        print(f"Froze all three historical A trajectories: {directory}", flush=True)
        return lock
    except Exception as error:
        pilot.write(directory / "failure.json", {
            "status": "archive_gate_failed", "utc": pilot.now(), "type": type(error).__name__,
            "error": str(error), "target_arrays_loaded": False, "optimizer_updates": 0,
        })
        raise


if __name__ == "__main__":
    prepare()
