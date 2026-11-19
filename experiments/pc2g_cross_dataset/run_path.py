"""Run the approved HUSTbearing 65 Hz two-path intervention."""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import subprocess
import sys

import numpy as np

from . import offline_pilot_diagnostics as archive
from . import tasks
from .run_rotation import save, utc


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pc2g_hust_65hz_path_20261119"
RUNS = ROOT / "runs/pc2g_hust_65hz_path_20261119"
PREREG = ROOT / "output/pc2g_hust_65hz_path_preregistration_20261119/HUST_65Hz_supervision_path_preregistration.md"
PROTOCOL = OUT / "protocol.json"
STEPS = 5000
ARM_SWITCHES = {"A": (True, True), "B": (False, True), "C": (True, False), "D": (False, False)}


def rows_for(arms):
    rows = []
    for arm in arms:
        ce, consistency = ARM_SWITCHES[arm]
        for seed in range(3):
            identifier = f"hust-t3-L0-s{seed}-" + ("full-B1" if arm == "A" else f"path-{arm}")
            rows.append(dict(id=identifier, arm=arm, dataset="hust", target=3, labeled=0, seed=seed,
                             mode="full", B_weight=0.1, ce65=ce, cons65=consistency))
    return rows


def verify():
    protocol = archive.read(PROTOCOL)
    if protocol["rows"] != rows_for("BCD") or protocol["baseline_rows"] != rows_for("A"):
        raise ValueError("Frozen path-intervention rows changed")
    for name, fingerprint in protocol["input_sha256"].items():
        if archive.sha(ROOT / name) != fingerprint:
            raise ValueError(f"Frozen input changed: {name}")
    return protocol


def freeze():
    if PROTOCOL.exists():
        return verify()
    old = archive.read(archive.OUTPUT / "protocol.json")
    paths = list(old["input_sha256"]) + [
        "experiments/pc2g_cross_dataset/rotation_worker.py",
        "experiments/pc2g_cross_dataset/run_rotation.py",
        "experiments/pc2g_cross_dataset/run_path.py",
        "experiments/pc2g_cross_dataset/path_worker.py",
        PREREG.relative_to(ROOT).as_posix(),
        (archive.OUTPUT / "protocol.json").relative_to(ROOT).as_posix(),
    ]
    for name, fingerprint in old["input_sha256"].items():
        if archive.sha(ROOT / name) != fingerprint:
            raise ValueError(f"Archived training input changed: {name}")
    fingerprints = {}
    for r in rows_for("A"):
        folder = archive.RUNS / r["id"]
        receipt = archive.read(folder / "source_complete.json")
        if receipt["actual_updates"] != STEPS or receipt["checkpoint_rule"] != "fixed_step_5000":
            raise ValueError(f"Invalid reference checkpoint: {r['id']}")
        files = {name: digest for name, digest in receipt["artifacts_sha256"].items()}
        for name, digest in files.items():
            if archive.sha(folder / name) != digest:
                raise ValueError(f"Archived A artifact changed: {r['id']}/{name}")
        fingerprints[r["id"]] = archive.sha(folder / "source_complete.json")
    protocol = dict(
        created_utc=utc(), scope="HUSTbearing 65 Hz supervision-path intervention",
        runs_dir=str(RUNS), baseline_runs_dir=str(archive.RUNS), target=3,
        labeled_hz=20, unlabeled_hz=[35,65], target_hz=80,
        seeds=[0,1,2], steps=STEPS, checkpoint_rule="fixed_step_5000", validation_records=0,
        baseline_target_results_known=True, budget_full_training=9, budget_short_optimizer_updates=120,
        short_updates_per_seed=40, batch_per_domain=64,
        consistency_denominator=192,
        ce_rule="65 Hz unlabeled CE gate in both main heads; original per-domain selection denominators",
        consistency_rule="Gate only direct 65 Hz distances before mean over all 192 positions",
        main_forward="All 192 signals in both forward passes, unchanged BN restoration and perturbation RNG",
        target_release="After all nine new source models and all twelve paired source archives are verified",
        comparisons=["B−A", "D−C", "C−A", "D−B", "(D−C)−(B−A)", "D−A"],
        primary="B−A 80 Hz Accuracy, same-seed descriptive paired contrasts",
        preregistration=str(PREREG), rows=rows_for("BCD"), baseline_rows=rows_for("A"),
        baseline_source_receipt_sha256=fingerprints,
        input_sha256={name:archive.sha(ROOT/name) for name in sorted(set(paths))},
    )
    save(PROTOCOL,protocol)
    return protocol


def status(stage, **fields):
    save(OUT / "status.json",dict(stage=stage,planned_new=9,baseline=3,updated_utc=utc(),**fields))


def child(action, *, row=None, seed=None):
    if seed is not None:
        label, identity = f"seed{seed}", ["--seed",str(seed)]
    else:
        label, identity = row["id"], ["--id",row["id"]]
    logs = OUT / "logs"
    logs.mkdir(parents=True,exist_ok=True)
    with (logs/f"{label}-{action}.log").open("ab") as stream:
        subprocess.run([sys.executable,"-B","-m","experiments.pc2g_cross_dataset.path_worker",
                        action,"--protocol",str(PROTOCOL),*identity],cwd=ROOT,
                       stdout=stream,stderr=subprocess.STDOUT,check=True)


def audit_preflight():
    checks = []
    for seed in range(3):
        folder = OUT/"preflight"/f"seed{seed}"
        path = folder/"preflight_complete.json"
        if not path.is_file():
            if folder.exists():
                raise ValueError(f"Incomplete short check needs diagnosis before spending further updates: {folder}")
            status("preflight",seed=seed)
            child("preflight",seed=seed)
        row = archive.read(path)
        if (row["seed"] != seed or not row["complete"] or row["updates"] != 40
            or not row["a_equivalence_exact"] or not row["direct_gate_checks"]
            or row["target_arrays_loaded"] or row["fixed_consistency_denominator"]!=192
            or row["arm_updates"] != {a:8 for a in ("reference_A","A","B","C","D")}):
            raise ValueError(f"Short check did not establish A and path equivalence: seed {seed}")
        checks.append(row)
    save(OUT/"preflight_complete.json",dict(complete=True,optimizer_updates=120,
                                             a_equivalence_exact=True,checks=checks))


def audit_losses(folder,row,receipt,trace):
    name="head_ce_by_step.csv"
    if archive.sha(folder/name)!=receipt["artifacts_sha256"][name]:
        raise ValueError(f"Loss trace digest mismatch: {row['id']}")
    with (folder/name).open(encoding="utf-8-sig",newline="") as stream:
        records=list(csv.DictReader(stream))
    if [int(x["step"]) for x in records]!=list(range(1,STEPS+1)):
        raise ValueError(f"Loss timeline incomplete: {row['id']}")

    def column(key):
        values=np.asarray([float(r[key]) for r in records])
        if not np.isfinite(values).all() or (values<0).any():
            raise ValueError(f"Invalid loss field {key}: {row['id']}")
        return values

    ce, cons=row["ce65"],row["cons65"]
    for name,value in (("ce65",ce),("cons65",cons),("consistency_denominator",192),
                       ("labeled_domain",0),("unlabeled_domain_1",1),("unlabeled_domain_2",2)):
        if not (column(name)==value).all():
            raise ValueError(f"Loss field {name} unexpectedly changes: {row['id']}")
    for head in ("main_common_pseudo_ce_u2","main_specific_pseudo_ce_u2"):
        np.testing.assert_array_equal(column(head),column(head+"_raw")*ce)
    per_domain = []
    for hz in (20,35,65):
        actual=column(f"consistency_effective_{hz}")
        expected=column(f"consistency_distance_sum_{hz}")/192*(cons if hz==65 else 1)
        np.testing.assert_allclose(actual,expected,rtol=2e-6,atol=1e-8)
        per_domain.append(actual)
    np.testing.assert_allclose(column("consistency_total_effective"),sum(per_domain),rtol=2e-6,atol=1e-8)
    if archive.sha(folder/"loss_history.json")!=receipt["artifacts_sha256"]["loss_history.json"]:
        raise ValueError(f"Loss snapshot digest mismatch: {row['id']}")
    history=archive.read(folder/"loss_history.json")
    if [s["step"] for s in history]!=[1,*range(250,STEPS+1,250)]:
        raise ValueError(f"Wrong loss heartbeat schedule: {row['id']}")
    for snapshot in history:
        step=int(snapshot["step"])-1
        at=records[step]
        terms=snapshot["terms"]
        np.testing.assert_allclose(float(at["consistency_total_effective"]),terms["consistency"],rtol=2e-6,atol=1e-8)
        if trace["actual_mask"][step].sum(axis=1).tolist()!=[terms["selected_1"],terms["selected_2"]]:
            raise ValueError(f"Selected counts differ: {row['id']}")
    return len(records)


def audit_sources(protocol):
    anchors={}
    checked=[]
    total=0
    records=[x["record_id"] for d in (0,1,2) for x in tasks.records("hust") if int(x["domain_id"])==d]
    for row in protocol["baseline_rows"]+protocol["rows"]:
        reused=row["arm"]=="A"
        root=archive.RUNS if reused else RUNS
        folder=root/row["id"]
        if reused and archive.sha(folder/"source_complete.json")!=protocol["baseline_source_receipt_sha256"][row["id"]]:
            raise ValueError(f"Archived source receipt differs: {row['id']}")
        trace,receipt,_=archive.load_trace(row,root)
        if not reused and any(receipt[k]!=row[k] for k in ("arm","ce65","cons65")):
            raise ValueError(f"Source receipt records a different intervention: {row['id']}")
        if receipt["validation_records"]!=0 or receipt["checkpoint_rule"]!="fixed_step_5000":
            raise ValueError(f"Unexpected model selection: {row['id']}")
        if (receipt["source_records"]!=records or receipt["main_forward_calls"]!=10000
            or receipt["bn_restorations"]!=5000):
            raise ValueError(f"Invalid source records, forward count, or BN count: {row['id']}")
        if archive.sha(folder/"last.pt")!=receipt["artifacts_sha256"]["last.pt"]:
            raise ValueError(f"Saved checkpoint digest mismatch: {row['id']}")
        if reused:
            anchors[row["seed"]]=(trace,receipt)
        original,reference=anchors[row["seed"]]
        for field in archive.TRACE_FIELDS+("actual_mask","actual_labels"):
            if not np.array_equal(original[field],trace[field]):
                raise ValueError(f"Prediction or batch path mismatch at {field}: {row['id']}")
        for field in ("initial","batch_initial","batch_digest","trajectory_digest","perturb_initial"):
            if receipt[field]!=reference[field]:
                raise ValueError(f"Pairing mismatch at {field}: {row['id']}")
        for field in ("aux_hash","queue_hash","batch_generator_hash","perturb_generator_hash"):
            if receipt["final"][field]!=reference["final"][field]:
                raise ValueError(f"Final auxiliary state or RNG mismatch at {field}: {row['id']}")
        count=0 if reused else audit_losses(folder,row,receipt,trace)
        total+=count
        checked.append(dict(id=row["id"],arm=row["arm"],seed=row["seed"],reused=reused,
                            paired_source_trace=True,complete_updates=STEPS,split_loss_rows=count))
    if len(checked)!=12 or total!=45000:
        raise ValueError("Wrong number of source checkpoints or split loss rows")
    return dict(complete=True,models=9,total_with_baseline=12,actual_ce_rows=total,
                short_optimizer_updates=120,protocol_sha256=archive.sha(PROTOCOL),
                checks=checked,completed_utc=utc())


def merge_results(protocol, release):
    reference_y=None
    merged=[]
    for row in protocol["baseline_rows"]+protocol["rows"]:
        reused=row["arm"]=="A"
        folder=(archive.RUNS if reused else RUNS)/row["id"]
        result=archive.read(folder/"result.json")
        expected={k:v for k,v in row.items() if not reused or k not in ("arm","ce65","cons65")}
        if any(result[k]!=v for k,v in expected.items()) or result["checkpoint_step"]!=STEPS:
            raise ValueError(f"Wrong target-archive identity: {row['id']}")
        if not reused and datetime.fromisoformat(result["evaluated_utc"])<=datetime.fromisoformat(release["completed_utc"]):
            raise ValueError(f"Target evaluation occurred before release: {row['id']}")
        if result["checkpoint_sha256"]!=archive.read(folder/"source_complete.json")["artifacts_sha256"]["last.pt"]:
            raise ValueError(f"Target result tied to wrong checkpoint: {row['id']}")
        path=folder/"target_predictions.npz"
        if archive.sha(path)!=result["prediction_sha256"]:
            raise ValueError(f"Saved prediction digest mismatch: {row['id']}")
        with np.load(path,allow_pickle=False) as source:
            y,logits=source["labels"],source["logits"]
        if y.shape!=(729,) or logits.shape!=(729,9) or not np.isfinite(logits).all():
            raise ValueError(f"Unexpected target data shape or logits: {row['id']}")
        if np.bincount(y,minlength=9).tolist()!=[81]*9:
            raise ValueError(f"Unexpected target class support: {row['id']}")
        if reference_y is None:
            reference_y=y.copy()
        elif not np.array_equal(reference_y,y):
            raise ValueError(f"Target row order differs: {row['id']}")
        cm=np.bincount(9*y+logits.argmax(axis=1),minlength=81).reshape(9,9)
        if cm.tolist()!=result["metrics"]["confusion_matrix"]:
            raise ValueError(f"Target confusion matrix mismatch: {row['id']}")
        merged.append({**result,**row,"run_dir":str(folder),"reused":reused})
    return dict(complete=True,scope="65 Hz supervision-path intervention",rows=merged)


def controller():
    protocol=freeze()
    audit_preflight()
    for i,row in enumerate(protocol["rows"]):
        folder=RUNS/row["id"]
        if not (folder/"source_complete.json").is_file():
            if folder.exists():
                raise ValueError(f"Inspect incomplete run before continuing: {folder}")
            status("source_training",complete_new=i,current=row["id"])
            child("train",row=row)
    verify()
    status("source_audit",complete_new=9)
    audit=audit_sources(protocol)
    gate=OUT/"all_sources_complete.json"
    if gate.exists():
        old=archive.read(gate)
        audit["completed_utc"]=old["completed_utc"]
        if audit!=old:
            raise ValueError("Released source set differs from the verified archive")
    else:
        save(gate,audit)
    save(OUT/"source_pairing_audit.json",audit)
    for i,row in enumerate(protocol["rows"]):
        if not (RUNS/row["id"]/"result.json").is_file():
            status("target_evaluation",complete_new=9,evaluated_new=i,current=row["id"])
            child("evaluate",row=row)
    status("analysis",complete_new=9,evaluated_new=9)
    save(OUT/"results.json",merge_results(protocol,audit))
    for name in ("source_path","report_path"):
        with (OUT/f"{name}.log").open("ab") as stream:
            subprocess.run([sys.executable,"-B","-m",f"experiments.pc2g_cross_dataset.{name}"],
                           cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    status("complete",complete_new=9,evaluated_new=9,total_models=12)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",choices=("freeze","controller"))
    args=parser.parse_args()
    if args.step=="freeze":
        freeze()
    else:
        try:
            controller()
        except Exception as exc:
            save(OUT/"failure.json",dict(error=repr(exc),utc=utc()))
            raise
