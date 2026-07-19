from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AIProvider, AIChatHistory, User
from schemas import (
    AIChatRequest, AIMultiCompareRequest, AIChatHistoryCreate,
    AIChatHistoryUpdate, AIChatHistoryResponse, AIChatMessage
)
from routers.auth import get_current_user
import httpx
import json
import time
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["ai_aggregator"])


def get_openai_compatible_response(api_url: str, api_key: str, model: str, messages: list, stream: bool):
    """Proxy to OpenAI-compatible endpoints (OpenAI, DeepSeek, OpenRouter, Azure etc.)"""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {"model": model or "gpt-3.5-turbo", "messages": messages, "stream": stream}
    return api_url, headers, body


def get_claude_response(api_key: str, messages: list):
    """Proxy to Claude-compatible endpoints"""
    return None  # Placeholder - would use Anthropic SDK


def get_gemini_response(api_key: str, messages: list):
    """Proxy to Gemini-compatible endpoints"""
    return None  # Placeholder - would use Google AI SDK


@router.post("/chat")
async def ai_chat(request: AIChatRequest, db: Session = Depends(get_db)):
    """Send a chat request through any configured AI provider."""
    provider = db.query(AIProvider).filter(AIProvider.id == request.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.api_type == "web":
        raise HTTPException(status_code=400, detail="This provider is web-only. Configure API key for chat.")

    msgs_for_api = [m.model_dump() for m in request.messages]

    try:
        if provider.api_type in ("openai", "azure", "deepseek", "openrouter"):
            api_url, headers, body = get_openai_compatible_response(
                provider.api_url, provider.api_key, request.model, msgs_for_api, request.stream
            )

            if request.stream:
                async def stream_response():
                    async with httpx.AsyncClient(timeout=120) as client:
                        async with client.stream("POST", api_url, json=body, headers=headers) as resp:
                            async for chunk in resp.aiter_bytes():
                                yield chunk

                return StreamingResponse(stream_response(), media_type="text/event-stream")

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(api_url, json=body, headers=headers)
                return resp.json()

        elif provider.api_type == "claude":
            # Anthropic API format
            headers = {
                "x-api-key": provider.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            system_msgs = [m for m in msgs_for_api if m["role"] == "system"]
            user_msgs = [m for m in msgs_for_api if m["role"] != "system"]
            body = {
                "model": request.model or "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "messages": user_msgs
            }
            if system_msgs:
                body["system"] = system_msgs[0]["content"]

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post("https://api.anthropic.com/v1/messages", json=body, headers=headers)
                data = resp.json()
                return {
                    "choices": [{"message": {"role": "assistant",
                                             "content": data.get("content", [{}])[0].get("text", "")}}]
                }

        elif provider.api_type == "gemini":
            headers = {"Content-Type": "application/json"}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model or 'gemini-pro'}:generateContent?key={provider.api_key}"
            contents = [{"role": "user" if m["role"] != "assistant" else "model",
                         "parts": [{"text": m["content"]}]} for m in msgs_for_api if m["role"] != "system"]

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json={"contents": contents}, headers=headers)
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {"choices": [{"message": {"role": "assistant", "content": text}}]}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def multi_compare(request: AIMultiCompareRequest, db: Session = Depends(get_db)):
    """Send the same prompt to multiple providers and return side-by-side results."""
    results = []
    messages = [{"role": "user", "content": request.prompt}]

    for i, pid in enumerate(request.provider_ids):
        provider = db.query(AIProvider).filter(AIProvider.id == pid).first()
        if not provider or provider.api_type == "web":
            results.append({"provider_id": pid, "provider_name": provider.name if provider else "Unknown",
                            "content": "Provider not configured for API chat", "error": True})
            continue

        model = request.models[i] if i < len(request.models) else ""
        try:
            if provider.api_type in ("openai", "azure", "deepseek", "openrouter"):
                api_url, headers, body = get_openai_compatible_response(
                    provider.api_url, provider.api_key, model, messages, False
                )
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(api_url, json=body, headers=headers)
                    data = resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                results.append({"provider_id": pid, "provider_name": provider.name, "content": content})

            elif provider.api_type == "claude":
                headers = {
                    "x-api-key": provider.api_key, "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                body = {"model": model or "claude-3-5-sonnet-20241022",
                        "max_tokens": 4096, "messages": [{"role": "user", "content": request.prompt}]}
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post("https://api.anthropic.com/v1/messages", json=body, headers=headers)
                    data = resp.json()
                    content = data.get("content", [{}])[0].get("text", "No response")
                results.append({"provider_id": pid, "provider_name": provider.name, "content": content})

            elif provider.api_type == "gemini":
                model_name = model or "gemini-pro"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={provider.api_key}"
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(url, json={
                        "contents": [{"parts": [{"text": request.prompt}]}]
                    })
                    data = resp.json()
                    content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
                results.append({"provider_id": pid, "provider_name": provider.name, "content": content})

        except Exception as e:
            results.append({"provider_id": pid, "provider_name": provider.name,
                            "content": f"Error: {str(e)}", "error": True})

    return {"prompt": request.prompt, "results": results}


# Chat History
@router.get("/history", response_model=List[AIChatHistoryResponse])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(AIChatHistory).filter(
        AIChatHistory.user_id == current_user.id
    ).order_by(AIChatHistory.updated_at.desc()).all()


@router.post("/history", response_model=AIChatHistoryResponse)
def create_chat_history(
    data: AIChatHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = AIChatHistory(
        user_id=current_user.id,
        provider_id=data.provider_id,
        title=data.title,
        model=data.model,
        messages="[]"
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.put("/history/{chat_id}", response_model=AIChatHistoryResponse)
def update_chat_history(
    chat_id: int,
    data: AIChatHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = db.query(AIChatHistory).filter(
        AIChatHistory.id == chat_id, AIChatHistory.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Not found")
    if data.title is not None:
        chat.title = data.title
    if data.messages is not None:
        chat.messages = data.messages
    chat.updated_at = datetime.utcnow()
    db.commit()
    return chat


@router.delete("/history/{chat_id}")
def delete_chat_history(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = db.query(AIChatHistory).filter(
        AIChatHistory.id == chat_id, AIChatHistory.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(chat)
    db.commit()
    return {"ok": True}
