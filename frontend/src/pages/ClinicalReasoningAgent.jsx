import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import { C, PT, getToken } from "../shared";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function analyzeReasoning(profile) {
  const token = await getToken();
  const r = await fetch(`${API}/api/v1/reasoning/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(profile),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || `Server error ${r.status}`);
  }
  return r.json();
}

const RISK_COLORS = { "Diabetes": "#ff9100", "Heart Disease": "#ff1744", "Hypertension": "#7c4dff", "Stress Syndrome": "#00e5ff", "Anemia": "#00ff9d" };
const YEAR = 2026;

export default function ClinicalReasoningAgent() {
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState("");
  const [step,    setStep]    = useState("idle"); // idle | simulating | narrating | done

  const run = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      setStep("simulating");
      await new Promise(r => setTimeout(r, 600));
      setStep("narrating");
      const data = await analyzeReasoning({
        name:      PT.name,
        age:       PT.age,
        gender:    PT.gender,
        vitals:    PT.vitals,
        lifestyle: { smoking: PT.life.smk, exercise_days_per_week: PT.life.ex, sleep_hours: PT.life.sleep, diet_quality: PT.life.diet },
        history:   PT.hx,
      });
      setResult(data);
      setStep("done");
    } catch (e) {
      setError(e.message);
      setStep("idle");
    } finally {
      setLoading(false);
    }
  };

  // Build chart data from trajectories
  const chartData = result ? [YEAR, YEAR+1, YEAR+3, YEAR+5, YEAR+10].map((yr, i) => {
    const keys = ["current","1yr","3yr","5yr","10yr"];
    const row = { year: yr.toString() };
    Object.entries(result.trajectories || {}).forEach(([disease, traj]) => {
      row[disease] = i === 0 ? traj.current : traj.horizons?.[keys[i]];
    });
    return row;
  }) : [];

  return (
    <div className="fu" style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:8 }}>
          <div style={{ fontSize:32 }}>🧠</div>
          <div>
            <div className="sora gt" style={{ fontSize:26, fontWeight:800 }}>Clinical Reasoning Agent</div>
            <div style={{ fontSize:13, color:"rgba(255,255,255,0.38)", marginTop:2 }}>
              Multi-year disease progression simulation · Causal chain AI · Intervention forks
            </div>
          </div>
        </div>
        <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginTop:12 }}>
          {["UKPDS Risk Engine","Framingham Study","WHO/ICMR Guidelines","RAG Grounded","Groq LLM Narration"].map(t => (
            <span key={t} className="chip chip-c" style={{ fontSize:10 }}>{t}</span>
          ))}
        </div>
      </div>

      {/* Patient context card */}
      <div className="card" style={{ padding:18, marginBottom:20, display:"flex", gap:20, alignItems:"center", flexWrap:"wrap" }}>
        <div style={{ fontSize:40 }}>👤</div>
        <div>
          <div className="sora" style={{ fontSize:16, fontWeight:700 }}>{PT.name}</div>
          <div style={{ fontSize:12, color:"rgba(255,255,255,0.38)", marginTop:2 }}>
            {PT.age}y · {PT.gender} · BMI {PT.vitals.bmi} · {PT.loc}
          </div>
          <div style={{ fontSize:11, color:"rgba(255,255,255,0.25)", marginTop:4 }}>
            {PT.hx.join(" · ")}
          </div>
        </div>
        <button
          className="btn btn-solid" onClick={run} disabled={loading}
          style={{ marginLeft:"auto", padding:"13px 32px", fontSize:14, opacity: loading ? 0.7 : 1 }}
        >
          {loading ? "Reasoning..." : "🧠 Run Clinical Reasoning Agent"}
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="card" style={{ padding:32, textAlign:"center", marginBottom:20 }}>
          <div style={{ fontSize:36, marginBottom:16, animation:"hbeat 1.2s ease-in-out infinite" }}>🫀</div>
          <div className="sora" style={{ fontSize:16, fontWeight:700, marginBottom:8 }}>
            {step === "simulating" ? "Simulating 10-year disease trajectory..." : "Generating causal chain narrative..."}
          </div>
          <div style={{ fontSize:12, color:"rgba(255,255,255,0.35)" }}>
            {step === "simulating"
              ? "Running UKPDS / Framingham / JNC-8 progression models"
              : "RAG retrieving WHO/ICMR guidelines · Groq narrating causal chain"}
          </div>
        </div>
      )}

      {error && (
        <div className="card" style={{ padding:18, marginBottom:20, borderColor:"rgba(255,23,68,0.3)" }}>
          <span style={{ color:C.rd }}>⚠ {error}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Primary threat banner */}
          {result.primary_threat && (
            <div style={{
              padding:"20px 24px", borderRadius:14, marginBottom:20,
              background: result.primary_threat.already_high
                ? "rgba(255,23,68,0.1)" : "rgba(255,145,0,0.1)",
              border:`1px solid ${result.primary_threat.already_high ? C.rd : C.am}`,
            }}>
              <div style={{ display:"flex", alignItems:"center", gap:12 }}>
                <div style={{ fontSize:28 }}>⚠️</div>
                <div>
                  <div className="sora" style={{ fontSize:15, fontWeight:700, color: result.primary_threat.already_high ? C.rd : C.am }}>
                    Primary Threat: {result.primary_threat.disease}
                  </div>
                  <div style={{ fontSize:13, color:"rgba(255,255,255,0.6)", marginTop:3 }}>
                    {result.primary_threat.already_high
                      ? `Already at high-risk threshold — ${result.primary_threat.current_risk.toFixed(0)}% current risk`
                      : `Onset predicted ~${result.primary_threat.onset_year} (${result.primary_threat.years_from_now} year${result.primary_threat.years_from_now > 1 ? "s":""})`}
                    {" · "}{result.primary_threat.source}
                  </div>
                </div>
                {!result.primary_threat.already_high && (
                  <div style={{ marginLeft:"auto", textAlign:"center" }}>
                    <div className="sora count-glow" style={{ fontSize:32, fontWeight:800, color:C.am }}>
                      {result.primary_threat.onset_year}
                    </div>
                    <div style={{ fontSize:10, color:"rgba(255,255,255,0.3)" }}>PREDICTED ONSET</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Causal chain — the killer GenAI output */}
          <div className="card" style={{ padding:24, marginBottom:20 }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:14 }}>
              <span style={{ fontSize:18 }}>🔗</span>
              <span className="sora" style={{ fontSize:15, fontWeight:700 }}>AI Causal Chain Analysis</span>
              <span className="chip chip-c" style={{ fontSize:10, marginLeft:8 }}>RAG Grounded</span>
              {result.rag_sources?.length > 0 && (
                <span style={{ fontSize:10, color:"rgba(255,255,255,0.25)", marginLeft:4 }}>
                  via {result.rag_sources[0]}
                </span>
              )}
            </div>
            <div style={{
              fontSize:14, lineHeight:1.8, color:"rgba(255,255,255,0.82)",
              background:"rgba(0,229,255,0.03)", borderRadius:10,
              padding:"16px 20px", border:"1px solid rgba(0,229,255,0.08)",
              fontStyle:"normal",
            }}>
              {result.causal_chain}
            </div>
            <div style={{ fontSize:10, color:"rgba(255,255,255,0.2)", marginTop:10 }}>
              {result.reasoning_method}
            </div>
          </div>

          {/* 10-year trajectory chart */}
          <div className="card" style={{ padding:24, marginBottom:20 }}>
            <div className="sora" style={{ fontSize:15, fontWeight:700, marginBottom:4 }}>
              📈 10-Year Disease Progression Trajectories
            </div>
            <div style={{ fontSize:11, color:"rgba(255,255,255,0.3)", marginBottom:18 }}>
              Computed via validated progression models · Thresholds shown as reference lines
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="year" tick={{ fill:"rgba(255,255,255,0.4)", fontSize:11 }} />
                <YAxis domain={[0,100]} tick={{ fill:"rgba(255,255,255,0.4)", fontSize:11 }} unit="%" />
                <Tooltip
                  contentStyle={{ background:"#07102a", border:"1px solid rgba(0,229,255,0.2)", borderRadius:8, fontSize:12 }}
                  formatter={(v, n) => [`${v?.toFixed(1)}%`, n]}
                />
                <Legend wrapperStyle={{ fontSize:11, color:"rgba(255,255,255,0.5)" }} />
                <ReferenceLine y={60} stroke="rgba(255,145,0,0.3)" strokeDasharray="4 4" label={{ value:"Onset zone", fill:"rgba(255,145,0,0.5)", fontSize:10 }} />
                {Object.keys(result.trajectories || {}).map(disease => (
                  <Line
                    key={disease}
                    type="monotone"
                    dataKey={disease}
                    stroke={RISK_COLORS[disease] || C.cy}
                    strokeWidth={2}
                    dot={{ r:4, fill:RISK_COLORS[disease] || C.cy }}
                    activeDot={{ r:6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* All onset events */}
          {result.onset_events?.length > 0 && (
            <div className="card" style={{ padding:24, marginBottom:20 }}>
              <div className="sora" style={{ fontSize:15, fontWeight:700, marginBottom:14 }}>
                🗓 Predicted Onset Timeline
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))", gap:12 }}>
                {result.onset_events.map((e, i) => (
                  <div key={i} style={{
                    padding:14, borderRadius:11,
                    background: e.already_high ? "rgba(255,23,68,0.08)" : "rgba(255,145,0,0.06)",
                    border:`1px solid ${e.already_high ? "rgba(255,23,68,0.25)" : "rgba(255,145,0,0.2)"}`,
                  }}>
                    <div style={{ fontSize:11, fontWeight:700, color: RISK_COLORS[e.disease] || C.cy, marginBottom:4 }}>
                      {e.disease}
                    </div>
                    <div className="sora" style={{ fontSize:22, fontWeight:800, color: e.already_high ? C.rd : C.am }}>
                      {e.already_high ? "NOW" : e.onset_year}
                    </div>
                    <div style={{ fontSize:11, color:"rgba(255,255,255,0.35)", marginTop:3 }}>
                      {e.already_high ? `${e.current_risk.toFixed(0)}% — already high` : `${e.years_from_now}y · ${e.projected_risk.toFixed(0)}% projected`}
                    </div>
                    {e.source && <div style={{ fontSize:9, color:"rgba(255,255,255,0.2)", marginTop:4 }}>{e.source}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Intervention forks */}
          {result.intervention_forks?.length > 0 && (
            <div className="card" style={{ padding:24, marginBottom:20 }}>
              <div className="sora" style={{ fontSize:15, fontWeight:700, marginBottom:4 }}>🔀 Intervention Forks — 5-Year Projection</div>
              <div style={{ fontSize:11, color:"rgba(255,255,255,0.3)", marginBottom:18 }}>
                What changes if {result.patient_name} acts now vs waits
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))", gap:16 }}>
                {result.intervention_forks.map((fork, i) => (
                  <div key={i} style={{
                    padding:18, borderRadius:13,
                    background: i === 0 ? "rgba(255,23,68,0.06)" : i === 1 ? "rgba(255,145,0,0.06)" : "rgba(0,255,157,0.06)",
                    border:`1px solid ${i === 0 ? "rgba(255,23,68,0.2)" : i === 1 ? "rgba(255,145,0,0.2)" : "rgba(0,255,157,0.2)"}`,
                  }}>
                    <div style={{ fontSize:11, fontWeight:700, color: i===0?C.rd:i===1?C.am:C.gr, marginBottom:6 }}>{fork.label}</div>
                    <div style={{ display:"flex", alignItems:"baseline", gap:6, marginBottom:8 }}>
                      <span className="sora" style={{ fontSize:28, fontWeight:800, color: i===0?C.rd:i===1?C.am:C.gr }}>
                        {fork.risk_5yr.toFixed(0)}%
                      </span>
                      <span style={{ fontSize:11, color:"rgba(255,255,255,0.4)" }}>5-year risk</span>
                      {fork.delta > 0 && (
                        <span style={{ fontSize:11, color:C.gr, marginLeft:"auto" }}>▼ {fork.delta.toFixed(0)}% reduction</span>
                      )}
                    </div>
                    {fork.actions?.length > 0 && (
                      <div style={{ marginBottom:10 }}>
                        {fork.actions.map((a,j) => (
                          <div key={j} style={{ fontSize:11, color:"rgba(255,255,255,0.55)", marginBottom:3 }}>• {a}</div>
                        ))}
                      </div>
                    )}
                    {fork.narrative && (
                      <div style={{ fontSize:12, color:"rgba(255,255,255,0.65)", fontStyle:"italic", lineHeight:1.6, borderTop:"1px solid rgba(255,255,255,0.06)", paddingTop:10 }}>
                        "{fork.narrative}"
                      </div>
                    )}
                    {fork.evidence && (
                      <div style={{ fontSize:9, color:"rgba(255,255,255,0.2)", marginTop:8 }}>{fork.evidence}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
