import { useState, useEffect, useRef, useMemo } from "react";
import { AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";

function HealthTimeline(){
  const [head,setHead]=useState(5);const [playing,setPlaying]=useState(false);const ref=useRef();
  useEffect(()=>{if(playing){ref.current=setInterval(()=>setHead(h=>{if(h>=5){setPlaying(false);return 5;}return h+1;}),900);}return()=>clearInterval(ref.current);},[playing]);
  const cur=TL[Math.min(head,TL.length-1)];
  const EVTS=[{m:"Sep",ev:"Started Metformin 500mg (prn) — pre-diabetic management",type:"med",icon:"💊"},{m:"Oct",ev:"High-stress project sprint — BP and stress markers worsened",type:"warn",icon:"⚠️"},{m:"Nov",ev:"Joined gym · 2x/week strength training routine",type:"pos",icon:"💪"},{m:"Dec",ev:"Sleep protocol started — improved to 6.5h, BP trending down",type:"pos",icon:"😴"},{m:"Jan",ev:"Full metabolic panel — pre-diabetic state confirmed, HbA1c 5.9%",type:"check",icon:"🔬"},{m:"Feb",ev:"Current — BMI trending down · Health Score improved to 72",type:"pos",icon:"📉"}];
  const TC={med:C.cy,warn:C.am,pos:C.gr,check:C.pu};
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div><h1 className="sec-h">{"⏱️"} Health Timeline Playback</h1><p className="sec-s">Replay your complete health journey · Interactive scrubber · Animated event log</p></div>
      <div className="card fu" style={{padding:22}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:18}}>
          <div><div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>Health Score Trajectory — {cur.m} 2025-26</div><div style={{fontSize:11,color:"rgba(255,255,255,0.28)",marginTop:2}}>Drag slider or press Play to replay your health story</div></div>
          <div style={{display:"flex",gap:8}}>
            <button className="btn btn-cy" onClick={()=>{setPlaying(false);setHead(0);}} style={{fontSize:12,padding:"8px 14px"}}>{"⏮"} Reset</button>
            <button className="btn btn-solid" onClick={()=>{if(!playing){setHead(0);setPlaying(true);}else setPlaying(false);}} style={{fontSize:12,padding:"8px 14px"}}>{playing?"⏸ Pause":"▶ Play"}</button>
          </div>
        </div>
        <div style={{display:"flex",gap:12,justifyContent:"center",marginBottom:18,flexWrap:"wrap"}}>
          {[{l:"Health Score",v:cur.sc,c:C.cy},{l:"Diabetes Risk",v:cur.dia+"%",c:C.am},{l:"Stress Level",v:cur.stress+"%",c:C.pu},{l:"Blood Pressure",v:cur.bp+" sys",c:C.rd}].map(({l,v,c},i)=>(
            <div key={i} style={{textAlign:"center",padding:"12px 20px",background:`${c}0f`,borderRadius:12,border:`1px solid ${c}28`,minWidth:110}}><div className="mono" style={{fontSize:22,fontWeight:500,color:c}}>{v}</div><div style={{fontSize:10,color:"rgba(255,255,255,0.33)",marginTop:4}}>{l}</div></div>
          ))}
        </div>
        <input type="range" min={0} max={5} step={1} value={head} className="slider" onChange={e=>setHead(parseInt(e.target.value))} style={{background:`linear-gradient(to right,${C.cy} ${(head/5)*100}%,rgba(255,255,255,0.1) ${(head/5)*100}%)`,marginBottom:8}}/>
        <div style={{display:"flex",justifyContent:"space-between",fontSize:10,color:"rgba(255,255,255,0.25)"}}>{TL.map((d,i)=><span key={i}>{d.m}</span>)}</div>
        <ResponsiveContainer width="100%" height={175} style={{marginTop:20}}>
          <AreaChart data={TL.slice(0,head+1)}>
            <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={C.cy} stopOpacity={.28}/><stop offset="95%" stopColor={C.cy} stopOpacity={0}/></linearGradient></defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/>
            <XAxis dataKey="m" tick={{fill:"rgba(255,255,255,0.35)",fontSize:11}}/><YAxis tick={{fill:"rgba(255,255,255,0.35)",fontSize:11}}/>
            <Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/>
            <Area type="monotone" dataKey="sc" stroke={C.cy} fill="url(#tg)" strokeWidth={2.5} name="Health Score" dot={{fill:C.cy,r:4,strokeWidth:0}}/>
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="card fu" style={{padding:22}}>
        <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:18}}>{"📋"} Health Events Log</div>
        <div style={{position:"relative",paddingLeft:28}}>
          <div style={{position:"absolute",left:12,top:0,bottom:0,width:1.5,background:"rgba(0,229,255,0.12)",borderRadius:1}}/>
          {EVTS.slice(0,head+1).map((ev,i)=>(
            <div key={i} style={{position:"relative",marginBottom:20,animation:"fadeUp .4s ease"}}>
              <div style={{position:"absolute",left:-28,width:26,height:26,borderRadius:"50%",background:`${TC[ev.type]}18`,border:`1px solid ${TC[ev.type]}35`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:13}}>{ev.icon}</div>
              <div style={{padding:"10px 14px",background:"rgba(255,255,255,0.025)",borderRadius:10,border:"1px solid rgba(255,255,255,0.06)"}}>
                <div style={{fontSize:10,color:TC[ev.type],fontWeight:600,marginBottom:4,letterSpacing:.5}}>{ev.m} 2025</div>
                <div style={{fontSize:13,color:"rgba(255,255,255,0.73)"}}>{ev.ev}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


export default HealthTimeline;
