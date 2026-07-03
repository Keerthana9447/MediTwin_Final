import { useState, useEffect, useRef, useMemo } from "react";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";

export function Avatar({score,risks}){
  const [beat,setBeat]=useState(false);
  useEffect(()=>{const i=setInterval(()=>setBeat(b=>!b),900);return()=>clearInterval(i);},[]);
  const col=score>75?C.gr:score>50?C.am:C.rd;
  return(
    <div style={{position:"relative",width:180,height:272,margin:"0 auto"}}>
      {[220,178,144].map((s,i)=>(
        <div key={i} style={{position:"absolute",left:"50%",top:"46%",width:s,height:s,marginLeft:-s/2,marginTop:-s/2,border:`1px solid ${col}`,borderRadius:"50%",opacity:0.06+i*0.04,animation:`aura ${2+i*0.55}s ease-in-out infinite`,animationDelay:`${i*0.4}s`,boxShadow:`0 0 ${18+i*10}px ${col}28`}}/>
      ))}
      <svg width="180" height="272" viewBox="0 0 180 272" style={{position:"relative",zIndex:2}}>
        <defs>
          <filter id="gw"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <radialGradient id="bg" cx="50%" cy="35%" r="65%"><stop offset="0%" stopColor={col} stopOpacity="0.22"/><stop offset="100%" stopColor={col} stopOpacity="0.03"/></radialGradient>
          <linearGradient id="sp" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={col} stopOpacity="0.75"/><stop offset="100%" stopColor={col} stopOpacity="0"/></linearGradient>
        </defs>
        <circle cx="90" cy="38" r="30" fill="url(#bg)" stroke={col} strokeWidth="1.5" filter="url(#gw)" opacity="0.9"/>
        <rect x="82" y="65" width="16" height="14" rx="6" fill={col} opacity="0.18"/>
        <ellipse cx="90" cy="135" rx="46" ry="58" fill="url(#bg)" stroke={col} strokeWidth="1.5" opacity="0.88" filter="url(#gw)"/>
        <circle cx="75" cy="113" r="9" fill={risks.heart>40?C.rd:C.gr} opacity={beat?0.92:0.42} style={{transition:"opacity .35s"}} filter="url(#gw)"/>
        <text x="75" y="118" textAnchor="middle" fontSize="11" fill="#fff" opacity="0.9">{"♥"}</text>
        <ellipse cx="67" cy="133" rx="11" ry="15" fill={C.cy} opacity="0.11" stroke={C.cy} strokeWidth="0.8"/>
        <ellipse cx="113" cy="133" rx="11" ry="15" fill={C.cy} opacity="0.11" stroke={C.cy} strokeWidth="0.8"/>
        <ellipse cx="92" cy="157" rx="14" ry="8" fill={C.am} opacity={risks.diabetes>35?0.2:0.07} stroke={C.am} strokeWidth="0.8"/>
        <line x1="90" y1="78" x2="90" y2="190" stroke="url(#sp)" strokeWidth="1.2" strokeDasharray="5 4" opacity="0.4"/>
        <ellipse cx="34" cy="140" rx="13" ry="44" fill={col} opacity="0.1" stroke={col} strokeWidth="1"/>
        <ellipse cx="146" cy="140" rx="13" ry="44" fill={col} opacity="0.1" stroke={col} strokeWidth="1"/>
        <ellipse cx="72" cy="230" rx="18" ry="42" fill={col} opacity="0.1" stroke={col} strokeWidth="1"/>
        <ellipse cx="108" cy="230" rx="18" ry="42" fill={col} opacity="0.1" stroke={col} strokeWidth="1"/>
        <text x="90" y="43" textAnchor="middle" fontSize="14" fontWeight="800" fontFamily="Sora" fill={col} filter="url(#gw)">{score}</text>
      </svg>
      <svg width="180" height="26" viewBox="0 0 180 26" style={{position:"absolute",bottom:0,left:0}}>
        <polyline points="0,13 20,13 30,3 40,23 50,13 75,13 83,7 90,21 97,13 180,13" fill="none" stroke={col} strokeWidth="1.6" opacity="0.55" strokeDasharray="200" strokeDashoffset={beat?0:200} style={{transition:"stroke-dashoffset .85s ease"}}/>
      </svg>
    </div>
  );
}

export function Gauge({score}){
  const ang=(score/100)*180-90,col=score>75?C.gr:score>50?C.am:C.rd,r=80;
  const x=100+r*Math.cos(ang*Math.PI/180),y=100-r*Math.sin(ang*Math.PI/180);
  const lx=100+65*Math.cos(ang*Math.PI/180),ly=100-65*Math.sin(ang*Math.PI/180);
  return(
    <svg width="200" height="112" viewBox="0 0 200 112">
      <defs>
        <linearGradient id="gg" x1="0%" x2="100%"><stop offset="0%" stopColor={C.rd}/><stop offset="50%" stopColor={C.am}/><stop offset="100%" stopColor={C.gr}/></linearGradient>
        <filter id="gf"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="13" strokeLinecap="round"/>
      <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gg)" strokeWidth="13" strokeLinecap="round" opacity="0.32"/>
      <path d={`M 20 100 A 80 80 0 ${score>50?1:0} 1 ${x} ${y}`} fill="none" stroke={col} strokeWidth="13" strokeLinecap="round" filter="url(#gf)"/>
      <line x1="100" y1="100" x2={lx} y2={ly} stroke={col} strokeWidth="2.5" strokeLinecap="round"/>
      <circle cx="100" cy="100" r="6" fill={col} filter="url(#gf)"/>
      <text x="100" y="82" textAnchor="middle" fontSize="30" fontWeight="800" fontFamily="Sora" fill={col}>{score}</text>
      <text x="100" y="97" textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.32)" letterSpacing="2">HEALTH SCORE</text>
    </svg>
  );
}

export function MTile({icon,label,val,unit="",sub="",col=C.cy,trend=null}){
  return(
    <div className="mc fu">
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
        <div style={{width:35,height:35,borderRadius:9,background:`${col}1a`,border:`1px solid ${col}28`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:17}}>{icon}</div>
        {trend!=null&&<span style={{fontSize:11,fontWeight:700,padding:"2px 8px",borderRadius:6,background:`${trend>0?C.rd:C.gr}18`,color:trend>0?C.rd:C.gr}}>{trend>0?"↑":"↓"}{Math.abs(trend)}%</span>}
      </div>
      <div className="mono" style={{fontSize:26,fontWeight:500,color:col,lineHeight:1}}>{val}<span style={{fontSize:12,fontWeight:400,color:"rgba(255,255,255,0.28)",marginLeft:3}}>{unit}</span></div>
      <div style={{fontSize:11,color:"rgba(255,255,255,0.38)",marginTop:5}}>{label}</div>
      {sub&&<div style={{fontSize:10,color:col,marginTop:3,opacity:.75}}>{sub}</div>}
    </div>
  );
}

export function RBar({label,val,conf=null}){
  const fc=val>60?C.rd:val>35?C.am:C.gr;
  return(
    <div style={{marginBottom:16}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:7,fontSize:13}}>
        <span style={{color:"rgba(255,255,255,0.68)"}}>{label}</span>
        <div style={{display:"flex",gap:8,alignItems:"center"}}>
          {conf&&<span style={{fontSize:10,color:"rgba(255,255,255,0.28)"}}>AI {conf}%</span>}
          <span className="mono" style={{fontWeight:500,color:fc}}>{val}%</span>
        </div>
      </div>
      <div className="bar-w"><div className="bar-f" style={{width:`${val}%`,background:`linear-gradient(90deg,${fc}78,${fc})`}}/></div>
    </div>
  );
}

export function Dots(){
  return(<div style={{display:"flex",gap:6}}>{[0,1,2].map(i=><div key={i} style={{width:9,height:9,borderRadius:"50%",background:C.cy,animation:`blink .7s ease-in-out infinite`,animationDelay:`${i*.18}s`}}/>)}</div>);
}


export default Dots;
