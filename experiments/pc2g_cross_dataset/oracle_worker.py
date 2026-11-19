"""Run the fixed-source 65 Hz label intervention and audit both main heads."""
import argparse
import csv
import math
import time
from pathlib import Path
from types import SimpleNamespace

from . import oracle_archive as frozen
from . import path_worker as path


rotation = path.rotation
core = path.core
pilot = path.pilot
tasks = path.tasks
np = path.np
torch = path.torch
ROOT = path.ROOT
STEPS = path.STEPS
OUTPUT = ROOT / "output" / "pc2g_hust_65hz_oracle_preregistration_20261119"
RUNS = ROOT / "runs" / "pc2g_hust_65hz_oracle_20261119"
PREFLIGHT = {"native_A": 12, "archive_replay_A": 12, "O": 16}
TRACE_KEYS = ("indices", "raw_labels", "q_labels", "actual_labels", "raw_mask", "q_mask", "actual_mask")
HEAD_COLUMNS = (
    *path.HEAD_COLUMNS, "main_common_pseudo_ce_u2_count", "main_specific_pseudo_ce_u2_count",
    "main_common_pseudo_ce_u2_original", "main_specific_pseudo_ce_u2_original",
)


def row_for(seed):
    return dict(id=f"hust-t3-L0-s{seed}-oracle", dataset="hust", target=3, labeled=0,
                seed=seed, mode="full", B_weight=0.1, ce65=True, cons65=True, arm="O")


def load_sources(device):
    rows = frozen.training_rows()
    if {int(row["domain_id"]) for row in rows} != {0, 1, 2}:
        raise ValueError("Training manifest must contain exactly the three source domains")
    if any(row["class_id"] for row in rows if int(row["domain_id"]) != 0):
        raise ValueError("Non-labeled truth reached the ordinary source manifest")
    training, records = {}, []
    for domain in (0, 1, 2):
        signals, labels = tasks.load_domain("hust", rows, domain, domain == 0, ROOT)
        if len(signals) != 729 or ((labels is None) != (domain != 0)):
            raise ValueError("Training population or source label scope changed")
        x = core.base.normalize(torch.from_numpy(signals).to(device))
        y = (torch.from_numpy(labels).to(device) if domain == 0
             else torch.full((len(x),), -1, dtype=torch.long, device=device))
        training[domain] = (x, y)
        records.extend(row["record_id"] for row in rows if int(row["domain_id"]) == domain)
    if torch.unique(training[0][1]).tolist() != list(range(9)):
        raise ValueError("Labeled source class coverage changed")
    return training, records


class OracleRecorder(path.PathLossRecorder):
    """Freeze U2 order and change only the two U2 CE target arguments."""

    def __init__(self, config, mode, **kwargs):
        super().__init__(config, mode, **kwargs)
        self.variant = config["variant"]
        self.training_archive = config["training_archive"]
        self.archive = config["device_archive"]
        self.truth = config["selected_65hz_truth"]
        core.require((self.truth is not None) == (self.variant == "O"), "Oracle truth scope changed")

    def factory(self, *args):
        model = super().factory(*args)

        def observe_clean(module, inputs, result):
            if self.frame["main_batch_sizes"] == [192]:
                specific, common, _ = result
                self.frame["clean_heads"] = (common.detach(), specific.detach())

        self.handles.append(model.sharedNet3.register_forward_hook(observe_clean))
        return model

    def select(self, adjusted, ratio, classwise):
        branch = self.selection_calls
        step = self.completed
        count = int(self.training_archive["selected_count"][step, branch])
        expected = self.archive["ordered_positions"][step, branch, :count]
        core.require(torch.equal(self.frame[f"raw{branch}"], self.archive["anchor_raw_logits"][step, branch])
                     and torch.equal(adjusted.detach(), self.archive["anchor_adjusted_logits"][step, branch]),
                     f"Auxiliary logits differ from A at step {step + 1}, branch {branch + 1}")
        if branch == 0 or self.variant == "native_A":
            indices, labels = super().select(adjusted, ratio, classwise)
            core.require(torch.equal(indices, expected),
                         f"Native CE batch order differs from A archive at step {step + 1}")
        else:
            core.require(ratio == 0.6 and classwise is True, "Frozen selector call changed")
            for key in TRACE_KEYS[1:]:
                self.frame.setdefault(key, []).append(self.archive[key][step, branch])
            self.selection_calls += 1
            indices, labels = expected, self.frame["actual_labels"][branch]
        core.require(torch.equal(labels, self.archive["actual_labels"][step, branch]),
                     f"Historical pseudo-label mismatch at step {step + 1}")
        self.frame.setdefault("consumed_indices", []).append(indices)
        return indices, labels

    def ce_nonempty(self, logits, labels):
        call = self.ce_calls
        branch = call % 2
        indices = self.frame["consumed_indices"][branch]
        original = self.frame["actual_labels"][branch][indices]
        start = 64 * (branch + 1)
        all_rows = self.frame["clean_heads"][call // 2][start:start + 64]
        core.require(torch.equal(labels, original) and torch.equal(logits.detach(), all_rows[indices]),
                     f"Main head {call + 1} received unexpected CE rows or targets")
        if branch == 0:
            return super().ce_nonempty(logits, labels)
        if self.variant == "O":
            if call == 1:
                step_truth = self.truth[self.completed]
                core.require(torch.equal(step_truth >= 0, self.frame["actual_mask"][branch]),
                             "Oracle supplied truth outside A's selected positions")
                truth = step_truth[indices]
                self.oracle_labels = torch.where(truth == original, original, truth)
            labels = self.oracle_labels
            core.require(len(labels) == len(indices) and labels.dtype == torch.long
                         and not labels.requires_grad, "Invalid hard Oracle targets")
            if self.config["technical"]:
                audit_direct_gradient(all_rows, indices, original, labels)
        with torch.no_grad():
            original_ce = core.base.ce_nonempty(logits.detach(), original)
        self.u2_inputs.append((len(labels), float(original_ce)))
        return super().ce_nonempty(logits, labels)

    def loss(self, model, batches, args, progress, perturb_rng=None):
        step = self.completed
        core.require(np.array_equal(np.stack(self.pending), self.training_archive["indices"][step]),
                     f"Source batch differs from A at step {step + 1}")
        self.u2_inputs = []
        self.oracle_labels = None
        result = super().loss(model, batches, args, progress, perturb_rng)
        payload = self.payload[-1]
        for key in TRACE_KEYS:
            core.require(np.array_equal(payload[key], self.training_archive[key][step]),
                         f"A archive trace differs at step {step + 1}: {key}")
        ordered = self.training_archive["ordered_positions"][step]
        payload["consumed_order"] = ordered.copy()
        (common_n, common_original), (specific_n, specific_original) = self.u2_inputs
        count = int(self.training_archive["selected_count"][step, 1])
        core.require(common_n == specific_n == count, "Original U2 CE denominator changed")
        self.head_terms[-1].extend((common_n, specific_n, common_original, specific_original))
        if self.variant == "O":
            payload["actual_labels"][1, ordered[1, :count]] = self.oracle_labels.cpu().numpy()
        return result


def audit_direct_gradient(rows, indices, original, corrected):
    """Hold both main heads' logits fixed while checking the 65 Hz CE change."""
    rows = rows.detach().clone().requires_grad_(True)
    before = core.base.ce_nonempty(rows[indices], original)
    after = core.base.ce_nonempty(rows[indices], corrected)
    old_grad, = torch.autograd.grad(before, rows)
    new_grad, = torch.autograd.grad(after, rows)
    selected = torch.zeros(len(rows), dtype=torch.bool, device=rows.device)
    selected[indices] = True
    core.require(not bool(old_grad[~selected].any()) and not bool(new_grad[~selected].any()),
                 "Unselected positions received direct U2 CE gradients")
    if len(indices):
        changes = (torch.nn.functional.one_hot(original, 9)
                   - torch.nn.functional.one_hot(corrected, 9)) / len(indices)
        torch.testing.assert_close(new_grad[indices] - old_grad[indices],
                                   changes, atol=2e-8, rtol=2e-6)


class ShortOracleRecorder(path.ShortStateAudit, OracleRecorder):
    def __init__(self, config, mode, **kwargs):
        super().__init__(config, mode, **kwargs)
        self.segment_steps = config["segment_steps"]
        self.rng_states = []

    def after_step(self):
        super().after_step()
        self.rng_states.append(dict(
            batch=core.generator_hash(self.batch_rng),
            perturb=core.generator_hash(self.perturb_rng),
            cpu=core.state_hash({"rng": torch.get_rng_state()}),
            cuda=core.state_hash({"rng": torch.cuda.get_rng_state()}),
        ))
        if self.completed == self.segment_steps:
            updates = [int(branch.updates) for branch in self.model.pseudo_alignment]
            core.require(updates == [self.segment_steps] * 2, "DA queue update count changed")
            self.final = core.model_hashes(self.model)
            self.final.update(perturb_generator_hash=self.rng_states[-1]["perturb"],
                              batch_generator_hash=self.rng_states[-1]["batch"])


def saves(folder, steps, recorder, model, config, *, formal):
    with (folder / "head_ce_by_step.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEAD_COLUMNS)
        writer.writerows(recorder.head_terms)
    np.savez_compressed(folder / "training_predictions.npz", **{
        key: np.stack([row[key] for row in recorder.payload]) for key in recorder.payload[0]})
    pilot.write(folder / "loss_history.json", recorder.heartbeats)
    names = ["config.json", "head_ce_by_step.csv", "training_predictions.npz", "loss_history.json"]
    if formal:
        torch.save(dict(state_dict=model.state_dict(), step=steps, config=config), folder / "last.pt")
        names.append("last.pt")
    else:
        pilot.write(folder / "stepwise_states.json", dict(
            segment_end_step=steps, schedule_steps=STEPS, final=recorder.final,
            states=recorder.update_states, losses=recorder.step_losses, rng=recorder.rng_states))
        names.append("stepwise_states.json")
    return {name: pilot.sha(folder / name) for name in names}


def historical_receipt(seed):
    folder = pilot.RUNS / f"hust-t3-L0-s{seed}-full-B1"
    return folder, pilot.read(folder / "source_complete.json")


def execute(seed, variant, steps, folder, source_data, archive, device):
    formal = steps == STEPS
    row = row_for(seed)
    folder.mkdir(parents=True, exist_ok=False)
    training, source_records = source_data
    archive_hash = frozen.archive_sha256(seed)
    config = dict(row, variant=variant, technical=not formal, fixed=core.FIXED,
                  checkpoint_rule="fixed_step_5000", source_records=source_records,
                  sources=[0, 1, 2], target_arrays_loaded=False, validation_records=0,
                  archive_sha256=archive_hash, torch_version=str(torch.__version__),
                  gpu=torch.cuda.get_device_name())
    pilot.write(folder / "config.json", config)
    settings = path.settings_for(row, folder, device)
    settings.update(variant=variant, technical=not formal, segment_steps=steps, training_archive=archive,
                    device_archive={key: torch.from_numpy(archive[key]).to(device) for key in (
                        *TRACE_KEYS[1:], "ordered_positions", "anchor_raw_logits", "anchor_adjusted_logits")},
                    selected_65hz_truth=(torch.from_numpy(frozen.load_oracle_truth(seed)).to(device)
                                         if variant == "O" else None))
    recorder_class = OracleRecorder if formal else ShortOracleRecorder
    run_updates = core.clone_function(rotation.run_updates, {"HeadLossRecorder": recorder_class})
    started = time.perf_counter()
    try:
        recorder, model = run_updates(settings, training, device, steps, record_heads=True)
        if len(recorder.head_terms) != steps or recorder.final is None:
            raise RuntimeError("Incomplete source telemetry or model state")
        if not formal and not (len(recorder.update_states) == len(recorder.rng_states) == steps):
            raise RuntimeError("Short segment did not capture every optimizer and RNG state")
        historical_folder, baseline = historical_receipt(seed)
        if (recorder.initial != baseline["initial"] or
                recorder.batch_initial_hash != baseline["batch_initial"] or
                recorder.perturb_initial_hash != baseline["perturb_initial"]):
            raise RuntimeError("Initialization or RNG differs from historical A")
        if variant != "O" and recorder.heartbeats[0] != pilot.read(historical_folder / "loss_history.json")[0]:
            raise RuntimeError("Native initial loss differs from historical A")
        batch_digest = recorder.batch_hasher.hexdigest()
        trajectory_digest = recorder.trajectory_hasher.hexdigest()
        if formal and (batch_digest != baseline["batch_digest"]
                       or trajectory_digest != baseline["trajectory_digest"]
                       or any(recorder.final[key] != baseline["final"][key]
                              for key in baseline["final"] if key != "main_hash")):
            raise RuntimeError("Full Oracle source/auxiliary trajectory differs from A")
        artifacts = saves(folder, steps, recorder, model, config, formal=formal)
        result = dict(
            row, variant=variant, complete=True, actual_updates=steps, checkpoint_step=steps,
            completed_utc=pilot.now(), training_seconds=time.perf_counter() - started,
            checkpoint_rule="fixed_step_5000", target_arrays_loaded=False, validation_records=0,
            sources=[0, 1, 2], source_records=source_records, initial=recorder.initial,
            final=recorder.final, batch_initial=recorder.batch_initial_hash,
            perturb_initial=recorder.perturb_initial_hash, batch_digest=batch_digest,
            trajectory_digest=trajectory_digest, head_ce_rows=len(recorder.head_terms),
            main_forward_calls=recorder.main_forward_calls,
            bn_restorations=recorder.bn_restorations_checked, fixed_consistency_denominator=192,
            unlabeled_truth_used=variant == "O", oracle_truth_domain_hz=65 if variant == "O" else None,
            oracle_truth_use="selected_65hz_two_main_heads_only" if variant == "O" else None,
            two_main_heads_using_identical_oracle_targets=variant == "O",
            archive_sha256=archive_hash, archive_manifest_sha256=pilot.sha(frozen.FROZEN_DIR / "manifest.json"),
            artifacts_sha256=artifacts,
        )
        return result
    except Exception as exc:
        pilot.write(folder / "source_failure.json", dict(step_budget=steps, variant=variant,
                    error=repr(exc), target_arrays_loaded=False, recorded_at=pilot.now()))
        raise


def preflight(seed):
    """Use fresh initial states and spend exactly 40 source updates per seed."""
    if (OUTPUT / "preflight_complete.json").exists():
        raise FileExistsError("Preflight was already completed")
    folder = OUTPUT / "preflight" / f"seed{seed}"
    folder.mkdir(parents=True, exist_ok=False)
    device = rotation.setup_device("cuda")
    archive = frozen.load_archive(seed)
    source_data = load_sources(device)
    for variant, steps in PREFLIGHT.items():
        receipt = execute(seed, variant, steps, folder / variant, source_data, archive, device)
        pilot.write(folder / variant / "short_complete.json", receipt)
    left, right = folder / "native_A", folder / "archive_replay_A"
    for file in ("stepwise_states.json", "head_ce_by_step.csv"):
        if pilot.sha(left / file) != pilot.sha(right / file):
            raise RuntimeError(f"Native A differs from replay A in seed {seed}: {file}")
    with (np.load(left / "training_predictions.npz", allow_pickle=False) as native_trace,
          np.load(right / "training_predictions.npz", allow_pickle=False) as replay_trace):
        if any(not np.array_equal(native_trace[key], replay_trace[key]) for key in native_trace.files):
            raise RuntimeError(f"Native A differs from replay A in seed {seed}: trace")
    native = pilot.read(left / "stepwise_states.json")
    oracle = pilot.read(folder / "O" / "stepwise_states.json")
    if oracle["rng"][:12] != native["rng"]:
        raise RuntimeError("Oracle changed the paired stochastic streams")
    first_native, first_oracle = native["losses"][0]["terms"], oracle["losses"][0]["terms"]
    for key in ("aux_ce", "mmd", "entropy", "orth", "consistency"):
        if first_native[key] != first_oracle[key]:
            raise RuntimeError(f"Oracle changed fixed-state term {key}")
    pilot.write(folder / "complete.json", dict(
        complete=True, seed=seed, actual_updates=sum(PREFLIGHT.values()), target_arrays_loaded=False,
        native_and_archive_replay_identical=True, fixed_state_direct_gradient_checked_every_O_step=True,
        archive_sha256=frozen.archive_sha256(seed),
        short_receipts_sha256={variant: pilot.sha(folder / variant / "short_complete.json")
                               for variant in PREFLIGHT},
    ))


def train(seed):
    gate = pilot.read(OUTPUT / "preflight_complete.json")
    if (gate["complete"] is not True or gate["actual_updates"] != 120
            or gate["archive_manifest_sha256"] != pilot.sha(frozen.FROZEN_DIR / "manifest.json")):
        raise PermissionError("Formal training requires the complete 120-update gate")
    for paired_seed in range(3):
        seed_gate = OUTPUT / "preflight" / f"seed{paired_seed}" / "complete.json"
        if pilot.sha(seed_gate) != gate["by_seed"][str(paired_seed)]:
            raise PermissionError("Preflight receipt changed")
    device = rotation.setup_device("cuda")
    folder = RUNS / row_for(seed)["id"]
    receipt = execute(seed, "O", STEPS, folder, load_sources(device), frozen.load_archive(seed), device)
    pilot.write(folder / "source_complete.json", receipt)


def evaluate(seed):
    gate = pilot.read(OUTPUT / "all_sources_complete.json")
    if gate.get("complete") is not True or gate.get("models") != 3 or gate.get("checkpoint_step") != STEPS:
        raise PermissionError("Target evaluation requires all three audited sources")
    for paired_seed in range(3):
        folder = RUNS / row_for(paired_seed)["id"]
        item = gate["by_seed"][str(paired_seed)]
        file = folder / "source_complete.json"
        receipt = pilot.read(file)
        if (pilot.sha(file) != item["source_receipt_sha256"] or
                pilot.sha(folder / "last.pt") != item["checkpoint_sha256"] or
                receipt["artifacts_sha256"]["last.pt"] != item["checkpoint_sha256"] or
                receipt["actual_updates"] != STEPS or receipt["target_arrays_loaded"] is not False):
            raise PermissionError("Source receipt or checkpoint differs from release")
    row = row_for(seed)
    folder = RUNS / row["id"]
    result = folder / "result.json"
    if result.exists():
        raise FileExistsError(result)
    receipt = pilot.read(folder / "source_complete.json")
    device = rotation.setup_device("cuda")
    state = torch.load(folder / "last.pt", map_location=device, weights_only=False)
    if state["step"] != STEPS or any(state["config"][key] != value for key, value in row.items()):
        raise ValueError("Misbound fixed-step Oracle checkpoint")
    model = core.base.make_model(SimpleNamespace(**path.settings_for(row, folder, device)), 9).to(device)
    model.load_state_dict(state["state_dict"], strict=True)
    signals, labels = tasks.load_test_domain("hust", row["target"])
    if labels.shape != (729,) or not np.array_equal(np.bincount(labels), np.full(9, 81)):
        raise ValueError("Target population differs from the frozen 80 Hz task")
    metrics, logits = core.base.evaluate(model, torch.from_numpy(signals), torch.from_numpy(labels),
                                         "msdgn", device)
    core.finite_tensors([logits], "held-out logits")
    predictions = folder / "target_predictions.npz"
    with predictions.open("xb") as stream:
        np.savez_compressed(stream, logits=logits.numpy(), labels=labels)
    pilot.write(result, dict(row, metrics=metrics, checkpoint_step=STEPS,
                checkpoint_sha256=receipt["artifacts_sha256"]["last.pt"],
                training_seconds=receipt["training_seconds"], evaluated_utc=pilot.now(),
                prediction_sha256=pilot.sha(predictions)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preflight", "train", "evaluate"))
    parser.add_argument("--seed", type=int, choices=(0, 1, 2), required=True)
    args = parser.parse_args()
    pilot.enable_file_retries()
    {"preflight": preflight, "train": train, "evaluate": evaluate}[args.phase](args.seed)


if __name__ == "__main__":
    main()
