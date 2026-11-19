"""HUSTbearing stage-2 inventory and whole-acquisition window reader.

Use `python -m experiments.pc2g_cross_dataset.hust --build-manifest` to
re-audit the source files. For training, pass one included CSV row at a time
to read_windows, after assigning whole record_ids to roles.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("output/pc2g_cross_dataset_stage2/hust_manifest.csv")
AUDIT_DIR = Path("output/da_b_dataset_assessment_20260914")
RAW = Path("data/HUSTbearing_CHAOZHAO1/raw")
QUARANTINE = AUDIT_DIR / "hust_numeric_audit_v3/quarantined_author_payloads"
README = ("https://github.com/CHAOZHAO-1/HUSTbearing-dataset/blob/"
          "554fe1269055660c41e9011fe97b971348bdec7f/README.md")
ALL_SPEEDS = (20, 25, 30, 35, 40, 60, 65, 70, 75, 80)
SPEEDS = (20, 35, 65, 80)
STATES = ("H", "0.5X_I", "I", "0.5X_O", "O", "0.5X_B", "B", "0.5X_C", "C")
FAMILIES = {"H": "healthy", "I": "inner_race", "O": "outer_race",
            "B": "ball", "C": "inner_and_outer_races"}
FS_HZ = 25_600
N_SAMPLES = 262_144
WINDOW = 3_200


def _sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _signal_digest(signal):
    """Hash decoded samples in their recorded precision (little-endian float64)."""
    return hashlib.sha256(np.ascontiguousarray(signal, dtype="<f8")).hexdigest()


def _read_payload(path, columns=None):
    # These author .xls files are tab-delimited text with a DAQ header.
    with path.open("rb") as f:
        header = []
        for _ in range(100):
            line = f.readline().decode("utf-8").strip()
            if line == "Data":
                break
            header.append(line)
        else:
            raise ValueError(f"{path}: missing Data marker")
        if (not header[0].startswith("Title:") or
                f"Total Data Rows\t{N_SAMPLES}" not in header or
                "Legend\tSpeed\tX\tY\tZ" not in header):
            raise ValueError(f"{path}: unrecognized acquisition header")
        title = header[0].partition(":")[2].strip()
        data = np.loadtxt(f, delimiter="\t", usecols=columns, dtype=np.float64)
    return title, data


def _audit_record(root, entry, previous):
    name = entry["name"]
    state = entry["health_code"]
    condition = entry["condition_name"]
    speed = None if condition.startswith("VS_") else int(condition[:-2])
    if name.casefold() != f"{state}_{condition}.xls".casefold():
        raise ValueError(f"{name}: author inventory mismatch")
    candidates = [folder / name for folder in (RAW, QUARANTINE) if (root / folder / name).is_file()]
    if len(candidates) != 1:
        raise ValueError(f"{name}: expected exactly one local raw or quarantined payload")
    relative_path = candidates[0]
    path = root / relative_path
    raw_hash = _sha256(path)
    if raw_hash != previous["raw_sha256"] or entry["id"] != previous["id"]:
        raise ValueError(f"{name}: source differs from the acquisition audit")
    title, data = _read_payload(path)
    if data.shape != (N_SAMPLES, 5) or not np.isfinite(data).all():
        raise ValueError(f"{name}: invalid sample count, channels or values")
    # Timestamps are printed with six digits after the decimal point.
    if np.max(np.abs(data[:, 0] - np.arange(N_SAMPLES) / FS_HZ)) > 0.500001e-6:
        raise ValueError(f"{name}: timestamps disagree with {FS_HZ} Hz")
    for i, axis in enumerate(("time", "speed", "X", "Y", "Z")):
        if _signal_digest(data[:, i]) != previous["signal_sha256"][axis]:
            raise ValueError(f"{name}: decoded {axis} samples disagree with prior raw audit")
    stem = Path(name).stem
    allowed_titles = {stem.casefold()}
    if speed is None:  # The acquisition system omits 'Hz' on variable-speed titles.
        allowed_titles.add(stem.casefold().removesuffix("hz"))
    title_agrees = title.casefold() in allowed_titles
    if title_agrees != previous["metadata_valid"]:
        raise ValueError(f"{name}: title no longer matches recorded metadata decision")
    if not title_agrees:
        status = "quarantined_title_mismatch"
    elif speed is None:
        status = "excluded_variable_speed"
    elif speed not in SPEEDS:
        status = "excluded_other_constant_speed"
    else:
        status = "included"
    included = status == "included"
    family = FAMILIES[state[-1]]
    severity = "none" if state == "H" else ("medium" if state.startswith("0.5X_") else "severe")
    return {
        "dataset": "HUSTbearing_CHAOZHAO1", "record_id": f"HUST:{stem}",
        "filename": name, "relative_path": relative_path.as_posix(),
        "source_file_id": entry["id"], "raw_sha256": raw_hash, "raw_bytes": path.stat().st_size,
        "payload_title": title, "metadata_valid": int(title_agrees),
        "health_code": state, "fault_family": family, "severity": severity,
        "class_id": STATES.index(state) if title_agrees else "",
        "condition": condition, "condition_type": "variable" if speed is None else "constant",
        "speed_hz": "" if speed is None else speed, "speed_definition": "motor_set_frequency",
        "domain_id": SPEEDS.index(speed) if included else "",
        "fs_hz": FS_HZ, "n_samples": len(data), "axes": "X|Y|Z",
        "input_axis": "X", "input_axis_definition": "author_X_vibration_direction",
        "signal_sha256": previous["signal_sha256"]["X"],
        "acquisition_unit": "one_independent_acquisition_per_file",
        "bearing_group": f"HUST:{state}" if title_agrees else "",
        "bearing_serial": "",
        "bearing_group_basis": ("author_confirmed_same_bearing_across_speeds_within_state"
                                if title_agrees else "filename_and_header_disagree"),
        "included": int(included), "status": status,
        "window_length": WINDOW, "window_stride": WINDOW,
        "window_count": N_SAMPLES // WINDOW if included else 0,
        "metadata_source": README,
    }


def build_manifest(root=ROOT):
    """Validate all 99 author payloads and (re)create the stage-2 inventory."""
    root = Path(root)
    inventory = json.loads((root / AUDIT_DIR / "hust_inventory_v1.json").read_text("utf-8"))["rows"]
    audit = json.loads((root / AUDIT_DIR / "hust_numeric_audit_v3/results.json").read_text("utf-8"))
    previous = {row["name"]: row for row in audit["rows"]}
    expected = {(s, cond) for s in STATES for cond in (*[f"{x}hz" for x in ALL_SPEEDS], "vs_0_40_0hz")}
    cells = {(r["health_code"], r["condition_name"].casefold()) for r in inventory}
    paths = {p.name for folder in (RAW, QUARANTINE) for p in (root / folder).glob("*.xls")}
    if (cells != expected or len(inventory) != 99 or len({r["id"] for r in inventory}) != 99 or
            {r["name"] for r in inventory} != paths or set(previous) != paths):
        raise ValueError("Expected the complete 9-state by 11-condition HUSTbearing release")
    rows = [_audit_record(root, entry, previous[entry["name"]]) for entry in inventory]
    counts = Counter(row["status"] for row in rows)
    if counts != {"included": 36, "excluded_other_constant_speed": 54,
                  "excluded_variable_speed": 7, "quarantined_title_mismatch": 2}:
        raise ValueError(f"Inventory decision counts changed: {counts}")
    if any(len({row[key] for row in rows}) != len(rows) for key in ("raw_sha256", "signal_sha256")):
        raise ValueError("Duplicate raw acquisition or identical X signal")
    output = root / MANIFEST
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=output.parent,
                            delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    Path(f.name).replace(output)
    return rows


def read_windows(record, root=ROOT):
    """Read one selected file as (raw float32 windows, int64 sample starts)."""
    if str(record["included"]) != "1" or record["status"] != "included":
        raise ValueError(f"Record excluded from this protocol: {record['record_id']}")
    path = Path(root) / record["relative_path"]
    if (record["record_id"] != f"HUST:{path.stem}" or record["input_axis"] != "X" or
            int(record["fs_hz"]) != FS_HZ or int(record["window_length"]) != WINDOW or
            int(record["window_stride"]) != WINDOW):
        raise ValueError(f"{path}: inconsistent record or window metadata")
    if _sha256(path) != record["raw_sha256"]:
        raise ValueError(f"{path}: raw SHA-256 mismatch")
    title, signal = _read_payload(path, columns=2)
    if (title != record["payload_title"] or signal.shape != (N_SAMPLES,) or
            _signal_digest(signal) != record["signal_sha256"]):
        raise ValueError(f"{path}: acquisition title or X signal mismatch")
    count = N_SAMPLES // WINDOW
    if int(record["window_count"]) != count:
        raise ValueError(f"{path}: incorrect window count")
    windows = signal[:count * WINDOW].astype(np.float32).reshape(count, WINDOW)
    return windows, np.arange(count, dtype=np.int64) * WINDOW


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-manifest", action="store_true", required=True)
    args = parser.parse_args()
    manifest_rows = build_manifest()
    print(dict(Counter(row["status"] for row in manifest_rows)))
