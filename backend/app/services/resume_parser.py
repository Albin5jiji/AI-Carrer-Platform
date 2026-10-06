"""Conservative PDF text extraction for uploaded resumes; never invents profile facts."""
from io import BytesIO
import re


HEADINGS = {
    "education": "education",
    "education & coursework": "education",
    "education and coursework": "education",
    "academic background": "education",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "work history": "experience",
    "internships": "experience",
    "internship experience": "experience",
    "projects": "projects",
    "personal projects": "projects",
    "academic projects": "projects",
    "selected projects": "projects",
    "skills": "skills",
    "technical skills": "skills",
    "skills & tools": "skills",
    "skills and tools": "skills",
    "technical proficiencies": "skills",
    "certifications": "achievements",
    "certificates": "achievements",
    "achievements": "achievements",
    "awards": "achievements",
}


def _lines(data: bytes) -> list[str]:
    from pypdf import PdfReader

    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
    return [" ".join(raw.split()).strip() for raw in text.splitlines()]


def parse_pdf(data: bytes) -> dict[str, list[str]]:
    """Extract known resume sections without inventing facts."""

    result = {"education": [], "experience": [], "projects": [], "skills": [], "achievements": [], "links": []}
    section: str | None = None
    for line in _lines(data):
        if not line:
            continue
        normalized = re.sub(r"^[•·\-–—\s]+|[:\s]+$", "", line.lower())
        key = HEADINGS.get(normalized)
        if key:
            section = key
            continue
        if section and len(line) <= 500:
            result[section].append(line)
        result["links"].extend(url for url in re.findall(r"https?://[^\s)]+", line) if url not in result["links"])
    return result


def extract_summary(data: bytes) -> str | None:
    """Use a short pre-heading profile line as a summary when the PDF provides one."""

    candidates: list[str] = []
    for line in _lines(data):
        normalized = re.sub(r"^[•·\-–—\s]+|[:\s]+$", "", line.lower())
        if HEADINGS.get(normalized):
            break
        if len(line) < 35 or len(line) > 400 or "@" in line or "http" in line.lower():
            continue
        candidates.append(line)
        if len(candidates) == 2:
            break
    return " ".join(candidates)[:500] or None
