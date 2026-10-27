"""Text normalization and sentence segmentation."""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Sentence:
    index: int
    start: int
    end: int
    text: str


def clean_text(text: str) -> str:
    """Normalize text while keeping punctuation and readable spacing."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[\t\r\n]+", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


def split_sentences(text: str) -> list[Sentence]:
    """Simple, deterministic sentence splitter with character offsets."""
    result = []
    for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text):
        chunk = match.group()
        leading = len(chunk) - len(chunk.lstrip())
        trailing = len(chunk) - len(chunk.rstrip())
        if chunk.strip():
            start = match.start() + leading
            end = match.end() - trailing
            result.append(Sentence(len(result), start, end, text[start:end]))
    return result
