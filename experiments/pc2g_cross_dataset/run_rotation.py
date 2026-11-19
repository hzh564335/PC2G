"""Run the frozen HUSTbearing 80 Hz labeled-source rotation."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from . import offline_pilot_diagnostics as pilot
from . import tasks


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pc2g_hust_role_rotation_20261118"
RUNS = ROOT / "runs/pc2g_hust_role_rotation_20261118"
PROTOCOL = OUT / "protocol.json"
STEPS = 5000
MODES = ("raw", "labels_only", "selection_only", "full")
SPEEDS = (20, 35, 65, 80)


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    for attempt in range(60):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 59:
                raise
            time.sleep(0.05)


def rows_for(roles):
    return [
        dict(id=f"hust-t3-L{labeled}-s{seed}-{mode}-B{int(bool(weight))}", dataset="hust",
             target=3, labeled=labeled, seed=seed, mode=mode, B_weight=weight)
        for labeled in roles for seed in range(3) for mode in MODES for weight in (0.0, 0.1)
    ]


def freeze():
    if PROTOCOL.exists():
        return verify()
    old = pilot.read(pilot.OUTPUT / "protocol.json")
    baseline = rows_for((0,))
    if [r for r in old["rows"] if r["dataset"] == "hust"] != baseline:
        raise ValueError("Archived HUST identities differ from the authorized baseline")
    study = tasks.records("hust")
    if [(d, sum(int(r["window_count"]) for r in study if int(r["domain_id"]) == d))
        for d in range(4)] != [(d, 729) for d in range(4)]:
        raise ValueError("Physical-domain pairing expects the original 729 windows per domain")
    code_files = (
        "experiments/pc2g_cross_dataset/run_rotation.py",
        "experiments/pc2g_cross_dataset/rotation_worker.py",
        "experiments/pc2g_cross_dataset/tasks.py",
        "experiments/pc2g_cross_dataset/hust.py",
        "experiments/pc2g_cross_dataset/offline_pilot_diagnostics.py",
        "experiments/pc2g_cross_dataset/run_pilot.py",
        "experiments/pc2g_research_audit/core.py",
        "experiments/da_mechanism_diagnosis/replay_training.py",
        "experiments/msdgn_distribution/train.py",
        "experiments/msdgn_distribution/modules.py",
        "experiments/msdgn_distribution/compatible_model.py",
        "repos/MSDGN/mmd.py",
        "output/pc2g_cross_dataset_stage2/hust_manifest.csv",
    )
    manifest = code_files[-1]
    if pilot.sha(ROOT / manifest) != old["input_sha256"][manifest]:
        raise ValueError("HUST source/target record manifest changed since the pilot")
    source_references = {
        row["id"]: pilot.sha(pilot.RUNS / row["id"] / "source_complete.json") for row in baseline
    }
    protocol = dict(
        created_utc=utc(), scope="HUSTbearing labeled-source role rotation",
        runs_dir=str(RUNS), baseline_runs_dir=str(pilot.RUNS), target=3,
        domains=list(SPEEDS), new_labeled_roles=[1, 2], reused_labeled_role=0,
        seeds=[0, 1, 2], steps=STEPS, checkpoint_rule="fixed_step_5000",
        source_validation_records=0, batch_per_domain=64,
        optimizer="Adam", weight_decay=0.0005,
        lr_rule="0.001 / (1 + 10 * (step - 1) / 5000) ** 0.75",
        profile="paper_objective", prior_queue_length=128,
        consistency_weight_levels=[0.0, 0.1],
        pairing="Same seed initialization. Draw for physical domains 0,1,2, then order the tensors [L,U1,U2]. Perturbation follows the original role-slot RNG.",
        supervision_diagnostics="Offline source truth after full source training; per-domain and per-class counts and nominal CE weight. Actual per-head per-domain training CE recorded for new models only.",
        target_release="New target evaluation after all 48 source models complete and all 72 source traces pass pairing.",
        primary_metrics=["target_accuracy", "target_macro_f1", "target_class_recall", "target_predicted_normal_fraction"],
        within_role_contrasts=["Full−Select", "Label−Raw", "Select−Raw", "Full−Label−Select+Raw"],
        contrasts_condition_on="Report with B off and with B on separately; three paired optimization seeds, descriptive.",
        rows=rows_for((1,2)), baseline_rows=baseline, baseline_source_receipt_sha256=source_references,
        baseline_protocol_sha256=pilot.sha(pilot.OUTPUT / "protocol.json"),
        input_sha256={name: pilot.sha(ROOT / name) for name in code_files},
    )
    save(PROTOCOL, protocol)
    return protocol


def verify():
    protocol = pilot.read(PROTOCOL)
    if protocol["rows"] != rows_for((1,2)) or protocol["baseline_rows"] != rows_for((0,)):
        raise ValueError("Frozen experiment identities differ")
    for name, digest in protocol["input_sha256"].items():
        if pilot.sha(ROOT / name) != digest:
            raise ValueError(f"Frozen input changed: {name}")
    if pilot.sha(pilot.OUTPUT / "protocol.json") != protocol["baseline_protocol_sha256"]:
        raise ValueError("The original pilot protocol changed")
    return protocol


def run_child(action, row, short=False):
    logdir = OUT / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    logpath = logdir / f"{row['id']}-{action}{'-short' if short else ''}.log"
    cmd = [sys.executable, "-B", "-m", "experiments.pc2g_cross_dataset.rotation_worker",
           action, "--protocol", str(PROTOCOL), "--id", row["id"]]
    if short:
        cmd.append("--short")
    with logpath.open("ab") as log:
        start = log.tell()
        outcome = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if outcome.returncode:
        with logpath.open("rb") as log:
            log.seek(start)
            details = log.read().decode("utf-8", errors="replace")
        if ("WinError 5" in details or "WinError 32" in details) and action == "train":
            folder = (OUT / "preflight" if short else RUNS) / row["id"]
            if folder.is_dir():
                archived = OUT / "interrupted_attempts" / f"{folder.name}-{'short' if short else 'full'}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                if not folder.resolve().is_relative_to(ROOT) or not archived.resolve().is_relative_to(OUT):
                    raise ValueError("Interrupted attempt paths outside workspace")
                archived.parent.mkdir(parents=True, exist_ok=True)
                folder.rename(archived)
                save(archived / "interruption.json", dict(utc=utc(), cause="Windows file sharing violation", log=str(logpath)))
            with logpath.open("ab") as log:
                subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        else:
            raise RuntimeError(f"{action} failed for {row['id']}. See {logpath}.\n{details[-2500:]}")


def audit_ce(folder, receipt, trace, role):
    name = "head_ce_by_step.csv"
    if pilot.sha(folder / name) != receipt["artifacts_sha256"][name]:
        raise ValueError(f"Unmatched loss breakdown checksum: {folder}")
    with (folder / name).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if [int(r["step"]) for r in rows] != list(range(1, STEPS+1)):
        raise ValueError(f"Missing loss steps in {folder}")
    sources = [role] + [i for i in range(3) if i != role]
    fields = ("aux_labeled_ce_1", "aux_labeled_ce_2", "main_common_labeled_ce", "main_specific_labeled_ce",
              "main_common_pseudo_ce_u1", "main_common_pseudo_ce_u2",
              "main_specific_pseudo_ce_u1", "main_specific_pseudo_ce_u2", "main_ramp")
    values = np.array([[float(row[k]) for k in fields] for row in rows])
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError(f"Nonfinite or negative cross-entropy in {folder}")
    for row in rows:
        if [int(row[k]) for k in ("labeled_domain", "unlabeled_domain_1", "unlabeled_domain_2")] != sources:
            raise ValueError(f"Loss columns mislabeled in {folder}")
    expected_ramp = 2 / (1 + np.exp(-10 * np.arange(1, STEPS+1) / STEPS)) - 1
    np.testing.assert_allclose(values[:,8], expected_ramp, rtol=2e-6, atol=1e-8)
    if pilot.sha(folder / "loss_history.json") != receipt["artifacts_sha256"]["loss_history.json"]:
        raise ValueError(f"Loss heartbeat file differs from receipt {folder}")
    for snap in pilot.read(folder / "loss_history.json"):
        step = int(snap["step"]) - 1
        v = values[step]
        terms = snap["terms"]
        np.testing.assert_allclose([v[0]+v[1],v[2]+v[4]+v[5],v[3]+v[6]+v[7]],
                                   [terms["aux_ce"],terms["main_ce"],terms["specific_ce"]], rtol=2e-6, atol=1e-8)
        if [int(v) for v in trace["actual_mask"][step].sum(axis=1)] != [terms["selected_1"],terms["selected_2"]]:
            raise ValueError(f"Selected counts differ from source heartbeat in {folder}")
    return len(rows)


def audit_sources(protocol):
    masks = ("raw_mask", "q_mask", "raw_labels", "q_labels")
    groups = {}
    physical_anchors = {}
    manifest = tasks.records("hust")
    total_ce = 0
    for row in protocol["baseline_rows"] + protocol["rows"]:
        role, seed = row["labeled"], row["seed"]
        root = RUNS if role else pilot.RUNS
        folder = root / row["id"]
        if not role and pilot.sha(folder / "source_complete.json") != protocol["baseline_source_receipt_sha256"][row["id"]]:
            raise ValueError(f"Archived source receipt changed: {row['id']}")
        trace, receipt, digest = pilot.load_trace(row, root)
        if receipt["validation_records"] != 0 or receipt["checkpoint_rule"] != "fixed_step_5000":
            raise ValueError(f"Unexpected model selection in {row['id']}")
        if pilot.sha(folder / "last.pt") != receipt["artifacts_sha256"]["last.pt"]:
            raise ValueError(f"Final checkpoint changed for {row['id']}")
        sources = [role] + [d for d in range(3) if d != role]
        record_order = [r["record_id"] for d in sources for r in manifest if int(r["domain_id"]) == d]
        if receipt["source_records"] != record_order:
            raise ValueError(f"Source record ordering differs for {row['id']}")
        physical = np.ascontiguousarray(trace["indices"][:,np.argsort(sources),:], dtype="<i8")
        pair = (hashlib.sha256(physical.tobytes()).hexdigest(), receipt["initial"])
        if role == 0:
            physical_anchors.setdefault(seed,pair)
        if pair != physical_anchors[seed]:
            raise ValueError(f"Physical domain sampling or initialization differs for {row['id']}")
        if role:
            total_ce += audit_ce(folder, receipt, trace, role)
        bon = bool(row["B_weight"])
        if receipt["main_forward_calls"] != STEPS * (2 if bon else 1) or receipt["bn_restorations"] != STEPS * int(bon):
            raise ValueError(f"Invalid B execution count for {row['id']}")
        rng = receipt["final"]["perturb_generator_hash"]
        if not bon and rng != receipt["perturb_initial"]:
            raise ValueError(f"Unexpected perturbation RNG consumption for {row['id']}")
        # Role changes are allowed to change auxiliary training. Only compare both label paths within role.
        group = groups.setdefault((role,seed), dict(rows=0, receipt=receipt, trace=trace, bon_rng=None))
        reference = group["receipt"]
        for field in ("batch_digest", "trajectory_digest", "batch_initial", "perturb_initial"):
            if receipt[field] != reference[field]:
                raise ValueError(f"{field} differs within a paired cell: {row['id']}")
        for field in ("aux_hash", "queue_hash", "batch_generator_hash"):
            if receipt["final"][field] != reference["final"][field]:
                raise ValueError(f"Final {field} differs within role: {row['id']}")
        if any(not np.array_equal(trace[k],group["trace"][k]) for k in masks):
            raise ValueError(f"Unpaired auxiliary predictions for {row['id']}")
        if bon:
            if group["bon_rng"] is not None and rng != group["bon_rng"]:
                raise ValueError(f"Unpaired perturbation RNG for {row['id']}")
            group["bon_rng"] = rng
        group["rows"] += 1
    details = [dict(labeled=role,labeled_hz=SPEEDS[role],seed=seed,runs=g["rows"],
                    physical_batch_sha256=physical_anchors[seed][0],
                    initialization_paired_across_roles=True, physical_samples_paired_across_roles=True,
                    auxiliary_trajectories_paired_within_role=True)
               for (role,seed),g in groups.items()]
    if len(details)!=9 or any(x["runs"]!=8 for x in details) or total_ce != 240000:
        raise ValueError("Full pairing or CE archive incomplete")
    return dict(complete=True,models=48,total_with_baseline=72,baseline_models=24,
                actual_ce_rows=total_ce,checks=details,completed_utc=utc())


def merge_results(protocol, release):
    old = pilot.read(pilot.OUTPUT / "results.json")
    prior = {x["id"]: x for x in old["rows"] if x["dataset"]=="hust"}
    all_results=[]
    target_labels = None
    for row in protocol["baseline_rows"] + protocol["rows"]:
        reused = row["labeled"] == 0
        folder = (pilot.RUNS if reused else RUNS) / row["id"]
        result = prior[row["id"]] if reused else pilot.read(folder / "result.json")
        if any(result[key] != value for key,value in row.items()) or result["checkpoint_step"] != STEPS:
            raise ValueError(f"Wrong target-evaluation identity for {row['id']}")
        pred_file = folder / "target_predictions.npz"
        if pilot.sha(pred_file) != result["prediction_sha256"]:
            raise ValueError(f"Wrong target prediction checksum for {row['id']}")
        with np.load(pred_file, allow_pickle=False) as data:
            y, logits = data["labels"],data["logits"]
        if y.shape != (729,) or logits.shape != (729,9) or not np.isfinite(logits).all():
            raise ValueError(f"Invalid target logits or labels for {row['id']}")
        if np.bincount(y, minlength=9).tolist() != [81]*9:
            raise ValueError(f"Wrong target class support for {row['id']}")
        if target_labels is None:
            target_labels = y.copy()
        elif not np.array_equal(y, target_labels):
            raise ValueError(f"Target label order differs for {row['id']}")
        if not reused and datetime.fromisoformat(result["evaluated_utc"]) <= datetime.fromisoformat(release["completed_utc"]):
            raise ValueError(f"Target evaluated before the source release: {row['id']}")
        source_receipt = pilot.read(folder / "source_complete.json")
        if result["checkpoint_sha256"] != source_receipt["artifacts_sha256"]["last.pt"]:
            raise ValueError(f"Target result tied to a different checkpoint: {row['id']}")
        cm=np.bincount(9*y+logits.argmax(axis=1), minlength=81).reshape(9,9)
        if cm.tolist()!=result["metrics"]["confusion_matrix"]:
            raise ValueError(f"Wrong target confusion matrix for {row['id']}")
        all_results.append(dict(result,reused=reused,run_dir=str(folder)))
    return dict(complete=True,scope="HUSTbearing labeled-source role rotation",rows=all_results)


def status(stage, **extra):
    save(OUT / "status.json", dict(stage=stage, planned_new=48, baseline=24, updated_utc=utc(), **extra))


def controller():
    protocol = freeze()
    rows = protocol["rows"]
    status("preflight")
    preflight = []
    for row in (r for r in rows if r["seed"]==0):
        receipt = OUT / "preflight" / row["id"] / "short_complete.json"
        if not receipt.is_file():
            run_child("train", row, short=True)
        check = pilot.read(receipt)
        if (any(check[key] != value for key, value in row.items()) or check["updates"] != 8
                or not check["observational_equivalence"] or check["head_ce_rows"] != 8):
            raise ValueError(f"Loss observation preflight failed: {row['id']}")
        preflight.append(check)
    for role in (1,2):
        paired = [r for r in preflight if r["labeled"] == role]
        if len(paired) != 8 or any(any(r[k] != paired[0][k] for k in ("initial","batch_digest","trajectory_digest"))
                                   for r in paired):
            raise ValueError(f"Short-run pairing differed for role {role}")
    save(OUT/"preflight_complete.json",dict(complete=True,source_runs=16,updates=8,
                                            observational_equivalence=True,checks=preflight))
    for i,row in enumerate(rows):
        folder = RUNS / row["id"]
        if not (folder / "source_complete.json").is_file():
            if folder.exists():
                raise ValueError(f"Inspect existing incomplete training folder {folder}")
            status("source_training",complete_new=i,current=row["id"])
            run_child("train", row)
    verify()
    audit = audit_sources(protocol)
    audit["protocol_sha256"] = pilot.sha(PROTOCOL)
    gate = OUT / "all_sources_complete.json"
    if gate.exists():
        previous = pilot.read(gate)
        audit["completed_utc"] = previous["completed_utc"]
        if previous != audit:
            raise ValueError("Previously released source audit differs from the checked archive")
    save(OUT / "source_pairing_audit.json",audit)
    if not gate.exists():
        save(gate,audit)
    for i,row in enumerate(rows):
        if not (RUNS / row["id"] / "result.json").is_file():
            status("target_evaluation",complete_new=48,evaluated_new=i,current=row["id"])
            run_child("evaluate",row)
    status("analysis",complete_new=48,evaluated_new=48)
    save(OUT / "results.json",merge_results(protocol, audit))
    for module in ("pseudo_rotation","report_rotation"):
        with (OUT/f"{module}.log").open("ab") as log:
            subprocess.run([sys.executable,"-B","-m",f"experiments.pc2g_cross_dataset.{module}"],
                           cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    status("complete",complete_new=48,evaluated_new=48,total_models=72)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",choices=("freeze","controller"))
    args=parser.parse_args()
    if args.step == "freeze":
        freeze()
    else:
        try:
            controller()
        except Exception as exc:
            save(OUT/"failure.json",dict(error=repr(exc),utc=utc()))
            raise
