import { useState, useEffect, useRef, useMemo } from "react";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";
import { Avatar, Gauge, MTile, RBar, Dots } from "../components/SharedUI";

function DiseaseRisk(){
  const DS=[
    {n:"Hypertension",pct:PT.risks.bp,conf:89,col:C.rd,icon:"🫀",factors:[["Family History",28],["Chronic Stress",22],["Sleep Deficit",18],["Sedentary Life",15],["High Sodium",10]]},
    {n:"Stress / Fatigue",pct:PT.risks.stress,conf:91,col:C.pu,icon:"🧠",factors:[["Sleep Deprivation",35],["Work Pressure",25],["Low Exercise",20],["BMI >25",12],["Caffeine Excess",8]]},
    {n:"Type 2 Diabetes",pct:PT.risks.diabetes,conf:84,col:C.am,icon:"🩸",factors:[["Pre-diabetic Glucose",28],["Family History",22],["BMI 27.4",18],["Inactivity",15],["Poor Diet",10]]},
    {n:"Heart Disease",pct:PT.risks.heart,conf:79,col:C.rd,icon:"❤️",factors:[["High LDL",25],["BP Elevation",20],["Sedentary Life",18],["Chronic Stress",15],["Abdominal Fat",12]]},
    {n:"Anemia",pct:PT.risks.anemia,conf:82,col:C.ye,icon:"🔬",factors:[["Low Hemoglobin",40],["Poor Nutrition",30],["Fatigue Pattern",20],["Low Ferritin",10]]}];
  const [sel,setSel]=useState(DS[0]);
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div><h1 className="sec-h">{"📊"} Disease Risk Prediction Engine</h1><p className="sec-s">Ensemble ML · Explainable AI · SHAP-style feature attribution · 23 clinical parameters</p></div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:18}}>{"🎯"} ML Risk Predictions</div>
          {DS.map((d,i)=>(
            <div key={i} onClick={()=>setSel(d)} style={{padding:"14px 16px",marginBottom:10,borderRadius:12,cursor:"pointer",background:sel.n===d.n?`${d.col}10`:"rgba(255,255,255,0.025)",border:`1px solid ${sel.n===d.n?d.col+"38":"rgba(255,255,255,0.05)"}`,transition:"all .18s"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}><div style={{display:"flex",alignItems:"center",gap:10}}><span style={{fontSize:20}}>{d.icon}</span><span style={{fontSize:13,fontWeight:600}}>{d.n}</span></div><div style={{textAlign:"right"}}><div className="mono" style={{fontSize:20,fontWeight:500,color:d.col}}>{d.pct}%</div><div style={{fontSize:9,color:"rgba(255,255,255,0.28)"}}>AI conf: {d.conf}%</div></div></div>
              <div className="bar-w"><div className="bar-f" style={{width:`${d.pct}%`,background:`linear-gradient(90deg,${d.col}72,${d.col})`}}/></div>
            </div>
          ))}
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          <div className="card fu" style={{padding:22}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"🔬"} SHAP Attribution — {sel.n}</div>
            {sel.factors.map(([f,v],i)=>(
              <div key={i} style={{marginBottom:13}}><div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:6}}><span style={{color:"rgba(255,255,255,0.62)"}}>{f}</span><span className="mono" style={{color:sel.col,fontWeight:500}}>{v}%</span></div><div className="bar-w"><div className="bar-f" style={{width:`${v*2.2}%`,background:`linear-gradient(90deg,${sel.col}60,${sel.col})`}}/></div></div>
            ))}
            <div style={{marginTop:16,padding:"10px 14px",background:"rgba(255,255,255,0.03)",borderRadius:10,fontSize:12,color:"rgba(255,255,255,0.38)"}}>Ensemble (XGB + RF + LR) · Confidence: <span className="mono" style={{color:sel.col}}>{sel.conf}%</span></div>
          </div>
          <div className="card fu" style={{padding:22,flex:1}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:14}}>Multi-System Risk Radar</div>
            <ResponsiveContainer width="100%" height={210}><RadarChart data={RADAR}><PolarGrid stroke="rgba(255,255,255,0.07)"/><PolarAngleAxis dataKey="s" tick={{fill:"rgba(255,255,255,0.4)",fontSize:11}}/><PolarRadiusAxis angle={30} domain={[0,100]} tick={false}/><Radar dataKey="v" stroke={C.cy} fill={C.cy} fillOpacity={0.12} strokeWidth={2}/><Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/></RadarChart></ResponsiveContainer>
          </div>
        </div>
        <div className="card fu" style={{gridColumn:"1/-1",padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:18}}>{"📈"} 6-Month Risk Trend Timeline</div>
          <ResponsiveContainer width="100%" height={185}><LineChart data={TL}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/><XAxis dataKey="m" tick={{fill:"rgba(255,255,255,0.35)",fontSize:11}}/><YAxis tick={{fill:"rgba(255,255,255,0.35)",fontSize:11}} domain={[0,85]}/><Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/><Legend wrapperStyle={{fontSize:11,color:"rgba(255,255,255,0.4)"}}/><Line type="monotone" dataKey="dia" stroke={C.am} strokeWidth={2} dot={{fill:C.am,r:3}} name="Diabetes %"/><Line type="monotone" dataKey="heart" stroke={C.rd} strokeWidth={2} dot={{fill:C.rd,r:3}} name="Heart Risk %"/><Line type="monotone" dataKey="stress" stroke={C.pu} strokeWidth={2} dot={{fill:C.pu,r:3}} name="Stress %"/><Line type="monotone" dataKey="sc" stroke={C.cy} strokeWidth={2} dot={{fill:C.cy,r:3}} name="Health Score"/></LineChart></ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}


export default DiseaseRisk;
