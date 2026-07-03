/**
 * MediTwin AI — API Service Layer
 * All calls to FastAPI backend (Groq model: openai/gpt-oss-120b)
 */

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API = `${BASE}/api/v1`;

let _token = null;

export const setToken = (t) => { _token = t; };
export const getToken = () => _token;

const headers = (extra = {}) => ({
  "Content-Type": "application/json",
  ...((_token) ? { Authorization: `Bearer ${_token}` } : {}),
  ...extra,
});

const handle = async (res) => {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
};

// ── Auth ─────────────────────────────────────────────────
export const authAPI = {
  register: (body) =>
    fetch(`${API}/auth/register`, { method: "POST", headers: headers(), body: JSON.stringify(body) }).then(handle),
  login: (body) =>
    fetch(`${API}/auth/login`, { method: "POST", headers: headers(), body: JSON.stringify(body) }).then(handle),
  me: () =>
    fetch(`${API}/auth/me`, { headers: headers() }).then(handle),
};

// ── Health ────────────────────────────────────────────────
export const healthAPI = {
  recordVitals: (vitals) =>
    fetch(`${API}/health/vitals`, { method: "POST", headers: headers(), body: JSON.stringify(vitals) }).then(handle),
  getLiveVitals: () =>
    fetch(`${API}/health/vitals/live`, { headers: headers() }).then(handle),
  getTimeline: (months = 6) =>
    fetch(`${API}/health/timeline?months=${months}`, { headers: headers() }).then(handle),
  getHistory: (days = 30) =>
    fetch(`${API}/health/vitals/history?days=${days}`, { headers: headers() }).then(handle),
};

// ── AI ───────────────────────────────────────────────────
export const aiAPI = {
  chat: (messages, patientContext) =>
    fetch(`${API}/ai/chat`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ messages, patient_context: patientContext }),
    }).then(handle),

  generateHealthTwin: (profile) =>
    fetch(`${API}/ai/health-twin`, {
      method: "POST", headers: headers(),
      body: JSON.stringify(profile),
    }).then(handle),

  simulateWhatIf: (current, proposed) =>
    fetch(`${API}/ai/whatif`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ current_profile: current, proposed_changes: proposed }),
    }).then(handle),

  getRecommendations: (profile, category) =>
    fetch(`${API}/ai/recommendations`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ patient_profile: profile, category }),
    }).then(handle),
};

// ── Reports ───────────────────────────────────────────────
export const reportsAPI = {
  analyzeFile: (formData) =>
    fetch(`${API}/reports/analyze`, {
      method: "POST",
      headers: { ...(_token ? { Authorization: `Bearer ${_token}` } : {}) },
      body: formData,
    }).then(handle),

  analyzeText: (text) =>
    fetch(`${API}/reports/analyze-text`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ text }),
    }).then(handle),
};

// ── Triage ────────────────────────────────────────────────
export const triageAPI = {
  admitPatient: (patient) =>
    fetch(`${API}/triage/admit`, {
      method: "POST", headers: headers(),
      body: JSON.stringify(patient),
    }).then(handle),
  getQueue: () =>
    fetch(`${API}/triage/queue`, { headers: headers() }).then(handle),
  getStats: () =>
    fetch(`${API}/triage/stats`, { headers: headers() }).then(handle),
  dischargePatient: (id) =>
    fetch(`${API}/triage/discharge/${id}`, { method: "DELETE", headers: headers() }).then(handle),
};

// ── ML Validation Engine (real trained models + SHAP) ──────
export const mlAPI = {
  getAllMetrics: () =>
    fetch(`${API}/ml/metrics`, { headers: headers() }).then(handle),
  getMetrics: (disease) =>
    fetch(`${API}/ml/metrics/${disease}`, { headers: headers() }).then(handle),
  predict: (disease, patientProfile) =>
    fetch(`${API}/ml/predict/${disease}`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ patient_profile: patientProfile }),
    }).then(handle),
  crossValidate: (disease, patientProfile) =>
    fetch(`${API}/ml/cross-validate/${disease}`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ patient_profile: patientProfile }),
    }).then(handle),
};

// ── Demo Mode ──────────────────────────────────────────────
export const demoAPI = {
  listPatients: () =>
    fetch(`${API}/demo/patients`, { headers: headers() }).then(handle),
  getPatient: (id) =>
    fetch(`${API}/demo/patient/${id}`, { headers: headers() }).then(handle),
};

// ── Story Mode ─────────────────────────────────────────────
export const storyAPI = {
  generate: (profile) =>
    fetch(`${API}/story/generate`, {
      method: "POST", headers: headers(),
      body: JSON.stringify(profile),
    }).then(handle),
};

// ── Biological Age Card ────────────────────────────────────
export const bioAgeAPI = {
  getCard: (patientProfile, years = 1) =>
    fetch(`${API}/timemachine/bioage-card`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ current_profile: patientProfile, years, apply_prevention: [] }),
    }).then(handle),
};

// ── Parallel Universe Simulator ────────────────────────────
export const parallelAPI = {
  simulate: (baseProfile, timelines, years = 10) =>
    fetch(`${API}/parallel/simulate`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({ base_profile: baseProfile, timelines, years }),
    }).then(handle),
};

// ── Wearable Digital Twin ──────────────────────────────────
export const wearableAPI = {
  getStream: (patientName, baseProfile, durationSeconds = 30) =>
    fetch(`${API}/wearable/stream`, {
      method: "POST", headers: headers(),
      body: JSON.stringify({
        patient_name: patientName,
        base_profile: baseProfile,
        duration_seconds: durationSeconds,
      }),
    }).then(handle),
  getLive: () =>
    fetch(`${API}/wearable/live`, { headers: headers() }).then(handle),
};

// ── Population Health Intelligence ─────────────────────────
export const populationAPI = {
  getDistrictData: (state = "all") =>
    fetch(`${API}/population/districts?state=${state}`, { headers: headers() }).then(handle),
  getAlerts: () =>
    fetch(`${API}/population/alerts`, { headers: headers() }).then(handle),
};

// ── Federated Learning ─────────────────────────────────────
export const federatedAPI = {
  simulate: (rounds = 5) =>
    fetch(`${API}/federated/simulate?rounds=${rounds}`, { headers: headers() }).then(handle),
  getArchitecture: () =>
    fetch(`${API}/federated/architecture`, { headers: headers() }).then(handle),
};
