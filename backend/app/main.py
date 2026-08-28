import json
import os
from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, create_model

HERE = Path(__file__).parent
MODEL_PATH = HERE / "model" / "model.joblib"
META_PATH = HERE / "model" / "feature_meta.json"

with open(META_PATH) as f:
    FEATURE_META = json.load(f)

FEATURE_NAMES = [f["name"] for f in FEATURE_META["features"]]

model = joblib.load(MODEL_PATH)

# Build a Pydantic model dynamically so every one of the 30 features is
# required and typed as float, without hand-writing 30 fields.
_fields = {name: (float, ...) for name in FEATURE_NAMES}
PredictionInput: type[BaseModel] = create_model("PredictionInput", **_fields)


class PredictionOutput(BaseModel):
    diagnosis: str
    malignant_probability: float
    benign_probability: float


origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app = FastAPI(
    title="Breast Cancer Detection API",
    description="Serves predictions from a RandomForest classifier trained "
    "on the Wisconsin Diagnostic Breast Cancer dataset.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "breast-cancer-detection-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/features")
def features():
    """Feature metadata (min/max/mean/step) used to build UI sliders."""
    return FEATURE_META


@app.post("/predict", response_model=PredictionOutput)
def predict(payload: PredictionInput):
    try:
        row: Dict[str, float] = payload.model_dump()
        X = pd.DataFrame([row], columns=FEATURE_NAMES)
        proba = model.predict_proba(X)[0]
        benign_p, malignant_p = float(proba[0]), float(proba[1])
        diagnosis = "Malignant" if malignant_p >= 0.5 else "Benign"
        return PredictionOutput(
            diagnosis=diagnosis,
            malignant_probability=round(malignant_p, 4),
            benign_probability=round(benign_p, 4),
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))
