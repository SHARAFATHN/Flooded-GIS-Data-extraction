"""Context-driven toponym resolution; never guess when evidence ties."""

from .gazetteer import Gazetteer, Mention, Place


def _context_support(candidate: Place, context: Place) -> int:
    """Heuristic spatial consistency score (not a calibrated probability)."""
    if candidate.id == context.id:
        return 0
    score = 0
    if context.kind == "state" and candidate.admin1 == context.name:
        score += 7
    if context.kind == "country" and candidate.country == context.name:
        score += 6
    if candidate.kind == "state" and context.admin1 == candidate.name:
        score += 7
    if candidate.kind == "country" and context.country == candidate.name:
        score += 6
    if candidate.admin1 and context.admin1 and candidate.admin1 == context.admin1:
        score += 4
    if candidate.country == context.country and context.kind != "country":
        score += 2
    return score


def resolve_mentions(mentions: list[Mention], gazetteer: Gazetteer) -> None:
    """Set a unique place when supported; preserve ambiguity otherwise."""
    for m in mentions:
        if len(m.candidate_ids) == 1:
            m.place_id = m.candidate_ids[0]
            m.status = "resolved"
            m.resolution_method = "unique_gazetteer_match"
        elif not m.candidate_ids:
            m.status = "not_in_gazetteer"
            m.resolution_method = "no_gazetteer_candidate"
        else:
            m.status = "ambiguous"
            m.resolution_method = "insufficient_context"

    # Iterations allow e.g. 'Georgia' to be grounded by a uniquely resolved Atlanta.
    for _ in range(3):
        progressed = False
        for m in mentions:
            if m.status != "ambiguous":
                continue
            contexts = [
                other for other in mentions
                if other is not m and other.sentence_index == m.sentence_index
                and other.place_id is not None
            ]
            if not contexts:
                continue
            candidates = []
            for place_id in m.candidate_ids:
                place = gazetteer.places[place_id]
                score = sum(_context_support(place, gazetteer.places[c.place_id]) for c in contexts)
                candidates.append((score, place_id))
            candidates.sort(reverse=True)
            if candidates[0][0] >= 2 and (len(candidates) == 1 or candidates[0][0] > candidates[1][0]):
                m.place_id = candidates[0][1]
                m.status = "resolved"
                m.resolution_method = "contextual_gazetteer_resolution"
                progressed = True
        if not progressed:
            break
