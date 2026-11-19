"""Fixed-step worker for the two 65 Hz supervision-path interventions."""
import argparse
import csv
import math
from pathlib import Path
import time
from types import SimpleNamespace

from . import rotation_worker as rotation


pilot = rotation.pilot
core = rotation.core
tasks = rotation.tasks
np = rotation.np
torch = rotation.torch
ROOT = rotation.ROOT
STEPS = rotation.STEPS
SHORT_STEPS = rotation.SHORT_STEPS
ARM_SWITCHES = {"A": (True, True), "B": (False, True), "C": (True, False), "D": (False, False)}
SAMPLES_PER_SOURCE = 64
CONSISTENCY_DENOMINATOR = 3 * SAMPLES_PER_SOURCE
U65 = slice(2 * SAMPLES_PER_SOURCE, CONSISTENCY_DENOMINATOR)
HEAD_COLUMNS = (
    *rotation.HEAD_COLUMNS,
    "main_common_pseudo_ce_u2_raw", "main_specific_pseudo_ce_u2_raw",
    "consistency_distance_sum_20", "consistency_distance_sum_35", "consistency_distance_sum_65",
    "consistency_effective_20", "consistency_effective_35", "consistency_effective_65",
    "consistency_denominator", "consistency_total_effective", "ce65", "cons65",
)


def pseudo_ce_for_loss(raw_ce, enabled):
    return raw_ce if enabled else raw_ce * 0


def consistency_distances(clean, altered):
    clean_unit = core.F.normalize(clean.detach(), dim=1)
    altered_unit = core.F.normalize(altered, dim=1)
    return (clean_unit - altered_unit).square().sum(dim=1)


def without_65_consistency(distances):
    weights = torch.ones_like(distances)
    weights[U65] = 0
    return (distances * weights).mean()


class PathLossRecorder(rotation.HeadLossRecorder):
    """Mask only the specified direct terms, with separate raw-loss telemetry."""

    def __init__(self, config, mode, **kwargs):
        super().__init__(config, mode, **kwargs)
        if config["sources"] != [0, 1, 2]:
            raise ValueError("The masked U2 slot must be the physical 65 Hz source")
        self.ce65 = config["ce65"]
        self.cons65 = config["cons65"]
        self.direct_probe = {}

    def ce_nonempty(self, logits, labels):
        slot = self.ce_calls
        raw = core.AuditRecorder.ce_nonempty(self, logits, labels)
        effective = raw
        if slot in (1, 3):
            effective = pseudo_ce_for_loss(raw, self.ce65)
            self.raw_ce65.append(raw.detach())
            if self.config.get("capture_direct_probe") and self.completed == 0:
                self.direct_probe[f"ce65_logits_{slot}"] = logits.detach().clone()
                self.direct_probe[f"ce65_labels_{slot}"] = labels.detach().clone()
        self.unlabeled.append(effective.detach())
        return effective

    def consistency(self, clean, altered):
        if self.config.get("capture_direct_probe") and self.completed == 0:
            self.direct_probe.update(clean=clean.detach().clone(), altered=altered.detach().clone())
        if self.cons65:
            # Preserve the exact original reduction/operation order in A and B.
            effective = super().consistency(clean, altered)
            with torch.no_grad():
                distances = consistency_distances(clean, altered)
        else:
            self.consistency_calls += 1
            core.require(self.consistency_calls == 1 and self.selection_calls == 2,
                         "Unexpected consistency call order")
            core.require(len(clean) == len(altered) == CONSISTENCY_DENOMINATOR,
                         "The masked loss needs three full source batches")
            distances = consistency_distances(clean, altered)
            effective = without_65_consistency(distances)
        self.distance_sums = distances.detach().reshape(3, SAMPLES_PER_SOURCE).sum(dim=1)
        return effective

    def loss(self, model, batches, args, progress, perturb_rng=None):
        self.raw_ce65 = []
        total, terms, buffers = super().loss(model, batches, args, progress, perturb_rng)
        if len(self.raw_ce65) != 2:
            raise RuntimeError("Both 65 Hz pseudo-label head losses must be computed")
        scalars = torch.cat((torch.stack(self.raw_ce65), self.distance_sums,
                             terms["consistency"].detach().reshape(1))).cpu().numpy()
        core.finite_numbers(scalars.tolist(), "source-path diagnostics")
        if (scalars < 0).any():
            raise RuntimeError("Negative cross-entropy or squared distance")
        contributions = scalars[2:5] / CONSISTENCY_DENOMINATOR
        if not self.cons65:
            contributions[2] = 0
        if not np.isclose(contributions.sum(), scalars[5], rtol=2e-6, atol=1e-8):
            raise RuntimeError("Per-domain consistency does not reconstruct the loss")
        row = self.head_terms[-1]
        effective_common, effective_specific = row[9], row[11]
        if self.ce65:
            if (effective_common, effective_specific) != tuple(map(float, scalars[:2])):
                raise RuntimeError("Enabled 65 Hz cross-entropies must match the unmasked terms")
        elif effective_common != 0 or effective_specific != 0:
            raise RuntimeError("Disabled 65 Hz cross-entropies must be zero")
        row.extend((*map(float, scalars[:5]), *map(float, contributions),
                    CONSISTENCY_DENOMINATOR, float(scalars[5]), int(self.ce65), int(self.cons65)))
        return total, terms, buffers


class ShortStateAudit:
    """Hash per-update tensor and optimizer states during the authorized preflight."""

    def torch_proxy(self):
        proxy = super().torch_proxy()
        recorder = self
        self.update_states = []
        self.step_losses = []

        class ObservedAdam(proxy.optim.Adam):
            def step(self, *args, **kwargs):
                gradients = {
                    name: param.grad for name, param in recorder.model.named_parameters()
                    if param.grad is not None
                }
                gradient_hash = core.state_hash(gradients)
                result = super().step(*args, **kwargs)
                saved = self.state_dict()
                tensors = {
                    f"{parameter}:{key}": value
                    for parameter, state in saved["state"].items()
                    for key, value in state.items()
                    if torch.is_tensor(value)
                }
                scalars = {
                    str(parameter): {key: value for key, value in state.items() if not torch.is_tensor(value)}
                    for parameter, state in saved["state"].items()
                }
                recorder.update_states.append(dict(
                    model=core.state_hash(recorder.model.state_dict()),
                    gradients=gradient_hash, optimizer_tensors=core.state_hash(tensors),
                    optimizer_scalars=scalars, optimizer_groups=saved["param_groups"],
                    bn=core.state_hash(dict(recorder.model.named_buffers())),
                ))
                return result

        proxy.optim = SimpleNamespace(Adam=ObservedAdam)
        return proxy

    def loss(self, *args, **kwargs):
        loss, terms, buffers = super().loss(*args, **kwargs)
        self.step_losses.append(dict(total=float(loss.detach()),
            terms={key: float(value.detach()) if torch.is_tensor(value) else value
                   for key, value in terms.items()}))
        return loss, terms, buffers


class ShortReferenceRecorder(ShortStateAudit, core.AuditRecorder):
    def __init__(self, config, **kwargs):
        super().__init__(config, **dict(kwargs, record_trace=True))


class ShortPathRecorder(ShortStateAudit, PathLossRecorder):
    pass


def run_updates(settings, training, device, steps, reference=False):
    """Reuse the frozen loop and vary only recorder bindings for local execution."""
    short = steps == SHORT_STEPS
    replacement = (ShortPathRecorder if short else PathLossRecorder)
    original = (ShortReferenceRecorder if short else core.AuditRecorder)
    local_run = core.clone_function(rotation.run_updates, {
        "HeadLossRecorder": replacement,
        "core": SimpleNamespace(AuditRecorder=original),
    })
    return local_run(settings, training, device, steps, record_heads=not reference)


def read_protocol(path):
    protocol = pilot.read(path)
    rows = protocol["rows"]
    if len(rows) != 9 or len({row["id"] for row in rows}) != 9:
        raise ValueError("The protocol must contain exactly nine unique fresh models")
    combinations = {(r["arm"], r["seed"]) for r in rows}
    if combinations != {(arm, seed) for arm in ("B", "C", "D") for seed in range(3)}:
        raise ValueError("The intervention arms or seed pairing differ from the approved design")
    for row in rows:
        flags = (row["ce65"], row["cons65"])
        expected_id = f"hust-t3-L0-s{row['seed']}-path-{row['arm']}"
        if (
            row["dataset"] != "hust" or row["target"] != 3 or row["labeled"] != 0
            or row["mode"] != "full" or row["B_weight"] != 0.1 or row["id"] != expected_id
            or not all(isinstance(value, bool) for value in flags)
            or flags != ARM_SWITCHES[row["arm"]]
        ):
            raise ValueError(f"Unexpected frozen configuration {row}")
    for relative, expected in protocol["input_sha256"].items():
        if pilot.sha(ROOT / relative) != expected:
            raise ValueError(f"Frozen input changed: {relative}")
    return protocol


def settings_for(row, folder, device):
    settings = rotation.configure(row, folder, device)
    settings.update(ce65=row["ce65"], cons65=row["cons65"])
    return settings


def audit_short_trace(recorder, arm):
    expected_updates = SHORT_STEPS
    if (recorder.completed != expected_updates or recorder.trace_steps != expected_updates
            or len(recorder.update_states) != expected_updates
            or recorder.main_forward_calls != 2 * expected_updates
            or recorder.bn_restorations_checked != expected_updates):
        raise RuntimeError(f"Source-forward or optimizer budget differs for {arm}")
    if arm != "reference_A":
        if len(recorder.head_terms) != expected_updates:
            raise RuntimeError(f"Missing head/consistency telemetry in {arm}")
        records = [dict(zip(HEAD_COLUMNS, row, strict=True)) for row in recorder.head_terms]
        for row in records:
            if row["consistency_denominator"] != CONSISTENCY_DENOMINATOR:
                raise RuntimeError("The consistency denominator must be the full batch size")
            if not row["cons65"] and row["consistency_effective_65"] != 0:
                raise RuntimeError("A masked consistency contribution reached the loss")
            if not row["ce65"] and any(row[key] != 0 for key in (
                "main_common_pseudo_ce_u2", "main_specific_pseudo_ce_u2"
            )):
                raise RuntimeError("A masked pseudo-label contribution reached the loss")
    return dict(updates=recorder.completed, main_forward_calls=recorder.main_forward_calls,
                bn_restorations=recorder.bn_restorations_checked,
                batch_digest=recorder.batch_hasher.hexdigest(),
                trajectory_digest=recorder.trajectory_hasher.hexdigest(),
                batch_rng_final=core.generator_hash(recorder.batch_rng),
                perturb_rng_final=core.generator_hash(recorder.perturb_rng),
                initial=recorder.initial, model=recorder.update_states[-1]["model"],
                optimizer_tensors=recorder.update_states[-1]["optimizer_tensors"])


def audit_direct_terms(reference, probe):
    """Check effects on actual first-batch logits/features with source state held fixed."""
    ce65 = 0.0
    for slot in (1, 3):
        logits = probe[f"ce65_logits_{slot}"].clone().requires_grad_(True)
        labels = probe[f"ce65_labels_{slot}"]
        raw = core.base.ce_nonempty(logits, labels)
        enabled = pseudo_ce_for_loss(raw, True)
        disabled = pseudo_ce_for_loss(raw, False)
        enabled_gradient, = torch.autograd.grad(enabled, logits, retain_graph=True)
        disabled_gradient, = torch.autograd.grad(disabled, logits)
        if (disabled.item() != 0 or torch.count_nonzero(disabled_gradient).item() != 0
                or not torch.equal(raw.detach(), enabled.detach())
                or len(labels) and torch.count_nonzero(enabled_gradient).item() == 0):
            raise RuntimeError("The CE switch did not remove exactly the direct 65 Hz gradient")
        ce65 += float(raw.detach())
    clean = probe["clean"].clone().requires_grad_(True)
    altered = probe["altered"].clone().requires_grad_(True)
    all_samples = core.base.paired_consistency(clean, altered)
    distances = consistency_distances(clean, altered)
    masked = without_65_consistency(distances)
    expected_removed = distances[U65].sum() / CONSISTENCY_DENOMINATOR
    torch.testing.assert_close(all_samples - masked, expected_removed, rtol=1e-5, atol=1e-7)
    clean_before, grad_before = torch.autograd.grad(all_samples, (clean, altered), retain_graph=True,
                                                   allow_unused=True)
    clean_after, grad_after = torch.autograd.grad(masked, (clean, altered), allow_unused=True)
    if clean_before is not None or clean_after is not None:
        raise RuntimeError("Clean-anchor gradient stop changed")
    torch.testing.assert_close(grad_before[:U65.start], grad_after[:U65.start], rtol=0, atol=0)
    if torch.count_nonzero(grad_after[U65]).item() != 0:
        raise RuntimeError("A direct 65 Hz consistency gradient reached masked feature rows")
    ramp = 2 / (1 + math.exp(-10 / STEPS)) - 1
    # Match the archived objective's grouping, only recomputing this equality
    # on reference first-batch intermediates, never on different trained states.
    terms = reference["terms"]
    original = terms["aux_ce"] + 0.5 * terms["mmd"] + 0.005 * terms["entropy"]
    main = terms["main_ce"] + terms["specific_ce"] + terms["orth"]
    def recomputed(ce65_enabled, cons65_enabled):
        return (original + ramp * (main if ce65_enabled else main - ce65)
                + 0.1 * ramp * float((all_samples if cons65_enabled else masked).detach()))
    reconstructed = {arm: recomputed(*flags) for arm, flags in ARM_SWITCHES.items()}
    if not math.isclose(reconstructed["A"], reference["total"], rel_tol=2e-6, abs_tol=1e-7):
        raise RuntimeError("Preflight objective did not reconstruct the actual archived computation")
    for left, right, expected in (
        ("A", "B", ramp * ce65), ("C", "D", ramp * ce65),
        ("A", "C", 0.1 * ramp * float(expected_removed.detach())),
        ("B", "D", 0.1 * ramp * float(expected_removed.detach())),
    ):
        if not math.isclose(reconstructed[left] - reconstructed[right], expected,
                            rel_tol=1e-5, abs_tol=1e-7):
            raise RuntimeError(f"Direct fixed-state loss difference failed for {left}−{right}")
    return dict(checked=True, direct_feature_gradients_checked=True,
                consistency_denominator=CONSISTENCY_DENOMINATOR, checked_reference_step=1,
                unmasked_pseudo_ce65_both_heads=ce65,
                raw_consistency65=float(expected_removed.detach()),
                fixed_state_loss_by_arm=reconstructed)


def verify_archived_reference(anchor, reference):
    """Check against source-only pilot artifacts before treating the pilot as A."""
    folder = pilot.RUNS / anchor["id"]
    receipt = pilot.read(folder / "source_complete.json")
    if (receipt["id"] != anchor["id"] or receipt["seed"] != anchor["seed"]
            or receipt["complete"] is not True or receipt["actual_updates"] != STEPS
            or receipt["target_arrays_loaded"] is not False or receipt["unlabeled_truth_used"] is not False
            or receipt["checkpoint_step"] != STEPS or receipt["initial"] != reference.initial
            or receipt["batch_initial"] != reference.batch_initial_hash
            or receipt["perturb_initial"] != reference.perturb_initial_hash):
        raise RuntimeError("Source-only reference A receipt differs from the short reference run")
    trace_file = folder / "training_predictions.npz"
    loss_file = folder / "loss_history.json"
    for path in (trace_file, loss_file):
        if pilot.sha(path) != receipt["artifacts_sha256"][path.name]:
            raise RuntimeError(f"Archived A source artifact altered: {path.name}")
    with np.load(trace_file, allow_pickle=False) as archived:
        for name in ("indices", "raw_labels", "q_labels", "actual_labels", "raw_mask", "q_mask", "actual_mask"):
            observed = np.stack([row[name] for row in reference.payload])
            if len(archived[name]) != STEPS or not np.array_equal(archived[name][:SHORT_STEPS], observed):
                raise RuntimeError(f"Reference A differs from archived first eight updates at {name}")
    if pilot.read(loss_file)[0] != reference.heartbeats[0]:
        raise RuntimeError("Reference A differs from the archived first-step loss")


def preflight(seed, protocol_path, protocol):
    pilot.enable_file_retries()
    device = rotation.setup_device("cuda")
    folder = protocol_path.parent / "preflight" / f"seed{seed}"
    folder.mkdir(parents=True, exist_ok=False)
    reference_row = next(row for row in protocol["rows"] if row["seed"] == seed and row["arm"] == "B")
    anchor = dict(reference_row, id=f"hust-t3-L0-s{seed}-full-B1", arm="A", ce65=True, cons65=True)
    reference_settings = settings_for(anchor, None, device)
    reference_settings["output"] = None
    training, _ = rotation.load_training(reference_settings, device)
    ref, _ = run_updates(reference_settings, training, device, SHORT_STEPS, reference=True)
    reference_audit = audit_short_trace(ref, "reference_A")
    verify_archived_reference(anchor, ref)
    reference_audit["archived_source_agreement"] = True
    pilot.write(folder / "reference_A.json", reference_audit)
    audits = [dict(arm="reference_A", **reference_audit)]
    probe = None
    for arm, switches in ARM_SWITCHES.items():
        row = dict(anchor, arm=arm, ce65=switches[0], cons65=switches[1])
        settings = dict(settings_for(row, None, device), output=None, capture_direct_probe=(arm == "A"))
        rec, _ = run_updates(settings, training, device, SHORT_STEPS)
        current = audit_short_trace(rec, arm)
        for key in ("batch_digest", "trajectory_digest", "batch_rng_final", "perturb_rng_final", "initial"):
            if reference_audit[key] != current[key]:
                raise RuntimeError(f"Paired source trajectories differ in preflight arm {arm} at {key}")
        if arm == "A":
            if ref.update_states != rec.update_states or ref.step_losses != rec.step_losses:
                raise RuntimeError("New full-open A does not match reference A exactly")
            probe = audit_direct_terms(ref.step_losses[0], rec.direct_probe)
        audits.append(dict(arm=arm, **current))
        pilot.write(folder / f"{arm}.json", current)
    if probe is None:
        raise RuntimeError("Missing A fixed-state gate test")
    pilot.write(folder / "preflight_complete.json", dict(
        complete=True, seed=seed, updates=5 * SHORT_STEPS,
        arm_updates={item["arm"]: item["updates"] for item in audits},
        a_equivalence_exact=True, direct_gate_checks=True,
        fixed_consistency_denominator=CONSISTENCY_DENOMINATOR, target_arrays_loaded=False,
        protocol_sha256=pilot.sha(protocol_path), direct_probe=probe, arms=audits,
    ))


def require_preflight(protocol_path):
    expected_hash = pilot.sha(protocol_path)
    for seed in range(3):
        name = protocol_path.parent / "preflight" / f"seed{seed}" / "preflight_complete.json"
        receipt = pilot.read(name)
        if (receipt["complete"] is not True or receipt["seed"] != seed or receipt["updates"] != 40
                or receipt["a_equivalence_exact"] is not True or receipt["direct_gate_checks"] is not True
                or receipt["target_arrays_loaded"] is not False or receipt["protocol_sha256"] != expected_hash):
            raise PermissionError("All three authorized preflight seeds must pass before full training")


def train(row, folder, protocol_path):
    require_preflight(protocol_path)
    pilot.enable_file_retries()
    device = rotation.setup_device("cuda")
    folder.mkdir(parents=True, exist_ok=False)
    settings = settings_for(row, folder, device)
    training, source_records = rotation.load_training(settings, device)
    config = dict(row, fixed=core.FIXED, selected_step=STEPS, checkpoint_rule="fixed_step_5000",
                  classes=9, sources=settings["sources"], source_counts=[729, 729, 729],
                  source_records=source_records, torch_version=str(torch.__version__),
                  gpu=torch.cuda.get_device_name(), target_arrays_loaded=False, validation_records=0,
                  fixed_consistency_denominator=CONSISTENCY_DENOMINATOR)
    pilot.write(folder / "config.json", config)
    started = time.perf_counter()
    recorder, model = run_updates(settings, training, device, STEPS)
    training_seconds = time.perf_counter() - started
    if recorder.final is None or len(recorder.head_terms) != STEPS or len(recorder.payload) != STEPS:
        raise RuntimeError("Incomplete frozen checkpoint, loss archive or source trace")
    with (folder / "head_ce_by_step.csv").open("x", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(HEAD_COLUMNS)
        writer.writerows(recorder.head_terms)
    torch.save(dict(state_dict=model.state_dict(), step=STEPS, config=config), folder / "last.pt")
    np.savez_compressed(folder / "training_predictions.npz", **{
        key: np.stack([frame[key] for frame in recorder.payload]) for key in recorder.payload[0]
    })
    pilot.write(folder / "loss_history.json", recorder.heartbeats)
    names = ("last.pt", "training_predictions.npz", "loss_history.json", "head_ce_by_step.csv", "config.json")
    pilot.write(folder / "source_complete.json", dict(
        row, complete=True, actual_updates=STEPS, checkpoint_step=STEPS,
        completed_utc=pilot.now(), training_seconds=training_seconds,
        checkpoint_rule="fixed_step_5000", target_arrays_loaded=False,
        unlabeled_truth_used=False, validation_records=0, sources=settings["sources"],
        source_records=source_records, initial=recorder.initial, final=recorder.final,
        batch_initial=recorder.batch_initial_hash, perturb_initial=recorder.perturb_initial_hash,
        main_forward_calls=recorder.main_forward_calls, bn_restorations=recorder.bn_restorations_checked,
        head_ce_rows=len(recorder.head_terms), fixed_consistency_denominator=CONSISTENCY_DENOMINATOR,
        batch_digest=recorder.batch_hasher.hexdigest(), trajectory_digest=recorder.trajectory_hasher.hexdigest(),
        artifacts_sha256={name: pilot.sha(folder / name) for name in names},
    ))


def evaluate(row, runs, protocol_path, protocol):
    gate = pilot.read(protocol_path.parent / "all_sources_complete.json")
    if gate.get("complete") is not True or gate.get("models") != 9:
        raise PermissionError("Target evaluation requires all nine new source-trained checkpoints")
    if gate.get("protocol_sha256") != pilot.sha(protocol_path):
        raise PermissionError("The source release must match the frozen protocol")
    for candidate in protocol["rows"]:
        completed = pilot.read(runs / candidate["id"] / "source_complete.json")
        if (completed["id"] != candidate["id"] or completed["complete"] is not True
                or completed["actual_updates"] != STEPS or completed["target_arrays_loaded"] is not False):
            raise PermissionError("The frozen source table is incomplete")
    folder = runs / row["id"]
    result_path = folder / "result.json"
    if result_path.exists():
        raise FileExistsError(result_path)
    receipt = pilot.read(folder / "source_complete.json")
    checkpoint = folder / "last.pt"
    checkpoint_sha = pilot.sha(checkpoint)
    if checkpoint_sha != receipt["artifacts_sha256"]["last.pt"]:
        raise ValueError("Fixed-step checkpoint differs from the source receipt")
    device = rotation.setup_device("cuda")
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    if state["step"] != STEPS or any(state["config"][key] != value for key, value in row.items()):
        raise ValueError("Misbound fixed-step checkpoint")
    args = SimpleNamespace(**settings_for(row, folder, device))
    model = core.base.make_model(args, 9).to(device)
    model.load_state_dict(state["state_dict"], strict=True)
    signals, labels = tasks.load_test_domain("hust", row["target"])
    metrics, logits = core.base.evaluate(model, torch.from_numpy(signals), torch.from_numpy(labels),
                                         "msdgn", device)
    if labels.shape != (729,) or not np.array_equal(np.bincount(labels), np.full(9, 81)):
        raise ValueError("Target population differs from the frozen 80 Hz task")
    predictions = folder / "target_predictions.npz"
    temporary = predictions.with_suffix(".tmp")
    with temporary.open("wb") as output:
        np.savez_compressed(output, logits=logits.numpy(), labels=labels)
    pilot.retry_file_operation(lambda: temporary.replace(predictions))
    pilot.write(result_path, dict(
        row, metrics=metrics, checkpoint_step=STEPS, checkpoint_sha256=checkpoint_sha,
        training_seconds=receipt["training_seconds"], evaluated_utc=pilot.now(),
        prediction_sha256=pilot.sha(predictions),
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "train", "evaluate"))
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--id")
    parser.add_argument("--seed", type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    path = args.protocol.resolve()
    protocol = read_protocol(path)
    if args.action == "preflight":
        if args.seed is None or args.id is not None:
            parser.error("preflight requires --seed and has no --id")
        preflight(args.seed, path, protocol)
        return
    if not args.id or args.seed is not None:
        parser.error("train/evaluate require --id and have no --seed")
    row = next(row for row in protocol["rows"] if row["id"] == args.id)
    runs = (ROOT / protocol["runs_dir"]).resolve()
    if args.action == "train":
        train(row, runs / row["id"], path)
    else:
        evaluate(row, runs, path, protocol)


if __name__ == "__main__":
    main()
