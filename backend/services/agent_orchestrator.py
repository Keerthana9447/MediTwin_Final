"""
MediTwin AI — Multi-Agent Specialist Orchestrator
═══════════════════════════════════════════════════════════════
Replaces a single generic LLM call with role-scoped specialist
agents that each reason over the SAME clinical_risk_service output
but with a different lens and a restricted view of the data (e.g.
the Nutrition agent doesn't see raw BP numbers, only diet-relevant
risks) — then a lightweight aggregator resolves agreement/disagreement
into a consensus, surfacing divergence rather than hiding it.

This is a genuine architectural decomposition (concurrent asyncio
fan-out via asyncio.gather, independent prompts per role), not a
single prompt asking the LLM to "pretend" to be four people.
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations
import asyncio
import re
from typing import Any

from services.groq_service import GroqService

# Each agent: (role_name, system_prompt, relevant_risk_keys)
_AGENT_SPECS: list[tuple[str, str, list[str]]] = [
    (
        "Cardiologist Agent",
        "You are a cardiology specialist AI. Focus ONLY on cardiovascular and "
        "hypertension risk. Be clinically precise. Max 50 words.",
        ["Heart Disease", "Hypertension"],
    ),
    (
        "Endocrinologist Agent",
        "You are an endocrinology specialist AI. Focus ONLY on diabetes/metabolic "
        "risk. Be clinically precise. Max 50 words.",
        ["Diabetes"],
    ),
    (
        "Preventive Medicine Agent",
        "You are a preventive medicine specialist AI. Focus on the SINGLE highest-leverage "
        "lifestyle change across all risks given. Be specific and actionable. Max 50 words.",
        ["Heart Disease", "Hypertension", "Diabetes", "Stress Syndrome", "Anemia"],
    ),
]


def _format_risk_context(risks: dict[str, float], keys: list[str]) -> str:
    relevant = {k: v for k, v in risks.items() if k in keys}
    if not relevant:
        return "No specific risk data in this agent's domain."
    return "; ".join(f"{k}: {v:.0f}%" for k, v in relevant.items())


async def _run_agent(
    groq: GroqService, role: str, system_prompt: str, focus_keys: list[str],
    name: str, age: int, risks: dict[str, float],
    rag_context: str = "",
) -> dict[str, Any]:
    ctx = _format_risk_context(risks, focus_keys)
    # Inject RAG-retrieved guidelines into the system prompt
    augmented_system = system_prompt
    if rag_context:
        augmented_system = f"{system_prompt}\n\n{rag_context}"
    prompt = (
        f"Patient: {name}, {age}y. Relevant risk scores: {ctx}. "
        "Give your specialist recommendation, citing any relevant guideline if applicable."
    )
    try:
        text, _ = await groq.chat(
            [{"role": "user", "content": prompt}], system=augmented_system,
            max_tokens=150, temperature=0.4,
        )
    except Exception as exc:
        text = f"[Agent unavailable: {exc}]"

    # Confidence heuristic: based on how much relevant risk data this agent had
    relevant_count = sum(1 for k in focus_keys if k in risks)
    confidence = min(1.0, 0.5 + 0.1 * relevant_count)

    return {
        "role": role,
        "recommendation": text.strip(),
        "confidence": round(confidence, 2),
        "focus_risks": [k for k in focus_keys if k in risks],
    }


_ACTION_WORDS = re.compile(
    r"\b(reduce|increase|quit|stop|start|monitor|avoid|limit|maintain|exercise|sleep|diet)\b",
    re.IGNORECASE,
)


def _detect_divergence(opinions: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """
    Lightweight, deterministic divergence check (no extra LLM call needed):
    compares the recommended ACTION verbs each agent used. If agents share
    no action-word overlap, that's flagged as a point of divergence; shared
    action words across 2+ agents are flagged as agreement. This keeps the
    consensus step fast, free, and auditable rather than another opaque
    LLM judgment call.
    """
    action_sets = []
    for op in opinions:
        words = {w.lower() for w in _ACTION_WORDS.findall(op["recommendation"])}
        action_sets.append((op["role"], words))

    agreement: list[str] = []
    divergence: list[str] = []
    for i in range(len(action_sets)):
        for j in range(i + 1, len(action_sets)):
            role_a, words_a = action_sets[i]
            role_b, words_b = action_sets[j]
            shared = words_a & words_b
            if shared:
                agreement.append(f"{role_a} and {role_b} both emphasize: {', '.join(sorted(shared))}")
            elif words_a and words_b:
                divergence.append(f"{role_a} and {role_b} prioritize different actions")

    if not agreement:
        agreement = ["No overlapping action terms detected — agents addressed distinct domains."]
    if not divergence:
        divergence = ["No conflicting recommendations detected."]
    return agreement, divergence


async def run_consensus(
    groq: GroqService, name: str, age: int, risks: dict[str, float],
) -> dict[str, Any]:
    """Fans out all specialist agents CONCURRENTLY via asyncio.gather, then aggregates."""
    from services.rag_service import retrieve, format_context

    # Build per-agent RAG queries based on their focus domain
    agent_rag_queries = {
        "Cardiologist Agent":       "cardiovascular heart disease hypertension risk treatment",
        "Endocrinologist Agent":    "diabetes management HbA1c blood glucose insulin resistance",
        "Preventive Medicine Agent": "NCD prevention lifestyle modification physical activity diet",
    }

    tasks = []
    for role, sys_prompt, keys in _AGENT_SPECS:
        query = agent_rag_queries.get(role, "clinical guidelines prevention")
        chunks = retrieve(query, top_k=2)   # 2 chunks per agent keeps prompt size manageable
        rag_ctx = format_context(chunks)
        tasks.append(_run_agent(groq, role, sys_prompt, keys, name, age, risks, rag_ctx))

    opinions = await asyncio.gather(*tasks)
    opinions = list(opinions)

    agreement, divergence = _detect_divergence(opinions)

    summary_prompt = (
        f"Three specialist AI agents gave these recommendations for {name}, {age}y: "
        + " | ".join(f"{o['role']}: {o['recommendation']}" for o in opinions)
        + ". Synthesize into ONE unified action plan in max 70 words. "
        "If recommendations conflict, state how to prioritize them."
    )
    try:
        consensus_text, _ = await groq.chat(
            [{"role": "user", "content": summary_prompt}],
            system="You are MediTwin AI's consensus coordinator, synthesizing specialist opinions.",
            max_tokens=180, temperature=0.4,
        )
    except Exception as exc:
        consensus_text = f"[Consensus generation unavailable: {exc}]"

    return {
        "agents": opinions,
        "consensus_summary": consensus_text.strip(),
        "points_of_agreement": agreement,
        "points_of_divergence": divergence,
    }
