"""End-to-end information extraction pipeline for disaster reports."""

import re
from pathlib import Path
from .disambiguation import resolve_mentions
from .extractor import extract_mentions, try_load_spacy_model
from .gazetteer import Gazetteer
from .preprocessing import clean_text, split_sentences
from .relations import extract_spatial_relations


HAZARD_PATTERNS = [
    ("earthquake", r"\b(?:earthquake|seismic|aftershock)s?\b"),
    ("landslide", r"\b(?:landslide|mudslide)s?\b"),
    ("wildfire", r"\b(?:wildfire|brushfire|forest fire)s?\b"),
    ("flood", r"\b(?:flood|floods|flooding|floodwaters|flash flood|flash floods)\b"),
    ("tornado", r"\btornado(?:es|s)?\b"),
    ("hurricane", r"\bhurricanes?\b"),
    ("storm", r"\b(?:storm|storms|storm surge|heavy rainfall|thunderstorm|thunderstorms)\b"),
]


def classify_hazard(text: str) -> str:
    for hazard, pattern in HAZARD_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return hazard
    return "other_or_unknown"


class DisasterGeoPipeline:
    def __init__(self, gazetteer_file: str | Path, use_spacy: bool = False):
        self.gazetteer = Gazetteer(gazetteer_file)
        self.nlp = try_load_spacy_model() if use_spacy else None
        self.ner_mode = "hybrid_spacy_gazetteer" if self.nlp is not None else "gazetteer_only"

    def process(self, report: dict) -> dict:
        text = clean_text(str(report.get("text", "")))
        sentences = split_sentences(text)
        mentions = extract_mentions(text, sentences, self.gazetteer, self.nlp)
        resolve_mentions(mentions, self.gazetteer)
        relations = extract_spatial_relations(text, sentences, mentions, self.gazetteer)
        places = []
        for m in mentions:
            place = self.gazetteer.places.get(m.place_id) if m.place_id else None
            places.append({
                "mention": m.surface,
                "start": m.start,
                "end": m.end,
                "sentence_index": m.sentence_index,
                "source": m.source,
                "status": m.status,
                "resolution_method": m.resolution_method,
                "candidate_place_ids": m.candidate_ids,
                "place_id": m.place_id,
                "name": place.name if place else None,
                "kind": place.kind if place else None,
                "admin1": place.admin1 if place else None,
                "country": place.country if place else None,
                "latitude": place.latitude if place else None,
                "longitude": place.longitude if place else None,
                "geocode_method": "offline_gazetteer" if place else None,
            })
        return {
            "report_id": str(report.get("report_id", "")),
            "source": str(report.get("source", "")),
            "published_date": str(report.get("published_date", "")),
            "hazard": classify_hazard(text),
            "ner_mode": self.ner_mode,
            "text": text,
            "locations": places,
            "spatial_relations": relations,
        }
