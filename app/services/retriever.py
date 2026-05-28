import re
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.models import Chunk, Document


_TOKEN = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "for", "with", "by", "at", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "them", "us", "me",
    "from", "into", "about", "do", "does", "did", "doing", "done",
    "has", "have", "had", "having", "not", "no", "yes",
}


@dataclass
class RetrievedChunk:
    document_id: int
    document_name: str
    position: int
    content: str
    score: float


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if t.lower() not in _STOP and len(t) > 1]


def retrieve(db: Session, query: str, document_ids: list[int] | None, top_k: int) -> list[RetrievedChunk]:
    q = db.query(Chunk, Document).join(Document, Chunk.document_id == Document.id)
    if document_ids:
        q = q.filter(Chunk.document_id.in_(document_ids))
    rows = q.all()
    if not rows:
        return []

    corpus = [tokenize(chunk.content) for chunk, _ in rows]
    if not any(corpus):
        return []

    bm25 = BM25Okapi(corpus)
    tokens = tokenize(query)
    
    scores = bm25.get_scores(tokens) if tokens else [0.0] * len(rows)
    query_set = set(tokens) if tokens else set()

    candidates: list[tuple[tuple, float]] = []
    for (chunk, doc), score, chunk_tokens in zip(rows, scores, corpus):

        if query_set and not query_set.intersection(chunk_tokens):
            continue
        candidates.append(((chunk, doc), float(score)))

    candidates.sort(key=lambda x: x[1], reverse=True)
    candidates = candidates[:top_k]

    return [
        RetrievedChunk(
            document_id=doc.id,
            document_name=doc.filename,
            position=chunk.position,
            content=chunk.content,
            score=score,
        )
        for (chunk, doc), score in candidates
    ]
