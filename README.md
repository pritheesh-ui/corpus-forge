# Marginalia

A small reading room for your files. Upload sources, ask questions, get answers grounded in passages pulled from your documents — with citations.

Retrieval runs locally with BM25 (no LLM in the retrieval loop). Only the matching chunks plus your prompt go to the model. The codebase is FastAPI + Jinja2 + vanilla JS + SQLite.

## What you get

- Upload `.txt`, `.md`, `.pdf` and a long list of source files (`.py`, `.js`, `.ts`, `.go`, `.rs`, `.json`, `.yaml`, `.sql`, and more).
- Pick which documents are in scope per message.
- Four modes, each with tweakable parameters:
  - **Ask** — open Q&A; choose tone and explanation level.
  - **Quiz** — generate a study quiz; choose level, difficulty, question type, count.
  - **Test** — graded test with rubric and answer key.
  - **Code review** — senior-engineer review; pick focus area (correctness, performance, readability, security, or all).
- Every chat and message is stored in SQLite.

## Run it

```bash
cp .env.example .env
# put your GOOGLE_API_KEY in .env
# optionally override GEMINI_MODEL if needed
./run.sh
```

Then open <http://127.0.0.1:8000>.

## Tests

A small smoke test exercises upload, BM25 retrieval, chat creation, settings, and the graceful "no API key" error — no live model call needed.

```bash
. .venv/bin/activate
PYTHONPATH=. python tests/test_smoke.py
```

## Layout

```
app/
  main.py             FastAPI factory
  config.py           settings from .env
  database.py         SQLAlchemy engine + session
  models.py           Document, Chunk, Chat, Message
  routers/
    pages.py          GET / and /chat/{id}
    files.py          POST /files/upload, /files/{id}/delete
    chats.py          POST /chats/new, /chats/{id}/messages, /chats/{id}/settings
  services/
    extractor.py      text extraction (pdf + text-like files)
    chunker.py        paragraph-aware sliding window
    retriever.py      BM25 retrieval over stored chunks
    llm.py            Gemini client wrapper
  prompts/
    templates.py      system + user prompt builders per mode
  templates/          Jinja2 templates
  static/             CSS + JS
```

## Notes

- Retrieval is BM25 with a small stopword list and `[A-Za-z0-9_]+` tokenization — good enough for code and prose without embedding models.
- The model is configurable via `GEMINI_MODEL` in `.env`. Default is `gemini-flash-latest`.
- The dark accent color and Fraunces / IBM Plex Mono pairing live in `app/static/css/style.css` as CSS variables — change them freely.
