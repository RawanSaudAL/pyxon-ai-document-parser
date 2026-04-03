import io
import os
import re
import uuid
from typing import Any, Dict, List, Tuple

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
NUMBERED_SECTION_RE = re.compile(r"(?m)^\s*\d+[.)-]\s+")
BULLET_RE = re.compile(r"(?m)^\s*[-•*]\s+")
HEADING_RE = re.compile(
    r"^\s*((chapter|section|part)\s+\d+|[0-9]+[.)-]\s+|[A-Z][A-Z\s]{3,}|[\u0600-\u06FFA-Za-z0-9\s]{2,}[:：])\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def get_file_extension(file_name: str) -> str:
    return os.path.splitext(file_name.lower())[1]


def validate_file(file_name: str) -> Tuple[bool, str]:
    if not file_name:
        return False, "No file was provided."
    ext = get_file_extension(file_name)
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}"
    return True, ""


def safe_decode_bytes(data: bytes) -> str:
    encodings = ["utf-8", "utf-8-sig", "cp1256", "windows-1256", "latin-1"]
    for enc in encodings:
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    buffer = io.BytesIO(file_bytes)
    reader = PdfReader(buffer)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    buffer = io.BytesIO(file_bytes)
    doc = Document(buffer)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    return safe_decode_bytes(file_bytes).strip()


def extract_text(file_name: str, file_bytes: bytes) -> str:
    ext = get_file_extension(file_name)

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if ext == ".docx":
        return extract_text_from_docx(file_bytes)
    if ext == ".txt":
        return extract_text_from_txt(file_bytes)

    raise ValueError(f"Unsupported extension: {ext}")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_matching(text: str) -> str:
    text = normalize_text(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def contains_arabic(text: str) -> bool:
    return bool(ARABIC_RE.search(text or ""))


def contains_diacritics(text: str) -> bool:
    return bool(DIACRITICS_RE.search(text or ""))


def detect_language_label(text: str) -> str:
    return "arabic" if contains_arabic(text) else "english"


def detect_title(text: str, file_name: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        first = lines[0]
        if 3 <= len(first) <= 180:
            return first
    return os.path.splitext(file_name)[0]


def split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    cleaned = [p.strip() for p in paragraphs if p and p.strip()]
    if cleaned:
        return cleaned

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def find_headings(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headings = []

    for line in lines:
        if len(line) > 160:
            continue

        is_heading = (
            HEADING_RE.match(line) is not None
            or line.endswith(":")
            or line.endswith("：")
            or (len(line.split()) <= 10 and ":" in line)
        )

        if is_heading:
            headings.append(line)

    unique_headings = []
    seen = set()
    for heading in headings:
        if heading not in seen:
            unique_headings.append(heading)
            seen.add(heading)

    return unique_headings


def extract_key_concepts(text: str, headings: List[str]) -> List[str]:
    source = " ".join(headings) if headings else text[:1500]
    source = source.replace(":", " ").replace("،", " ").replace(",", " ")
    tokens = source.split()

    concepts = []
    seen = set()

    for token in tokens:
        cleaned = token.strip(" .,:;!?()[]{}\"'“”‘’")
        if len(cleaned) < 3:
            continue
        if cleaned.isdigit():
            continue
        if cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        concepts.append(cleaned)

    return concepts[:10]


def estimate_document_type(paragraphs: List[str], headings: List[str], text: str) -> str:
    if len(headings) >= 3:
        return "educational_or_article"
    if len(paragraphs) <= 3 and len(text) < 1200:
        return "short_document"
    if len(paragraphs) >= 8:
        return "long_form_document"
    return "general_document"


def analyze_document_structure(text: str, file_name: str) -> Dict[str, Any]:
    paragraphs = split_paragraphs(text)
    headings = find_headings(text)
    paragraph_lengths = [len(p.split()) for p in paragraphs] or [0]

    avg_paragraph_length = round(sum(paragraph_lengths) / len(paragraph_lengths), 2) if paragraph_lengths else 0
    numbered_sections = len(NUMBERED_SECTION_RE.findall(text))
    bullet_points = len(BULLET_RE.findall(text))
    line_count = len([line for line in text.splitlines() if line.strip()])
    title = detect_title(text, file_name)
    document_type = estimate_document_type(paragraphs, headings, text)
    key_concepts = extract_key_concepts(text, headings)

    return {
        "title": title,
        "document_type": document_type,
        "paragraph_count": len(paragraphs),
        "avg_paragraph_length": avg_paragraph_length,
        "heading_count": len(headings),
        "headings": headings[:10],
        "bullet_points": bullet_points,
        "numbered_sections": numbered_sections,
        "line_count": line_count,
        "has_arabic": contains_arabic(text),
        "has_diacritics": contains_diacritics(text),
        "language_label": detect_language_label(text),
        "key_concepts": key_concepts,
    }


def select_chunking_strategy(analysis: Dict[str, Any]) -> Tuple[str, str]:
    dynamic_score = 0
    fixed_score = 0
    reasons = []

    if analysis["heading_count"] >= 2:
        dynamic_score += 2
        reasons.append("Multiple headings detected")
    else:
        fixed_score += 1

    if analysis["numbered_sections"] >= 2 or analysis["bullet_points"] >= 2:
        dynamic_score += 1
        reasons.append("Structured list patterns detected")
    else:
        fixed_score += 1

    if analysis["avg_paragraph_length"] >= 120:
        dynamic_score += 1
        reasons.append("Average paragraph length is high")
    else:
        fixed_score += 1

    if analysis["paragraph_count"] <= 3 and analysis["line_count"] > 10:
        fixed_score += 2
        reasons.append("Few paragraph boundaries in a long document")
    else:
        dynamic_score += 1

    if dynamic_score > fixed_score:
        return "dynamic", "; ".join(reasons) if reasons else "Structured content detected"

    return "fixed", "; ".join(reasons) if reasons else "Simple structure detected"


def fixed_chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)

        if end == len(words):
            break

        start = max(end - overlap, start + 1)

    return chunks


def dynamic_chunk_text(text: str, max_words: int = 450, min_words: int = 80) -> List[str]:
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []

    chunks = []
    current_parts = []
    current_word_count = 0

    def flush() -> None:
        nonlocal current_parts, current_word_count
        if current_parts:
            merged = "\n\n".join(current_parts).strip()
            if merged:
                chunks.append(merged)
        current_parts = []
        current_word_count = 0

    for paragraph in paragraphs:
        word_count = len(paragraph.split())
        is_heading_like = (
            len(paragraph.split()) <= 12
            and (
                paragraph.endswith(":")
                or paragraph.endswith("：")
                or HEADING_RE.match(paragraph) is not None
            )
        )

        if is_heading_like and current_parts and current_word_count >= min_words:
            flush()

        if word_count > max_words:
            if current_parts:
                flush()
            oversized = fixed_chunk_text(paragraph, chunk_size=max_words, overlap=40)
            chunks.extend(oversized)
            continue

        if current_word_count + word_count > max_words and current_word_count >= min_words:
            flush()

        current_parts.append(paragraph)
        current_word_count += word_count

    if current_parts:
        flush()

    return [chunk for chunk in chunks if chunk.strip()]


def build_chunk_records(document_id: str, chunks: List[str], file_name: str, strategy: str) -> List[Dict[str, Any]]:
    records = []

    for idx, chunk in enumerate(chunks, start=1):
        records.append(
            {
                "chunk_id": f"{document_id}_chunk_{idx}",
                "document_id": document_id,
                "chunk_index": idx,
                "text": chunk,
                "length": len(chunk.split()),
                "source_file": os.path.splitext(file_name)[0],
                "strategy": strategy,
            }
        )

    return records


def generate_document_id() -> str:
    return str(uuid.uuid4())