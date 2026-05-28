from pathlib import Path
from pypdf import PdfReader


TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".log",
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".htm", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".java", ".kt", ".go", ".rs", ".rb", ".php",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cs",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql", ".proto",
    ".xml", ".csv", ".tsv",
    ".swift", ".dart", ".lua", ".r", ".jl",
    ".vue", ".svelte", ".astro",
}

ALLOWED_EXTENSIONS = TEXT_EXTENSIONS | {".pdf"}


def extension_of(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed(filename: str) -> bool:
    return extension_of(filename) in ALLOWED_EXTENSIONS


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    return _extract_text_file(path)


def _extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages).strip()


def _extract_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace").strip()
