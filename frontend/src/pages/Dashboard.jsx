import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";
import { Avatar, Gauge, MTile, RBar, Dots } from "../components/SharedUI";

function Dashboard(){
  const go = useNavigate();
  const [hr,setHr]=useState(78);
  const [data,setData]=useState(()=>Array.from({length:20},(_,i)=>({t:`${i}:00`,hr:74+Math.round(Math.sin(i*.5)*6),o2:95+Math.round(Math.random()*2),bp:126+Math.round(Math.sin(i*.3)*4)})));
  useEffect(()=>{
    const id=setInterval(()=>{
      const h=74+Math.round(Math.sin(Date.now()*.001)*7+Math.random()*4);
      setHr(h);
      setData(p=>[...p.slice(-19),{t:new Date().toLocaleTimeString("en",{hour:"2-digit",minute:"2-digit"}),hr:h,o2:95+Math.round(Math.random()*2),bp:126+Math.round(Math.sin(Date.now()*.0005)*4)}]);
    },2200);
    return()=>clearInterval(id);
  },[]);
  return(
    <div style={{display:"grid",gridTemplateColumns:"220px 1fr 200px",gap:18}}>
      <div style={{gridColumn:"1/-1",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div><h1 className="sec-h gt">Health Dashboard</h1><p className="sec-s">Real-time monitoring · {PT.name} · ID: {PT.id}</p></div>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          <div style={{display:"flex",alignItems:"center",gap:8,background:"rgba(0,255,157,0.08)",border:"1px solid rgba(0,255,157,0.2)",borderRadius:100,padding:"7px 14px",fontSize:12}}><span className="dot dot-live"/><span style={{color:C.gr}}>Live Monitoring</span></div>
          <button className="btn btn-solid" onClick={()=>go("/twin")}>View Full Twin →</button>
        </div>
      </div>
      <div className="card" style={{padding:22,display:"flex",flexDirection:"column",alignItems:"center",gap:12}}>
        <div style={{fontSize:9,color:"rgba(255,255,255,0.25)",letterSpacing:2,fontWeight:700,marginBottom:4}}>DIGITAL TWIN</div>
        <Avatar score={PT.score} risks={PT.risks}/>
        <Gauge score={PT.score}/>
        <span className="chip chip-a">{"⚠"} Moderate Risk</span>
        <div style={{fontSize:10,color:"rgba(255,255,255,0.22)"}}>{PT.lastVisit}</div>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:15}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:13}}>
          <MTile icon="❤️" label="Heart Rate" val={hr} unit="bpm" col={C.rd} trend={2} sub="Normal"/>
          <MTile icon="🩸" label="Blood Pressure" val={`${PT.vitals.sys}/${PT.vitals.dia}`} unit="mmHg" col={C.am} trend={3} sub="Pre-hypertensive"/>
          <MTile icon="🫁" label="SpO₂" val={PT.vitals.spo2} unit="%" col={C.cy} sub="Normal"/>
          <MTile icon="⚖️" label="BMI" val={PT.vitals.bmi} col={C.ye} trend={1} sub="Overweight"/>
          <MTile icon="🍬" label="Glucose" val={PT.vitals.glu} unit="mg/dL" col={C.am} trend={4} sub="Borderline"/>
          <MTile icon="🌡️" label="Temperature" val={PT.vitals.temp} unit="°F" col={C.pu} sub="Normal"/>
        </div>
        <div className="card" style={{padding:20,flex:1}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
            <div><div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>Live Vitals Stream</div><div style={{fontSize:11,color:"rgba(255,255,255,0.28)"}}>Real-time sensor data</div></div>
            <div style={{display:"flex",gap:18}}>{[{l:"HR",v:hr+" bpm",c:C.rd},{l:"SpO₂",v:PT.vitals.spo2+"%",c:C.cy},{l:"BP",v:"128",c:C.am}].map(({l,v,c},i)=>(
              <div key={i} style={{textAlign:"center"}}><div className="mono" style={{color:c,fontSize:16,fontWeight:500}}>{v}</div><div style={{fontSize:10,color:"rgba(255,255,255,0.28)"}}>{l}</div></div>
            ))}</div>
          </div>
          <ResponsiveContainer width="100%" height={145}>
            <AreaChart data={data}>
              <defs>{[{id:"hrg",c:C.rd},{id:"o2g",c:C.cy}].map(({id,c})=>(<linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={c} stopOpacity={.28}/><stop offset="95%" stopColor={c} stopOpacity={0}/></linearGradient>))}</defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/>
              <XAxis dataKey="t" tick={{fill:"rgba(255,255,255,0.25)",fontSize:10}} interval={4}/>
              <YAxis tick={{fill:"rgba(255,255,255,0.25)",fontSize:10}}/>
              <Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12,fontSize:12}}/>
              <Area type="monotone" dataKey="hr" stroke={C.rd} fill="url(#hrg)" strokeWidth={2} name="Heart Rate" dot={false}/>
              <Area type="monotone" dataKey="o2" stroke={C.cy} fill="url(#o2g)" strokeWidth={2} name="SpO2" dot={false}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:14}}>
        <div className="card" style={{padding:18,flex:1}}>
          <div style={{fontWeight:700,fontSize:13,fontFamily:"Sora",marginBottom:14,display:"flex",alignItems:"center",gap:8}}>{"🧠"} AI Insights <span className="chip chip-c" style={{fontSize:9}}>LIVE</span></div>
          {[{icon:"🔴",txt:"Stress 67% — amplified by 5.5h sleep deficit",col:C.rd},{icon:"⚠️",txt:"Hypertension risk 45% — limit sodium",col:C.am},{icon:"💡",txt:"30-min walk 3x/wk reduces diabetes risk 28%",col:C.cy},{icon:"✅",txt:"Cardiac markers stable — continue plan",col:C.gr}].map((ins,i)=>(
            <div key={i} style={{display:"flex",gap:9,padding:"9px 11px",marginBottom:8,background:`${ins.col}0a`,borderRadius:9,borderLeft:`3px solid ${ins.col}45`,fontSize:12,color:"rgba(255,255,255,0.7)"}}><span style={{flexShrink:0}}>{ins.icon}</span><span>{ins.txt}</span></div>
          ))}
        </div>
        <div className="card" style={{padding:18}}>
          <div style={{fontWeight:700,fontSize:13,fontFamily:"Sora",marginBottom:12}}>Quick Actions</div>
          {[["📄 Report Analyzer","reports"],["🔮 What-If Sim","whatif"],["🤖 AI Chat","chat"],["🚨 Triage","triage"]].map(([l,p],i)=>(
            <button key={i} className="btn btn-cy" onClick={()=>go("/"+p)} style={{width:"100%",marginBottom:8,textAlign:"left",display:"flex",gap:8,fontSize:12}}>{l}</button>
          ))}
        </div>
      </div>
    </div>
  );
}


export default Dashboard;
