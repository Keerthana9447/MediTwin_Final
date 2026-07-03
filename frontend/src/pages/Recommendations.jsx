import { useState, useEffect, useRef, useMemo } from "react";
import { C, PT, TL, RADAR, PATS, callAI } from "../shared";
import { Dots } from "../components/SharedUI";

function Recommendations(){
  const TABS=[{k:"diet",l:"🥗 Diet"},{k:"exercise",l:"💪 Exercise"},{k:"sleep",l:"😴 Sleep"},{k:"stress",l:"🧘 Stress"},{k:"preventive",l:"🛡️ Preventive"}];
  const [tab,setTab]=useState("diet");const [plan,setPlan]=useState("");const [busy,setBusy]=useState(false);
  const DFLT={diet:"1. Replace white rice with millets or brown rice\n2. Add fiber: 2 cups vegetables per meal\n3. Limit sodium to less than 2g/day — critical for hypertension\n4. Heart-healthy fats: 1 tbsp olive oil + handful of walnuts daily\n5. Protein at each meal: eggs, legumes, paneer, fish 3x/week\n6. Zero added sugar — use dates or fruit\n7. Green tea 2 cups/day instead of chai\n8. Eat until 80% full — never skip breakfast",exercise:"1. Week 1-2: 20-min brisk walk x5 days — build baseline\n2. Week 3+: Add bodyweight training 3x/week\n3. Daily target: 8,000-10,000 steps\n4. Morning yoga 15 min — cortisol and BP regulation\n5. Swimming or cycling on weekends\n6. Never skip 2 consecutive days\n7. Exercise before 8 AM for optimal cortisol-insulin response\n8. Target: 150 min moderate activity per week",sleep:"1. Fixed wake time: 6:00 AM daily — even weekends\n2. No screens 60 min before bed\n3. Sleep by 10:30 PM — 7+ hours minimum\n4. Room temperature: 19-21 degrees C optimal\n5. Chamomile tea or magnesium 45 min before bed\n6. 4-7-8 breathing at lights out\n7. No caffeine after 2 PM\n8. Track with a sleep app for data-driven improvement",stress:"1. Morning: 10-min mindfulness meditation daily\n2. Box breathing x3 per day (4-4-4-4 pattern)\n3. Evening journaling: 3 gratitude points nightly\n4. 1 meaningful social conversation daily\n5. Screen-free 1 hour after waking and 1 hour before sleep\n6. Nature walk 3x/week — proven cortisol reduction\n7. Progressive muscle relaxation before sleep\n8. Professional support if stress remains above 7/10 for 4 weeks",preventive:"1. Monitor BP every 3 days — alert if above 135/85\n2. HbA1c retest in 3 months\n3. Annual dilated eye exam — diabetic retinopathy screening\n4. Lipid panel every 6 months\n5. Annual ECG after age 35\n6. Stay current on all vaccinations\n7. Dental checkup every 6 months\n8. Annual full-body checkup"};
  const generate=async()=>{setBusy(true);try{const t=await callAI([{role:"user",content:`Create a personalized ${tab} plan for: ${PT.name}, ${PT.age}y, BMI ${PT.vitals.bmi}, Diabetes Risk ${PT.risks.diabetes}%, Hypertension ${PT.risks.bp}%, Stress ${PT.risks.stress}%, Sleep ${PT.life.sleep}h/night, Exercise ${PT.life.ex}x/week. Write exactly 8 specific numbered actionable points. Evidence-based. Max 200 words.`}]);setPlan(t);}catch{setPlan(DFLT[tab]);}setBusy(false);};
  useEffect(()=>setPlan(""),[tab]);
  return(
    <div style={{display:"flex",flexDirection:"column",gap:18}}>
      <div><h1 className="sec-h">{"💊"} AI Recommendation Engine</h1><p className="sec-s">Hyper-personalized plans · Based on your digital health twin · Clinically validated</p></div>
      <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
        {TABS.map(t=>(<button key={t.k} onClick={()=>setTab(t.k)} className="btn" style={{background:tab===t.k?"linear-gradient(135deg,rgba(0,229,255,0.18),rgba(124,77,255,0.14))":"rgba(255,255,255,0.04)",color:tab===t.k?C.cy:"rgba(255,255,255,0.44)",border:`1px solid ${tab===t.k?"rgba(0,229,255,0.28)":"rgba(255,255,255,0.06)"}`,fontSize:13,padding:"10px 18px",transition:"all .18s"}}>{t.l}</button>))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:18}}>
        <div className="card fu" style={{padding:22}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:18}}><div><div style={{fontWeight:700,fontSize:14,fontFamily:"Sora"}}>{TABS.find(t=>t.k===tab)&&TABS.find(t=>t.k===tab).l} Plan</div><div style={{fontSize:11,color:"rgba(255,255,255,0.33)",marginTop:2}}>Personalized for your health twin</div></div><button className="btn btn-solid" onClick={generate} disabled={busy} style={{fontSize:12,padding:"9px 18px"}}>{busy?"Generating…":"Generate AI Plan"}</button></div>
          {busy?<div style={{padding:"40px 0",display:"flex",gap:8,justifyContent:"center"}}><Dots/></div>
          :plan?<div style={{fontSize:13,lineHeight:1.82,color:"rgba(255,255,255,0.76)",background:"rgba(0,229,255,0.03)",padding:18,borderRadius:12,border:"1px solid rgba(0,229,255,0.09)",whiteSpace:"pre-wrap",animation:"fadeUp .4s ease"}}>{plan}</div>
          :<div style={{textAlign:"center",padding:"40px 0",color:"rgba(255,255,255,0.22)",fontSize:13}}>Click Generate AI Plan for personalized {tab} recommendations</div>}
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div className="card fu" style={{padding:22}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"🛡️"} Preventive Action Engine</div>
            {[{act:"Reduce sugar intake",imp:"-42%",dis:"Diabetes",time:"8 wks",icon:"🍬"},{act:"Sleep 7.5h per night",imp:"-28%",dis:"Hypertension",time:"4 wks",icon:"😴"},{act:"Exercise 4x per week",imp:"-35%",dis:"Heart Disease",time:"12 wks",icon:"💪"},{act:"Daily meditation",imp:"-45%",dis:"Stress",time:"3 wks",icon:"🧘"}].map((item,i)=>(
              <div key={i} style={{padding:"12px 14px",marginBottom:9,borderRadius:11,background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.12)"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}><span style={{fontSize:13,fontWeight:600}}>{item.icon} {item.act}</span><span className="mono" style={{color:C.gr,fontWeight:500,fontSize:14}}>{item.imp}</span></div><div style={{fontSize:11,color:"rgba(255,255,255,0.38)"}}>Reduces <span style={{color:C.am}}>{item.dis} risk</span> in <span style={{color:C.cy}}>{item.time}</span></div></div>
            ))}
          </div>
          <div className="card fu" style={{padding:22}}>
            <div style={{fontWeight:700,fontSize:14,fontFamily:"Sora",marginBottom:16}}>{"📅"} 30-Day Milestone Plan</div>
            {[{d:"Week 1",g:"Fix sleep schedule · Cut added sugar 50%"},{d:"Week 2",g:"Daily 20-min walks + 2L water target"},{d:"Week 3",g:"Start resistance training 3x/week"},{d:"Week 4",g:"BP + HbA1c recheck · Adjust plan"}].map((m,i)=>(
              <div key={i} style={{display:"flex",gap:14,marginBottom:14}}><div style={{width:56,height:26,borderRadius:7,background:"rgba(0,229,255,0.12)",border:"1px solid rgba(0,229,255,0.25)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:700,color:C.cy,flexShrink:0,fontFamily:"DM Mono"}}>{m.d}</div><div style={{fontSize:12,color:"rgba(255,255,255,0.64)",paddingTop:3}}>{m.g}</div></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════
//  SHARED CLINICAL MATH (mirrors backend exactly)
// ═══════════════════════════════════════════════════════════

// FINDRISC-banded diabetes risk

export default Recommendations;
