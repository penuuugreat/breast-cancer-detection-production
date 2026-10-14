# Breast Cancer Detection Production App

A full-stack machine learning app for estimating breast cancer risk from digitized fine-needle aspirate measurements. The project combines a FastAPI backend, a Vite + React frontend, and a pre-trained scikit-learn model trained on the Wisconsin Diagnostic Breast Cancer dataset.

## Overview

This app lets users adjust 30 tumor morphology features and see a live malignancy probability update in the browser. It is designed as a productized demo/prototype rather than a clinical tool.

Key details:
- Model: RandomForest classifier in a StandardScaler pipeline
- Dataset: Wisconsin Diagnostic Breast Cancer
- Backend: FastAPI
- Frontend: React + Vite
- Deployment options: Docker Compose, Render, Vercel
- Model artifacts: saved as joblib + feature metadata JSON

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── model/
│   │       ├── data.csv
│   │       ├── feature_meta.json
│   │       └── model.joblib
│   ├── Dockerfile
│   ├── render.yaml
│   ├── requirements.txt
│   └── train_model.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── orchestration/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Features

- Interactive 30-feature slider dashboard
- Live diagnosis and probability breakdown
- Model metrics displayed in the UI
- CORS-aware API configuration for local and deployed environments
- Swagger docs via FastAPI
- Docker-based local stack orchestration
- Optional orchestration profile for workflow automation

## Model and training

The model is trained using the script in [backend/train_model.py](backend/train_model.py). It:

1. loads the breast cancer dataset,
2. splits into train/test sets,
3. trains a `StandardScaler` + `RandomForestClassifier` pipeline,
4. evaluates accuracy and ROC AUC,
5. saves the trained model and feature metadata for the API and UI.

The generated artifacts are located in:
- [backend/app/model/model.joblib](backend/app/model/model.joblib)
- [backend/app/model/feature_meta.json](backend/app/model/feature_meta.json)

The project reports strong validation performance on the held-out test set, with metrics approximately:
- Accuracy: 96.5%
- ROC AUC: 0.997

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Docker (optional, for containerized local run)

### 1) Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python train_model.py
uvicorn app.main:app --reload --port 8000
```

Then open the API docs at:
- http://localhost:8000/docs
- http://localhost:8000/redoc

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend usually runs on:
- http://localhost:5173

Make sure the backend is running and that the frontend is configured with the right API URL.

### 3) Docker Compose

From the project root:

```bash
docker compose up --build
```

This starts:
- backend on port 8000
- frontend on port 5173
- optional orchestration service when using the orchestration profile

Example:

```bash
docker compose --profile orchestration up --build
```

## Environment variables

### Backend

Set `ALLOWED_ORIGINS` to allow browser requests from your frontend URL, for example:

```bash
ALLOWED_ORIGINS=http://localhost:5173
```

For multiple origins, separate them with commas:

```bash
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
```

### Frontend

Set `VITE_API_URL` so the UI calls the correct backend:

```bash
VITE_API_URL=http://localhost:8000
```

Note: Vite injects `VITE_*` values at build time, so changes require a fresh frontend rebuild or redeploy.

## API

The FastAPI backend exposes the following endpoints:

| Method | Route | Description |
| --- | --- | --- |
| GET | `/` | Basic service status |
| GET | `/health` | Health check |
| GET | `/features` | Returns feature metadata used by the UI |
| POST | `/predict` | Accepts 30 named feature values and returns diagnosis + probabilities |

### Example payload

```json
{
  "radius_mean": 14.1,
  "texture_mean": 19.5,
  "perimeter_mean": 92.3,
  "area_mean": 690.2,
  "smoothness_mean": 0.09,
  "compactness_mean": 0.1,
  "concavity_mean": 0.08,
  "concave points_mean": 0.05,
  "symmetry_mean": 0.18,
  "fractal_dimension_mean": 0.06,
  "radius_se": 0.7,
  "texture_se": 0.4,
  "perimeter_se": 4.2,
  "area_se": 45.0,
  "smoothness_se": 0.01,
  "compactness_se": 0.02,
  "concavity_se": 0.02,
  "concave points_se": 0.01,
  "symmetry_se": 0.02,
  "fractal_dimension_se": 0.003,
  "radius_worst": 17.4,
  "texture_worst": 22.1,
  "perimeter_worst": 109.0,
  "area_worst": 829.1,
  "smoothness_worst": 0.11,
  "compactness_worst": 0.15,
  "concavity_worst": 0.12,
  "concave points_worst": 0.08,
  "symmetry_worst": 0.2,
  "fractal_dimension_worst": 0.07
}
```

## Deployment

### Render (backend)

The repo includes a backend deployment file at [backend/render.yaml](backend/render.yaml). When using Render Blueprints:

1. Connect the repository to Render
2. Choose Blueprint deployment
3. Set the blueprint path to `backend/render.yaml`
4. Configure `ALLOWED_ORIGINS` for the frontend URL
5. Deploy the API

### Vercel (frontend)

1. Import the frontend folder as a Vercel project
2. Use the Vite preset
3. Add the `VITE_API_URL` environment variable
4. Deploy

### Docker

The project also includes a root [docker-compose.yml](docker-compose.yml) for local container-based development and testing.

## Notes

- This project is intended as a demonstration and portfolio app.
- It is not a medical device and should not be used for clinical decision-making.
- The UI includes a disclaimer to reinforce that limitation.
- The model is intentionally lightweight and deployment-friendly, avoiding heavier alternatives that would increase cold-start time and dependency size.

## License

This project is provided for learning and demonstration purposes. Add an explicit license if you plan to distribute it publicly.
