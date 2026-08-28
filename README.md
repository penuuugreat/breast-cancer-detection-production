# Breast Cancer Detection — Production App

A live diagnostic-style tool: adjust the 30 nuclear measurements from a
fine-needle aspirate and see a RandomForest classifier's malignancy read
update in real time. Trained on the Wisconsin Diagnostic Breast Cancer
dataset (96.5% test accuracy, 0.997 ROC AUC).

```
backend/    FastAPI service — serves /predict and /features
frontend/   React (Vite) UI — sliders + live gauge
```

The original notebook explored PyCaret/CatBoost (99.5% AUC) but PyCaret
pulls in a heavy dependency tree that's a poor fit for a free-tier Render
web service (slow cold builds, large image, longer cold starts). `backend/train_model.py`
retrains the same problem with a plain scikit-learn `StandardScaler` +
`RandomForestClassifier` pipeline — a few MB, sub-second startup, 96.5%
accuracy / 0.997 AUC — and ships `model.joblib` directly, so the API loads
a pre-trained artifact rather than retraining on every boot.

## Local development

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 train_model.py        # regenerates app/model/model.joblib + feature_meta.json
uvicorn app.main:app --reload --port 8000
```
API docs at `http://localhost:8000/docs`.

**Frontend**
```bash
cd frontend
cp .env.example .env.local    # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

## Deploying the backend to Render

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at the repo — `backend/render.yaml`
   is picked up automatically (or create a Web Service manually with root
   directory `backend`, build command `pip install -r requirements.txt`,
   start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Set the `ALLOWED_ORIGINS` env var to your deployed Vercel URL (comma-
   separated if you need more than one, e.g. preview + production).
4. Health check path is already set to `/health`.

A `Dockerfile` is included as an alternative if you'd rather deploy the
backend as a Docker-based Render service.

## Deploying the frontend to Vercel

1. Import the repo in Vercel, set the project root to `frontend`.
2. Framework preset: Vite (auto-detected).
3. Add an environment variable `VITE_API_URL` pointing at your Render
   backend URL, e.g. `https://breast-cancer-detection-api.onrender.com`.
4. Deploy. `vercel.json` handles SPA routing.

## API

| Method | Path        | Description                                   |
|--------|-------------|------------------------------------------------|
| GET    | `/health`   | Liveness check                                  |
| GET    | `/features` | Feature metadata (min/max/mean/step) for the UI |
| POST   | `/predict`  | Body: 30 named float features → diagnosis + probabilities |

## Notes

- Render's free tier spins down on inactivity — the first request after
  idle can take 30-60s while it cold-starts. The frontend shows a
  "Reading…" state during requests, but there's no explicit cold-start
  banner; add one if that matters for your use case.
- This is a portfolio/demo project trained on a public research dataset.
  It is not a medical device and isn't intended for clinical use — the UI
  says so in the footer of the results panel.
