"""Run the two authorized 24-model PC2G fixed-step pilots."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch

from experiments.pc2g_research_audit import core
from . import tasks


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pc2g_cross_dataset_pilot_20261117"
RUNS = ROOT / "runs/pc2g_cross_dataset_pilot_20261117"
MODES = ("raw", "labels_only", "selection_only", "full")
STEPS = 5000


def retry_file_operation(operation):
    for attempt in range(60):
        try:
            return operation()
        except PermissionError:
            if attempt == 59:
                raise
            time.sleep(0.05)


def enable_file_retries():
    original = core.atomic_json

    def atomic_json(path, value):
        return retry_file_operation(lambda: original(path, value))

    core.atomic_json = atomic_json


def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    retry_file_operation(lambda: temporary.replace(path))


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def entries():
    rows = []
    for dataset in ("cwru", "hust"):
        for seed in range(3):
            for mode in MODES:
                for weight in (0.0, 0.1):
                    name = f"{dataset}-t3-L0-s{seed}-{mode}-B{int(bool(weight))}"
                    rows.append(dict(id=name, dataset=dataset, target=3, labeled=0,
                                     seed=seed, mode=mode, B_weight=weight))
    return rows


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "protocol.json"
    if path.exists():
        verify()
        return
    rows = entries()
    code = [Path(__file__), Path(tasks.__file__), Path(tasks.cwru.__file__), Path(tasks.hust.__file__),
            Path(core.__file__), Path(core.replay.__file__), Path(core.base.__file__),
            ROOT / "experiments/msdgn_distribution/modules.py",
            ROOT / "experiments/msdgn_distribution/compatible_model.py", ROOT / "repos/MSDGN/mmd.py"]
    files = code + [tasks.OUTPUT / f"{ds}_manifest.csv" for ds in ("cwru", "hust")]
    protocol = dict(created_utc=now(), authorized="Both datasets, fixed step 5000, 24 models each",
                    checkpoint_rule="fixed_step_5000", validation_records=0,
                    scope="one target and one labeled-source role per dataset; implementation and empirical pilot",
                    target_domain_choice="domain 3, labeled domain 0 in both datasets, ascending domain numbering",
                    target_choice_reason="predefined highest-index domain, with lowest-index labeled source, before new target evaluation",
                    domains={"cwru": [0, 1, 2, 3], "hust": [20, 35, 65, 80]},
                    classes={"cwru": 4, "hust": 9}, seeds=[0,1,2], steps=STEPS,
                    batch_per_domain=64, optimizer="persistent Adam", initial_lr=0.001,
                    lr_rule="0.001 / (1 + 10 * (step - 1) / 5000) ** 0.75",
                    weight_decay=0.0005, ratio=0.6, alignment_window=128,
                    profile="paper_objective", fixed_B_weight=0.1,
                    primary_endpoint="clean target Accuracy", secondary_endpoint="clean Macro-F1 and per-class recall",
                    evaluation_release="after all 48 source models complete and pairing checks pass",
                    historical_target_results_known=True, rows=rows,
                    input_sha256={str(p.relative_to(ROOT).as_posix()): sha(p) for p in files})
    write(path, protocol)


def verify():
    protocol = read(OUT / "protocol.json")
    if protocol["rows"] != entries():
        raise ValueError("Pilot entries differ from frozen protocol")
    for name, digest in protocol["input_sha256"].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f"Frozen input changed: {name}")
    return protocol


def configure(row, output):
    values = dict(core.FIXED, distribution_alignment=True, consistency_weight=row["B_weight"],
                  data=tasks.OUTPUT / f"{row['dataset']}_manifest.csv", output=output,
                  sources=[0,1,2], target=3, labeled=0, seed=row["seed"], device="cuda",
                  allow_cpu=False, audit_mode=row["mode"], audit_coverage="all",
                  audit_save_logits=row["mode"] == "raw" and row["B_weight"] == 0)
    return values


def train(row, short=False):
    verify()
    enable_file_retries()
    folder = OUT / "preflight" / row["id"] if short else RUNS / row["id"]
    folder.mkdir(parents=True, exist_ok=False)
    cfg = configure(row, folder)
    random.seed(row["seed"])
    np.random.seed(row["seed"])
    torch.manual_seed(row["seed"])
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the frozen pilot")
    source_data = tasks.load_training_domains(row["dataset"], 3, 0)
    training = []
    source_records = []
    for domain, signals, labels in source_data:
        x = core.base.normalize(torch.from_numpy(signals).cuda())
        y = torch.from_numpy(labels).cuda() if labels is not None else torch.full((len(x),), -1, dtype=torch.long, device="cuda")
        training.append((x, y))
        source_records.extend(r["record_id"] for r in tasks.records(row["dataset"]) if int(r["domain_id"]) == domain)
    args = SimpleNamespace(**cfg)
    classes = len(torch.unique(training[0][1]))
    if classes != {"cwru":4,"hust":9}[row["dataset"]]:
        raise ValueError("Source class coverage differs from frozen protocol")
    recorder = core.AuditRecorder(cfg, limit=STEPS, mode=row["mode"], coverage="all", record_trace=True)
    model = recorder.factory(args, classes).cuda()
    for aligner in model.pseudo_alignment:
        aligner.set_labeled_prior(training[0][1])
    groups = [dict(params=list(model.sharedNet1.parameters()) + list(model.sharedNet2.parameters()) +
                         list(model.sharedNet3.parameters()), scale=1.0),
              dict(params=list(model.cls_fc1.parameters()) + list(model.cls_fc2.parameters()), scale=1.0)]
    optimizer = recorder.torch_proxy().optim.Adam(groups, lr=0.001, weight_decay=0.0005)
    batch_rng = torch.Generator(device="cuda").manual_seed(row["seed"] + 101)
    perturb_rng = torch.Generator(device="cuda").manual_seed(row["seed"] + 202)
    write(folder / "config.json", dict(row, fixed=core.FIXED, selected_step=STEPS,
          checkpoint_rule="fixed_step_5000", classes=classes,
          source_counts=[len(x) for x,_ in training], source_records=source_records,
          torch_version=str(torch.__version__), gpu=torch.cuda.get_device_name(),
          target_arrays_loaded=False, validation_records=0))
    started = time.perf_counter()
    try:
        for step in range(1, 9 if short else STEPS+1):
            model.train()
            rate = 0.001 / (1 + 10 * (step - 1) / STEPS) ** 0.75
            for group in optimizer.param_groups:
                group["lr"] = rate
            batches = []
            for x,y in training:
                idx = recorder.randint(len(x), (64,), device="cuda", generator=batch_rng)
                batches.append((x[idx], y[idx]))
            optimizer.zero_grad(set_to_none=True)
            loss, terms, buffers = recorder.loss(model, batches, args, step / STEPS, perturb_rng)
            loss.backward()
            if buffers is not None:
                with torch.no_grad():
                    for name, buffer in model.sharedNet3.named_buffers():
                        buffer.copy_(buffers[name])
            optimizer.step()
            if step == 1 or step % 250 == 0:
                print(json.dumps(dict(id=row["id"], step=step, loss=float(loss.detach()),
                                     elapsed_seconds=time.perf_counter()-started)), flush=True)
        seconds = time.perf_counter()-started
        if short:
            hashes = core.model_hashes(model)
            result = dict(id=row["id"], complete=True, short_check=True, updates=8,
                          final=hashes, batch_digest=recorder.batch_hasher.hexdigest(),
                          trajectory_digest=recorder.trajectory_hasher.hexdigest(),
                          main_forward_calls=recorder.main_forward_calls,
                          bn_restorations=recorder.bn_restorations_checked)
            write(folder / "short_complete.json", result)
            return
        if recorder.completed != STEPS or recorder.trace_steps != STEPS or recorder.final is None:
            raise RuntimeError("Incomplete source training")
        checkpoint = folder / "last.pt"
        torch.save(dict(state_dict=model.state_dict(), step=STEPS, config=read(folder / "config.json")), checkpoint)
        np.savez_compressed(folder / "training_predictions.npz", **{
            key:np.stack([frame[key] for frame in recorder.payload]) for key in recorder.payload[0]})
        write(folder / "loss_history.json", recorder.heartbeats)
        receipt = dict(row, complete=True, actual_updates=STEPS, checkpoint_step=STEPS,
                       completed_utc=now(), training_seconds=seconds, checkpoint_rule="fixed_step_5000",
                       target_arrays_loaded=False, unlabeled_truth_used=False, validation_records=0,
                       source_records=source_records, initial=recorder.initial, final=recorder.final,
                       batch_initial=recorder.batch_initial_hash, perturb_initial=recorder.perturb_initial_hash,
                       batch_digest=recorder.batch_hasher.hexdigest(),
                       trajectory_digest=recorder.trajectory_hasher.hexdigest(),
                       main_forward_calls=recorder.main_forward_calls, bn_restorations=recorder.bn_restorations_checked,
                       artifacts_sha256={name:sha(folder/name) for name in
                                         ("last.pt","training_predictions.npz","loss_history.json","config.json")})
        write(folder / "source_complete.json", receipt)
    finally:
        recorder.close()


def check_pairs(short=False):
    keys = ("aux_hash","base_aux_hash","queue_hash","main_hash")
    checks = []
    for ds in ("cwru", "hust"):
        for seed in (range(1) if short else range(3)):
            selected = [r for r in entries() if r["dataset"] == ds and r["seed"] == seed]
            receipts = [read((OUT / "preflight" if short else RUNS) / r["id"] /
                             ("short_complete.json" if short else "source_complete.json")) for r in selected]
            if not all(all(r[k]==receipts[0][k] for k in ("batch_digest","trajectory_digest")) for r in receipts):
                raise RuntimeError(f"Source trajectories not paired for {ds} seed {seed}")
            for r in receipts:
                for key in keys:
                    if not short and r["initial"][key] != receipts[0]["initial"][key]:
                        raise RuntimeError("Initialization differs between paired models")
                for key in ("aux_hash","base_aux_hash","queue_hash"):
                    if r["final"][key] != receipts[0]["final"][key]:
                        raise RuntimeError("Auxiliary states differ between paired models")
                bon = int("-B1" in r["id"])
                n = 8 if short else STEPS
                if r["main_forward_calls"] != n*(1+bon) or r["bn_restorations"] != n*bon:
                    raise RuntimeError("Forward or BN restore counts differ from protocol")
            checks.append(dict(dataset=ds,seed=seed,paired_models=len(receipts),
                               batch_and_aux_trajectory_equal=True,auxiliary_and_queue_endpoints_equal=True))
    return checks


def evaluate(row):
    verify()
    folder = RUNS / row["id"]
    receipt = read(folder / "source_complete.json")
    path = folder / "last.pt"
    if sha(path) != receipt["artifacts_sha256"]["last.pt"]:
        raise RuntimeError("Final checkpoint changed")
    cp = torch.load(path, map_location="cuda", weights_only=False)
    if cp["step"] != STEPS or cp["config"]["id"] != row["id"]:
        raise RuntimeError("Incorrect checkpoint identity or step")
    cfg = configure(row, folder)
    model = core.base.make_model(SimpleNamespace(**cfg), cp["config"]["classes"]).cuda()
    model.load_state_dict(cp["state_dict"], strict=True)
    signals, labels = tasks.load_test_domain(row["dataset"], 3)
    metrics, logits = core.base.evaluate(model, torch.from_numpy(signals), torch.from_numpy(labels),
                                          "msdgn", torch.device("cuda"))
    np.savez_compressed(folder / "target_predictions.npz", logits=logits.numpy(), labels=labels)
    result = dict(row, metrics=metrics, checkpoint_step=STEPS, checkpoint_sha256=sha(path),
                  training_seconds=receipt["training_seconds"], evaluated_utc=now(),
                  prediction_sha256=sha(folder/"target_predictions.npz"))
    write(folder / "result.json", result)
    return result


def child(action, row, short=False):
    command = [sys.executable,"-B","-m","experiments.pc2g_cross_dataset.run_pilot",action,"--id",row["id"]]
    if short:
        command.append("--short")
    logdir = OUT / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    with (logdir / f"{row['id']}-{'short' if short else action}.log").open("a",encoding="utf-8") as log:
        subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)


def controller():
    freeze()
    rows = entries()
    write(OUT/"status.json",dict(stage="preflight",pid=os.getpid(),started_utc=now(),planned=48))
    if not (OUT/"preflight_complete.json").exists():
        for row in [r for r in rows if r["seed"]==0]:
            if not (OUT/"preflight"/row["id"]/"short_complete.json").exists():
                child("train",row,short=True)
        write(OUT/"preflight_complete.json",dict(complete=True,checks=check_pairs(short=True),target_evaluated=False))
    for index,row in enumerate(rows):
        receipt = RUNS/row["id"]/"source_complete.json"
        if not receipt.exists():
            if (RUNS/row["id"]).exists():
                raise RuntimeError(f"Incomplete existing run needs explicit diagnosis: {row['id']}")
            write(OUT/"status.json",dict(stage="source_training",current=row["id"],completed=index,planned=48,
                                        pid=os.getpid(),updated_utc=now()))
            child("train",row)
        verify()
    checks = check_pairs()
    write(OUT/"all_sources_complete.json",dict(complete=True,checks=checks,models=48,completed_utc=now()))
    results=[]
    for row in rows:
        write(OUT/"status.json",dict(stage="final_evaluation",current=row["id"],completed=len(results),planned=48,
                                    pid=os.getpid(),updated_utc=now()))
        path=RUNS/row["id"]/"result.json"
        if not path.exists():
            child("evaluate",row)
        results.append(read(path))
    write(OUT/"results.json",dict(complete=True,scope="pilot",rows=results))
    subprocess.run([sys.executable,"-B","-m","experiments.pc2g_cross_dataset.report_pilot"],cwd=ROOT,check=True)
    write(OUT/"status.json",dict(stage="complete",completed=48,planned=48,pid=None,completed_utc=now()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("freeze","controller","train","evaluate"))
    parser.add_argument("--id")
    parser.add_argument("--short",action="store_true")
    args=parser.parse_args()
    if args.action=="freeze":
        freeze()
    elif args.action=="controller":
        try:
            controller()
        except Exception as exc:
            write(OUT/"failure.json",dict(error=repr(exc),utc=now()))
            raise
    else:
        row=next(r for r in entries() if r["id"]==args.id)
        train(row,args.short) if args.action=="train" else evaluate(row)


if __name__=="__main__":
    main()
