# 🧬 Breast Cancer Detection — Production App

A live diagnostic-style tool: adjust the 30 nuclear measurements from a
fine-needle aspirate and watch a RandomForest classifier's malignancy read
update in real time. Trained on the Wisconsin Diagnostic Breast Cancer
dataset — **96.5 % test accuracy · 0.997 ROC AUC**.

<p align="center">
  <img src="docs/images/app-ui.jpg" alt="Breast Cancer Risk Estimator UI: 30 sliders, live malignancy gauge, 96.5% accuracy and 0.997 ROC AUC" width="820">
  <br>
  <em>The app: adjust 30 nuclear measurements and watch the classifier's read update live.</em>
</p>

<p align="center">
  <img src="docs/images/dagster-retrain-run.png" alt="Dagster retrain job: candidate_model passed its AUC quality gate and live_model was promoted" width="720">
  <br>
  <em>Automated retraining (Dagster): train → AUC quality gate → promote. Both assets materialized, gate 1/1 passed.</em>
</p>

```
📦 backend/    → FastAPI service — serves /predict and /features
🖥  frontend/   → React (Vite) UI — sliders + live gauge
```

ℹ️ The original notebook explored PyCaret/CatBoost (99.5 % AUC), but PyCaret
pulls in a heavy dependency tree that's a poor fit for a free-tier Render
web service (slow cold builds, large image, longer cold starts).
`backend/train_model.py` retrains the same problem with a plain scikit-learn
`StandardScaler` + `RandomForestClassifier` pipeline — a few MB, sub-second
startup, 96.5 % accuracy / 0.997 AUC — and ships `model.joblib` directly, so
the API loads a pre-trained artifact rather than retraining on every boot.

---

## ⚙️ Local development

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 train_model.py        # regenerates app/model/model.joblib + feature_meta.json
uvicorn app.main:app --reload --port 8000
```
→ API docs at `http://localhost:8000/docs`

**Frontend**
```bash
cd frontend
cp .env.example .env.local    # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

---

## 🐳 Run everything with Docker Compose

```bash
docker compose up --build
```
- Frontend → http://localhost:5173
- API docs → http://localhost:8000/docs

The frontend waits for the backend's `/health` check before starting.
Override defaults by copying `.env.example` to `.env`. `VITE_API_URL` is baked
in at build time and must be reachable from your **browser**; if you change
the frontend port or host, update `ALLOWED_ORIGINS` to match.

---

## 🔁 Scheduled retraining (Dagster)

```bash
docker compose --profile orchestration up --build
```
Dagster UI → http://localhost:3000. The `retrain` job runs weekly (Sun 03:00)
once the schedule is switched on in the UI, or on demand via **Materialize all**:

`candidate_model` (train to scratch dir) → `auc_gate` (blocking: AUC ≥ `MIN_AUC`
and no more than 0.005 below the live model) → `live_model` (atomic swap into
`backend/app/model`). Run `docker compose restart backend` to load a promoted
model.

<p align="center">
  <img src="docs/images/dagster-pipeline-graph.png" alt="Dagster pipeline graph: candidate_model feeds auc_gate, which guards live_model" width="420">
</p>

⚠️ `data.csv` is a static dataset with a fixed seed, so retraining reproduces
essentially the same model today. The pipeline pays off once you point
`train_model.py` at a data source that changes.

---

## 🚀 Deploying the backend to Render

The repo ships a ready-made `backend/render.yaml`. Render's Blueprint
feature only looks at the **repo root** for `render.yaml` by default, so
point it at the right path explicitly:

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, connect the repo.
3. When prompted, set:
   | Field | Value |
   |---|---|
   | **Blueprint Name** | anything, e.g. `breast-cancer-detection` |
   | **Branch** | `main` |
   | **Blueprint Path** | `backend/render.yaml` ⚠️ *not* the default `render.yaml` |
4. Render parses the file and shows the `breast-cancer-detection-api` web
   service for review — approve it.
5. Set the `ALLOWED_ORIGINS` env var to your deployed frontend URL
   (comma-separated if you need more than one, e.g. preview + production).
6. ✅ Health check path is already set to `/health`.

**No Blueprint?** Create a Web Service manually instead:
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

A `Dockerfile` is included as an alternative if you'd rather deploy the
backend as a Docker-based Render service.

---

## ▲ Deploying the frontend to Vercel

1. Import the repo in Vercel, set the project root to `frontend`.
2. Framework preset: Vite (auto-detected).
3. Add an environment variable `VITE_API_URL` → your Render backend URL,
   e.g. `https://breast-cancer-detection-api.onrender.com`.
4. Deploy. `vercel.json` handles SPA routing.

### Alternative: frontend on Render (Static Site)
| Field | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |
| **Environment Variables** | `VITE_API_URL` → your backend's Render URL |

⚠️ Vite bakes `VITE_*` vars in **at build time** — changing the value later
needs a fresh deploy, not just a restart. And once the frontend is live,
update the backend's `ALLOWED_ORIGINS` to match its new URL, or CORS will
block every request.

---

## 📡 API

| Method | Path        | Description                                   |
|--------|-------------|------------------------------------------------|
| GET    | `/health`   | Liveness check                                  |
| GET    | `/features` | Feature metadata (min/max/mean/step) for the UI |
| POST   | `/predict`  | Body: 30 named float features → diagnosis + probabilities |

---

## 📝 Notes

- ⏳ Render's free tier spins down on inactivity — the first request after
  idle can take 30–60 s while it cold-starts. The frontend shows a
  "Reading…" state during requests, but there's no explicit cold-start
  banner; add one if that matters for your use case.
- ⚕️ This is a portfolio/demo project trained on a public research dataset.
  It is **not** a medical device and isn't intended for clinical use — the
  UI says so in the footer of the results panel.
