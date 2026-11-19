"""Fixed-step training and evaluation worker for the HUST source-role rotation."""
import argparse
import csv
import math
import os
from pathlib import Path
import random
import time
from types import SimpleNamespace

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch

from experiments.pc2g_research_audit import core
from . import run_pilot as pilot
from . import tasks


ROOT = Path(__file__).resolve().parents[2]
STEPS = pilot.STEPS
SHORT_STEPS = 8
HEAD_NAMES = (
    "aux_labeled_ce_1", "aux_labeled_ce_2",
    "main_common_labeled_ce", "main_specific_labeled_ce",
    "main_common_pseudo_ce_u1", "main_common_pseudo_ce_u2",
    "main_specific_pseudo_ce_u1", "main_specific_pseudo_ce_u2",
)
HEAD_COLUMNS = (
    "step", "labeled_domain", "unlabeled_domain_1", "unlabeled_domain_2",
    *HEAD_NAMES, "main_ramp",
)


class ObserveFunctional:
    """Return the original CE result and keep its detached scalar."""

    def __init__(self, previous):
        self.previous = previous
        self.observed = []

    def cross_entropy(self, *args, **kwargs):
        value = self.previous.cross_entropy(*args, **kwargs)
        self.observed.append(value.detach())
        return value

    def __getattr__(self, name):
        return getattr(self.previous, name)


class HeadLossRecorder(core.AuditRecorder):
    """Observe terms in a private clone of the actual frozen loss function."""

    def __init__(self, config, mode, **kwargs):
        super().__init__(config, limit=STEPS, mode=mode, coverage="all", **kwargs)
        self.functional = ObserveFunctional(core.base.F)
        self.original_loss = core.clone_function(self.original_loss, {"F": self.functional})
        self.unlabeled = []
        self.head_terms = []

    def ce_nonempty(self, logits, labels):
        value = super().ce_nonempty(logits, labels)
        self.unlabeled.append(value.detach())
        return value

    def loss(self, model, batches, args, progress, perturb_rng=None):
        self.functional.observed.clear()
        self.unlabeled.clear()
        total, terms, buffers = super().loss(model, batches, args, progress, perturb_rng)
        labeled = self.functional.observed
        pseudo = self.unlabeled
        if (len(labeled), len(pseudo)) != (4, 4):
            raise RuntimeError("Unexpected classified loss term count")
        combined = [terms[key].detach() for key in ("aux_ce", "main_ce", "specific_ce")]
        values = torch.stack([*labeled, *pseudo, *combined]).cpu().numpy()
        aux1, aux2, common_l, specific_l, common_u1, common_u2, specific_u1, specific_u2 = values[:8]
        expected = [aux1 + aux2, (common_l + common_u1) + common_u2, (specific_l + specific_u1) + specific_u2]
        if not np.array_equal(expected, values[8:]):
            raise RuntimeError("Captured classifier terms do not reconstruct the original loss")
        self.head_terms.append([self.completed + 1, *self.config["sources"],
                                *map(float, values[:8]), 2 / (1 + math.exp(-10 * progress)) - 1])
        return total, terms, buffers


def validate_row(row):
    if (
        row["dataset"] != "hust"
        or row["target"] != 3
        or row["labeled"] not in (1, 2)
        or row["seed"] not in (0, 1, 2)
        or row["mode"] not in pilot.MODES
        or row["B_weight"] not in (0.0, 0.1)
    ):
        raise ValueError(f"Unexpected role-rotation cell: {row}")
    run_id = f"hust-t3-L{row['labeled']}-s{row['seed']}-{row['mode']}-B{int(bool(row['B_weight']))}"
    if row["id"] != run_id:
        raise ValueError(f"The run ID must encode the frozen role, seed, mode, and B: {run_id}")


def read_protocol(path):
    protocol = pilot.read(path)
    rows = protocol["rows"]
    if len(rows) != 48 or len({row["id"] for row in rows}) != 48:
        raise ValueError("The frozen rotation requires 48 unique new cells")
    for row in rows:
        validate_row(row)
    for file_name, checksum in protocol["input_sha256"].items():
        if pilot.sha(ROOT / file_name) != checksum:
            raise ValueError(f"Frozen input changed: {file_name}")
    return protocol


def configure(row, folder, device):
    settings = pilot.configure(row, folder)
    labeled = row["labeled"]
    settings.update(labeled=labeled, sources=[labeled, *[d for d in (0, 1, 2) if d != labeled]],
                    device=device.type)
    return settings


def setup_device(device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the frozen rotation")
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    return torch.device(device_name)


def load_training(settings, device):
    source_data = tasks.load_training_domains("hust", settings["target"], settings["labeled"])
    manifest = tasks.records("hust")
    if [d for d, _, _ in source_data] != settings["sources"]:
        raise ValueError("Training source order differs from the frozen role order")
    training = {}
    source_records = []
    for domain, signals, labels in source_data:
        if len(signals) != 729 or (labels is None) == (domain == settings["labeled"]):
            raise ValueError("Source sizes or label access differ from the frozen task")
        x = core.base.normalize(torch.from_numpy(signals).to(device))
        y = (torch.from_numpy(labels).to(device) if labels is not None
             else torch.full((len(x),), -1, dtype=torch.long, device=device))
        training[domain] = (x, y)
        source_records.extend(record["record_id"] for record in manifest if int(record["domain_id"]) == domain)
    if sorted(torch.unique(training[settings["labeled"]][1]).tolist()) != list(range(9)):
        raise ValueError("The labeled source does not cover the frozen nine states")
    return training, source_records


def run_updates(settings, training, device, num_steps, record_heads):
    random.seed(settings["seed"])
    np.random.seed(settings["seed"])
    torch.manual_seed(settings["seed"])
    mode = settings["audit_mode"]
    if record_heads:
        recorder = HeadLossRecorder(settings, mode, record_trace=True)
    else:
        recorder = core.AuditRecorder(settings, limit=STEPS, mode=mode, coverage="all", record_trace=False)
    args = SimpleNamespace(**settings)
    model = recorder.factory(args, 9).to(device)
    for aligner in model.pseudo_alignment:
        aligner.set_labeled_prior(training[settings["labeled"]][1])
    groups = [
        dict(params=list(model.sharedNet1.parameters()) + list(model.sharedNet2.parameters())
             + list(model.sharedNet3.parameters()), scale=1.0),
        dict(params=list(model.cls_fc1.parameters()) + list(model.cls_fc2.parameters()), scale=1.0),
    ]
    optimizer = recorder.torch_proxy().optim.Adam(groups, lr=0.001, weight_decay=0.0005)
    batch_rng = torch.Generator(device=device).manual_seed(settings["seed"] + 101)
    perturb_rng = torch.Generator(device=device).manual_seed(settings["seed"] + 202)
    try:
        for step in range(1, num_steps + 1):
            model.train()
            rate = 0.001 / (1 + 10 * (step - 1) / STEPS) ** 0.75
            for group in optimizer.param_groups:
                group["lr"] = rate
            # Draw in physical-domain order to match the original L0 pilot at
            # every step. The tensors and recorder indices use role order.
            batch_indices = {
                d: recorder.randint(len(training[d][0]), (64,), device=device, generator=batch_rng)
                for d in (0, 1, 2)
            }
            physical_pending = recorder.pending
            recorder.pending = [physical_pending[d] for d in settings["sources"]]
            batches = [(training[d][0][batch_indices[d]], training[d][1][batch_indices[d]])
                       for d in settings["sources"]]
            optimizer.zero_grad(set_to_none=True)
            loss, _, buffers = recorder.loss(model, batches, args, step / STEPS, perturb_rng)
            loss.backward()
            if buffers is not None:
                with torch.no_grad():
                    for name, buffer in model.sharedNet3.named_buffers():
                        buffer.copy_(buffers[name])
            optimizer.step()
            if record_heads and (step == 1 or step % 250 == 0):
                print(f"step={step} loss={float(loss.detach()):.12g}", flush=True)
    finally:
        recorder.close()
    if recorder.completed != num_steps or recorder.trace_steps != num_steps:
        raise RuntimeError("Optimizer or recorder did not capture every update")
    return recorder, model


def archive_heads(path, rows):
    with path.open("x", encoding="utf-8-sig", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(HEAD_COLUMNS)
        writer.writerows(rows)


def train(row, folder, *, short, device_name):
    pilot.enable_file_retries()
    device = setup_device(device_name)
    folder.mkdir(parents=True, exist_ok=False)
    settings = configure(row, folder, device)
    training, source_records = load_training(settings, device)
    config = dict(row, fixed=core.FIXED, selected_step=STEPS, checkpoint_rule="fixed_step_5000",
                  classes=9, sources=settings["sources"], source_counts=[729, 729, 729],
                  source_records=source_records, torch_version=str(torch.__version__),
                  gpu=torch.cuda.get_device_name() if device.type == "cuda" else None,
                  target_arrays_loaded=False, validation_records=0)
    pilot.write(folder / "config.json", config)
    started = time.perf_counter()
    steps = SHORT_STEPS if short else STEPS
    recorder, model = run_updates(settings, training, device, steps, record_heads=True)
    training_seconds = time.perf_counter() - started
    archive_heads(folder / "head_ce_by_step.csv", recorder.head_terms)
    digests = dict(batch_digest=recorder.batch_hasher.hexdigest(),
                   trajectory_digest=recorder.trajectory_hasher.hexdigest())
    if short:
        reference, reference_model = run_updates(dict(settings, output=None), training, device, steps,
                                                 record_heads=False)
        final = core.model_hashes(model)
        equivalent = (final == core.model_hashes(reference_model)
                      and recorder.initial == reference.initial
                      and digests["batch_digest"] == reference.batch_hasher.hexdigest()
                      and digests["trajectory_digest"] == reference.trajectory_hasher.hexdigest()
                      and recorder.heartbeats == reference.heartbeats
                      and core.generator_hash(recorder.perturb_rng) == core.generator_hash(reference.perturb_rng)
                      and core.generator_hash(recorder.batch_rng) == core.generator_hash(reference.batch_rng))
        if not equivalent:
            raise RuntimeError("Observation changed the eight-update reference trajectory")
        pilot.write(folder / "short_complete.json", dict(
            row, complete=True, short_check=True, updates=steps, initial=recorder.initial,
            final=final, observational_equivalence=True, head_ce_rows=len(recorder.head_terms),
            main_forward_calls=recorder.main_forward_calls,
            bn_restorations=recorder.bn_restorations_checked, **digests))
        return
    if recorder.final is None or len(recorder.head_terms) != STEPS or len(recorder.payload) != STEPS:
        raise RuntimeError("Final checkpoint or trace incomplete")
    torch.save(dict(state_dict=model.state_dict(), step=STEPS, config=config), folder / "last.pt")
    np.savez_compressed(folder / "training_predictions.npz", **{
        field: np.stack([r[field] for r in recorder.payload]) for field in recorder.payload[0]})
    pilot.write(folder / "loss_history.json", recorder.heartbeats)
    artifact_names = ("last.pt", "training_predictions.npz", "loss_history.json",
                      "head_ce_by_step.csv", "config.json")
    pilot.write(folder / "source_complete.json", dict(
        row, complete=True, actual_updates=STEPS, checkpoint_step=STEPS,
        completed_utc=pilot.now(), training_seconds=training_seconds,
        checkpoint_rule="fixed_step_5000", target_arrays_loaded=False,
        unlabeled_truth_used=False, validation_records=0, sources=settings["sources"],
        source_records=source_records, initial=recorder.initial, final=recorder.final,
        batch_initial=recorder.batch_initial_hash, perturb_initial=recorder.perturb_initial_hash,
        main_forward_calls=recorder.main_forward_calls, bn_restorations=recorder.bn_restorations_checked,
        head_ce_rows=len(recorder.head_terms),
        artifacts_sha256={name: pilot.sha(folder / name) for name in artifact_names}, **digests))


def evaluate(row, runs, protocol_path, protocol):
    gate = pilot.read(protocol_path.parent / "all_sources_complete.json")
    if gate.get("complete") is not True or gate.get("models") != 48:
        raise PermissionError("All 48 new source runs must be complete before opening the target")
    if "protocol_sha256" in gate and gate["protocol_sha256"] != pilot.sha(protocol_path):
        raise PermissionError("The evaluation release refers to a different protocol")
    for candidate in protocol["rows"]:
        completed = pilot.read(runs / candidate["id"] / "source_complete.json")
        if (completed["id"] != candidate["id"] or completed["complete"] is not True
                or completed["actual_updates"] != STEPS or completed["target_arrays_loaded"] is not False):
            raise PermissionError("The frozen source table is incomplete")
    folder = runs / row["id"]
    if (folder / "result.json").exists():
        raise FileExistsError(folder / "result.json")
    receipt = pilot.read(folder / "source_complete.json")
    checkpoint = folder / "last.pt"
    checkpoint_sha = pilot.sha(checkpoint)
    if checkpoint_sha != receipt["artifacts_sha256"]["last.pt"]:
        raise ValueError("Fixed-step checkpoint hash differs from the training receipt")
    device = setup_device("cuda")
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    if state["step"] != STEPS or any(state["config"][key] != value for key, value in row.items()):
        raise ValueError("Fixed-step checkpoint identity differs from the frozen row")
    settings = configure(row, folder, device)
    model = core.base.make_model(SimpleNamespace(**settings), 9).to(device)
    model.load_state_dict(state["state_dict"], strict=True)
    signals, labels = tasks.load_test_domain("hust", row["target"])
    metrics, logits = core.base.evaluate(model, torch.from_numpy(signals), torch.from_numpy(labels),
                                         "msdgn", device)
    if len(labels) != 729 or not np.array_equal(np.bincount(labels), np.full(9, 81)):
        raise ValueError("Target population differs from the frozen 80 Hz task")
    predictions = folder / "target_predictions.npz"
    temporary = predictions.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, logits=logits.numpy(), labels=labels)
    pilot.retry_file_operation(lambda: temporary.replace(predictions))
    pilot.write(folder / "result.json", dict(
        row, metrics=metrics, checkpoint_step=STEPS, checkpoint_sha256=checkpoint_sha,
        training_seconds=receipt["training_seconds"], evaluated_utc=pilot.now(),
        prediction_sha256=pilot.sha(predictions)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("train", "evaluate"))
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if args.device == "cpu" and not args.short:
        parser.error("The CPU path is only for an eight-step source preflight")
    if args.action != "train" and args.short:
        parser.error("Preflight cannot evaluate the target")
    protocol_path = args.protocol.resolve()
    protocol = read_protocol(protocol_path)
    row = next(r for r in protocol["rows"] if r["id"] == args.id)
    runs = (ROOT / protocol["runs_dir"]).resolve()
    if args.action == "train":
        folder = (protocol_path.parent / "preflight" if args.short else runs) / row["id"]
        train(row, folder, short=args.short, device_name=args.device)
    else:
        evaluate(row, runs, protocol_path, protocol)


if __name__ == "__main__":
    main()
