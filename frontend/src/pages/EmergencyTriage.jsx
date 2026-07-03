import { useState, useEffect, useRef, useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";

function EmergencyTriage(){
  const [sel,setSel]=useState(null);
  const LC={cr:C.rd,hi:C.am,md:C.ye,lo:C.gr};
  const LL={cr:"🚨 CRITICAL",hi:"🔴 HIGH",md:"🟡 MEDIUM",lo:"🟢 LOW"};
  const sorted=[...PATS].sort((a,b)=>b.sc-a.sc);
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
        <div><h1 className="sec-h">{"🚨"} Emergency Triage System</h1><p className="sec-s">AI-powered patient prioritization · Real-time severity scoring · Hospital command center</p></div>
        <div style={{display:"flex",alignItems:"center",gap:8,padding:"9px 18px",background:"rgba(255,23,68,0.1)",border:"1px solid rgba(255,23,68,0.28)",borderRadius:100,fontSize:12}}><span className="dot" style={{background:C.rd,animation:"blink .9s ease-in-out infinite",width:7,height:7}}/><span style={{color:C.rd,fontWeight:700}}>{sorted.filter(p=>p.lvl==="cr"||p.lvl==="hi").length} HIGH PRIORITY</span></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14}}>
        {[{l:"Total Patients",v:PATS.length,c:C.cy,icon:"👥"},{l:"Critical",v:PATS.filter(p=>p.lvl==="cr").length,c:C.rd,icon:"🚨"},{l:"High Priority",v:PATS.filter(p=>p.lvl==="hi").length,c:C.am,icon:"⚠️"},{l:"Avg Wait",v:"12 min",c:C.gr,icon:"⏱️"}].map(({l,v,c,icon},i)=>(
          <div key={i} className="mc" style={{textAlign:"center"}}><div style={{fontSize:26,marginBottom:8}}>{icon}</div><div className="mono" style={{fontSize:28,fontWeight:500,color:c}}>{v}</div><div style={{fontSize:11,color:"rgba(255,255,255,0.33)",marginTop:4}}>{l}</div></div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"📋"} Priority Queue</div>
          {sorted.map((pt,i)=>(
            <div key={i} className={`tri-${pt.lvl}`} onClick={()=>setSel(sel&&sel.id===pt.id?null:pt)} style={{marginBottom:10,cursor:"pointer",transition:"all .2s",transform:sel&&sel.id===pt.id?"scale(1.02)":"scale(1)"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
                <div style={{display:"flex",gap:12,alignItems:"center"}}><div style={{width:34,height:34,borderRadius:9,background:`${LC[pt.lvl]}20`,border:`1px solid ${LC[pt.lvl]}35`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,fontWeight:700,color:LC[pt.lvl],fontFamily:"DM Mono"}}>{i+1}</div><div><div style={{fontSize:14,fontWeight:600}}>{pt.name}</div><div style={{fontSize:11,color:"rgba(255,255,255,0.38)"}}>{pt.age}y · {pt.id}</div></div></div>
                <div style={{textAlign:"right"}}><div className="mono" style={{fontSize:20,fontWeight:500,color:LC[pt.lvl]}}>{pt.sc}</div><span className={`chip chip-${pt.lvl==="cr"?"r":pt.lvl==="hi"?"a":pt.lvl==="md"?"c":"g"}`} style={{fontSize:9}}>{LL[pt.lvl]}</span></div>
              </div>
              <div style={{marginTop:10,fontSize:12,color:"rgba(255,255,255,0.6)"}}>{pt.cond}</div>
              <div style={{marginTop:6,fontSize:10,color:"rgba(255,255,255,0.24)"}}>{pt.vi}</div>
            </div>
          ))}
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          {sel?(<div className="card fu" style={{padding:22,animation:"fadeUp .3s ease"}}>
            <div style={{fontSize:15,fontWeight:700,fontFamily:"Sora",color:LC[sel.lvl],marginBottom:18}}>{LL[sel.lvl]} — {sel.name}</div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:18}}>
              {[["🩸 Vitals",sel.vi],["📊 Score",sel.sc+"/100"],["👤 Age",sel.age+" years"],["🆔 ID",sel.id]].map(([l,v],i)=>(
                <div key={i} style={{padding:12,background:"rgba(255,255,255,0.035)",borderRadius:10,border:"1px solid rgba(255,255,255,0.06)"}}><div style={{fontSize:11,color:"rgba(255,255,255,0.33)",marginBottom:5}}>{l}</div><div className="mono" style={{fontSize:13,fontWeight:500}}>{v}</div></div>
              ))}
            </div>
            <div style={{padding:"12px 16px",background:"rgba(255,255,255,0.03)",borderRadius:10,marginBottom:16,fontSize:13,color:"rgba(255,255,255,0.73)"}}>{sel.cond}</div>
            <div style={{display:"flex",gap:10}}><button className="btn btn-rd" style={{flex:1,fontSize:12}}>{"🔔"} Alert Team</button><button className="btn btn-cy" style={{flex:1,fontSize:12}}>{"📋"} Full Profile</button></div>
          </div>):(<div className="card fu" style={{padding:22,display:"flex",alignItems:"center",justifyContent:"center",minHeight:200}}><div style={{textAlign:"center",color:"rgba(255,255,255,0.22)",fontSize:13}}><div style={{fontSize:40,marginBottom:12}}>{"👆"}</div>Select a patient to view details</div></div>)}
          <div className="card fu" style={{padding:22}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"📊"} Triage Distribution</div>
            <ResponsiveContainer width="100%" height={185}><PieChart><Pie data={[{n:"Critical",v:1},{n:"High",v:2},{n:"Medium",v:1},{n:"Low",v:1}]} cx="50%" cy="50%" innerRadius={48} outerRadius={78} dataKey="v">{[C.rd,C.am,C.ye,C.gr].map((c,i)=><Cell key={i} fill={c}/>)}</Pie><Tooltip contentStyle={{background:"#070d22",border:"1px solid rgba(0,229,255,0.2)",borderRadius:12}}/><Legend wrapperStyle={{fontSize:11,color:"rgba(255,255,255,0.4)"}}/></PieChart></ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}


export default EmergencyTriage;
