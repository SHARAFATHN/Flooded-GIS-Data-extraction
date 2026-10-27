"""Rule-based spatial relationship extraction."""

import re
from .gazetteer import Gazetteer, Mention
from .preprocessing import Sentence

RELATION_PATTERN = re.compile(
    r"(?<!\w)(north\s+of|south\s+of|east\s+of|west\s+of|near|along|within|around|between|toward|from|in|at)(?!\w)",
    flags=re.IGNORECASE,
)


def _entity_label(m: Mention | None, gazetteer: Gazetteer) -> str | None:
    return gazetteer.places[m.place_id].name if m and m.place_id else None


def extract_spatial_relations(
    text: str, sentences: list[Sentence], mentions: list[Mention], gazetteer: Gazetteer
) -> list[dict]:
    relations = []
    for sentence in sentences:
        resolved = [m for m in mentions if m.sentence_index == sentence.index and m.place_id]
        for match in RELATION_PATTERN.finditer(sentence.text):
            at_start = sentence.start + match.start()
            at_end = sentence.start + match.end()
            following = [m for m in resolved if m.start >= at_end and m.start - at_end <= 50]
            if not following:
                continue
            # Target must be immediately linked to preposition, not after another cue.
            target = min(following, key=lambda m: m.start)
            between = text[at_end:target.start]
            if re.search(r"[.!?;:]", between) or RELATION_PATTERN.search(between):
                continue
            preceding = [m for m in resolved if m.end <= at_start and at_start - m.end <= 65]
            # Prefer named localities rather than intervening state/country qualifiers.
            preceding.sort(key=lambda m: (
                gazetteer.places[m.place_id].kind in {"state", "country"},
                at_start - m.end,
            ))
            source = preceding[0] if preceding else None
            subject = text[max(sentence.start, at_start - 70):at_start].strip(" ,;:-")
            relations.append({
                "relation": re.sub(r"\s+", "_", match.group().lower()),
                "from_place_id": source.place_id if source else None,
                "from_place": _entity_label(source, gazetteer),
                "to_place_id": target.place_id,
                "to_place": _entity_label(target, gazetteer),
                "subject_text": subject if not source else None,
                "sentence_index": sentence.index,
            })
    return relations
