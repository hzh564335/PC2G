"""CWRU 0.007-inch drive-end subset at four motor loads.

The CWRU normal-baseline and 12k drive-end catalogs identify the recordings.
Smith & Randall (2015), Appendix A, Table A1 documents 48 kHz for normals
97–100 (https://doi.org/10.1016/j.ymssp.2015.04.021). The published fault
catalog contains additional fault sizes and outer-race positions. This subset
uses the four classes and record IDs in the project's original raw download.
"""

import csv
import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from scipy.io import loadmat
from scipy.signal import resample_poly


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("output/pc2g_cross_dataset_stage2/cwru_manifest.csv")
DATA = Path("data/CWRU")
SITE = "https://engineering.case.edu/bearingdatacenter"
NORMAL_CATALOG = f"{SITE}/normal-baseline-data"
FAULT_CATALOG = f"{SITE}/12k-drive-end-bearing-fault-data"
NORMAL_RATE_REFERENCE = "https://doi.org/10.1016/j.ymssp.2015.04.021"
SAMPLE_RATE = 12_000
WINDOW = 3_200
# Class order matches the original four-class raw-file pilot.
CLASSES = (("normal", 97), ("inner", 105), ("ball", 118), ("outer", 130))
CATALOG_RPM = (1797, 1772, 1750, 1730)


def _load_record(record, root):
    path = Path(root) / record["raw_path"]
    key = record["channel_key"]
    rpm_key = f"X{int(record['record_id']):03d}RPM"
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != record["sha256"]:
            raise ValueError(f"Raw recording differs from its download hash: {path}")
        stream.seek(0)
        mat = loadmat(stream, variable_names=[key, rpm_key])
    # The official 99.mat includes X098_DE_time as well as X099_DE_time.
    if key not in mat:
        raise ValueError(f"{path} does not contain {key}")
    native = np.asarray(mat[key]).squeeze()
    if native.ndim != 1 or not np.isfinite(native).all():
        raise ValueError(f"Invalid drive-end vibration trace in {path}")
    rate = int(record["native_sample_rate_hz"])
    if rate == 48_000:
        signal = resample_poly(native, up=1, down=4)
    elif rate == SAMPLE_RATE:
        signal = native
    else:
        raise ValueError(f"Unsupported drive-end sample rate {rate} for {path}")
    rpm = int(mat[rpm_key].item()) if rpm_key in mat else ""
    return np.asarray(signal, dtype=np.float32), native.size, rpm


def _window(signal):
    count = signal.size // WINDOW
    windows = signal[:count * WINDOW].reshape(count, WINDOW)
    if not count or np.any(np.ptp(windows, axis=1) == 0):
        raise ValueError("Recording contains no complete windows or a constant window")
    return windows, np.arange(count, dtype=np.int64) * WINDOW


def read_windows(record, root=ROOT):
    """Return raw-amplitude float32 windows and zero-based starts at 12 kHz."""
    signal, native_size, _ = _load_record(record, root)
    windows, starts = _window(signal)
    actual = (native_size, signal.size, SAMPLE_RATE, WINDOW, WINDOW, len(windows))
    fields = ("native_sample_count", "sample_count", "sample_rate_hz",
              "window_length", "window_stride", "window_count")
    if tuple(int(record[field]) for field in fields) != actual:
        raise ValueError(f"Window metadata mismatch for CWRU record {record['record_id']}")
    return windows, starts


def build_manifest(root=ROOT):
    root = Path(root)
    downloads = json.loads((root / DATA / "download_manifest.json").read_text(encoding="utf-8"))
    sources = {row["file"]: row for row in downloads}
    rows = []
    for load_hp, catalog_rpm in enumerate(CATALOG_RPM):
        for class_id, (class_name, base_id) in enumerate(CLASSES):
            file_id = base_id + load_hp
            filename = f"{file_id}.mat"
            source = sources[filename]
            normal = class_name == "normal"
            record = dict(
                dataset="CWRU", record_id=file_id, domain_id=load_hp, load_hp=load_hp,
                class_id=class_id, class_name=class_name,
                fault_diameter_in="" if normal else 0.007,
                outer_position="6 o'clock" if class_name == "outer" else "",
                catalog_rpm=catalog_rpm, raw_path=(DATA / "raw" / filename).as_posix(),
                channel_key=f"X{file_id:03d}_DE_time",
                native_sample_rate_hz=48_000 if normal else SAMPLE_RATE,
                sample_rate_hz=SAMPLE_RATE, source_url=source["url"],
                catalog_url=NORMAL_CATALOG if normal else FAULT_CATALOG,
                rate_reference=NORMAL_RATE_REFERENCE if normal else FAULT_CATALOG,
                sha256=source["sha256"],
            )
            signal, native_size, rpm = _load_record(record, root)
            windows, _ = _window(signal)
            record.update(measured_rpm=rpm, native_sample_count=native_size,
                          sample_count=signal.size, window_length=WINDOW, window_stride=WINDOW,
                          window_count=len(windows), discarded_tail_samples=signal.size % WINDOW)
            rows.append(record)
    return rows


def main():
    rows = build_manifest()
    target = ROOT / MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", dir=target.parent, encoding="utf-8",
                           newline="", delete=False) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    Path(stream.name).replace(target)
    print(f"{len(rows)} CWRU records, {sum(row['window_count'] for row in rows)} windows: {target}")


if __name__ == "__main__":
    main()
