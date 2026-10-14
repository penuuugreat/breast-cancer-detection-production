"""Dagster pipeline: retrain -> quality gate -> promote the live model.

candidate_model  trains into a scratch dir (never touches the live model)
auc_gate         blocking check; downstream promotion is skipped if it fails
live_model       atomically copies the candidate into backend/app/model
"""
import importlib.util
import os
import shutil
from pathlib import Path

import dagster as dg

BACKEND = Path(os.getenv("BACKEND_DIR", Path(__file__).resolve().parents[1] / "backend"))
LIVE_DIR = BACKEND / "app" / "model"
CANDIDATES = Path(os.getenv("DAGSTER_HOME", "/tmp/dagster")) / "candidates"
MIN_AUC = float(os.getenv("MIN_AUC", "0.99"))
MAX_REGRESSION = float(os.getenv("MAX_AUC_REGRESSION", "0.005"))


def _train_module():
    spec = importlib.util.spec_from_file_location("train_model", BACKEND / "train_model.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@dg.asset(description="Retrained model written to a scratch directory.")
def candidate_model(context: dg.AssetExecutionContext) -> dict:
    out = CANDIDATES / context.run.run_id
    metrics = _train_module().main(out_dir=out)
    context.add_output_metadata({k: round(v, 4) for k, v in metrics.items()})
    return {"dir": str(out), **metrics}


@dg.asset_check(asset=candidate_model, blocking=True)
def auc_gate(candidate_model: dict) -> dg.AssetCheckResult:
    live_meta = LIVE_DIR / "feature_meta.json"
    live_auc = None
    if live_meta.exists():
        import json
        live_auc = json.loads(live_meta.read_text())["metrics"]["test_roc_auc"]
    auc = candidate_model["test_roc_auc"]
    ok = auc >= MIN_AUC and (live_auc is None or auc >= live_auc - MAX_REGRESSION)
    return dg.AssetCheckResult(
        passed=ok,
        metadata={"candidate_auc": round(auc, 4), "live_auc": live_auc, "floor": MIN_AUC},
    )


@dg.asset(description="Live artifacts served by the API (backend/app/model).")
def live_model(context: dg.AssetExecutionContext, candidate_model: dict) -> None:
    src = Path(candidate_model["dir"])
    for name in ("model.joblib", "feature_meta.json"):
        tmp = LIVE_DIR / f".{name}.tmp"
        shutil.copyfile(src / name, tmp)
        os.replace(tmp, LIVE_DIR / name)  # atomic swap
    context.log.info("Promoted. Restart the API to load it: docker compose restart backend")


retrain_job = dg.define_asset_job("retrain", selection=[candidate_model, live_model])

weekly = dg.ScheduleDefinition(job=retrain_job, cron_schedule="0 3 * * 0")  # Sun 03:00

defs = dg.Definitions(
    assets=[candidate_model, live_model],
    asset_checks=[auc_gate],
    jobs=[retrain_job],
    schedules=[weekly],
)
