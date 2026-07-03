// MediTwin AI — Shared constants, styles, and demo data
// Extracted from App.jsx for clean modular architecture

export const C={cy:"#00e5ff",gr:"#00ff9d",rd:"#ff1744",am:"#ff9100",pu:"#7c4dff",ye:"#ffd740"};

export const PT={name:"Arjun Mehta",age:34,gender:"Male",blood:"B+",id:"MT-2026-0042",score:72,loc:"Hyderabad, India",lastVisit:"Mar 15, 2026",
  vitals:{hr:78,sys:128,dia:82,spo2:96,temp:98.4,glu:112,bmi:27.4,wt:82,ht:173},
  risks:{diabetes:38,heart:22,bp:45,anemia:12,stress:67},
  life:{sleep:5.5,ex:2,diet:5,hyd:1.8,stress:7,smk:false},
  meds:["Metformin 500mg (prn)","Cetirizine 10mg (seasonal)"],
  hx:["Paternal T2DM","Maternal Hypertension","Mild asthma","No drug allergies"]};

export const TL=[{m:"Sep",sc:65,dia:44,heart:26,stress:75,bp:134},{m:"Oct",sc:63,dia:46,heart:28,stress:80,bp:136},{m:"Nov",sc:68,dia:42,heart:24,stress:72,bp:130},{m:"Dec",sc:70,dia:40,heart:23,stress:68,bp:129},{m:"Jan",sc:69,dia:39,heart:22,stress:70,bp:130},{m:"Feb",sc:72,dia:38,heart:22,stress:67,bp:128}];
export const RADAR=[{s:"Cardiac",v:22},{s:"Metabolic",v:38},{s:"Neurological",v:67},{s:"Respiratory",v:15},{s:"Renal",v:8},{s:"Hepatic",v:12}];
export const PATS=[
  {id:"P-001",name:"Rahul Sharma",age:62,cond:"Chest Pain + Acute Hypertension",sc:92,lvl:"cr",vi:"168/98 mmHg | HR 112"},
  {id:"P-002",name:"Priya Nair",age:45,cond:"Hyperglycemia — Glucose 380 mg/dL",sc:78,lvl:"hi",vi:"142/88 mmHg | HR 95"},
  {id:"P-003",name:"Mohammed Ali",age:38,cond:"Severe Anxiety + Palpitations",sc:61,lvl:"md",vi:"130/84 mmHg | HR 102"},
  {id:"P-004",name:"Suresh Kumar",age:71,cond:"Diabetic Edema + Review",sc:70,lvl:"hi",vi:"150/92 mmHg | HR 88"},
  {id:"P-005",name:"Ananya Singh",age:28,cond:"Mild Anemia + Fatigue",sc:34,lvl:"lo",vi:"110/70 mmHg | HR 78"}];

// ── Real backend AI (Groq, via FastAPI) ─────────────────────────────────
// Was previously calling https://api.anthropic.com/v1/messages directly
// from the browser with no key — that only works inside Claude.ai's own
// artifact sandbox. Now routes through our own FastAPI backend, which has
// a real Groq key server-side and already-working /api/v1/ai/chat.
const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/v1";
const DEMO_EMAIL = "demo@meditwin.ai";
const DEMO_PASSWORD = "MediTwinDemo@2026";

let _authToken = null;
let _authPromise = null;

async function _ensureAuth() {
  if (_authToken) return _authToken;
  if (_authPromise) return _authPromise;
  _authPromise = (async () => {
    // Try login first; if the demo account doesn't exist yet, register it.
    let res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    });
    if (!res.ok) {
      res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Arjun Mehta", email: DEMO_EMAIL, password: DEMO_PASSWORD }),
      });
    }
    if (!res.ok) throw new Error("MediTwin backend auth failed");
    const data = await res.json();
    _authToken = data.access_token;
    return _authToken;
  })();
  try { return await _authPromise; } finally { _authPromise = null; }
}

async function _chatRequest(messages, sys = "") {
  const token = await _ensureAuth();
  // Most pages already embed full task-specific instructions in the user
  // message content. Where a distinct system prompt is also supplied
  // (e.g. AIChat.jsx), fold it in as leading context so nothing is lost —
  // the backend builds its own system prompt server-side from patient_context
  // on top of this.
  const msgs = sys
    ? [{ role: "user", content: `[Context: ${sys}]` }, ...messages]
    : messages;
  const patient_context = {
    name: PT.name, age: PT.age, health_score: PT.score,
    diabetes_risk: PT.risks.diabetes, bp_risk: PT.risks.bp,
    stress_risk: PT.risks.stress, bmi: PT.vitals.bmi,
  };
  const r = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ messages: msgs, patient_context }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || "API error");
  return d;
}

// Public helper — any page can call this to get a valid JWT without prop-drilling
export const getToken = () => _ensureAuth();

export const callAI = async (messages, sys = "") => {
  const d = await _chatRequest(messages, sys);
  return d.reply || "";
};

// Same call, but also returns the RAG-retrieved guideline sources the
// backend grounded its answer in — used by AIChat.jsx to show citation
// chips under each response (the visible answer to "how do you prevent
// hallucinations?"). Other pages can adopt this the same way; callAI is
// left untouched so none of the other ~20 call sites need to change.
export const callAIWithSources = async (messages, sys = "") => {
  const d = await _chatRequest(messages, sys);
  return { text: d.reply || "", sources: d.sources || [] };
};

export const S=`@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{font-family:'DM Sans',sans-serif;background:#02061a;color:#dff0ff;font-size:14px;line-height:1.5}
::-webkit-scrollbar{width:3px;height:3px}::-webkit-scrollbar-thumb{background:rgba(0,229,255,.18);border-radius:2px}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulseC{0%,100%{box-shadow:0 0 10px rgba(0,229,255,.25)}50%{box-shadow:0 0 28px rgba(0,229,255,.6),0 0 50px rgba(0,229,255,.12)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(200%)}}
@keyframes scanLine{0%{top:-4px;opacity:.8}95%{opacity:.8}100%{top:100%;opacity:0}}
@keyframes aura{0%,100%{transform:scale(1);opacity:.38}50%{transform:scale(1.08);opacity:.68}}
@keyframes hbeat{0%,100%{transform:scale(1)}14%{transform:scale(1.13)}28%{transform:scale(1)}42%{transform:scale(1.09)}70%{transform:scale(1)}}
.fu{animation:fadeUp .4s ease both}
.card{background:rgba(7,13,34,.82);backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);border:1px solid rgba(0,229,255,.09);border-radius:16px;position:relative;overflow:hidden}
.card::after{content:\'\';position:absolute;inset:0;background:linear-gradient(135deg,rgba(0,229,255,.022) 0%,transparent 55%);pointer-events:none;border-radius:inherit}
.gt{background:linear-gradient(135deg,#00e5ff,#7c4dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sora{font-family:\'Sora\',sans-serif}
.mono{font-family:\'DM Mono\',monospace}
.btn{padding:9px 20px;border-radius:10px;border:none;font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s ease;outline:none}
.btn-cy{background:rgba(0,229,255,.1);color:#00e5ff;border:1px solid rgba(0,229,255,.22)}
.btn-cy:hover{background:rgba(0,229,255,.2);box-shadow:0 0 18px rgba(0,229,255,.22);transform:translateY(-1px)}
.btn-solid{background:linear-gradient(135deg,#00e5ff,#7c4dff);color:#000;font-weight:700}
.btn-solid:hover{box-shadow:0 0 22px rgba(0,229,255,.38);transform:translateY(-1px)}
.btn-rd{background:rgba(255,23,68,.1);color:#ff1744;border:1px solid rgba(255,23,68,.22)}
.inp{background:rgba(255,255,255,.04);border:1px solid rgba(0,229,255,.09);border-radius:10px;padding:11px 16px;color:#dff0ff;font-family:\'DM Sans\',sans-serif;font-size:14px;outline:none;transition:all .2s;width:100%}
.inp:focus{border-color:#00e5ff;background:rgba(0,229,255,.04);box-shadow:0 0 0 3px rgba(0,229,255,.08)}
.inp::placeholder{color:#3d5978}
.slider{-webkit-appearance:none;appearance:none;width:100%;height:3px;border-radius:2px;outline:none;cursor:pointer}
.slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:14px;height:14px;border-radius:50%;background:#00e5ff;cursor:pointer;box-shadow:0 0 10px rgba(0,229,255,.6)}
.bar-w{height:5px;background:rgba(255,255,255,.07);border-radius:3px;overflow:hidden}
.bar-f{height:100%;border-radius:3px;transition:width 1.2s cubic-bezier(.4,0,.2,1);position:relative;overflow:hidden}
.bar-f::after{content:\'\';position:absolute;top:0;bottom:0;width:40%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.32),transparent);animation:shimmer 2s infinite}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:100px;font-size:11px;font-weight:700;letter-spacing:.4px}
.chip-r{background:rgba(255,23,68,.12);color:#ff1744;border:1px solid rgba(255,23,68,.22)}
.chip-a{background:rgba(255,145,0,.12);color:#ff9100;border:1px solid rgba(255,145,0,.22)}
.chip-g{background:rgba(0,255,157,.1);color:#00ff9d;border:1px solid rgba(0,255,157,.18)}
.chip-c{background:rgba(0,229,255,.1);color:#00e5ff;border:1px solid rgba(0,229,255,.18)}
.chip-p{background:rgba(124,77,255,.12);color:#b388ff;border:1px solid rgba(124,77,255,.22)}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot-live{background:#00ff9d;animation:blink 1.4s ease-in-out infinite}
.msg{border-radius:14px;padding:12px 16px;max-width:80%;font-size:13.5px;line-height:1.68;animation:fadeUp .3s ease}
.msg-u{background:linear-gradient(135deg,rgba(0,229,255,.14),rgba(124,77,255,.1));border:1px solid rgba(0,229,255,.2);align-self:flex-end;margin-left:auto}
.msg-a{background:rgba(255,255,255,.04);border:1px solid rgba(0,229,255,.09);align-self:flex-start}
.nav{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:11px;cursor:pointer;font-size:13px;font-weight:500;color:#3d5978;border:1px solid transparent;transition:all .18s ease;white-space:nowrap;overflow:hidden;user-select:none}
.nav:hover{color:#dff0ff;background:rgba(255,255,255,.04)}
.nav.on{color:#00e5ff;background:linear-gradient(135deg,rgba(0,229,255,.1),rgba(124,77,255,.07));border-color:rgba(0,229,255,.18)}
.mc{padding:16px;border-radius:13px;background:rgba(255,255,255,.03);border:1px solid rgba(0,229,255,.09);transition:all .2s;position:relative;overflow:hidden}
.mc:hover{border-color:rgba(0,229,255,.2);transform:translateY(-2px)}
.mc::before{content:\'\';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#00e5ff,transparent);opacity:0;transition:opacity .2s}
.mc:hover::before{opacity:1}
.tri-cr{background:rgba(255,23,68,.08);border:1px solid rgba(255,23,68,.28);border-radius:12px;padding:14px}
.tri-hi{background:rgba(255,145,0,.08);border:1px solid rgba(255,145,0,.25);border-radius:12px;padding:14px}
.tri-md{background:rgba(255,215,64,.06);border:1px solid rgba(255,215,64,.2);border-radius:12px;padding:14px}
.tri-lo{background:rgba(0,255,157,.06);border:1px solid rgba(0,255,157,.18);border-radius:12px;padding:14px}
.sec-h{font-family:\'Sora\',sans-serif;font-size:21px;font-weight:700;margin-bottom:4px}
.sec-s{font-size:12px;color:#3d5978;margin-bottom:20px}
@keyframes morphFuture{0%{opacity:0;transform:scale(.94) translateY(8px);filter:blur(6px);}100%{opacity:1;transform:scale(1) translateY(0);filter:blur(0);}}
@keyframes countGlow{0%{text-shadow:0 0 0px currentColor;}50%{text-shadow:0 0 22px currentColor;}100%{text-shadow:0 0 0px currentColor;}}
@keyframes pathPulse{0%,100%{stroke-opacity:.25;}50%{stroke-opacity:.85;}}
.morph{animation:morphFuture .5s cubic-bezier(.16,1,.3,1) both;}
.count-glow{animation:countGlow 1.4s ease-in-out infinite;}
.yr-btn{padding:10px 22px;border-radius:11px;font-size:13px;font-weight:700;cursor:pointer;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);color:rgba(255,255,255,.4);transition:all .18s;}
.yr-btn.on{background:linear-gradient(135deg,rgba(0,229,255,.18),rgba(124,77,255,.14));color:#00e5ff;border-color:rgba(0,229,255,.32);box-shadow:0 0 16px rgba(0,229,255,.12);}
.act-card{padding:14px;border-radius:13px;cursor:pointer;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.025);transition:all .18s;}
.act-card.on{border-color:rgba(0,255,157,.35);background:rgba(0,255,157,.06);box-shadow:0 0 18px rgba(0,255,157,.08);}
.tree-node{padding:10px 12px;border-radius:11px;min-width:108px;text-align:center;border:1px solid rgba(255,255,255,.07);background:rgba(255,255,255,.025);transition:all .18s;}
.tree-node.hl{transform:translateY(-3px);}
.heat-cell{width:34px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;}
`;

// ── ML Models (serialized weights — exported for ModelLab & crossValidation) ─
export const ML_MODELS = {
  "diabetes": {
    "coef": [
      0.07186663193560507,
      1.9753446509316885,
      0.0663462021415583,
      -0.16770720178143977,
      0.08912801536739293,
      1.2202305630072048,
      0.6963989843282782,
      0.903980954281414
    ],
    "intercept": -0.5114240920925058,
    "scaler_mean": [
      3.8631921824104234,
      123.71772313272504,
      69.51122176627213,
      23.608564402226637,
      122.19945020333566,
      32.233823292231136,
      0.4575205635620667,
      34.144951140065146
    ],
    "scaler_scale": [
      2.9947043769102604,
      31.013645061462142,
      19.026638243976873,
      12.85213948674304,
      85.40152908666546,
      7.490184848029553,
      0.3251490458903194,
      10.862787938896249
    ],
    "feature_names": [
      "Pregnancies",
      "Glucose",
      "BloodPressure",
      "SkinThickness",
      "Insulin",
      "BMI",
      "DiabetesPedigreeFunction",
      "Age"
    ],
    "metadata": {
      "disease": "Diabetes",
      "disease_key": "diabetes",
      "dataset_name": "Pima Indians Diabetes Database",
      "data_source": "offline_fallback",
      "n_samples": 768,
      "n_features": 8,
      "positive_rate": 0.345,
      "best_model": "logistic_regression",
      "model_kind": "linear",
      "explainability_method": "Permutation Importance (SHAP unavailable)",
      "all_models_compared": {
        "logistic_regression": {
          "accuracy": 0.8117,
          "f1": 0.7521,
          "roc_auc": 0.8954
        },
        "random_forest": {
          "accuracy": 0.7662,
          "f1": 0.64,
          "roc_auc": 0.8498
        },
        "gradient_boosting": {
          "accuracy": 0.7727,
          "f1": 0.6667,
          "roc_auc": 0.8322
        }
      },
      "metrics": {
        "accuracy": 0.8117,
        "precision": 0.6875,
        "recall": 0.8302,
        "f1": 0.7521,
        "roc_auc": 0.8954,
        "confusion_matrix": {
          "tn": 81,
          "fp": 20,
          "fn": 9,
          "tp": 44
        },
        "roc_curve": [
          {
            "fpr": 0.0,
            "tpr": 0.0
          },
          {
            "fpr": 0.0,
            "tpr": 0.0189
          },
          {
            "fpr": 0.0,
            "tpr": 0.4906
          },
          {
            "fpr": 0.0198,
            "tpr": 0.4906
          },
          {
            "fpr": 0.0198,
            "tpr": 0.5094
          },
          {
            "fpr": 0.0297,
            "tpr": 0.5094
          },
          {
            "fpr": 0.0297,
            "tpr": 0.5283
          },
          {
            "fpr": 0.0396,
            "tpr": 0.5283
          },
          {
            "fpr": 0.0396,
            "tpr": 0.6226
          },
          {
            "fpr": 0.0495,
            "tpr": 0.6226
          },
          {
            "fpr": 0.0495,
            "tpr": 0.6604
          },
          {
            "fpr": 0.0594,
            "tpr": 0.6604
          },
          {
            "fpr": 0.0594,
            "tpr": 0.717
          },
          {
            "fpr": 0.0891,
            "tpr": 0.717
          },
          {
            "fpr": 0.0891,
            "tpr": 0.7547
          },
          {
            "fpr": 0.1386,
            "tpr": 0.7547
          },
          {
            "fpr": 0.1386,
            "tpr": 0.7925
          },
          {
            "fpr": 0.1485,
            "tpr": 0.7925
          },
          {
            "fpr": 0.1485,
            "tpr": 0.8113
          },
          {
            "fpr": 0.198,
            "tpr": 0.8113
          },
          {
            "fpr": 0.198,
            "tpr": 0.8302
          },
          {
            "fpr": 0.2277,
            "tpr": 0.8302
          },
          {
            "fpr": 0.2277,
            "tpr": 0.8491
          },
          {
            "fpr": 0.2772,
            "tpr": 0.8491
          },
          {
            "fpr": 0.2772,
            "tpr": 0.8679
          },
          {
            "fpr": 0.3267,
            "tpr": 0.8679
          },
          {
            "fpr": 0.3267,
            "tpr": 0.8868
          },
          {
            "fpr": 0.4455,
            "tpr": 0.8868
          },
          {
            "fpr": 0.4455,
            "tpr": 0.9057
          },
          {
            "fpr": 0.505,
            "tpr": 0.9057
          },
          {
            "fpr": 0.505,
            "tpr": 0.9245
          },
          {
            "fpr": 0.5644,
            "tpr": 0.9245
          },
          {
            "fpr": 0.5644,
            "tpr": 0.9434
          },
          {
            "fpr": 0.5743,
            "tpr": 0.9434
          },
          {
            "fpr": 0.5743,
            "tpr": 0.9623
          },
          {
            "fpr": 0.604,
            "tpr": 0.9623
          },
          {
            "fpr": 0.604,
            "tpr": 0.9811
          },
          {
            "fpr": 0.6931,
            "tpr": 0.9811
          },
          {
            "fpr": 0.6931,
            "tpr": 1.0
          },
          {
            "fpr": 1.0,
            "tpr": 1.0
          }
        ]
      },
      "global_feature_importance": [
        {
          "feature": "Glucose",
          "importance": 1.9753
        },
        {
          "feature": "BMI",
          "importance": 1.2202
        },
        {
          "feature": "Age",
          "importance": 0.904
        },
        {
          "feature": "DiabetesPedigreeFunction",
          "importance": 0.6964
        },
        {
          "feature": "SkinThickness",
          "importance": 0.1677
        },
        {
          "feature": "Insulin",
          "importance": 0.0891
        },
        {
          "feature": "Pregnancies",
          "importance": 0.0719
        },
        {
          "feature": "BloodPressure",
          "importance": 0.0663
        }
      ],
      "trained_at": "2026-06-18T04:21:01Z",
      "training_time_ms": 659
    }
  },
  "heart": {
    "coef": [
      0.31096012623377667,
      0.6378155254212907,
      0.6936636675747998,
      0.6361384468057879,
      0.47535155360479575,
      0.1567428115293479,
      0.07433214865865044,
      -1.269830961008473,
      1.1809721081594216,
      0.5577603452328724,
      -0.019206493580810197,
      0.8254876017832057,
      -0.07648068844307875
    ],
    "intercept": 0.11936489848291988,
    "scaler_mean": [
      54.22314049586777,
      0.6652892561983471,
      1.4586776859504131,
      133.98596152371667,
      250.6564478970107,
      0.1322314049586777,
      1.0,
      150.02698506495724,
      0.371900826446281,
      1.0673393776327,
      0.9917355371900827,
      0.7520661157024794,
      4.6735537190082646
    ],
    "scaler_scale": [
      8.942874353782104,
      0.47188924737208937,
      1.0872795242633089,
      18.638195776560742,
      55.84357783803708,
      0.3387421740813096,
      0.8028873514843496,
      24.160155951372484,
      0.4833121162715185,
      0.8353040488200325,
      0.8331545923101678,
      1.0186767606734488,
      1.8864575483760568
    ],
    "feature_names": [
      "age",
      "sex",
      "cp",
      "trestbps",
      "chol",
      "fbs",
      "restecg",
      "thalach",
      "exang",
      "oldpeak",
      "slope",
      "ca",
      "thal"
    ],
    "metadata": {
      "disease": "Heart Disease",
      "disease_key": "heart",
      "dataset_name": "UCI Heart Disease (Cleveland)",
      "data_source": "offline_fallback",
      "n_samples": 303,
      "n_features": 13,
      "positive_rate": 0.482,
      "best_model": "logistic_regression",
      "model_kind": "linear",
      "explainability_method": "Permutation Importance (SHAP unavailable)",
      "all_models_compared": {
        "logistic_regression": {
          "accuracy": 0.8361,
          "f1": 0.8333,
          "roc_auc": 0.9149
        },
        "random_forest": {
          "accuracy": 0.8689,
          "f1": 0.8621,
          "roc_auc": 0.9149
        },
        "gradient_boosting": {
          "accuracy": 0.7541,
          "f1": 0.7368,
          "roc_auc": 0.8728
        }
      },
      "metrics": {
        "accuracy": 0.8361,
        "precision": 0.8065,
        "recall": 0.8621,
        "f1": 0.8333,
        "roc_auc": 0.9149,
        "confusion_matrix": {
          "tn": 26,
          "fp": 6,
          "fn": 4,
          "tp": 25
        },
        "roc_curve": [
          {
            "fpr": 0.0,
            "tpr": 0.0
          },
          {
            "fpr": 0.0,
            "tpr": 0.0345
          },
          {
            "fpr": 0.0,
            "tpr": 0.4483
          },
          {
            "fpr": 0.0312,
            "tpr": 0.4483
          },
          {
            "fpr": 0.0312,
            "tpr": 0.5517
          },
          {
            "fpr": 0.0625,
            "tpr": 0.5517
          },
          {
            "fpr": 0.0625,
            "tpr": 0.7586
          },
          {
            "fpr": 0.0938,
            "tpr": 0.7586
          },
          {
            "fpr": 0.0938,
            "tpr": 0.8276
          },
          {
            "fpr": 0.125,
            "tpr": 0.8276
          },
          {
            "fpr": 0.125,
            "tpr": 0.8621
          },
          {
            "fpr": 0.3438,
            "tpr": 0.8621
          },
          {
            "fpr": 0.3438,
            "tpr": 0.8966
          },
          {
            "fpr": 0.375,
            "tpr": 0.8966
          },
          {
            "fpr": 0.375,
            "tpr": 0.9655
          },
          {
            "fpr": 0.5938,
            "tpr": 0.9655
          },
          {
            "fpr": 0.5938,
            "tpr": 1.0
          },
          {
            "fpr": 1.0,
            "tpr": 1.0
          }
        ]
      },
      "global_feature_importance": [
        {
          "feature": "thalach",
          "importance": 1.2698
        },
        {
          "feature": "exang",
          "importance": 1.181
        },
        {
          "feature": "ca",
          "importance": 0.8255
        },
        {
          "feature": "cp",
          "importance": 0.6937
        },
        {
          "feature": "sex",
          "importance": 0.6378
        },
        {
          "feature": "trestbps",
          "importance": 0.6361
        },
        {
          "feature": "oldpeak",
          "importance": 0.5578
        },
        {
          "feature": "chol",
          "importance": 0.4754
        },
        {
          "feature": "age",
          "importance": 0.311
        },
        {
          "feature": "fbs",
          "importance": 0.1567
        },
        {
          "feature": "thal",
          "importance": 0.0765
        },
        {
          "feature": "restecg",
          "importance": 0.0743
        },
        {
          "feature": "slope",
          "importance": 0.0192
        }
      ],
      "trained_at": "2026-06-18T04:21:01Z",
      "training_time_ms": 454
    }
  },
  "stroke": {
    "coef": [
      2.0167428379974286,
      0.6225987992399706,
      0.4706442192267566,
      1.0884396839956372,
      0.4172888946343729,
      -0.012462496609689368,
      0.012462496609689368,
      0.03068094873637015,
      -0.03068094873637015,
      0.07436853717358718,
      -0.1745626897641977,
      -0.043499002070497776,
      0.07050271225138836,
      -0.033372563437177795,
      -0.006331614129809144,
      0.006331614129809777,
      0.002255078875557976,
      -0.04831103586496257,
      0.06969378607119714,
      -0.04617404971741917
    ],
    "intercept": -2.118803679187042,
    "scaler_mean": [
      43.351404354753754,
      0.10004892367906067,
      0.05626223091976516,
      157.00058575675996,
      28.93004770235669,
      0.5858610567514677,
      0.4141389432485323,
      0.34711350293542076,
      0.6528864970645792,
      0.12181996086105674,
      0.011007827788649706,
      0.574119373776908,
      0.1687866927592955,
      0.12426614481409001,
      0.48948140900195697,
      0.5105185909980431,
      0.31800391389432486,
      0.1670743639921722,
      0.36350293542074363,
      0.1514187866927593
    ],
    "scaler_scale": [
      19.574786344182897,
      0.3000652204933444,
      0.2304274121967557,
      53.54972025310291,
      7.771726651951757,
      0.4925727143615751,
      0.4925727143615751,
      0.4760522229916894,
      0.4760522229916894,
      0.3270777552767292,
      0.10433913702932596,
      0.4944758016636849,
      0.3745634059898002,
      0.32988493458648016,
      0.4998893469993315,
      0.4998893469993315,
      0.46570100347993143,
      0.37304225080917863,
      0.48100784958379067,
      0.3584566050852619
    ],
    "feature_names": [
      "age",
      "hypertension",
      "heart_disease",
      "avg_glucose_level",
      "bmi",
      "gender_Female",
      "gender_Male",
      "ever_married_No",
      "ever_married_Yes",
      "work_type_Govt_job",
      "work_type_Never_worked",
      "work_type_Private",
      "work_type_Self-employed",
      "work_type_children",
      "Residence_type_Rural",
      "Residence_type_Urban",
      "smoking_status_Unknown",
      "smoking_status_formerly smoked",
      "smoking_status_never smoked",
      "smoking_status_smokes"
    ],
    "metadata": {
      "disease": "Stroke",
      "disease_key": "stroke",
      "dataset_name": "Stroke Prediction Dataset (Kaggle, fedesoriano)",
      "data_source": "offline_fallback",
      "n_samples": 5110,
      "n_features": 20,
      "positive_rate": 0.052,
      "best_model": "logistic_regression",
      "model_kind": "linear",
      "explainability_method": "Permutation Importance (SHAP unavailable)",
      "all_models_compared": {
        "logistic_regression": {
          "accuracy": 0.8503,
          "f1": 0.3704,
          "roc_auc": 0.9193
        },
        "random_forest": {
          "accuracy": 0.8796,
          "f1": 0.3881,
          "roc_auc": 0.901
        },
        "gradient_boosting": {
          "accuracy": 0.9481,
          "f1": 0.209,
          "roc_auc": 0.8974
        }
      },
      "metrics": {
        "accuracy": 0.8503,
        "precision": 0.2368,
        "recall": 0.8491,
        "f1": 0.3704,
        "roc_auc": 0.9193,
        "confusion_matrix": {
          "tn": 824,
          "fp": 145,
          "fn": 8,
          "tp": 45
        },
        "roc_curve": [
          {
            "fpr": 0.0,
            "tpr": 0.0
          },
          {
            "fpr": 0.0,
            "tpr": 0.0189
          },
          {
            "fpr": 0.001,
            "tpr": 0.0566
          },
          {
            "fpr": 0.0021,
            "tpr": 0.0755
          },
          {
            "fpr": 0.0031,
            "tpr": 0.0943
          },
          {
            "fpr": 0.0093,
            "tpr": 0.1132
          },
          {
            "fpr": 0.0114,
            "tpr": 0.1321
          },
          {
            "fpr": 0.0134,
            "tpr": 0.1509
          },
          {
            "fpr": 0.0155,
            "tpr": 0.2075
          },
          {
            "fpr": 0.0196,
            "tpr": 0.2264
          },
          {
            "fpr": 0.0217,
            "tpr": 0.2453
          },
          {
            "fpr": 0.0227,
            "tpr": 0.3208
          },
          {
            "fpr": 0.0248,
            "tpr": 0.3585
          },
          {
            "fpr": 0.0289,
            "tpr": 0.4151
          },
          {
            "fpr": 0.0351,
            "tpr": 0.434
          },
          {
            "fpr": 0.0361,
            "tpr": 0.4717
          },
          {
            "fpr": 0.0372,
            "tpr": 0.4906
          },
          {
            "fpr": 0.0413,
            "tpr": 0.5094
          },
          {
            "fpr": 0.0444,
            "tpr": 0.5472
          },
          {
            "fpr": 0.0537,
            "tpr": 0.5849
          },
          {
            "fpr": 0.0578,
            "tpr": 0.6226
          },
          {
            "fpr": 0.063,
            "tpr": 0.6415
          },
          {
            "fpr": 0.0764,
            "tpr": 0.6604
          },
          {
            "fpr": 0.0774,
            "tpr": 0.6792
          },
          {
            "fpr": 0.0795,
            "tpr": 0.6981
          },
          {
            "fpr": 0.0867,
            "tpr": 0.717
          },
          {
            "fpr": 0.0898,
            "tpr": 0.7358
          },
          {
            "fpr": 0.1176,
            "tpr": 0.7547
          },
          {
            "fpr": 0.1424,
            "tpr": 0.7736
          },
          {
            "fpr": 0.1445,
            "tpr": 0.7925
          },
          {
            "fpr": 0.1496,
            "tpr": 0.8113
          },
          {
            "fpr": 0.1713,
            "tpr": 0.8491
          },
          {
            "fpr": 0.1858,
            "tpr": 0.8679
          },
          {
            "fpr": 0.2157,
            "tpr": 0.8868
          },
          {
            "fpr": 0.2611,
            "tpr": 0.9057
          },
          {
            "fpr": 0.2714,
            "tpr": 0.9245
          },
          {
            "fpr": 0.29,
            "tpr": 0.9434
          },
          {
            "fpr": 0.4076,
            "tpr": 0.9623
          },
          {
            "fpr": 0.4799,
            "tpr": 0.9811
          },
          {
            "fpr": 1.0,
            "tpr": 1.0
          }
        ]
      },
      "global_feature_importance": [
        {
          "feature": "age",
          "importance": 2.0167
        },
        {
          "feature": "avg_glucose_level",
          "importance": 1.0884
        },
        {
          "feature": "hypertension",
          "importance": 0.6226
        },
        {
          "feature": "heart_disease",
          "importance": 0.4706
        },
        {
          "feature": "bmi",
          "importance": 0.4173
        },
        {
          "feature": "work_type_Never_worked",
          "importance": 0.1746
        },
        {
          "feature": "work_type_Govt_job",
          "importance": 0.0744
        },
        {
          "feature": "work_type_Self-employed",
          "importance": 0.0705
        },
        {
          "feature": "smoking_status_never smoked",
          "importance": 0.0697
        },
        {
          "feature": "smoking_status_formerly smoked",
          "importance": 0.0483
        },
        {
          "feature": "smoking_status_smokes",
          "importance": 0.0462
        },
        {
          "feature": "work_type_Private",
          "importance": 0.0435
        },
        {
          "feature": "work_type_children",
          "importance": 0.0334
        },
        {
          "feature": "ever_married_Yes",
          "importance": 0.0307
        },
        {
          "feature": "ever_married_No",
          "importance": 0.0307
        },
        {
          "feature": "gender_Female",
          "importance": 0.0125
        },
        {
          "feature": "gender_Male",
          "importance": 0.0125
        },
        {
          "feature": "Residence_type_Urban",
          "importance": 0.0063
        },
        {
          "feature": "Residence_type_Rural",
          "importance": 0.0063
        },
        {
          "feature": "smoking_status_Unknown",
          "importance": 0.0023
        }
      ],
      "trained_at": "2026-06-18T04:21:03Z",
      "training_time_ms": 1637
    }
  }
};

// ── Clinical scoring helpers (exported for FamilyTwin, CostTimeBomb, ModelLab) ─
export function findriscPct(age, bmi, exDays, diet, glucose, familyDiabetes) {
  let pts = 0;
  pts += age < 45 ? 0 : age <= 54 ? 2 : age <= 64 ? 3 : 4;
  pts += bmi < 25 ? 0 : bmi <= 30 ? 1 : 3;
  pts += exDays >= 4 ? 0 : 2;
  pts += diet >= 7 ? 0 : 1;
  pts += glucose >= 100 ? 5 : 0;
  pts += familyDiabetes ? 5 : 0;
  if (pts < 7) return 1;
  if (pts < 12) return 4;
  if (pts < 15) return 17;
  if (pts < 21) return 33;
  return 50;
}

export function heartPct(age, sbp, smoking, glucose, familyCVD, bmi, exDays, stress) {
  let pts = 0;
  pts += age < 40 ? 0 : age < 50 ? 1 : age < 60 ? 2 : 3;
  pts += sbp < 120 ? 0 : sbp < 140 ? 1 : sbp < 160 ? 2 : 3;
  pts += smoking ? 2 : 0;
  pts += glucose >= 126 ? 2 : 0;
  pts += familyCVD ? 2 : 0;
  pts += bmi >= 30 ? 1 : 0;
  pts += exDays < 1 ? 1 : 0;
  pts += stress >= 8 ? 1 : 0;
  if (pts <= 2) return 4;
  if (pts <= 5) return 9;
  if (pts <= 8) return 18;
  return 32;
}

