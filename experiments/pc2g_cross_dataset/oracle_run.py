"""Execute the authorized Oracle protocol with separate source and target processes."""
import subprocess
import sys

from . import oracle_source_audit
from . import oracle_worker as worker


pilot = worker.pilot
frozen = worker.frozen
OUTPUT = worker.OUTPUT
RUNS = worker.RUNS
SEEDS = (0, 1, 2)


def launch(phase, seed):
    log = OUTPUT / "logs" / f"{phase}_s{seed}.log"
    with log.open("x", encoding="utf-8") as stream:
        subprocess.run(
            [sys.executable, "-B", "-m", "experiments.pc2g_cross_dataset.oracle_worker",
             phase, "--seed", str(seed)],
            cwd=worker.ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True,
        )


def update_audit(phase, passed_checks, **details):
    file = OUTPUT / "oracle_implementation_audit.json"
    audit = pilot.read(file)
    audit["status"] = phase
    execution = audit.setdefault("execution", {})
    execution.update(details)
    for check in audit["implementation_and_runtime_checks"]:
        if check["id"] in passed_checks:
            check["status"] = "passed"
    pilot.write(file, audit)


def status(phase, **values):
    state = dict(phase=phase, at_utc=pilot.now(), **values)
    pilot.write(OUTPUT / "execution_status.json", state)
    print(state, flush=True)


def main():
    pilot.enable_file_retries()
    (OUTPUT / "logs").mkdir(exist_ok=False)
    stage = "archive"
    seed = None
    try:
        status(stage)
        lock = frozen.prepare()
        lock_hash = pilot.sha(frozen.FROZEN_DIR / "manifest.json")
        if lock["status"] != "order_rebuilt_and_membership_matched" or lock["target_arrays_loaded"]:
            raise RuntimeError("Archive reconstruction must pass before the technical preflight")
        update_audit("archive_order_verified", {"archive_order"}, archive_manifest_sha256=lock_hash)

        stage = "preflight"
        technical = {}
        for seed in SEEDS:
            status(stage, seed=seed)
            launch(stage, seed)
            file = OUTPUT / "preflight" / f"seed{seed}" / "complete.json"
            receipt = pilot.read(file)
            if (receipt["complete"] is not True or receipt["actual_updates"] != 40
                    or receipt["target_arrays_loaded"]):
                raise RuntimeError(f"Technical check did not release seed {seed}")
            technical[str(seed)] = pilot.sha(file)
        pilot.write(OUTPUT / "preflight_complete.json", dict(
            complete=True, actual_updates=120, target_arrays_loaded=False,
            archive_manifest_sha256=lock_hash, by_seed=technical,
        ))
        update_audit("technical_check_passed", {
            "native_A_prefix", "sham_A_equivalence", "O_65hz_only", "weights_and_gradients",
            "sources_and_target_holdout",
        }, technical_updates=120)
        status("preflight_complete", actual_updates=120)

        stage = "train"
        for seed in SEEDS:
            status(stage, seed=seed, completed_models=seed, total_models=3)
            launch(stage, seed)

        stage = "source_audit"
        seed = None
        status(stage)
        audit = oracle_source_audit.verify_and_write(OUTPUT, RUNS, frozen.FROZEN_DIR)
        if not audit["passed"] or audit["target_arrays_loaded"] or len(audit["seeds"]) != 3:
            raise RuntimeError("Formal source audit did not pass for all Oracle seeds")
        pilot.write(OUTPUT / "all_sources_complete.json", dict(
            complete=True, models=3, checkpoint_step=5000, total_source_updates=15000,
            by_seed={str(item["seed"]): item for item in audit["seeds"]},
            source_audit_artifacts_sha256=audit["artifacts_sha256"],
            archive_manifest_sha256=lock_hash,
        ))
        update_audit("all_sources_verified", {"formal_source_gate"}, source_audit=audit)

        stage = "evaluate"
        for seed in SEEDS:
            status(stage, seed=seed, checkpoint_step=5000)
            launch(stage, seed)

        stage = "report"
        seed = None
        status(stage)
        subprocess.run([sys.executable, "-B", "-m", "experiments.pc2g_cross_dataset.oracle_report"],
                       cwd=worker.ROOT, check=True)
        update_audit("completed", set(), target_evaluations=3, formal_updates=15000,
                     total_actual_updates=15120, historical_A_B_retrained=False)
        status("complete", technical_updates=120, formal_models=3, formal_updates=15000,
               target_evaluations=3)
    except Exception as error:
        update_audit("stopped_on_failure", set(), failed_phase=stage, failed_seed=seed,
                     error=repr(error))
        status("stopped_on_failure", failed_phase=stage, seed=seed, error=repr(error))
        raise


if __name__ == "__main__":
    main()
