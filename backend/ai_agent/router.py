"""FastAPI routes for the multimodal AI agent."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.ai_agent.agent import run_multimodal_chat
from backend.ai_agent.schemas import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multimodal agent chat",
)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    """Send a text (+ optional images) message to the multimodal agent."""
    try:
        reply = run_multimodal_chat(
            payload.message,
            images=payload.images,
            history=[item.model_dump() for item in payload.history],
        )
    except RuntimeError as exc:
        # Missing API key / config
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent upstream error: {exc}",
        ) from exc

    return AgentChatResponse(reply=reply)
