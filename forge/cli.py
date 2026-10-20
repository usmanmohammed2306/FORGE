"""The evidence-first command line, currently with a CPU data analysis backend."""

import json
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from forge import __version__
from forge.artifacts import ArtifactCorruption, ArtifactStore
from forge.audit import audit_run, audit_workspace
from forge.benchmark import analyze as analyze_benchmark
from forge.benchmark import preregister as preregister_benchmark
from forge.buckets import recommend_buckets
from forge.bundle import export_bundle, import_bundle, verify_bundle
from forge.canonical import canonical_bytes
from forge.contracts import Experiment
from forge.data import build_dataset
from forge.doctor import diagnose
from forge.evaluation import audit_comparison, compare_submissions
from forge.hardware import probe
from forge.preflight import preflight
from forge.recovery import check_l0_recovery
from forge.registry import RunRegistry
from forge.release import verify_release_index
from forge.runner import load_experiment, load_report, run_experiment, verify_reproduction_source
from forge.verifier import score_and_store

app = typer.Typer(help="Forge: measure first, optimize second.", no_args_is_help=True)
experiment_app = typer.Typer(help="Validate declarative experiment contracts.")
runs_app = typer.Typer(help="Inspect local development runs.")
artifact_app = typer.Typer(help="Inspect content-addressed evidence.")
release_app = typer.Typer(help="Audit the frozen V1 release contract.")
buckets_app = typer.Typer(help="Optimize bucket ladders using observed lengths.")
data_app = typer.Typer(help="Build deterministic small CPU data-lineage fixtures.")
verifier_app = typer.Typer(help="Score bounded L0 function-repair submissions.")
bundle_app = typer.Typer(help="Move audited local CPU evidence between workspaces.")
l0_app = typer.Typer(help="Run tiny CPU correctness and recovery exercises.")
accelerator_app = typer.Typer(help="Probe real CUDA or HPU readiness without speed claims.")
benchmark_app = typer.Typer(help="Preregister and inspect preliminary A100 comparison evidence.")
app.add_typer(experiment_app, name="experiment")
app.add_typer(runs_app, name="runs")
app.add_typer(artifact_app, name="artifact")
app.add_typer(release_app, name="release")
app.add_typer(buckets_app, name="buckets")
app.add_typer(data_app, name="data")
app.add_typer(verifier_app, name="verifier")
app.add_typer(bundle_app, name="bundle")
app.add_typer(l0_app, name="l0")
app.add_typer(accelerator_app, name="accelerator")
app.add_typer(benchmark_app, name="benchmark")


def _print(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, sort_keys=True))


def _experiment(path: Path) -> Experiment:
    try:
        return Experiment.model_validate_json(path.read_bytes())
    except (FileNotFoundError, ValidationError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="CONFIG") from error


def _workspace(path: Optional[Path]) -> Path:
    return (path or Path.cwd()).resolve()


@app.command()
def version() -> None:
    """Print the installed Forge version."""
    typer.echo(f"Forge {__version__}")


@app.command("hardware-probe")
def hardware_probe() -> None:
    """Report actual local CUDA/HPU availability without guessing a SKU."""
    _print(probe())


@accelerator_app.command("preflight")
def accelerator_preflight(
    backend: str,
    device_index: int = typer.Option(0, min=0),
    workspace: Optional[Path] = typer.Option(None),
    no_smoke: bool = typer.Option(False),
) -> None:
    """Record device identity and a tiny FP32/BF16 placement check."""
    try:
        report = preflight(backend, device_index=device_index, smoke=not no_smoke)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    report_ref = ArtifactStore(_workspace(workspace) / ".forge" / "artifacts").put(
        canonical_bytes(report)
    )
    _print({"report_ref": report_ref, "report": report})
    if report["status"] != "READY":
        raise typer.Exit(1)


@benchmark_app.command("preregister")
def benchmark_preregister(spec: Path, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Freeze a controlled A100 protocol before collecting trials."""
    try:
        result = preregister_benchmark(spec, _workspace(workspace))
    except (FileNotFoundError, UnicodeError, ValidationError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)


@benchmark_app.command("analyze")
def benchmark_analyze(index: Path, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Check paired input controls and emit an unauthenticated descriptive comparison."""
    try:
        result = analyze_benchmark(index, _workspace(workspace))
    except (FileNotFoundError, UnicodeError, ValidationError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)


@experiment_app.command("validate")
def experiment_validate(config: Path) -> None:
    """Validate a config and print its stable identity."""
    experiment = _experiment(config)
    _print({"name": experiment.name, "config_digest": experiment.config_digest})


@data_app.command("build")
def data_build(
    training_jsonl: Path,
    evaluation_jsonl: Path,
    workspace: Optional[Path] = typer.Option(None),
) -> None:
    """Filter and content-address a small training set against held-out examples."""
    try:
        result = build_dataset(training_jsonl, evaluation_jsonl, _workspace(workspace))
    except (ValueError, FileNotFoundError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)


@verifier_app.command("score")
def verifier_score(
    task: Path, source: Path, workspace: Optional[Path] = typer.Option(None)
) -> None:
    """Run a bounded AST interpreter; never execute arbitrary submitted Python."""
    try:
        result = score_and_store(task, source, _workspace(workspace))
    except (FileNotFoundError, UnicodeError, ValidationError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)
    if result["status"] != "SOLVED":
        raise typer.Exit(1)


@verifier_app.command("compare")
def verifier_compare(manifest: Path, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Run a paired L0 task campaign with an evidence-linked bootstrap report."""
    try:
        result = compare_submissions(manifest, _workspace(workspace))
    except (FileNotFoundError, UnicodeError, ValidationError, ValueError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)


@verifier_app.command("audit")
def verifier_audit(report_ref: str, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Replay all stored L0 tasks and rederive the paired comparison."""
    result = audit_comparison(report_ref, _workspace(workspace))
    _print(result)
    if result["status"] != "VALID":
        raise typer.Exit(1)


@app.command("run")
def run(config: Path, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Run the current CPU data experiment and save its passport."""
    experiment = _experiment(config)
    try:
        outcome = run_experiment(experiment, _workspace(workspace))
    except (ValueError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print({"run_id": outcome["passport"]["run_id"], "passport_ref": outcome["passport_ref"]})


@l0_app.command("recovery-check")
def l0_recovery_check(
    config: Path,
    split_step: int = typer.Option(5, min=1),
    workspace: Optional[Path] = typer.Option(None),
) -> None:
    """Compare uninterrupted CPU training with save-and-resume at one step."""
    experiment = _experiment(config)
    try:
        result = check_l0_recovery(experiment, _workspace(workspace), split_step)
    except (ValueError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)
    if result["report"]["status"] != "PASS":
        raise typer.Exit(1)


@app.command("reproduce")
def reproduce(run_id: str, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Rerun the verified config saved with an earlier local run."""
    root = _workspace(workspace)
    try:
        verify_reproduction_source(run_id, root)
        experiment = load_experiment(run_id, root)
        source_report_ref = RunRegistry(root / ".forge" / "registry.sqlite3").get(run_id)[
            "report_ref"
        ]
        outcome = run_experiment(experiment, root)
        if outcome["passport"]["report_ref"] != source_report_ref:
            raise ValueError(
                "the new report differs from the source; inspect both run passports before claiming reproduction"
            )
    except (KeyError, ValueError, FileNotFoundError, ArtifactCorruption) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(
        {
            "source_run_id": run_id,
            "new_run_id": outcome["passport"]["run_id"],
            "status": "EXACT_REPORT_MATCH",
        }
    )


@runs_app.command("list")
def runs_list(workspace: Optional[Path] = typer.Option(None)) -> None:
    """List local development runs."""
    _print(RunRegistry(_workspace(workspace) / ".forge" / "registry.sqlite3").list())


@runs_app.command("show")
def runs_show(run_id: str, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Show one run and verify its report and passport bytes."""
    root = _workspace(workspace) / ".forge"
    try:
        row = RunRegistry(root / "registry.sqlite3").get(run_id)
        if row["status"] == "complete":
            store = ArtifactStore(root / "artifacts")
            row["report"] = json.loads(store.get(row["report_ref"]))
            row["passport"] = json.loads(store.get(row["passport_ref"]))
    except (KeyError, ValueError, FileNotFoundError, ArtifactCorruption) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(row)


@runs_app.command("audit")
def runs_audit(
    run_id: Optional[str] = typer.Argument(None), workspace: Optional[Path] = typer.Option(None)
) -> None:
    """Verify local run/config/report/passport/checkpoint provenance links."""
    root = _workspace(workspace)
    result = audit_run(run_id, root) if run_id else audit_workspace(root)
    _print(result)
    if result["status"] != "VALID":
        raise typer.Exit(1)


@bundle_app.command("export")
def bundle_export(
    run_id: str, output: Path, workspace: Optional[Path] = typer.Option(None)
) -> None:
    """Package an audited CPU run without overwriting an existing file."""
    try:
        result = export_bundle(run_id, _workspace(workspace), output)
    except (ValueError, FileExistsError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print({"path": str(output), **result})


@bundle_app.command("verify")
def bundle_verify(path: Path) -> None:
    """Check archive safety, content hashes, and run provenance without extraction."""
    result = verify_bundle(path)
    _print(result)
    if result["status"] != "VALID":
        raise typer.Exit(1)


@bundle_app.command("import")
def bundle_import(path: Path, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Import a verified CPU run into a local workspace."""
    try:
        result = import_bundle(path, _workspace(workspace))
    except (ValueError, FileNotFoundError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print(result)


@app.command("doctor")
def doctor(run_id: str, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Give an evidence-limited recommendation for a local run."""
    try:
        report = load_report(run_id, _workspace(workspace))
    except (KeyError, ValueError, FileNotFoundError, ArtifactCorruption) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print({"run_id": run_id, "diagnosis": diagnose(report)})


@artifact_app.command("verify")
def artifact_verify(ref: str, workspace: Optional[Path] = typer.Option(None)) -> None:
    """Read and hash-check a stored artifact."""
    try:
        payload = ArtifactStore(_workspace(workspace) / ".forge" / "artifacts").get(ref)
    except (ValueError, FileNotFoundError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    _print({"status": "VALID", "reference": ref, "bytes": len(payload)})


@buckets_app.command("recommend")
def buckets_recommend(
    config: Path,
    max_buckets: int = typer.Option(5, min=1),
    compile_penalty_tokens: float = typer.Option(1000.0, min=0),
) -> None:
    """Predict a length ladder; accelerator measurements must validate it."""
    experiment = _experiment(config)
    if experiment.workload.kind != "packing":
        typer.echo("bucket recommendation requires a packing workload", err=True)
        raise typer.Exit(2)
    result = recommend_buckets(
        experiment.workload.sequence_lengths,
        max_buckets=max_buckets,
        compile_penalty_tokens=compile_penalty_tokens,
    )
    _print(
        {
            "config_digest": experiment.config_digest,
            "recommendation": result.as_dict(),
            "claim_limit": "Predicted padding and shape classes; compile cost has not been measured.",
        }
    )


@release_app.command("verify")
def release_verify(workspace: Optional[Path] = typer.Option(None)) -> None:
    """Fail closed until every release evidence gate is implemented and passed."""
    _print(verify_release_index(_workspace(workspace)))
    raise typer.Exit(1)
