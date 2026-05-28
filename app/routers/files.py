import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Chunk, Document
from app.services import chunker, extractor


router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    saved = 0
    skipped: list[str] = []
    max_bytes = settings.max_upload_mb * 1024 * 1024

    for file in files:
        if not file.filename:
            continue
        if not extractor.is_allowed(file.filename):
            skipped.append(f"{file.filename} (unsupported type)")
            continue

        raw = await file.read()
        if len(raw) > max_bytes:
            skipped.append(f"{file.filename} (too large)")
            continue
        if not raw:
            skipped.append(f"{file.filename} (empty)")
            continue

        ext = extractor.extension_of(file.filename)
        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = settings.upload_path / stored_name
        stored_path.write_bytes(raw)

        try:
            text = extractor.extract_text(stored_path)
        except Exception as e:
            stored_path.unlink(missing_ok=True)
            skipped.append(f"{file.filename} (extraction failed: {e})")
            continue

        if not text.strip():
            stored_path.unlink(missing_ok=True)
            skipped.append(f"{file.filename} (no readable text)")
            continue

        document = Document(
            filename=file.filename,
            stored_path=str(stored_path),
            extension=ext,
            size_bytes=len(raw),
            char_count=len(text),
        )
        db.add(document)
        db.flush()

        pieces = chunker.chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        for idx, piece in enumerate(pieces):
            db.add(Chunk(document_id=document.id, position=idx, content=piece))

        saved += 1

    db.commit()
    return {"saved": saved, "skipped": skipped}


@router.post("/{document_id}/delete")
def delete(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(404, "Document not found")

    path = Path(document.stored_path)
    path.unlink(missing_ok=True)

    db.delete(document)
    db.commit()
    return RedirectResponse("/", status_code=303)
