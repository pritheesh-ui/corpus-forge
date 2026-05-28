from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Chat, Document, Message
from app.prompts.templates import MODES, build_system_prompt, build_user_prompt
from app.services import llm, retriever


router = APIRouter(prefix="/chats", tags=["chats"])


class CreateChatRequest(BaseModel):
    title: str | None = None
    mode: str = "ask"
    options: dict = {}


class SendMessageRequest(BaseModel):
    content: str
    document_ids: list[int] = []


@router.post("/new")
def create_chat(payload: CreateChatRequest, db: Session = Depends(get_db)):
    if payload.mode not in MODES:
        raise HTTPException(400, "Unknown mode")
    chat = Chat(
        title=payload.title or _default_title(payload.mode),
        mode=payload.mode,
        options=payload.options or {},
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"id": chat.id}


@router.post("/{chat_id}/delete")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(404, "Chat not found")
    db.delete(chat)
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/{chat_id}/settings")
def update_settings(chat_id: int, payload: CreateChatRequest, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(404, "Chat not found")
    if payload.mode and payload.mode not in MODES:
        raise HTTPException(400, "Unknown mode")
    if payload.title is not None:
        chat.title = payload.title or chat.title
    chat.mode = payload.mode or chat.mode
    chat.options = payload.options or {}
    db.commit()
    return {"ok": True}


@router.post("/{chat_id}/messages")
def send_message(chat_id: int, payload: SendMessageRequest = Body(...), db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(404, "Chat not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(400, "Message is empty")

    valid_ids = _filter_document_ids(db, payload.document_ids)
    retrieved = retriever.retrieve(db, content, valid_ids, settings.top_k)
    sources_payload = [
        {
            "document_id": r.document_id,
            "document_name": r.document_name,
            "position": r.position,
            "score": round(r.score, 4),
            "preview": r.content[:280],
        }
        for r in retrieved
    ]

    user_msg = Message(chat_id=chat.id, role="user", content=content, sources={"selected": valid_ids})
    db.add(user_msg)
    db.flush()

    history = _history_for_prompt(chat)
    system = build_system_prompt(chat.mode, chat.options or {})
    user_prompt = build_user_prompt(
        content,
        [
            {"document_name": r.document_name, "position": r.position, "content": r.content}
            for r in retrieved
        ],
    )
    history.append({"role": "user", "content": user_prompt})

    try:
        answer = llm.complete(system, history)
    except llm.LLMError as e:
        db.rollback()
        raise HTTPException(503, str(e))

    assistant_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content=answer,
        sources={"retrieved": sources_payload},
    )
    db.add(assistant_msg)

    if chat.title in ("Untitled", _default_title(chat.mode)) and len(chat.messages) <= 1:
        chat.title = content[:60] + ("…" if len(content) > 60 else "")

    db.commit()
    return {
        "user": {"id": user_msg.id, "content": user_msg.content},
        "assistant": {
            "id": assistant_msg.id,
            "content": answer,
            "sources": sources_payload,
        },
    }


def _default_title(mode: str) -> str:
    return {
        "ask": "New question",
        "quiz": "New quiz",
        "test": "New test",
        "code_review": "New review",
    }.get(mode, "Untitled")


def _filter_document_ids(db: Session, ids: list[int]) -> list[int]:
    if not ids:
        return []
    found = db.query(Document.id).filter(Document.id.in_(ids)).all()
    return [row[0] for row in found]


def _history_for_prompt(chat: Chat) -> list[dict]:
    history: list[dict] = []
    for msg in chat.messages:
        history.append({"role": msg.role, "content": msg.content})
    return history
