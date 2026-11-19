"""Record-disjoint inputs for the CWRU and HUSTbearing four-domain experiments."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from . import cwru, hust


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pc2g_cross_dataset_stage2"
WINDOW = 3200
DOMAINS = tuple(range(4))


def records(dataset, directory=OUTPUT):
    if dataset not in ("cwru", "hust"):
        raise ValueError(f"Unrecognized dataset {dataset}")
    with (directory / f"{dataset}_manifest.csv").open(encoding="utf-8-sig", newline="") as source:
        return [row for row in csv.DictReader(source) if row.get("included", "1") == "1"]


def load_domain(dataset, rows, domain, labeled, root):
    read_windows = {"cwru": cwru.read_windows, "hust": hust.read_windows}[dataset]
    signals, labels = [], []
    for row in rows:
        if int(row["domain_id"]) != domain:
            continue
        x, starts = read_windows(row, root=root)
        count = int(row["window_count"])
        if x.dtype != np.float32 or x.shape != (count, WINDOW):
            raise ValueError(f"Unexpected window data for {row['record_id']}")
        if not np.array_equal(starts, np.arange(count, dtype=np.int64) * WINDOW):
            raise ValueError(f"Unexpected window offsets for {row['record_id']}")
        signals.append(x)
        if labeled:
            labels.append(np.full(count, int(row["class_id"]), dtype=np.int64))
    if not signals:
        raise ValueError(f"Empty domain {domain}")
    return np.concatenate(signals), np.concatenate(labels) if labeled else None


def load_training_domains(dataset, target, labeled, root=ROOT, directory=OUTPUT):
    """Return the three raw source arrays in MSDGN order, with labels only for L."""
    if target not in DOMAINS or labeled not in DOMAINS or target == labeled:
        raise ValueError("A distinct target and labeled source are required")
    rows = records(dataset, directory)
    sources = [labeled, *(d for d in DOMAINS if d not in (labeled, target))]
    return [(d, *load_domain(dataset, rows, d, d == labeled, root)) for d in sources]


def load_test_domain(dataset, target, root=ROOT, directory=OUTPUT):
    """Explicit evaluation entry point for use after the supervised model is frozen."""
    if target not in DOMAINS:
        raise ValueError(f"Unknown target {target}")
    return load_domain(dataset, records(dataset, directory), target, True, root)


def shifted_overlap(windows, rows, owners):
    """Verify exact inter-record suffix/prefix matches of at least 64 float32 values."""
    # Use canonical positive zero so longer np.array_equal matches cannot be
    # missed due to the bit representation of zeros in the two-value index.
    raw = np.ascontiguousarray(windows, dtype=np.float32)
    raw[raw == 0] = 0
    words = raw.view(np.uint32)
    prefix_keys = (words[:, 0].astype(np.uint64) << 32) | words[:, 1]
    order = np.argsort(prefix_keys)
    sorted_keys = prefix_keys[order]
    counts = Counter()
    examples = []
    for i, window in enumerate(words):
        ends = WINDOW - 64 + 1
        keys = (window[:ends].astype(np.uint64) << 32) | window[1:ends + 1]
        left = np.searchsorted(sorted_keys, keys)
        possible = np.flatnonzero(sorted_keys[np.minimum(left, len(order) - 1)] == keys)
        for offset in possible:
            right = np.searchsorted(sorted_keys, keys[offset], side="right")
            for j in order[left[offset]:right]:
                if owners[i] == owners[j] or (offset == 0 and j <= i):
                    continue
                if not np.array_equal(windows[i, offset:], windows[j, :WINDOW-offset]):
                    continue
                a, b = rows[owners[i]], rows[owners[j]]
                category = "between_domains" if a["domain_id"] != b["domain_id"] else "within_domain"
                counts[category] += 1
                if len(examples) < 6:
                    examples.append([a["record_id"], b["record_id"], int(offset)])
    return {"minimum_exact_samples": 64, "between_domains": counts["between_domains"],
            "within_domain": counts["within_domain"], "examples": examples}


def audit_dataset(dataset, root=ROOT, directory=OUTPUT):
    rows = records(dataset, directory)
    identifiers = [row["record_id"] for row in rows]
    if len(set(identifiers)) != len(rows):
        raise ValueError(f"Repeated record IDs for {dataset}")
    class_maps = {d: {} for d in DOMAINS}
    domains = {d: [] for d in DOMAINS}
    counts = Counter()
    buffers, owners = [], []
    fingerprint = {"raw": {}, "window_minmax": {}}
    repeated = Counter()
    for i, row in enumerate(rows):
        domain, cls = int(row["domain_id"]), int(row["class_id"])
        file_rows = [row]
        windows, _ = load_domain(dataset, file_rows, domain, False, root)
        if not np.isfinite(windows).all() or np.any(np.ptp(windows, axis=1) == 0):
            raise ValueError(f"Invalid windows in {row['record_id']}")
        count = len(windows)
        minimum = windows.min(axis=1, keepdims=True)
        normalized = (windows - minimum) / np.maximum(windows.max(axis=1, keepdims=True) - minimum, 1e-8)
        for stage, data in (("raw", windows), ("window_minmax", normalized)):
            for segment in data:
                key = hashlib.sha256(segment.tobytes()).digest()
                previous = fingerprint[stage].get(key)
                if previous is not None:
                    repeated[stage] += 1
                    if previous != domain:
                        repeated[f"{stage}_cross_domain"] += 1
                else:
                    fingerprint[stage][key] = domain
        buffers.append(windows)
        owners.extend([i] * count)
        domains[domain].append(row["record_id"])
        class_maps[domain][cls] = class_maps[domain].get(cls, 0) + 1
        counts[(domain, cls)] += count
    common = sorted(set.intersection(*(set(m) for m in class_maps.values())))
    if len(common) != {"cwru": 4, "hust": 9}[dataset] or any(set(m) != set(common) for m in class_maps.values()):
        raise ValueError(f"Inconsistent class coverage for {dataset}")
    tasks = []
    for target in DOMAINS:
        for labeled in DOMAINS:
            if labeled == target:
                continue
            unlabeled = [d for d in DOMAINS if d not in (target, labeled)]
            groups = {"labeled_train": domains[labeled], "unlabeled_train_1": domains[unlabeled[0]],
                      "unlabeled_train_2": domains[unlabeled[1]], "validation": [], "target_test": domains[target]}
            ids = [rid for group in groups.values() for rid in group]
            if Counter(ids) != Counter(identifiers):
                raise ValueError(f"Record assignment overlaps or is incomplete for {dataset}")
            tasks.append({"target": target, "labeled": labeled, "unlabeled": unlabeled, "record_roles": groups})
    duplicate_windows = {stage: repeated[stage] for stage in
                         ("raw", "window_minmax", "raw_cross_domain", "window_minmax_cross_domain")}
    return {"selected_records": len(rows), "unique_windows": len(fingerprint["raw"]),
            "window_occurrences": len(owners), "class_intersection": common,
            "records_by_domain_class": class_maps,
            "windows_by_domain_class": {d: {c: counts[(d,c)] for c in common} for d in DOMAINS},
            "duplicate_windows": duplicate_windows,
            "inter_record_shifted_overlap": shifted_overlap(np.concatenate(buffers), rows, owners),
            "tasks": tasks}


def main():
    data = {name: audit_dataset(name) for name in ("cwru", "hust")}
    result = {"phase": "data_feasibility", "trained_models": 0,
              "checkpoint_policy": "proposed_fixed_step_5000_pending_author_confirmation",
              "window_length": WINDOW, "stride": WINDOW, "normalization": "per-window min-max, denominator >= 1e-8",
              "datasets": data}
    path = OUTPUT / "dataset_statistics.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
