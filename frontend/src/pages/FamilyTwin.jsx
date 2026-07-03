import { useState, useEffect, useRef, useMemo } from "react";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PATS, PT, RADAR, TL, callAI, findriscPct, heartPct } from "../shared";
import { Avatar, Gauge, MTile, RBar, Dots } from "../components/SharedUI";


// Framingham-inspired hypertension risk
export function hyperPct(age, sbp, bmi, familyHyper, sleep, stress, diet) {
  let pts = 0;
  pts += age < 40 ? 0 : age < 55 ? 1 : 2;
  pts += sbp < 120 ? 0 : sbp < 130 ? 1 : sbp < 140 ? 2 : 4;
  pts += bmi < 25 ? 0 : bmi < 30 ? 1 : 2;
  pts += familyHyper ? 2 : 0;
  pts += sleep < 6 ? 2 : sleep < 7 ? 1 : 0;
  pts += stress >= 8 ? 2 : stress >= 6 ? 1 : 0;
  pts += diet < 5 ? 1 : 0;
  if (pts <= 2) return 8;
  if (pts <= 5) return 22;
  if (pts <= 8) return 45;
  return 65;
}

// Framingham-inspired heart disease risk

// Composite lifestyle-stress index
export function stressPct(sleep, exDays, stress, alcohol = 0) {
  let pts = 0;
  pts += sleep < 5.5 ? 3 : sleep < 6.5 ? 2 : sleep < 7.5 ? 1 : 0;
  pts += exDays === 0 ? 2 : exDays < 3 ? 1 : 0;
  pts += stress * 0.4;
  pts += alcohol > 7 ? 1 : 0;
  return Math.min(95, +((pts / 10) * 100).toFixed(1));
}

// Biological age (±15yr cap)
export function bioAge(age, bmi, sbp, glu, sleep, stress, smoking = false) {
  let delta = 0.3*(bmi-22) + 0.05*Math.max(0,sbp-120) + 0.05*Math.max(0,glu-90)
            + 0.8*Math.max(0,7-sleep) + 0.5*Math.max(0,stress-5) + (smoking?5:0);
  delta = Math.max(-15, Math.min(15, delta));
  return Math.round(age + delta);
}

// Organ health composite (0-100)
export function organScores(risks, sleep, age, smoking = false) {
  const clamp = v => Math.max(10, Math.min(100, Math.round(v)));
  return {
    Heart:    clamp(100 - (risks.heart*0.6 + risks.bp*0.4)),
    Pancreas: clamp(100 - risks.diabetes),
    Kidneys:  clamp(100 - (risks.bp*0.5 + risks.diabetes*0.3)),
    Lungs:    clamp(100 - (smoking?15:0) - Math.max(0,(age-40)*0.3)),
    Brain:    clamp(100 - (risks.stress*0.6 + Math.max(0,(7-sleep)*4))),
  };
}

// Overall health score (mirrors compute_health_score)
export function healthScoreOf(risks, sbp, bmi, sleep, stress) {
  const avg = (risks.diabetes+risks.heart+risks.bp+risks.anemia+risks.stress)/5;
  const bpPen  = Math.max(0,(sbp-120)*0.3);
  const bmiPen = Math.max(0,(bmi-25)*1.5);
  const slpPen = Math.max(0,(7-sleep)*3);
  const strPen = Math.max(0,(stress-5)*2);
  const base = 100 - (avg*0.5) - bpPen - bmiPen - slpPen - strPen;
  return Math.max(20, Math.min(100, Math.round(base)));
}

// ═══════════════════════════════════════════════════════════
//  COUNT-UP HOOK — for the ₹ savings / life-expectancy reveals
// ═══════════════════════════════════════════════════════════
export function useCountUp(target, duration = 800) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = null;
    let raf;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min(1, (ts - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setVal(target * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

// ═══════════════════════════════════════════════════════════
//  MODULE 1 — GENERATIONAL HEALTH TWIN (Family Health Intelligence)
// ═══════════════════════════════════════════════════════════

// Additive constant — append near other PT-adjacent constants in App.jsx
const FAMILY = [
  { id:"pgf", relation:"Paternal Grandfather", generation:-2, alive:false,
    conditions:["Type 2 Diabetes","Heart Disease"], ageAtDx:{"Type 2 Diabetes":48,"Heart Disease":65} },
  { id:"pgm", relation:"Paternal Grandmother", generation:-2, alive:true, age:80, conditions:[] },
  { id:"mgf", relation:"Maternal Grandfather", generation:-2, alive:false,
    conditions:["Hypertension"], ageAtDx:{"Hypertension":55} },
  { id:"mgm", relation:"Maternal Grandmother", generation:-2, alive:true, age:76, conditions:["Anemia"] },
  { id:"father", relation:"Father", generation:-1, name:"Rajesh", age:62, alive:true,
    conditions:["Type 2 Diabetes"], ageAtDx:{"Type 2 Diabetes":52} },
  { id:"mother", relation:"Mother", generation:-1, name:"Sunita", age:58, alive:true,
    conditions:["Hypertension"], ageAtDx:{"Hypertension":50} },
  { id:"sister", relation:"Younger Sister", generation:0, name:"Priya", age:29, alive:true,
    conditions:["Anemia"], ageAtDx:{"Anemia":26} },
  { id:"child", relation:"Future Child", generation:1, name:"—", alive:true, conditions:[], hypothetical:true },
];

const DZ = {
  diabetes: { label:"Diabetes",        icon:"🩸", color:C.am, kw:["diabetes","t2dm","sugar"] },
  heart:    { label:"Heart Disease",   icon:"❤️", color:C.rd, kw:["heart","cardiac","cvd"] },
  bp:       { label:"Hypertension",    icon:"🫀", color:C.rd, kw:["hypertension","bp","blood pressure"] },
  anemia:   { label:"Anemia",          icon:"🔬", color:C.ye, kw:["anemia"] },
  stress:   { label:"Stress Syndrome", icon:"🧠", color:C.pu, kw:["anxiety","depression","stress"] },
};

const degreeWeight = (m) => (m.generation===-1||m.generation===0) ? 1.0 : m.generation===-2 ? 0.4 : 0.3;
const onsetWeight  = (m,cond) => { const o=m.ageAtDx?.[cond]; return (o!=null && o<50) ? 1.3 : 1.0; };
const matchesDz    = (cond,key) => { const c=cond.toLowerCase(); return DZ[key].kw.some(k=>c.includes(k)); };

function computeHereditary() {
  return Object.entries(PT.risks).map(([key, base]) => {
    let weightSum = 0;
    const contributors = [];
    FAMILY.forEach(m => {
      if (m.hypothetical) return;
      m.conditions.forEach(cond => {
        if (matchesDz(cond, key)) {
          const w = degreeWeight(m) * onsetWeight(m, cond);
          weightSum += w;
          contributors.push({ relation:m.relation, condition:cond, age:m.ageAtDx?.[cond], weight:+w.toFixed(2) });
        }
      });
    });
    const multiplier = +Math.min(3, 1 + 0.5*weightSum).toFixed(2);
    const adjusted   = +Math.min(95, base*multiplier).toFixed(1);
    return { key, ...DZ[key], base, multiplier, adjusted, contributors };
  });
}

function FamilyTwin() {
  const hereditary = useMemo(() => computeHereditary(), []);
  const [hoveredDz, setHoveredDz] = useState(null);
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);

  const generations = [
    { label:"Grandparents", gen:-2 },
    { label:"Parents",      gen:-1 },
    { label:"You & Siblings", gen:0 },
    { label:"Future Generation", gen:1 },
  ];

  const sortedHereditary = [...hereditary].sort((a,b)=>b.adjusted-a.adjusted);
  const topRisk = sortedHereditary[0];

  const generate = async () => {
    setBusy(true);
    const top2 = sortedHereditary.slice(0,2);
    try {
      const t = await callAI([{role:"user",content:
        `Write a 3-sentence family health summary for ${PT.name}. Hereditary-adjusted top risks: `+
        top2.map(h=>`${h.label} ${h.adjusted}% (base ${h.base}%, family multiplier ${h.multiplier}x)`).join(", ")+
        `. Mention which relatives contribute most and one family-wide preventive action. Empathetic, evidence-based, max 80 words.`}]);
      setSummary(t);
    } catch {
      setSummary(`${PT.name}'s family history meaningfully raises ${topRisk.label.toLowerCase()} risk — `+
        `elevated ${topRisk.multiplier}x (to ${topRisk.adjusted}%) mainly due to `+
        `${topRisk.contributors[0]?.relation || "family history"}. A household-wide preventive plan `+
        `(shared diet changes, joint screening) is recommended for everyone living together.`);
    }
    setBusy(false);
  };

  return (
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div>
        <h1 className="sec-h">{"🌳"} Generational Health Twin</h1>
        <p className="sec-s">Multi-generation family graph · Hereditary risk modeling · Inheritance path visualization</p>
      </div>

      {/* Family Tree */}
      <div className="card fu" style={{padding:22}}>
        <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:18}}>{"🧬"} Family Health Tree</div>
        <div style={{display:"flex",flexDirection:"column",gap:18}}>
          {generations.map(({label,gen}) => {
            const members = gen===0
              ? [{ id:"self", relation:"You", name:PT.name, age:PT.age, alive:true, conditions:[], self:true },
                 ...FAMILY.filter(m=>m.generation===0)]
              : FAMILY.filter(m=>m.generation===gen);
            return (
              <div key={gen}>
                <div style={{fontSize:10,color:"rgba(255,255,255,0.28)",letterSpacing:2,marginBottom:8,fontWeight:700}}>
                  {label.toUpperCase()}
                </div>
                <div style={{display:"flex",gap:12,flexWrap:"wrap"}}>
                  {members.map((m,i)=>{
                    const riskScore = m.self ? null : m.hypothetical ? null : Math.min(95, m.conditions.length*22);
                    const col = riskScore==null ? C.cy : riskScore>50?C.rd:riskScore>0?C.am:C.gr;
                    const hl = hoveredDz && m.conditions?.some(c=>matchesDz(c,hoveredDz));
                    return (
                      <div key={i} className={`tree-node ${hl?"hl":""}`}
                        style={{borderColor: hl?`${col}55`:undefined, boxShadow: hl?`0 0 18px ${col}33`:undefined}}>
                        <div style={{fontSize:20,marginBottom:4}}>{m.self?"👤":m.hypothetical?"❓":m.alive?"🧑":"🕊️"}</div>
                        <div style={{fontSize:11,fontWeight:600,color:"rgba(255,255,255,0.8)"}}>{m.relation}</div>
                        <div style={{fontSize:9,color:"rgba(255,255,255,0.3)",marginTop:1}}>
                          {m.name && m.name!=="—" ? m.name : ""}{m.age?` · ${m.age}y`:""}{!m.alive?" (deceased)":""}
                        </div>
                        {m.conditions?.length>0 && (
                          <div style={{display:"flex",flexWrap:"wrap",gap:3,justifyContent:"center",marginTop:6}}>
                            {m.conditions.map((c,j)=>(
                              <span key={j} style={{fontSize:8,padding:"2px 6px",borderRadius:6,
                                background:`${col}18`,color:col,border:`1px solid ${col}30`}}>{c}</span>
                            ))}
                          </div>
                        )}
                        {m.hypothetical && <div style={{fontSize:8,color:"rgba(255,255,255,0.22)",marginTop:4}}>Simulated</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        {/* Hereditary Risk Bars */}
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"🧬"} Hereditary-Adjusted Risk</div>
          {sortedHereditary.map((h,i)=>(
            <div key={i} onMouseEnter={()=>setHoveredDz(h.key)} onMouseLeave={()=>setHoveredDz(null)} style={{marginBottom:16,cursor:"pointer"}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:6,fontSize:13}}>
                <span style={{color:"rgba(255,255,255,0.68)"}}>{h.icon} {h.label}</span>
                <div style={{display:"flex",gap:8,alignItems:"center"}}>
                  <span className="mono" style={{fontSize:11,color:"rgba(255,255,255,0.3)"}}>{h.base}% base</span>
                  {h.multiplier>1 && <span className="chip chip-a" style={{fontSize:9}}>x{h.multiplier} family</span>}
                  <span className="mono" style={{fontWeight:500,color:h.color}}>{h.adjusted}%</span>
                </div>
              </div>
              <div className="bar-w" style={{position:"relative"}}>
                <div style={{position:"absolute",height:"100%",width:`${h.base}%`,background:"rgba(255,255,255,0.12)",borderRadius:3}}/>
                <div className="bar-f" style={{width:`${h.adjusted}%`,background:`linear-gradient(90deg,${h.color}78,${h.color})`}}/>
              </div>
              {h.contributors.length>0 && (
                <div style={{fontSize:10,color:"rgba(255,255,255,0.32)",marginTop:5}}>
                  {h.contributors.map((c,j)=>(
                    <span key={j} style={{marginRight:10}}>↳ {c.relation}: {c.condition}{c.age?` (age ${c.age})`:""}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Genetic Risk Heatmap */}
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"🗺️"} Genetic Risk Heatmap</div>
          <div style={{overflowX:"auto"}}>
            <table style={{borderCollapse:"separate",borderSpacing:6,width:"100%"}}>
              <thead>
                <tr>
                  <th style={{textAlign:"left",fontSize:10,color:"rgba(255,255,255,0.3)",fontWeight:600}}>Member</th>
                  {Object.values(DZ).map((d,i)=>(
                    <th key={i} style={{fontSize:13,textAlign:"center"}} title={d.label}>{d.icon}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[{relation:"You", conditions:[]}, ...FAMILY.filter(m=>!m.hypothetical)].map((m,i)=>(
                  <tr key={i}>
                    <td style={{fontSize:11,color:"rgba(255,255,255,0.6)",paddingRight:8,whiteSpace:"nowrap"}}>{m.relation}</td>
                    {Object.entries(DZ).map(([key,d],j)=>{
                      const has = m.conditions?.some(c=>matchesDz(c,key));
                      return (
                        <td key={j}>
                          <div className="heat-cell" style={{
                            background: has ? `${d.color}28` : "rgba(255,255,255,0.03)",
                            border: `1px solid ${has?d.color+"40":"rgba(255,255,255,0.05)"}`,
                          }}>{has ? "●" : ""}</div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{marginTop:14,fontSize:11,color:"rgba(255,255,255,0.3)"}}>
            Hover a risk bar on the left to highlight matching family members above.
          </div>
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        {/* Family Preventive Actions */}
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"👨‍👩‍👧‍👦"} Family-Wide Preventive Actions</div>
          {sortedHereditary.filter(h=>h.multiplier>1.3).map((h,i)=>{
            const actions = {
              diabetes: "Family-wide annual HbA1c screening; shared low-glycemic diet plan",
              heart:    "Family cardiology screening from age 35 — early CVD in lineage",
              bp:       "Household sodium-reduction; shared home BP monitor",
              anemia:   "Iron-rich diet plan for the household; screen all members",
              stress:   "Shared family wellness routine — group activity, consistent sleep",
            };
            return (
              <div key={i} style={{padding:"12px 14px",marginBottom:9,borderRadius:11,
                background:`${h.color}0a`,border:`1px solid ${h.color}28`}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
                  <span style={{fontSize:13,fontWeight:600}}>{h.icon} {h.label}</span>
                  <span className={`chip chip-${h.adjusted>50?"r":"a"}`}>{h.adjusted}%</span>
                </div>
                <div style={{fontSize:12,color:"rgba(255,255,255,0.58)"}}>{actions[h.key]}</div>
              </div>
            );
          })}
          {sortedHereditary.filter(h=>h.multiplier>1.3).length===0 && (
            <div style={{textAlign:"center",padding:"20px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>
              No significant hereditary amplification detected
            </div>
          )}
        </div>

        {/* Next-Generation Risk */}
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"👶"} Future Generation Risk Simulation</div>
          <div style={{fontSize:12,color:"rgba(255,255,255,0.4)",marginBottom:14}}>
            Estimated inherited risk for a hypothetical child of {PT.name.split(" ")[0]}, based on your
            hereditary-adjusted profile (one additional generation of dilution applied):
          </div>
          {sortedHereditary.map((h,i)=>{
            const childRisk = +Math.min(95, h.adjusted*0.55).toFixed(1);
            return (
              <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",
                padding:"8px 0",borderBottom:"1px solid rgba(255,255,255,0.04)",fontSize:12}}>
                <span style={{color:"rgba(255,255,255,0.6)"}}>{h.icon} {h.label}</span>
                <span className="mono" style={{color:h.color,fontWeight:500}}>{childRisk}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Family Summary */}
      <div className="card fu" style={{padding:22}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>{"🧠"} AI Family Risk Summary</div>
          <button className="btn btn-solid" onClick={generate} disabled={busy} style={{fontSize:12,padding:"8px 16px"}}>
            {busy?"Generating…":summary?"Regenerate":"Generate →"}
          </button>
        </div>
        {busy ? <div style={{display:"flex",gap:8,padding:"20px 0",justifyContent:"center"}}><Dots/></div>
        : summary ? <div style={{fontSize:13,lineHeight:1.78,color:"rgba(255,255,255,0.76)",
            background:"rgba(124,77,255,0.05)",padding:18,borderRadius:12,border:"1px solid rgba(124,77,255,0.14)",
            animation:"fadeUp .4s ease"}}>{summary}</div>
        : <div style={{textAlign:"center",padding:"20px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>
            Click Generate for an AI-powered family risk narrative
          </div>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
//  MODULE 2 — HEALTH TIME MACHINE (Future Self Engine)
// ═══════════════════════════════════════════════════════════

export function projectProfile(years, withPrevention) {
  let { sys, glu } = { sys: PT.vitals.sys, glu: PT.vitals.glu };
  let bmi = PT.vitals.bmi;
  let sleep = PT.life.sleep, stress = PT.life.stress, exDays = PT.life.ex, diet = PT.life.diet;

  if (withPrevention) {
    bmi   = Math.max(21, bmi - 0.3*years);
    sys   = Math.max(112, sys - 0.6*years);
    glu   = Math.max(82, glu - 0.8*years);
    sleep = Math.min(8, sleep + 0.15*years);
    stress= Math.max(3, stress - 0.3*years);
    exDays= Math.min(6, exDays + 0.3*years);
  } else {
    const bmiDrift = exDays < 3 ? 0.15 : 0.03;
    const sbpDrift = (stress>=7 || sleep<6) ? 0.8 : 0.3;
    const gluDrift = diet < 6 ? 1.2 : 0.4;
    bmi += bmiDrift*years; sys += sbpDrift*years; glu += gluDrift*years;
  }

  const age = PT.age + years;
  const familyDiabetes = true, familyHyper = true, familyCVD = true; // from FAMILY data
  const risks = {
    diabetes: findriscPct(age, bmi, exDays, diet, glu, familyDiabetes),
    bp:       hyperPct(age, sys, bmi, familyHyper, sleep, stress, diet),
    heart:    heartPct(age, sys, PT.life.smk, glu, familyCVD, bmi, exDays, stress),
    anemia:   PT.risks.anemia, // largely lab-driven, held constant in simulation
    stress:   stressPct(sleep, exDays, stress),
  };
  const score = healthScoreOf(risks, sys, bmi, sleep, stress);
  const organs = organScores(risks, sleep, age, PT.life.smk);
  const bAge = bioAge(age, bmi, sys, glu, sleep, stress, PT.life.smk);

  return { age, bmi, sys, glu, sleep, stress, risks, score, organs, bAge };
}

export default FamilyTwin;
