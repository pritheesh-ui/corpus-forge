from dataclasses import dataclass


TONES = ["neutral", "friendly", "formal", "playful", "concise"]
LEVELS = ["beginner", "intermediate", "advanced", "expert"]
DIFFICULTIES = ["easy", "medium", "hard", "mixed"]
QUESTION_TYPES = ["multiple_choice", "short_answer", "true_false", "mixed"]
REVIEW_FOCUS = ["correctness", "performance", "readability", "security", "all"]

MODES = ["ask", "quiz", "test", "code_review"]


@dataclass
class ModeSpec:
    key: str
    label: str
    description: str
    options: dict


MODE_SPECS = {
    "ask": ModeSpec(
        key="ask",
        label="Ask",
        description="Ask any question about the documents in context.",
        options={
            "tone": TONES,
            "level": LEVELS,
        },
    ),
    "quiz": ModeSpec(
        key="quiz",
        label="Quiz",
        description="Generate a study quiz from the documents.",
        options={
            "level": LEVELS,
            "difficulty": DIFFICULTIES,
            "question_type": QUESTION_TYPES,
            "count": list(range(3, 16)),
        },
    ),
    "test": ModeSpec(
        key="test",
        label="Test",
        description="Build a graded test with an answer key.",
        options={
            "level": LEVELS,
            "difficulty": DIFFICULTIES,
            "question_type": QUESTION_TYPES,
            "count": list(range(5, 26)),
        },
    ),
    "code_review": ModeSpec(
        key="code_review",
        label="Code review",
        description="Review the code as a senior engineer.",
        options={
            "focus": REVIEW_FOCUS,
            "level": LEVELS,
            "tone": TONES,
        },
    ),
}


def build_system_prompt(mode: str, options: dict) -> str:
    if mode == "ask":
        tone = options.get("tone", "neutral")
        level = options.get("level", "intermediate")
        return (
            "You are a careful research assistant who answers using the provided source excerpts. "
            f"Adopt a {tone} tone and explain things at a {level} level. "
            "Stick to what the sources say. If something is not covered, say so plainly instead of guessing. "
            "Cite sources inline with the format [filename #chunk] right after the claim they support. "
            "Keep answers focused and skip filler."
        )

    if mode == "quiz":
        level = options.get("level", "intermediate")
        difficulty = options.get("difficulty", "medium")
        qtype = options.get("question_type", "mixed")
        count = options.get("count", 8)
        return (
            f"You are a study coach building a {difficulty}, {level}-level quiz with {count} questions "
            f"of type '{qtype}' from the provided source excerpts. "
            "Write each question so the answer is recoverable from the sources. "
            "Number questions and list options clearly. After the quiz, add an 'Answer key' section "
            "with brief explanations and source references in the form [filename #chunk]. "
            "Do not invent material that is not in the sources."
        )

    if mode == "test":
        level = options.get("level", "intermediate")
        difficulty = options.get("difficulty", "medium")
        qtype = options.get("question_type", "mixed")
        count = options.get("count", 12)
        return (
            f"You are an examiner writing a graded test: {count} {qtype} questions, "
            f"{difficulty} difficulty, aimed at a {level} learner. "
            "Use the provided source excerpts as the only material. "
            "Assign point values, total to 100, and include a scoring rubric. "
            "Provide an answer key with citations [filename #chunk] and a short rationale per question."
        )

    if mode == "code_review":
        focus = options.get("focus", "all")
        level = options.get("level", "intermediate")
        tone = options.get("tone", "neutral")
        focus_line = (
            "Cover correctness, performance, readability, and security."
            if focus == "all"
            else f"Focus primarily on {focus}, but flag anything else that is clearly broken."
        )
        return (
            f"You are a senior engineer reviewing the user's code. {focus_line} "
            f"Adjust your explanations to a {level} engineer and keep a {tone} tone. "
            "Structure the response as: Summary, Findings (grouped by severity: critical, major, minor, nit), "
            "Suggested patches (small diffs or rewritten snippets), and Open questions. "
            "Reference the file and chunk you are quoting with [filename #chunk]. "
            "If the user did not ask a specific question, give a full review of the retrieved code."
        )

    return "You are a helpful assistant. Answer using the provided sources when relevant."


def build_user_prompt(question: str, retrieved: list[dict]) -> str:
    if not retrieved:
        return (
            f"{question}\n\n"
            "No source excerpts were retrieved for this query. "
            "If the question requires sources, ask the user to upload relevant files."
        )

    blocks = []
    for r in retrieved:
        blocks.append(
            f"[{r['document_name']} #{r['position']}]\n{r['content']}"
        )
    sources = "\n\n---\n\n".join(blocks)

    return (
        "Source excerpts:\n\n"
        f"{sources}\n\n"
        "======\n\n"
        f"User request: {question}"
    )
