"""
Train and serialize the breast cancer classifier used by the FastAPI app.

Run once (locally or in CI) to produce app/model/model.joblib and
app/model/feature_meta.json. The API loads these artifacts at startup;
it does not train on request.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).parent
DATA_PATH = HERE / "app" / "model" / "data.csv"
MODEL_PATH = HERE / "app" / "model" / "model.joblib"
META_PATH = HERE / "app" / "model" / "feature_meta.json"

FEATURES = [
    "radius_mean", "texture_mean", "perimeter_mean", "area_mean",
    "smoothness_mean", "compactness_mean", "concavity_mean",
    "concave points_mean", "symmetry_mean", "fractal_dimension_mean",
    "radius_se", "texture_se", "perimeter_se", "area_se",
    "smoothness_se", "compactness_se", "concavity_se",
    "concave points_se", "symmetry_se", "fractal_dimension_se",
    "radius_worst", "texture_worst", "perimeter_worst", "area_worst",
    "smoothness_worst", "compactness_worst", "concavity_worst",
    "concave points_worst", "symmetry_worst", "fractal_dimension_worst",
]


def main(out_dir=None):
    """Train and save artifacts to out_dir (default: app/model). Returns metrics."""
    out = Path(out_dir) if out_dir else MODEL_PATH.parent
    out.mkdir(parents=True, exist_ok=True)
    model_path, meta_path = out / MODEL_PATH.name, out / META_PATH.name
    df = pd.read_csv(DATA_PATH)
    df = df.drop(columns=[c for c in ["id", "Unnamed: 32"] if c in df.columns])

    X = df[FEATURES]
    y = (df["diagnosis"] == "M").astype(int)  # 1 = malignant, 0 = benign

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=400,
            max_depth=6,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, proba)
    print(f"Test accuracy: {acc:.4f}")
    print(f"Test ROC AUC:  {auc:.4f}")

    # Refit on all data for the shipped artifact
    pipeline.fit(X, y)
    joblib.dump(pipeline, model_path)

    # Metadata used to build slider ranges + defaults in the frontend
    meta = {
        "features": [
            {
                "name": f,
                "label": f.replace("_", " ").title(),
                "min": round(float(X[f].min()), 5),
                "max": round(float(X[f].max()), 5),
                "mean": round(float(X[f].mean()), 5),
                "step": round(float((X[f].max() - X[f].min()) / 200), 6) or 0.001,
            }
            for f in FEATURES
        ],
        "metrics": {"test_accuracy": round(acc, 4), "test_roc_auc": round(auc, 4)},
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"Saved model -> {model_path}")
    print(f"Saved metadata -> {meta_path}")
    return {"test_accuracy": float(acc), "test_roc_auc": float(auc)}


if __name__ == "__main__":
    main()
