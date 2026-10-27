"""Hybrid geographical NER: a local gazetteer plus optional spaCy NER."""

from .gazetteer import Gazetteer, Mention
from .preprocessing import Sentence


def try_load_spacy_model(model_name: str = "en_core_web_sm"):
    """Return loaded NER model or None if unavailable; do not download files."""
    try:
        import spacy
        return spacy.load(model_name)
    except (ImportError, OSError):
        return None


def extract_mentions(
    text: str, sentences: list[Sentence], gazetteer: Gazetteer, nlp=None
) -> list[Mention]:
    mentions = gazetteer.match(text, sentences)
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ not in {"GPE", "LOC", "FAC"}:
                continue
            # Gazetteer mentions take precedence for overlapping spans.
            if any(ent.start_char < m.end and m.start < ent.end_char for m in mentions):
                continue
            sent_index = next((s.index for s in sentences if s.start <= ent.start_char < s.end), -1)
            if sent_index < 0:
                continue
            mentions.append(Mention(
                ent.text, ent.start_char, ent.end_char, sent_index,
                [], "spacy", None, "not_in_gazetteer", "unmatched_named_entity",
            ))
    return sorted(mentions, key=lambda m: (m.start, m.end))
