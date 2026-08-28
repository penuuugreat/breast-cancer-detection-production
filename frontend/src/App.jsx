import { useEffect, useMemo, useRef, useState } from "react";
import { getFeatureMeta, predict } from "./api";
import Gauge from "./Gauge";
import "./App.css";

const GROUPS = [
  { key: "mean", label: "Mean", suffix: "_mean" },
  { key: "se", label: "Std. Error", suffix: "_se" },
  { key: "worst", label: "Worst", suffix: "_worst" },
];

function baseLabel(name, suffix) {
  return name
    .replace(suffix, "")
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export default function App() {
  const [meta, setMeta] = useState(null);
  const [values, setValues] = useState({});
  const [activeGroup, setActiveGroup] = useState("mean");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | predicting | error
  const [errorMsg, setErrorMsg] = useState("");
  const debounceRef = useRef(null);

  useEffect(() => {
    getFeatureMeta()
      .then((m) => {
        setMeta(m);
        const defaults = {};
        m.features.forEach((f) => (defaults[f.name] = f.mean));
        setValues(defaults);
        setStatus("ready");
      })
      .catch((err) => {
        setErrorMsg(err.message);
        setStatus("error");
      });
  }, []);

  const featuresByGroup = useMemo(() => {
    if (!meta) return {};
    const grouped = { mean: [], se: [], worst: [] };
    meta.features.forEach((f) => {
      const group = GROUPS.find((g) => f.name.endsWith(g.suffix));
      if (group) grouped[group.key].push(f);
    });
    return grouped;
  }, [meta]);

  useEffect(() => {
    if (status === "loading" || status === "error" || !meta) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setStatus("predicting");
      predict(values)
        .then((r) => {
          setResult(r);
          setStatus("ready");
        })
        .catch((err) => {
          setErrorMsg(err.message);
          setStatus("error");
        });
    }, 250);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values]);

  const handleChange = (name, val) => {
    setValues((prev) => ({ ...prev, [name]: parseFloat(val) }));
  };

  const resetGroup = () => {
    if (!meta) return;
    const defaults = {};
    meta.features.forEach((f) => (defaults[f.name] = f.mean));
    setValues(defaults);
  };

  const malignantProb = result?.malignant_probability ?? 0;
  const riskLevel =
    malignantProb >= 0.5 ? "malignant" : malignantProb >= 0.25 ? "watch" : "benign";

  return (
    <div className="app" data-risk={riskLevel}>
      <header className="masthead">
        <div className="masthead-left">
          <span className="eyebrow">Cell Panel</span>
          <h1>Breast Cancer Risk Estimator</h1>
          <p className="dek">
            Adjust the 30 nuclear measurements from a fine-needle aspirate to
            see how a RandomForest classifier reads the sample, live.
          </p>
        </div>
        {meta && (
          <div className="model-card">
            <span className="model-card-label">Model — held-out test set</span>
            <div className="model-card-metrics">
              <div>
                <strong>{(meta.metrics.test_accuracy * 100).toFixed(1)}%</strong>
                <span>Accuracy</span>
              </div>
              <div>
                <strong>{meta.metrics.test_roc_auc.toFixed(3)}</strong>
                <span>ROC AUC</span>
              </div>
            </div>
          </div>
        )}
      </header>

      {status === "error" && (
        <div className="banner banner-error">
          Couldn't reach the prediction service: {errorMsg}. Confirm the API
          is running and VITE_API_URL is set correctly.
        </div>
      )}

      {status === "loading" && <div className="banner">Loading model…</div>}

      {meta && (
        <main className="layout">
          <section className="panel">
            <div className="tabs" role="tablist">
              {GROUPS.map((g) => (
                <button
                  key={g.key}
                  role="tab"
                  aria-selected={activeGroup === g.key}
                  className={activeGroup === g.key ? "tab active" : "tab"}
                  onClick={() => setActiveGroup(g.key)}
                >
                  {g.label}
                  <span className="tab-count">{featuresByGroup[g.key]?.length}</span>
                </button>
              ))}
              <button className="reset-btn" onClick={resetGroup}>
                Reset to dataset mean
              </button>
            </div>

            <div className="sliders">
              {(featuresByGroup[activeGroup] || []).map((f) => {
                const group = GROUPS.find((g) => g.key === activeGroup);
                return (
                  <div className="slider-row" key={f.name}>
                    <div className="slider-row-head">
                      <label htmlFor={f.name}>{baseLabel(f.name, group.suffix)}</label>
                      <output htmlFor={f.name}>{values[f.name]?.toFixed(4)}</output>
                    </div>
                    <input
                      id={f.name}
                      type="range"
                      min={f.min}
                      max={f.max}
                      step={f.step}
                      value={values[f.name] ?? f.mean}
                      onChange={(e) => handleChange(f.name, e.target.value)}
                    />
                    <div className="slider-row-range">
                      <span>{f.min}</span>
                      <span>{f.max}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <aside className="readout" aria-live="polite">
            <Gauge probability={malignantProb} />
            <div className="readout-diagnosis">
              <span className="readout-label">
                {status === "predicting" ? "Reading…" : "Diagnosis"}
              </span>
              <strong>{result ? result.diagnosis : "—"}</strong>
            </div>
            <div className="readout-probs">
              <div>
                <span>Malignant</span>
                <strong>{(malignantProb * 100).toFixed(1)}%</strong>
              </div>
              <div>
                <span>Benign</span>
                <strong>{((result?.benign_probability ?? 1) * 100).toFixed(1)}%</strong>
              </div>
            </div>
            <p className="disclaimer">
              Trained on the Wisconsin Diagnostic Breast Cancer dataset for
              demonstration purposes. Not a medical device — not for clinical
              use.
            </p>
          </aside>
        </main>
      )}
    </div>
  );
}
