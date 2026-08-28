const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export function getFeatureMeta() {
  return request("/features");
}

export function predict(values) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(values),
  });
}
