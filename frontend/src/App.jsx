/**
 * MediTwin AI — Focused Application Shell
 * 9 pages. One clear story. One killer GenAI feature.
 */
import { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { C, PT, S } from "./shared";

import Dashboard              from "./pages/Dashboard";
import DigitalTwin            from "./pages/DigitalTwin";
import ClinicalReasoningAgent from "./pages/ClinicalReasoningAgent";
import AIChat                 from "./pages/AIChat";
import DiseaseRisk            from "./pages/DiseaseRisk";
import WhatIf                 from "./pages/WhatIf";
import TimeMachine            from "./pages/TimeMachine";
import ReportAnalyzer         from "./pages/ReportAnalyzer";
import EmergencyTriage        from "./pages/EmergencyTriage";
import FamilyTwin             from "./pages/FamilyTwin";
import Recommendations        from "./pages/Recommendations";
import PreventiveImpact       from "./pages/PreventiveImpact";
import HealthTimeline         from "./pages/HealthTimeline";

const NAV = [
  { path:"/",         icon:"🏠", l:"Dashboard" },
  { path:"/twin",     icon:"🧬", l:"Digital Twin" },
  { path:"/reasoning",icon:"🧠", l:"Clinical Reasoning Agent", badge:"FLAGSHIP" },
  { path:"/chat",     icon:"🤖", l:"AI Assistant",  badge:"AI" },
  { path:"/risk",     icon:"📊", l:"Disease Risk" },
  { path:"/whatif",   icon:"🔮", l:"What-If Sim",   badge:"NEW" },
  { path:"/timemachine",icon:"⏳",l:"Time Machine",  badge:"NEW" },
  { path:"/reports",  icon:"📄", l:"Report Analyzer" },
  { path:"/triage",   icon:"🚨", l:"Emergency Triage", badge:"3" },
  { path:"/family",   icon:"🌳", l:"Family Twin",    badge:"NEW" },
  { path:"/recs",     icon:"💊", l:"Recommendations" },
  { path:"/impact",   icon:"💰", l:"Preventive ROI", badge:"NEW" },
  { path:"/timeline", icon:"⏱️", l:"Health Timeline" },
];

function Sidebar({ open, setOpen }) {
  const navigate  = useNavigate();
  const { pathname } = useLocation();
  return (
    <div style={{width:open?234:56,transition:"width .28s ease",background:"linear-gradient(180deg,#07102a 0%,#060d22 100%)",borderRight:"1px solid rgba(0,229,255,0.07)",display:"flex",flexDirection:"column",padding:"18px 10px",overflow:"hidden",flexShrink:0,zIndex:10}}>
      <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:28,paddingLeft:4}}>
        <div style={{width:36,height:36,borderRadius:10,background:"linear-gradient(135deg,rgba(0,229,255,0.35),rgba(124,77,255,0.35))",border:"1px solid rgba(0,229,255,0.3)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:20,flexShrink:0,animation:"pulseC 3s ease-in-out infinite"}}>🧬</div>
        {open&&<div><div className="sora gt" style={{fontSize:16,fontWeight:700,lineHeight:1}}>MediTwin AI</div><div style={{fontSize:9,color:"rgba(255,255,255,0.22)",letterSpacing:2,marginTop:2}}>DIGITAL HEALTH OS</div></div>}
      </div>
      <div style={{flex:1,overflowY:"auto",overflowX:"hidden",minHeight:0}}>
        {open&&<div style={{fontSize:9,color:"rgba(255,255,255,0.18)",letterSpacing:2,marginBottom:8,paddingLeft:12}}>NAVIGATION</div>}
        {NAV.map(n=>(
          <div key={n.path} className={`nav ${pathname===n.path?"on":""}`} onClick={()=>navigate(n.path)} style={{justifyContent:open?"flex-start":"center"}}>
            <span style={{fontSize:17,flexShrink:0}}>{n.icon}</span>
            {open&&<>
              <span style={{flex:1,overflow:"hidden",textOverflow:"ellipsis"}}>{n.l}</span>
              {n.badge&&<span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,
                background:n.badge==="FLAGSHIP"?"rgba(0,229,255,0.25)":n.badge==="3"?"rgba(255,23,68,0.25)":"rgba(124,77,255,0.2)",
                color:n.badge==="FLAGSHIP"?C.cy:n.badge==="3"?C.rd:"#b388ff"}}>{n.badge}</span>}
            </>}
          </div>
        ))}
      </div>
      {open&&<div style={{padding:"14px",background:"rgba(0,229,255,0.06)",borderRadius:11,border:"1px solid rgba(0,229,255,0.1)",marginBottom:10}}>
        <div style={{fontSize:10,color:C.cy,fontWeight:700,letterSpacing:1,marginBottom:7}}>ACTIVE PATIENT</div>
        <div style={{fontSize:13,fontWeight:600}}>{PT.name}</div>
        <div style={{fontSize:10,color:"rgba(255,255,255,0.33)",marginTop:1}}>{PT.id}</div>
        <div style={{display:"flex",alignItems:"center",gap:6,marginTop:8}}><span className="dot dot-live" style={{width:6,height:6}}/><span style={{fontSize:10,color:"#00ff9d"}}>Monitoring Active</span></div>
      </div>}
      <button onClick={()=>setOpen(o=>!o)} style={{width:"100%",padding:"9px",borderRadius:9,cursor:"pointer",background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.06)",color:"rgba(255,255,255,0.28)",fontSize:14,display:"flex",justifyContent:"center",outline:"none"}}>{open?"◀":"▶"}</button>
    </div>
  );
}

function TopBar() {
  const { pathname } = useLocation();
  const active = NAV.find(n=>n.path===pathname)||NAV[0];
  return (
    <div style={{padding:"14px 24px",display:"flex",justifyContent:"space-between",alignItems:"center",borderBottom:"1px solid rgba(255,255,255,0.04)",background:"rgba(2,6,26,0.85)",backdropFilter:"blur(20px)",flexShrink:0,zIndex:5}}>
      <div style={{display:"flex",alignItems:"center",gap:8,fontSize:12}}>
        <span style={{color:"rgba(255,255,255,0.22)"}}>MediTwin AI</span>
        <span style={{color:"rgba(255,255,255,0.14)"}}>/</span>
        <span style={{color:C.cy,fontWeight:600}}>{active.l}</span>
      </div>
      <div style={{display:"flex",gap:12,alignItems:"center"}}>
        <div style={{fontSize:12,color:"rgba(255,255,255,0.28)",fontFamily:"DM Mono"}}>{new Date().toLocaleDateString("en-IN",{weekday:"short",day:"numeric",month:"short",year:"numeric"})}</div>
        <div style={{display:"flex",alignItems:"center",gap:6,padding:"6px 12px",background:"rgba(0,255,157,0.08)",border:"1px solid rgba(0,255,157,0.18)",borderRadius:100,fontSize:11}}>
          <span className="dot dot-live" style={{width:6,height:6}}/><span style={{color:"#00ff9d"}}>All Systems Active</span>
        </div>
      </div>
    </div>
  );
}

function AppShell() {
  const [open,setOpen]=useState(true);
  const { pathname }=useLocation();
  return (
    <div style={{display:"flex",height:"100vh",overflow:"hidden",background:"#02061a"}}>
      <div style={{position:"fixed",inset:0,backgroundImage:"linear-gradient(rgba(0,229,255,0.022) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,0.022) 1px,transparent 1px)",backgroundSize:"44px 44px",pointerEvents:"none",zIndex:0}}/>
      <Sidebar open={open} setOpen={setOpen}/>
      <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden",position:"relative",zIndex:1}}>
        <TopBar/>
        <div key={pathname} style={{flex:1,overflowY:"auto",padding:"22px 24px",animation:"fadeUp .35s ease"}}>
          <Routes>
            <Route path="/"          element={<Dashboard/>}/>
            <Route path="/twin"      element={<DigitalTwin/>}/>
            <Route path="/reasoning" element={<ClinicalReasoningAgent/>}/>
            <Route path="/chat"      element={<AIChat/>}/>
            <Route path="/risk"      element={<DiseaseRisk/>}/>
            <Route path="/whatif"    element={<WhatIf/>}/>
            <Route path="/timemachine" element={<TimeMachine/>}/>
            <Route path="/reports"   element={<ReportAnalyzer/>}/>
            <Route path="/triage"    element={<EmergencyTriage/>}/>
            <Route path="/family"    element={<FamilyTwin/>}/>
            <Route path="/recs"      element={<Recommendations/>}/>
            <Route path="/impact"    element={<PreventiveImpact/>}/>
            <Route path="/timeline"  element={<HealthTimeline/>}/>
            <Route path="*"          element={<Dashboard/>}/>
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function MediTwinAI() {
  return (
    <>
      <style>{S}</style>
      <BrowserRouter>
        <AppShell/>
      </BrowserRouter>
    </>
  );
}
