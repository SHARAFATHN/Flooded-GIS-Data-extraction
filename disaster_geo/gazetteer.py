"""Offline place dictionary and gazetteer-backed entity recognition."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from .preprocessing import Sentence


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    kind: str
    admin1: str
    country: str
    latitude: float
    longitude: float
    aliases: tuple[str, ...] = ()


@dataclass
class Mention:
    surface: str
    start: int
    end: int
    sentence_index: int
    candidate_ids: list[str] = field(default_factory=list)
    source: str = "gazetteer"
    place_id: str | None = None
    status: str = "unresolved"
    resolution_method: str = ""


class Gazetteer:
    def __init__(self, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.places = {
            obj["id"]: Place(
                obj["id"], obj["name"], obj["kind"], obj.get("admin1", ""),
                obj["country"], float(obj["latitude"]), float(obj["longitude"]),
                tuple(obj.get("aliases", [])),
            )
            for obj in data
        }
        self.alias_to_ids: dict[str, list[str]] = {}
        for place in self.places.values():
            for alias in set((place.name, *place.aliases)):
                self.alias_to_ids.setdefault(alias.casefold(), []).append(place.id)
        aliases = sorted(self.alias_to_ids, key=lambda item: (-len(item), item))
        self.matcher = re.compile(
            r"(?<!\w)(?:" + "|".join(re.escape(alias) for alias in aliases) + r")(?!\w)",
            flags=re.IGNORECASE,
        )

    def match(self, text: str, sentences: list[Sentence]) -> list[Mention]:
        mentions = []
        for m in self.matcher.finditer(text):
            sent_index = next((s.index for s in sentences if s.start <= m.start() < s.end), -1)
            if sent_index < 0:
                continue
            mentions.append(Mention(
                m.group(), m.start(), m.end(), sent_index,
                list(self.alias_to_ids[m.group().casefold()]),
            ))
        return mentions
