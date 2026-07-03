import { useState, useEffect, useRef, useMemo } from "react";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";
import { Dots, Avatar } from "../components/SharedUI";
import { organScores, bioAge, projectProfile } from "./FamilyTwin";

function TimeMachine() {
  const [years, setYears] = useState(5);
  const [scenario, setScenario] = useState("status_quo"); // status_quo | with_prevention
  const [narrative, setNarrative] = useState("");
  const [busy, setBusy] = useState(false);

  const current = useMemo(() => ({
    age: PT.age, bmi: PT.vitals.bmi, score: PT.score,
    risks: PT.risks, organs: organScores(PT.risks, PT.life.sleep, PT.age, PT.life.smk),
    bAge: bioAge(PT.age, PT.vitals.bmi, PT.vitals.sys, PT.vitals.glu, PT.life.sleep, PT.life.stress, PT.life.smk),
  }), []);

  const futureA = useMemo(() => projectProfile(years, false), [years]); // status quo
  const futureB = useMemo(() => projectProfile(years, true),  [years]); // with prevention
  const future  = scenario==="with_prevention" ? futureB : futureA;

  const avatarCol = future.score>75?C.gr:future.score>50?C.am:C.rd;
  const scoreDelta = future.score - current.score;

  const riskRows = [
    {key:"diabetes", label:"Diabetes",      icon:"🩸"},
    {key:"heart",    label:"Heart Disease", icon:"❤️"},
    {key:"bp",       label:"Hypertension",  icon:"🫀"},
    {key:"stress",   label:"Stress",        icon:"🧠"},
  ];

  const generate = async () => {
    setBusy(true);
    const topChange = riskRows.map(r=>({...r, delta: future.risks[r.key]-current.risks[r.key]}))
      .sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta))[0];
    const changesStr = `${topChange.label} ${topChange.delta>0?"↑":"↓"}${Math.abs(topChange.delta).toFixed(0)}%`;
    const prompt = scenario==="with_prevention"
      ? `MediTwin Time Machine — 'Future B' for ${PT.name}, projecting ${years} years forward WITH sustained `+
        `preventive habits. Age ${current.age} -> ${future.age}. Health Score ${current.score} -> ${future.score}. `+
        `Key change: ${changesStr}. Write an encouraging cinematic 3-sentence narrative — "this is the future you can choose".`
      : `MediTwin Time Machine — status-quo for ${PT.name}, projecting ${years} years forward if habits continue `+
        `unchanged. Age ${current.age} -> ${future.age}. Health Score ${current.score} -> ${future.score}. `+
        `Key change: ${changesStr}. Write a vivid non-alarmist 3-sentence narrative — "this is where things are headed".`;
    try {
      const t = await callAI([{role:"user",content:prompt}]);
      setNarrative(t);
    } catch {
      setNarrative(scenario==="with_prevention"
        ? `At age ${future.age}, sustained healthy habits keep your health score near ${future.score}/100. ${changesStr} — a future you actively chose.`
        : `At age ${future.age}, if current habits continue, your health score trends toward ${future.score}/100. ${changesStr} — small changes now can shift this trajectory.`);
    }
    setBusy(false);
  };

  useEffect(()=>{ setNarrative(""); }, [years, scenario]);

  return (
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div>
        <h1 className="sec-h">{"⏳"} Health Time Machine</h1>
        <p className="sec-s">Future Self Engine · Age-risk progression simulation · Biological age projection</p>
      </div>

      {/* Controls */}
      <div className="card fu" style={{padding:18,display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:14}}>
        <div style={{display:"flex",gap:8}}>
          {[1,5,10].map(y=>(
            <button key={y} className={`yr-btn ${years===y?"on":""}`} onClick={()=>setYears(y)}>+{y} Year{y>1?"s":""}</button>
          ))}
        </div>
        <div style={{display:"flex",gap:8}}>
          <button className={`yr-btn ${scenario==="status_quo"?"on":""}`} onClick={()=>setScenario("status_quo")}>
            {"📉"} Future A — Status Quo
          </button>
          <button className={`yr-btn ${scenario==="with_prevention"?"on":""}`} onClick={()=>setScenario("with_prevention")}
            style={scenario==="with_prevention"?{borderColor:"rgba(0,255,157,.32)",background:"linear-gradient(135deg,rgba(0,255,157,.16),rgba(0,229,255,.1))",color:C.gr}:{}}>
            {"📈"} Future B — With Prevention
          </button>
        </div>
      </div>

      {/* Cinematic Comparison */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu morph" key={`cur-${years}-${scenario}`} style={{padding:24,display:"flex",flexDirection:"column",alignItems:"center",gap:10}}>
          <div style={{fontSize:9,color:"rgba(255,255,255,0.28)",letterSpacing:2,fontWeight:700}}>NOW — AGE {current.age}</div>
          <Avatar score={current.score} risks={current.risks}/>
          <div style={{display:"flex",gap:16,marginTop:6}}>
            <div style={{textAlign:"center"}}>
              <div className="mono" style={{fontSize:22,fontWeight:500,color:C.cy}}>{current.score}</div>
              <div style={{fontSize:9,color:"rgba(255,255,255,0.3)"}}>HEALTH SCORE</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div className="mono" style={{fontSize:22,fontWeight:500,color:"rgba(255,255,255,0.7)"}}>{current.bAge}</div>
              <div style={{fontSize:9,color:"rgba(255,255,255,0.3)"}}>BIOLOGICAL AGE</div>
            </div>
          </div>
        </div>

        <div className="card fu morph" key={`fut-${years}-${scenario}`} style={{padding:24,display:"flex",flexDirection:"column",alignItems:"center",gap:10,
          border:`1px solid ${avatarCol}28`}}>
          <div style={{fontSize:9,color:avatarCol,letterSpacing:2,fontWeight:700}}>
            +{years}YR — AGE {future.age} {scenario==="with_prevention"?"(WITH PREVENTION)":"(STATUS QUO)"}
          </div>
          <Avatar score={future.score} risks={future.risks}/>
          <div style={{display:"flex",gap:16,marginTop:6}}>
            <div style={{textAlign:"center"}}>
              <div className="mono count-glow" style={{fontSize:22,fontWeight:500,color:avatarCol}}>{future.score}</div>
              <div style={{fontSize:9,color:"rgba(255,255,255,0.3)"}}>
                HEALTH SCORE {scoreDelta!==0 && <span style={{color:scoreDelta>0?C.gr:C.rd}}>({scoreDelta>0?"+":""}{scoreDelta})</span>}
              </div>
            </div>
            <div style={{textAlign:"center"}}>
              <div className="mono" style={{fontSize:22,fontWeight:500,color:"rgba(255,255,255,0.7)"}}>{future.bAge}</div>
              <div style={{fontSize:9,color:"rgba(255,255,255,0.3)"}}>BIOLOGICAL AGE</div>
            </div>
          </div>
        </div>
      </div>

      {/* Disease Progression + Organ Health */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"📊"} Disease Risk Progression</div>
          {riskRows.map((r,i)=>{
            const cur = current.risks[r.key], fut = future.risks[r.key], delta = fut-cur;
            const col = fut>50?C.rd:fut>25?C.am:C.gr;
            return (
              <div key={i} style={{marginBottom:14}}>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:6}}>
                  <span style={{color:"rgba(255,255,255,0.6)"}}>{r.icon} {r.label}</span>
                  <span className="mono">
                    <span style={{color:"rgba(255,255,255,0.35)"}}>{cur}%</span>
                    <span style={{color:"rgba(255,255,255,0.2)",margin:"0 4px"}}>→</span>
                    <span style={{color:col,fontWeight:600}}>{fut}%</span>
                    <span style={{color:delta>0?C.rd:C.gr,marginLeft:6}}>({delta>0?"+":""}{delta.toFixed(0)}%)</span>
                  </span>
                </div>
                <div className="bar-w" style={{position:"relative"}}>
                  <div style={{position:"absolute",height:"100%",width:`${cur}%`,background:"rgba(255,255,255,0.12)",borderRadius:3}}/>
                  <div className="bar-f" style={{width:`${fut}%`,background:`linear-gradient(90deg,${col}78,${col})`}}/>
                </div>
              </div>
            );
          })}
        </div>

        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"🫁"} Organ Health Trajectory</div>
          {Object.keys(current.organs).map((organ,i)=>{
            const cur = current.organs[organ], fut = future.organs[organ];
            const delta = fut - cur;
            const col = fut>70?C.gr:fut>45?C.am:C.rd;
            const icons = {Heart:"❤️",Pancreas:"🩸",Kidneys:"🫘",Lungs:"🫁",Brain:"🧠"};
            return (
              <div key={i} style={{marginBottom:14}}>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:6}}>
                  <span style={{color:"rgba(255,255,255,0.6)"}}>{icons[organ]} {organ}</span>
                  <span className="mono">
                    <span style={{color:"rgba(255,255,255,0.35)"}}>{cur}%</span>
                    <span style={{color:"rgba(255,255,255,0.2)",margin:"0 4px"}}>→</span>
                    <span style={{color:col,fontWeight:600}}>{fut}%</span>
                    <span style={{color:delta<0?C.rd:C.gr,marginLeft:6}}>({delta>0?"+":""}{delta})</span>
                  </span>
                </div>
                <div className="bar-w"><div className="bar-f" style={{width:`${fut}%`,background:`linear-gradient(90deg,${col}78,${col})`}}/></div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Narrative */}
      <div className="card fu" style={{padding:22}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>{"🎬"} The Story of Your Future</div>
          <button className="btn btn-solid" onClick={generate} disabled={busy} style={{fontSize:12,padding:"8px 16px"}}>
            {busy?"Narrating…":narrative?"Regenerate":"Narrate This Future →"}
          </button>
        </div>
        {busy ? <div style={{display:"flex",gap:8,padding:"20px 0",justifyContent:"center"}}><Dots/></div>
        : narrative ? <div style={{fontSize:13,lineHeight:1.8,color:"rgba(255,255,255,0.78)",
            background:`${avatarCol}0a`,padding:18,borderRadius:12,border:`1px solid ${avatarCol}28`,animation:"fadeUp .4s ease"}}>
            {narrative}
          </div>
        : <div style={{textAlign:"center",padding:"20px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>
            Click to generate a cinematic narrative for this exact future scenario
          </div>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
//  MODULE 3 — AI PREVENTIVE IMPACT ENGINE (ROI Calculator)
// ═══════════════════════════════════════════════════════════

export const ACTIONS = {
  sleep_8h:      { label:"Sleep 8 Hours/Night",   icon:"😴", rrr:{bp:0.15, stress:0.25}, lifeYears:1.0,
                   desc:"Consistent 7-8h sleep — reduces cortisol-driven BP and stress" },
  walk_10k:      { label:"Walk 10,000 Steps/Day", icon:"🚶", rrr:{diabetes:0.30, heart:0.25, bp:0.20}, lifeYears:3.0,
                   desc:"~150 min/week moderate activity — DPP-aligned metabolic benefit" },
  reduce_sugar:  { label:"Reduce Added Sugar",    icon:"🍬", rrr:{diabetes:0.20}, lifeYears:1.0,
                   desc:"Low-glycemic diet shift — reduces glucose trajectory" },
  reduce_sodium: { label:"Reduce Sodium Intake",  icon:"🧂", rrr:{bp:0.25, heart:0.10}, lifeYears:1.0,
                   desc:"DASH-aligned sodium reduction — proven BP reduction" },
  quit_smoking:  { label:"Quit Smoking",          icon:"🚭", rrr:{heart:0.50, bp:0.10}, lifeYears:3.0,
                   desc:"Excess CVD risk declines substantially within 1 year of cessation" },
  meditation:    { label:"Daily Meditation",      icon:"🧘", rrr:{stress:0.35, bp:0.10}, lifeYears:0.5,
                   desc:"10-min daily mindfulness — measurable cortisol/BP reduction" },
  weight_loss:   { label:"5-7% Weight Loss",      icon:"⚖️", rrr:{diabetes:0.45, heart:0.15, bp:0.20}, lifeYears:2.0,
                   desc:"Sustained moderate weight loss — DPP headline metabolic benefit" },
};

export const TREATMENT_COST_INR = { diabetes:300000, heart:500000, bp:150000, anemia:20000, stress:50000 };
export const DIMINISH = { 1:1.0, 2:0.9, 3:0.8 };
export const DIMINISH_DEFAULT = 0.72;
export const MAX_LIFE_GAIN = 8.0;


export default TimeMachine;
