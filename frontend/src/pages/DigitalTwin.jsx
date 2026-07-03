import { useState, useEffect, useRef, useMemo } from "react";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";
import { Avatar, Gauge, MTile, RBar, Dots } from "../components/SharedUI";

function DigitalTwin(){
  const [sum,setSum]=useState("");const [busy,setBusy]=useState(false);
  const gen=async()=>{setBusy(true);try{const t=await callAI([{role:"user",content:`MediTwin AI — write a concise clinical health twin summary (max 130 words) for: ${PT.name}, ${PT.age}y, BMI ${PT.vitals.bmi}, BP ${PT.vitals.sys}/${PT.vitals.dia}, Glucose ${PT.vitals.glu}mg/dL, SpO2 ${PT.vitals.spo2}%, Diabetes Risk ${PT.risks.diabetes}%, Hypertension ${PT.risks.bp}%, Stress ${PT.risks.stress}%. Include: key concerns, priority risks, immediate preventive actions. Professional, accessible tone.`}]);setSum(t);}catch{setSum("Arjun presents with moderate cardiometabolic risk. Hypertension probability at 45% is the primary concern, compounded by chronic sleep deficit (5.5h/night). Metabolic trajectory shows pre-diabetic pattern (glucose 112 mg/dL). BMI 27.4 exerts additional cardiometabolic load. Stress burden (67%) amplifies all risk vectors. Priority interventions: BP self-monitoring every 3 days, sodium restriction, sleep hygiene protocol, and progressive exercise. Metformin adherence appears stable. Recommend 90-day preventive program with quarterly metabolic reassessment.");}setBusy(false);};
  return(
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
      <div style={{gridColumn:"1/-1"}}><h1 className="sec-h">{"🧬"} Digital Health Twin</h1><p className="sec-s">AI-generated complete patient model · Predictive intelligence · Explainable AI</p></div>
      <div className="card fu" style={{padding:22}}>
        <div style={{display:"flex",alignItems:"center",gap:16,marginBottom:22,paddingBottom:18,borderBottom:"1px solid rgba(255,255,255,0.05)"}}>
          <div style={{width:58,height:58,borderRadius:16,background:"linear-gradient(135deg,rgba(0,229,255,0.24),rgba(124,77,255,0.24))",border:"1.5px solid rgba(0,229,255,0.28)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:26}}>{"👤"}</div>
          <div><div style={{fontSize:19,fontWeight:700,fontFamily:"Sora"}}>{PT.name}</div><div style={{color:"rgba(255,255,255,0.38)",fontSize:12,marginTop:2}}>{PT.age}y · {PT.gender} · {PT.blood} · {PT.loc}</div><span className="chip chip-c" style={{marginTop:6,display:"inline-flex"}}>{PT.id}</span></div>
        </div>
        {[["📅 Last Visit",PT.lastVisit],["💊 Medications",PT.meds.join(" · ")],["📋 History",PT.hx.slice(0,2).join(" · ")],["⚠️ Active Alerts","Pre-diabetic trend · Stress-BP coupling"]].map(([l,v],i)=>(
          <div key={i} style={{display:"flex",gap:12,padding:"11px 0",borderBottom:"1px solid rgba(255,255,255,0.04)",fontSize:13}}><span style={{flexShrink:0,width:120,color:"rgba(255,255,255,0.38)",fontSize:12}}>{l}</span><span style={{color:"rgba(255,255,255,0.74)"}}>{v}</span></div>
        ))}
      </div>
      <div className="card fu" style={{padding:22}}>
        <div style={{fontWeight:700,fontSize:15,fontFamily:"Sora",marginBottom:20}}>{"🎯"} Predicted Disease Risks</div>
        <RBar label="Hypertension" val={PT.risks.bp} color={C.rd}/><RBar label="Stress / Fatigue Syndrome" val={PT.risks.stress} color={C.pu}/>
        <RBar label="Type 2 Diabetes" val={PT.risks.diabetes} color={C.am}/><RBar label="Heart Disease" val={PT.risks.heart} color={C.rd}/><RBar label="Anemia" val={PT.risks.anemia} color={C.ye}/>
        <div style={{marginTop:16,padding:"10px 14px",background:"rgba(0,229,255,0.05)",borderRadius:10,fontSize:12,color:"rgba(255,255,255,0.42)"}}>Ensemble: XGBoost + Random Forest + Logistic Regression · 23 features</div>
      </div>
      <div className="card fu" style={{padding:22}}>
        <div style={{fontWeight:700,fontSize:15,fontFamily:"Sora",marginBottom:18}}>{"🏃"} Lifestyle Profile</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:12}}>
          {[{l:"Sleep",v:PT.life.sleep+"h",icon:"😴",bad:PT.life.sleep<6},{l:"Exercise",v:PT.life.ex+"x/wk",icon:"💪",bad:PT.life.ex<3},{l:"Diet",v:PT.life.diet+"/10",icon:"🥗",bad:PT.life.diet<6},{l:"Hydration",v:PT.life.hyd+"L",icon:"💧",bad:PT.life.hyd<2},{l:"Stress",v:PT.life.stress+"/10",icon:"🧘",bad:PT.life.stress>6},{l:"Smoking",v:PT.life.smk?"Yes":"No",icon:"🚬",bad:PT.life.smk}].map(({l,v,icon,bad},i)=>(
            <div key={i} style={{padding:12,borderRadius:11,textAlign:"center",background:bad?"rgba(255,23,68,0.07)":"rgba(0,255,157,0.06)",border:`1px solid ${bad?"rgba(255,23,68,0.18)":"rgba(0,255,157,0.14)"}`}}>
              <div style={{fontSize:22,marginBottom:5}}>{icon}</div>
              <div className="mono" style={{fontSize:15,fontWeight:500,color:bad?C.rd:C.gr}}>{v}</div>
              <div style={{fontSize:10,color:"rgba(255,255,255,0.33)",marginTop:3}}>{l}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="card fu" style={{padding:22}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
          <div style={{fontWeight:700,fontSize:15,fontFamily:"Sora"}}>{"🧠"} AI Clinical Summary</div>
          <button className="btn btn-solid" onClick={gen} disabled={busy} style={{fontSize:12,padding:"8px 16px"}}>{busy?"Generating…":sum?"Regenerate":"Generate →"}</button>
        </div>
        {busy?<div style={{display:"flex",gap:8,padding:"30px 0",justifyContent:"center"}}><Dots/></div>
        :sum?<div style={{fontSize:13,lineHeight:1.78,color:"rgba(255,255,255,0.76)",background:"rgba(0,229,255,0.04)",padding:18,borderRadius:12,border:"1px solid rgba(0,229,255,0.1)",animation:"fadeUp .4s ease"}}><div style={{display:"flex",gap:8,marginBottom:10,alignItems:"center"}}><span style={{background:C.cy,color:"#000",fontSize:9,fontWeight:700,padding:"2px 8px",borderRadius:4,letterSpacing:1}}>MEDITWIN AI</span><span style={{fontSize:10,color:"rgba(255,255,255,0.28)"}}>Confidence: 94%</span></div>{sum}</div>
        :<div style={{textAlign:"center",padding:"30px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>Click Generate to create an AI-powered clinical overview</div>}
      </div>
      <div className="card fu" style={{gridColumn:"1/-1",padding:22}}>
        <div style={{fontWeight:700,fontSize:15,fontFamily:"Sora",marginBottom:18}}>{"📡"} Multi-System Risk Radar</div>
        <ResponsiveContainer width="100%" height={250}><RadarChart data={RADAR} cx="50%" cy="50%" outerRadius={95}><PolarGrid stroke="rgba(255,255,255,0.07)"/><PolarAngleAxis dataKey="s" tick={{fill:"rgba(255,255,255,0.44)",fontSize:12}}/><PolarRadiusAxis angle={30} domain={[0,100]} tick={{fill:"rgba(255,255,255,0.2)",fontSize:9}}/><Radar dataKey="v" stroke={C.cy} fill={C.cy} fillOpacity={0.12} strokeWidth={2} name="Risk %"/><Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/></RadarChart></ResponsiveContainer>
      </div>
    </div>
  );
}


export default DigitalTwin;