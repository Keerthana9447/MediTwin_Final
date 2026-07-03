"""MediTwin AI — Groq LLM Service | Model: openai/gpt-oss-120b"""
from __future__ import annotations
import os, time, logging
from typing import Any

logger  = logging.getLogger("meditwin.groq")
MODEL   = os.getenv("GROQ_MODEL",        "openai/gpt-oss-120b")
MAX_TOK = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
TEMP    = float(os.getenv("GROQ_TEMPERATURE", "0.7"))


class GroqService:
    def __init__(self) -> None:
        self.model = MODEL
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from groq import AsyncGroq
            key = os.getenv("GROQ_API_KEY", "")
            if not key:
                logger.warning("GROQ_API_KEY not set in .env — AI features will return placeholder responses")
                return
            self._client = AsyncGroq(api_key=key)
            logger.info("Groq client ready | model: %s", self.model)
        except ImportError:
            logger.warning("groq package not installed — run: pip install groq")

    async def chat(
        self,
        messages:    list[dict[str, str]],
        system:      str = "",
        max_tokens:  int = MAX_TOK,
        temperature: float = TEMP,
    ) -> tuple[str, int]:
        if self._client is None:
            return ("AI service unavailable. Please set GROQ_API_KEY in your .env file "
                    "and restart the server.", 0)
        payload: list[dict[str, str]] = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend(messages)
        t0 = time.monotonic()
        try:
            resp = await self._client.chat.completions.create(
                model=self.model, messages=payload,
                max_tokens=max_tokens, temperature=temperature,
            )
            ms     = int((time.monotonic() - t0) * 1000)
            text   = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            logger.info("Groq %dms %d tokens", ms, tokens)
            return text, tokens
        except Exception as exc:
            logger.error("Groq API error: %s", exc)
            raise RuntimeError(f"AI service error: {exc}") from exc

    # ── Helpers ───────────────────────────────────────────
    async def health_summary(self, ctx: dict[str, Any]) -> str:
        prompt = (
            f"Write a concise clinical health twin summary (max 130 words) for: "
            f"{ctx.get('name')}, {ctx.get('age')}y {ctx.get('gender')}, "
            f"BMI {ctx.get('bmi')}, BP {ctx.get('bp')}, "
            f"Glucose {ctx.get('glucose')}mg/dL, SpO2 {ctx.get('spo2')}%, "
            f"Diabetes Risk {ctx.get('diabetes_risk',0):.0f}%, "
            f"Hypertension {ctx.get('bp_risk',0):.0f}%, "
            f"Stress {ctx.get('stress_risk',0):.0f}%, "
            f"Sleep {ctx.get('sleep')}h, Exercise {ctx.get('exercise')}x/week. "
            "Include: key concerns, priority risks, immediate preventive actions."
        )
        sys = ("You are MediTwin AI, a preventive healthcare intelligence system. "
               "Write concise, evidence-based, clinical summaries. "
               "Always recommend consulting a physician for serious concerns.")
        t, _ = await self.chat([{"role":"user","content":prompt}], system=sys, max_tokens=350, temperature=0.5)
        return t

    async def analyze_report(self, text: str) -> str:
        prompt = (
            f"Analyze this medical report and provide:\n"
            f"1) CRITICAL FINDINGS (abnormal values with severity)\n"
            f"2) PLAIN LANGUAGE EXPLANATION (no medical jargon)\n"
            f"3) RISK ASSESSMENT\n"
            f"4) IMMEDIATE RECOMMENDATIONS (numbered)\n\n{text}"
        )
        sys = "You are MediTwin AI Report Analyzer. Be precise, clinically accurate, and actionable."
        t, _ = await self.chat([{"role":"user","content":prompt}], system=sys, max_tokens=800, temperature=0.3)
        return t

    async def recommendations(self, ctx: dict[str, Any], category: str) -> str:
        prompt = (
            f"Create a personalized {category} plan for: {ctx.get('name')}, {ctx.get('age')}y, "
            f"BMI {ctx.get('bmi')}, Diabetes {ctx.get('diabetes_risk',0):.0f}%, "
            f"Hypertension {ctx.get('bp_risk',0):.0f}%, Stress {ctx.get('stress_risk',0):.0f}%, "
            f"Sleep {ctx.get('sleep')}h/night, Exercise {ctx.get('exercise')}x/week. "
            "Write exactly 8 specific numbered actionable points. Evidence-based. Max 200 words."
        )
        t, _ = await self.chat([{"role":"user","content":prompt}], max_tokens=400, temperature=0.6)
        return t

    async def explain_risk_drivers(
        self, name: str, age: int, disease: str,
        top_components: list[dict[str, Any]], probability: float, tool_used: str,
    ) -> str:
        """
        Fuses the glass-box point breakdown from clinical_risk_service
        (the literal SHAP-equivalent for our rule-based scores) into a
        ranked, plain-language narrative: "Your risk increased primarily
        due to X, Y" — citing the actual contributing factors, not a
        generic LLM guess.
        """
        ranked = sorted(top_components, key=lambda c: abs(c.get("points", 0)), reverse=True)[:3]
        factors_txt = "; ".join(
            f"{c['factor']} (+{c['points']} pts) — {c['detail']}" for c in ranked
        )
        prompt = (
            f"Patient: {name}, {age}y. Disease: {disease}. "
            f"Calculated risk: {probability:.0f}% via {tool_used}. "
            f"Top contributing factors, ranked by point weight: {factors_txt}. "
            "In max 60 words, explain in plain language WHY this risk is what it is, "
            "naming the top 1-2 factors specifically. Do not invent factors not listed. "
            "Format: 'Your {disease} risk is primarily driven by ...'"
        )
        sys = ("You are MediTwin AI's explainability layer. You only narrate the exact "
               "factors given to you — never invent or assume additional clinical findings.")
        t, _ = await self.chat([{"role": "user", "content": prompt}], system=sys, max_tokens=150, temperature=0.3)
        return t

    async def whatif(self, name: str, age: int, changes: dict, current: int, projected: int) -> str:
        prompt = (
            f"MediTwin What-If for {name}, {age}y. "
            f"Proposed changes: {list(changes.items())}. "
            f"Projected health score: {current} -> {projected}. "
            "Write 3 encouraging evidence-based sentences. Include realistic timeline for results."
        )
        t, _ = await self.chat([{"role":"user","content":prompt}], max_tokens=250, temperature=0.7)
        return t

    async def chat_patient(self, messages: list[dict], ctx: dict[str, Any]) -> tuple[str, int]:
        sys = (
            f"You are MediTwin AI Health Assistant. "
            f"Patient: {ctx.get('name')}, {ctx.get('age')}y, "
            f"Health Score {ctx.get('health_score')}/100, "
            f"Diabetes Risk {ctx.get('diabetes_risk',0):.0f}%, "
            f"Hypertension {ctx.get('bp_risk',0):.0f}%, "
            f"Stress {ctx.get('stress_risk',0):.0f}%, BMI {ctx.get('bmi')}. "
            "Be concise, empathetic, evidence-based. Always recommend physician for serious concerns."
        )
        return await self.chat(messages, system=sys, max_tokens=600)

    async def biological_age_narrative(
        self,
        chrono_age: int,
        bio_age: int,
        patient_name: str,
        top_causes: list[str],
    ) -> str:
        """Generates the biological age shock explanation — 2 crisp sentences."""
        gap = bio_age - chrono_age
        if gap > 0:
            prompt = (
                f"MediTwin Biological Age: {patient_name} is chronologically {chrono_age} "
                f"but biologically {bio_age} — {gap} years older than their birth certificate. "
                f"Primary accelerators: {', '.join(top_causes) if top_causes else 'stress, sleep deficit, sedentary lifestyle'}. "
                "Write EXACTLY 2 sentences: "
                "1) The stark reality — specific, no jargon. "
                "2) What specifically reverses this in 90 days — concrete, measurable. "
                "Max 55 words total."
            )
        else:
            prompt = (
                f"MediTwin Biological Age: {patient_name} is chronologically {chrono_age} "
                f"but biologically {bio_age} — {abs(gap)} years YOUNGER than their age. "
                "Write EXACTLY 2 celebratory but science-grounded sentences. Max 45 words."
            )
        text, _ = await self.chat([{"role": "user", "content": prompt}], max_tokens=120, temperature=0.5)
        return text

    async def story_act(
        self,
        act: int,
        patient_name: str,
        context: dict[str, Any],
    ) -> str:
        """Generates one act of the 5-act health story for presentation mode."""
        act_prompts = {
            1: (
                f"Story Mode ACT 1 — 'Who They Are'. Patient: {patient_name}, context: {context}. "
                "Write 2 vivid, human sentences about this person's daily life right now. "
                "Specific. No medical jargon. Max 40 words."
            ),
            2: (
                f"Story Mode ACT 2 — 'The Warning Signs'. Patient: {patient_name}, context: {context}. "
                "Write 2 sentences naming the invisible health signals active right now. "
                "Clinical but accessible. Specific numbers where relevant. Max 45 words."
            ),
            3: (
                f"Story Mode ACT 3 — 'The Dark Future'. Patient: {patient_name}, context: {context}. "
                "Write 2-3 sentences describing the 5-year status-quo trajectory. "
                "Honest, specific numbers, not alarmist. Max 50 words."
            ),
            4: (
                f"Story Mode ACT 4 — 'The Turning Point'. Patient: {patient_name}, context: {context}. "
                "Write 2 sentences naming exactly 3 actions that change everything. "
                "Concrete, achievable. Max 40 words."
            ),
            5: (
                f"Story Mode ACT 5 — 'The Future They Choose'. Patient: {patient_name}, context: {context}. "
                "Write 2-3 sentences describing the 5-year future WITH prevention. "
                "Inspiring, specific numbers. Max 50 words."
            ),
        }
        text, _ = await self.chat(
            [{"role": "user", "content": act_prompts.get(act, act_prompts[1])}],
            max_tokens=100,
            temperature=0.7,
        )
        return text

    # ── RAG-grounded chat ─────────────────────────────────────────
    async def chat_patient_rag(
        self,
        messages: list[dict],
        ctx: dict[str, Any],
        rag_context: str = "",
    ) -> tuple[str, int]:
        """
        RAG-augmented patient chat. Injects retrieved guideline context
        directly into the system prompt so the LLM is grounded before it
        generates a single token. The rag_context block (built by
        rag_service.RAGService.build_context_prompt) tells the model
        exactly which guidelines to cite and explicitly forbids inventing
        statistics — the core hallucination-prevention mechanism, and the
        concrete answer to "how do you prevent hallucinations?"
        """
        patient_sys = (
            f"You are MediTwin AI Health Assistant. "
            f"Patient: {ctx.get('name')}, {ctx.get('age')}y, "
            f"Health Score {ctx.get('health_score', 70)}/100, "
            f"Diabetes Risk {ctx.get('diabetes_risk', 0):.0f}%, "
            f"Hypertension {ctx.get('bp_risk', 0):.0f}%, "
            f"Stress {ctx.get('stress_risk', 0):.0f}%, BMI {ctx.get('bmi', 25)}. "
            "Be concise, empathetic, evidence-based. "
            "Always recommend physician consultation for serious concerns. "
            "NEVER invent specific statistics or thresholds — only cite sources provided to you."
        )
        full_system = f"{patient_sys}\n\n{rag_context}" if rag_context else patient_sys
        return await self.chat(messages, system=full_system, max_tokens=700)

    async def recommendations_rag(
        self,
        ctx: dict[str, Any],
        category: str,
        rag_context: str = "",
    ) -> str:
        """RAG-grounded recommendations — cites retrieved guidelines by number."""
        prompt = (
            f"Create a personalized {category} plan for: {ctx.get('name')}, {ctx.get('age')}y, "
            f"BMI {ctx.get('bmi')}, Diabetes Risk {ctx.get('diabetes_risk', 0):.0f}%, "
            f"Hypertension Risk {ctx.get('bp_risk', 0):.0f}%, Stress {ctx.get('stress_risk', 0):.0f}%, "
            f"Sleep {ctx.get('sleep')}h/night, Exercise {ctx.get('exercise')}x/week. "
            "Write exactly 8 numbered, specific, actionable points. "
            "Cite the relevant guideline source in brackets after each point where applicable. "
            "Evidence-based only. Max 220 words."
        )
        sys = f"You are MediTwin AI Recommendation Engine.\n\n{rag_context}" if rag_context else \
              "You are MediTwin AI Recommendation Engine. Evidence-based, cite sources."
        t, _ = await self.chat([{"role": "user", "content": prompt}], system=sys, max_tokens=450, temperature=0.5)
        return t


_instance: GroqService | None = None

def get_groq_service() -> GroqService:
    global _instance
    if _instance is None:
        _instance = GroqService()
    return _instance
