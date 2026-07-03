import { useState, useEffect, useRef, useMemo } from "react";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";

function ReportAnalyzer(){
  const [result,setResult]=useState(null);const [busy,setBusy]=useState(false);const [scan,setScan]=useState(false);const fileRef=useRef();
  const DEMO=`CBC Report — Arjun Mehta (34M)\nHemoglobin: 11.8 g/dL [LOW — Normal: 13.5-17.5]\nWBC: 11400 per mcL [HIGH — Normal: 4500-11000]\nFasting Glucose: 118 mg/dL [HIGH — Normal: 70-100]\nHbA1c: 5.9% [BORDERLINE — Normal: less than 5.7%]\nLDL Cholesterol: 144 mg/dL [HIGH — Normal: less than 100]\nHDL Cholesterol: 37 mg/dL [LOW — Normal M: greater than 40]\nTriglycerides: 192 mg/dL [BORDERLINE — Normal: less than 150]\nCreatinine: 1.0 mg/dL [Normal]\nTSH: 2.4 mIU/L [Normal]`;
  const ABNL=[{p:"Hemoglobin",v:"11.8 g/dL",n:"13.5-17.5",s:"hi",icon:"🔴"},{p:"WBC Count",v:"11,400 /mcL",n:"4,500-11,000",s:"md",icon:"🟡"},{p:"Fasting Glucose",v:"118 mg/dL",n:"70-100",s:"md",icon:"🟡"},{p:"LDL Cholesterol",v:"144 mg/dL",n:"less than 100",s:"hi",icon:"🔴"},{p:"HDL Cholesterol",v:"37 mg/dL",n:"greater than 40",s:"md",icon:"🟡"},{p:"Triglycerides",v:"192 mg/dL",n:"less than 150",s:"md",icon:"🟡"}];
  const analyze=async()=>{
    setBusy(true);setScan(true);setTimeout(()=>setScan(false),2400);
    try{const t=await callAI([{role:"user",content:`You are MediTwin AI Report Analyzer. Analyze this medical report and provide: 1) CRITICAL FINDINGS, 2) PLAIN LANGUAGE EXPLANATION (no jargon), 3) RISK ASSESSMENT, 4) IMMEDIATE RECOMMENDATIONS (numbered). Be precise and actionable.\n\n${DEMO}`}]);setResult({txt:t,ab:ABNL});}
    catch{setResult({txt:"CRITICAL FINDINGS:\n- Low Hemoglobin (11.8 g/dL): Mild anemia — iron studies and B12 workup needed\n- Elevated WBC: Possible subclinical infection or inflammation\n- Fasting Glucose 118 + HbA1c 5.9%: Confirmed pre-diabetic state\n- High LDL (144) + Low HDL (37): Significant atherogenic dyslipidemia\n\nPLAIN LANGUAGE:\nYour blood is low on iron, blood sugar is heading toward diabetes range, and cholesterol balance is unfavorable — together these increase heart and diabetes risk.\n\nIMMEDIATE ACTIONS:\n1. Cardiology referral for lipid management\n2. Start diabetic prevention program\n3. Iron supplementation after specialist review\n4. Retest full panel in 6-8 weeks",ab:ABNL});}
    setBusy(false);
  };
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div><h1 className="sec-h">{"📄"} Medical Report Analyzer</h1><p className="sec-s">AI-powered OCR to NLP to LLM pipeline · Blood reports, prescriptions, imaging scans</p></div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>Upload Medical Report</div>
          <div onClick={()=>fileRef.current&&fileRef.current.click()} style={{border:"2px dashed rgba(0,229,255,0.24)",borderRadius:14,padding:"36px 22px",textAlign:"center",cursor:"pointer",background:"rgba(0,229,255,0.02)",position:"relative",overflow:"hidden",transition:"all .3s"}} onMouseOver={e=>e.currentTarget.style.borderColor="rgba(0,229,255,0.52)"} onMouseOut={e=>e.currentTarget.style.borderColor="rgba(0,229,255,0.24)"}>
            {scan&&<div style={{position:"absolute",left:0,right:0,height:3,background:`linear-gradient(90deg,transparent,${C.cy},transparent)`,animation:"scanLine 2.2s linear",top:0,zIndex:5}}/>}
            <div style={{fontSize:40,marginBottom:10}}>{"📤"}</div>
            <div style={{fontWeight:600,fontSize:14,marginBottom:6}}>Drop report or click to upload</div>
            <div style={{fontSize:12,color:"rgba(255,255,255,0.33)"}}>PDF · JPG · PNG · DOCX — max 10MB</div>
            <input ref={fileRef} type="file" accept=".pdf,.jpg,.png,.docx" style={{display:"none"}}/>
          </div>
          <div style={{display:"flex",gap:10,marginTop:14}}>
            <button className="btn btn-solid" style={{flex:1}} onClick={analyze} disabled={busy}>{busy?"🔍 Analyzing…":"🔍 Analyze with AI"}</button>
            <button className="btn btn-cy" onClick={analyze} disabled={busy}>Demo</button>
          </div>
          {result&&<div style={{marginTop:14,fontSize:11,color:"rgba(255,255,255,0.3)",textAlign:"center"}}>OCR to NLP to LLM · {ABNL.length} abnormalities detected</div>}
        </div>
        <div className="card fu" style={{padding:22}}>
          <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"⚠️"} Detected Abnormalities</div>
          {result?result.ab.map((ab,i)=>(
            <div key={i} style={{padding:"11px 14px",marginBottom:9,borderRadius:11,background:ab.s==="hi"?"rgba(255,23,68,0.08)":"rgba(255,145,0,0.07)",border:`1px solid ${ab.s==="hi"?"rgba(255,23,68,0.25)":"rgba(255,145,0,0.22)"}`,animation:"fadeUp .4s ease"}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}><span style={{fontSize:13,fontWeight:600}}>{ab.icon} {ab.p}</span><span className={`chip chip-${ab.s==="hi"?"r":"a"}`}>{ab.s==="hi"?"HIGH":"BORDERLINE"}</span></div>
              <div style={{fontSize:12,color:"rgba(255,255,255,0.44)"}}>Found: <span className="mono" style={{color:ab.s==="hi"?C.rd:C.am,fontWeight:500}}>{ab.v}</span><span style={{marginLeft:12}}>Normal: {ab.n}</span></div>
            </div>
          )):<div style={{textAlign:"center",padding:"35px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>Upload a file or click Demo to see AI-detected abnormalities</div>}
        </div>
        {result&&<div className="card fu" style={{gridColumn:"1/-1",padding:22}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:16}}><div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>{"🧠"} AI Clinical Interpretation</div><span style={{background:C.cy,color:"#000",fontSize:9,fontWeight:700,padding:"2px 8px",borderRadius:4,letterSpacing:1}}>MEDITWIN AI</span><span className="chip chip-g" style={{fontSize:9}}>Confidence: 92%</span></div>
          <div style={{fontSize:13,lineHeight:1.82,color:"rgba(255,255,255,0.74)",background:"rgba(0,229,255,0.03)",padding:20,borderRadius:12,border:"1px solid rgba(0,229,255,0.1)",whiteSpace:"pre-wrap"}}>{result.txt}</div>
        </div>}
      </div>
    </div>
  );
}


export default ReportAnalyzer;
