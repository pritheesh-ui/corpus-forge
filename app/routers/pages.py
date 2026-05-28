import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Chat, Document
from app.prompts.templates import MODE_SPECS


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _modes_json() -> str:
    return json.dumps({k: asdict(v) for k, v in MODE_SPECS.items()})


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    chats = db.query(Chat).order_by(Chat.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "documents": documents,
            "chats": chats,
            "chat": None,
            "modes": MODE_SPECS,
            "modes_json": _modes_json(),
        },
    )


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
def chat_page(chat_id: int, request: Request, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if chat is None:
        return HTMLResponse("Chat not found", status_code=404)
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    chats = db.query(Chat).order_by(Chat.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "chat": chat,
            "documents": documents,
            "chats": chats,
            "modes": MODE_SPECS,
            "active_mode": MODE_SPECS.get(chat.mode, MODE_SPECS["ask"]),
            "modes_json": _modes_json(),
        },
    )
