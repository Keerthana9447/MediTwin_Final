import { useState, useEffect, useRef, useMemo } from "react";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";

function WhatIf(){
  const BASE={diabetes:38,heart:22,bp:45,stress:67,score:72};
  const [p,setP]=useState({sleep:5.5,ex:2,diet:5,stress:7,hyd:1.8,smk:0});
  const [insight,setInsight]=useState("");const [busy,setBusy]=useState(false);
  const calc=()=>{
    const tot=(p.sleep-5.5)*3.2+(p.ex-2)*5.5+(p.diet-5)*2.2+(7-p.stress)*2.5+(p.hyd-1.8)*4.5-p.smk*16;
    return{diabetes:Math.max(5,Math.min(95,BASE.diabetes-tot*.6)),heart:Math.max(5,Math.min(95,BASE.heart-tot*.4)),bp:Math.max(5,Math.min(95,BASE.bp-tot*.52)),stress:Math.max(5,Math.min(95,BASE.stress-tot*.72)),score:Math.max(20,Math.min(98,BASE.score+tot*.48))};
  };
  const proj=calc();
  const BARS=[{l:"Diabetes",b:BASE.diabetes,a:Math.round(proj.diabetes)},{l:"Heart",b:BASE.heart,a:Math.round(proj.heart)},{l:"Hypertension",b:BASE.bp,a:Math.round(proj.bp)},{l:"Stress",b:BASE.stress,a:Math.round(proj.stress)}];
  const getInsight=async()=>{
    setBusy(true);
    const ch=[];
    if(p.sleep!==5.5)ch.push(`sleep to ${p.sleep}h/night`);if(p.ex!==2)ch.push(`exercise to ${p.ex}x/week`);if(p.diet!==5)ch.push(`diet quality to ${p.diet}/10`);if(p.stress!==7)ch.push(`stress to ${p.stress}/10`);if(p.hyd!==1.8)ch.push(`hydration to ${p.hyd}L/day`);if(p.smk>0)ch.push(`smoking ${p.smk} cigs/day`);
    try{const t=await callAI([{role:"user",content:`MediTwin What-If for ${PT.name}, ${PT.age}y. Change: ${ch.join(", ")||"no changes"}. Projected: Diabetes ${proj.diabetes.toFixed(0)}% (from 38%), Hypertension ${proj.bp.toFixed(0)}% (from 45%), Score ${proj.score.toFixed(0)} (from 72). Write 3 sentences max — encouraging, evidence-based. Include realistic timeline.`}]);setInsight(t);}
    catch{setInsight(`Making these lifestyle changes could significantly improve your health trajectory. ${proj.score>BASE.score?`Your projected health score increases by ${(proj.score-BASE.score).toFixed(0)} points`:"Maintaining current habits sustains your baseline"} with consistent effort over 8-12 weeks. Each change compounds — the combined cardiometabolic impact is clinically meaningful.`);}
    setBusy(false);
  };
  const SL=[{k:"sleep",l:"Sleep Duration",min:4,max:9,step:.5,u:"hrs",icon:"😴"},{k:"ex",l:"Exercise Days / Week",min:0,max:7,step:1,u:"days",icon:"💪"},{k:"diet",l:"Diet Quality",min:1,max:10,step:1,u:"/10",icon:"🥗"},{k:"stress",l:"Stress Level (lower = better)",min:1,max:10,step:1,u:"/10",icon:"🧘"},{k:"hyd",l:"Daily Water Intake",min:.5,max:4,step:.5,u:"L",icon:"💧"},{k:"smk",l:"Cigarettes / Day",min:0,max:20,step:1,u:"/day",icon:"🚬"}];
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div><h1 className="sec-h">{"🔮"} What-If Lifestyle Simulator</h1><p className="sec-s">Modify habits in real-time · AI instantly simulates your future health trajectory</p></div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:20}}>{"🎛️"} Adjust Your Lifestyle</div>
          {SL.map(({k,l,min,max,step,u,icon})=>{const pct=((p[k]-min)/(max-min))*100;return(
            <div key={k} style={{marginBottom:22}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:9,fontSize:13}}><span style={{color:"rgba(255,255,255,0.64)"}}>{icon} {l}</span><span className="mono" style={{color:C.cy,fontWeight:500}}>{p[k]}{u}</span></div>
              <input type="range" min={min} max={max} step={step} value={p[k]} className="slider" onChange={e=>setP(prev=>({...prev,[k]:parseFloat(e.target.value)}))} style={{background:`linear-gradient(to right,${C.cy} ${pct}%,rgba(255,255,255,0.1) ${pct}%)`}}/>
              <div style={{display:"flex",justifyContent:"space-between",fontSize:9,color:"rgba(255,255,255,0.2)",marginTop:3}}><span>{min}{u}</span><span>{max}{u}</span></div>
            </div>
          );})}
          <button className="btn btn-solid" style={{width:"100%",marginTop:4}} onClick={getInsight} disabled={busy}>{busy?"🔮 Simulating…":"🔮 Get AI Impact Analysis"}</button>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          <div className="card fu" style={{padding:22}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"📊"} Health Score Impact</div>
            <div style={{display:"flex",gap:24,justifyContent:"center",alignItems:"center",padding:"8px 0 20px"}}>
              <div style={{textAlign:"center"}}><div style={{fontSize:11,color:"rgba(255,255,255,0.3)",marginBottom:4,letterSpacing:1}}>CURRENT</div><div className="mono" style={{fontSize:46,fontWeight:500,color:C.am}}>72</div></div>
              <div style={{fontSize:28,color:"rgba(255,255,255,0.2)"}}>→</div>
              <div style={{textAlign:"center"}}><div style={{fontSize:11,color:"rgba(255,255,255,0.3)",marginBottom:4,letterSpacing:1}}>PROJECTED</div><div className="mono" style={{fontSize:46,fontWeight:500,color:proj.score>72?C.gr:C.rd}}>{Math.round(proj.score)}</div></div>
              <div style={{padding:"10px 16px",borderRadius:12,background:`${proj.score>72?C.gr:C.rd}15`,fontSize:20,fontWeight:700,fontFamily:"DM Mono",color:proj.score>72?C.gr:C.rd}}>{proj.score>72?"+":""}{(proj.score-72).toFixed(0)}</div>
            </div>
          </div>
          <div className="card fu" style={{padding:22,flex:1}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>Before vs After Risk</div>
            <ResponsiveContainer width="100%" height={200}><BarChart data={BARS} barGap={3}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/><XAxis dataKey="l" tick={{fill:"rgba(255,255,255,0.35)",fontSize:10}}/><YAxis tick={{fill:"rgba(255,255,255,0.35)",fontSize:10}} domain={[0,80]}/><Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/><Bar dataKey="b" fill="rgba(255,145,0,0.55)" name="Current %" radius={[4,4,0,0]}/><Bar dataKey="a" fill="rgba(0,229,255,0.55)" name="Projected %" radius={[4,4,0,0]}/><Legend wrapperStyle={{fontSize:11,color:"rgba(255,255,255,0.44)"}}/></BarChart></ResponsiveContainer>
          </div>
        </div>
        {insight&&<div className="card fu" style={{gridColumn:"1/-1",padding:22}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}><div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>{"🧠"} AI Impact Analysis</div><span className="chip chip-p">XAI POWERED</span></div>
          <div style={{fontSize:13,lineHeight:1.8,color:"rgba(255,255,255,0.75)",background:"rgba(124,77,255,0.05)",padding:20,borderRadius:12,border:"1px solid rgba(124,77,255,0.14)",animation:"fadeUp .4s ease"}}>{insight}</div>
        </div>}
      </div>
    </div>
  );
}


export default WhatIf;
