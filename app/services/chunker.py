import re


_PARA_SPLIT = re.compile(r"\n\s*\n")


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]
    chunks: list[str] = []
    buffer = ""

    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= size:
            buffer = f"{buffer}\n\n{para}".strip() if buffer else para
            continue

        if buffer:
            chunks.append(buffer)
            buffer = _tail(buffer, overlap)

        if len(para) <= size:
            buffer = f"{buffer}\n\n{para}".strip() if buffer else para
        else:
            chunks.extend(_split_long(para, size, overlap, prefix=buffer))
            buffer = _tail(chunks[-1], overlap) if chunks else ""

    if buffer:
        chunks.append(buffer)

    return [c.strip() for c in chunks if c.strip()]


def _tail(text: str, overlap: int) -> str:
    if overlap <= 0 or len(text) <= overlap:
        return text if overlap > 0 else ""
    return text[-overlap:]


def _split_long(text: str, size: int, overlap: int, prefix: str = "") -> list[str]:
    out: list[str] = []
    start = 0
    first = True
    while start < len(text):
        end = min(start + size, len(text))
        slice_ = text[start:end]
        if first and prefix:
            slice_ = f"{prefix}\n\n{slice_}"
            first = False
        out.append(slice_)
        if end == len(text):
            break
        start = end - overlap
    return out
