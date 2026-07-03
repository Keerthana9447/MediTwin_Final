"""MediTwin AI — RAG Knowledge Base Router

Live, judge-facing demonstration of the retrieval mechanism behind every
AI-generated response in this app. Answers "how do you prevent
hallucinations?" concretely: ask any health question via /retrieve and see
exactly which guideline chunks would be injected into the LLM's prompt,
with sources attached.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from routers.auth import get_current_user
from services.rag_service import RAGService, get_rag_service, TOTAL_CARDS

router = APIRouter()


@router.get("/topics")
async def list_topics(
    user: dict       = Depends(get_current_user),
    rag:  RAGService = Depends(get_rag_service),
) -> dict:
    """Returns all guideline topics indexed in the RAG knowledge base."""
    return {
        "total_cards": TOTAL_CARDS,
        "topics": rag.list_topics(),
        "retrieval_method": "TF-IDF cosine similarity (scikit-learn)",
        "note": (
            "Knowledge base covers WHO, ADA, ACC/AHA, Framingham, DPP, DASH, "
            "ICMR, NPCDCS, AHA/ASA, and NFHS-5 India guidelines — all paraphrased, "
            "never reproduced verbatim from any copyrighted publication."
        ),
    }


@router.post("/retrieve")
async def retrieve_live(
    query: str,
    k: int = 4,
    user: dict       = Depends(get_current_user),
    rag:  RAGService = Depends(get_rag_service),
) -> dict:
    """Live retrieval test — returns top-k cards for any query. Useful for demo."""
    cards = rag.retrieve(query, top_k=k)
    return {
        "query": query,
        "retrieved": [
            {
                "id": c["id"], "topic": c["topic"], "source": c["source"],
                "preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
            }
            for c in cards
        ],
    }


@router.post("/index-report")
async def index_report(
    body: dict,
    user: dict       = Depends(get_current_user),
    rag:  RAGService = Depends(get_rag_service),
) -> dict:
    """Index a patient's uploaded lab report text for session-scoped RAG retrieval."""
    report_text = body.get("text", "")
    if not report_text.strip():
        return {"status": "error", "message": "No text provided"}
    rag.add_session_document(report_text, source=f"Patient Report — {body.get('filename', 'uploaded')}")
    return {
        "status": "indexed",
        "cards_added": len(rag._session_texts),
        "message": "Report indexed. AI chat will now reference your actual report alongside medical guidelines.",
    }
