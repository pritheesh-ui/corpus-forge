import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


class LLMError(Exception):
    pass


def _format_prompt(system: str, messages: list[dict]) -> str:
    parts = [f"System: {system}".strip()]
    for msg in messages:
        role = msg.get("role", "user").lower()
        label = "Assistant" if role == "assistant" else "System" if role == "system" else "User"
        parts.append(f"{label}: {msg.get('content', '').strip()}")
    return "\n\n".join(parts).strip()


def _extract_text(element) -> str:
    if element is None:
        return ""
    if isinstance(element, str):
        return element
    if isinstance(element, dict):
        if "text" in element:
            return element["text"]
        if "parts" in element:
            return "".join(_extract_text(item) for item in element["parts"])
        if "content" in element:
            return _extract_text(element["content"])
        if "output" in element:
            return _extract_text(element["output"])
    if isinstance(element, list):
        return "".join(_extract_text(item) for item in element)
    return ""


def _parse_responsepayload(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""
    if "candidates" in payload:
        return "\n".join(
            _extract_text(candidate.get("content")) for candidate in payload.get("candidates", [])
        ).strip()
    if "output" in payload:
        return _extract_text(payload["output"]).strip()
    if "content" in payload:
        return _extract_text(payload["content"]).strip()
    return ""


def complete(system: str, messages: list[dict], max_tokens: int = 8192) -> str:
    if not settings.google_api_key:
        raise LLMError("GOOGLE_API_KEY is not set. Add it to .env to enable chat.")

    model_name = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    prompt_text = _format_prompt(system, messages)

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        },
    }
    
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": settings.google_api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            response_text = response.read().decode("utf-8")
            response_json = json.loads(response_text)
            
            print("\n" + "="*40 + " GEMINI RAW RESPONSE " + "="*40)
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            print("="*101 + "\n")
            
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        raise LLMError(f"Gemini API error: {error.code} {error.reason}: {body}") from error
    except URLError as error:
        raise LLMError(f"Gemini network error: {error.reason}") from error

    answer = _parse_responsepayload(response_json)
    if not answer:
        raise LLMError("Gemini API returned no text response.")
    return answer