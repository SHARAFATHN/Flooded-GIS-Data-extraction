"""Export extracted results to JSON, CSV, GeoJSON, and an optional Folium map."""

import csv
import html
import json
from collections import Counter
from pathlib import Path


LOCATION_FIELDS = [
    "report_id", "published_date", "hazard", "mention", "place_id", "name",
    "kind", "admin1", "country", "latitude", "longitude", "resolution_method",
    "geocode_method", "source_text",
]
RELATION_FIELDS = [
    "report_id", "hazard", "relation", "from_place_id", "from_place", "to_place_id",
    "to_place", "subject_text", "sentence_index",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(results: list[dict], outdir: str | Path, make_map: bool = True) -> dict:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    locations, relations, features = [], [], []
    unresolved = []
    for report in results:
        for loc in report["locations"]:
            if loc["status"] != "resolved":
                unresolved.append({
                    "report_id": report["report_id"], "mention": loc["mention"],
                    "status": loc["status"], "candidate_place_ids": loc["candidate_place_ids"],
                })
                continue
            row = {
                "report_id": report["report_id"],
                "published_date": report["published_date"],
                "hazard": report["hazard"],
                "mention": loc["mention"],
                "place_id": loc["place_id"],
                "name": loc["name"],
                "kind": loc["kind"],
                "admin1": loc["admin1"],
                "country": loc["country"],
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "resolution_method": loc["resolution_method"],
                "geocode_method": loc["geocode_method"],
                "source_text": report["text"],
            }
            locations.append(row)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc["longitude"], loc["latitude"]],
                },
                "properties": {k: v for k, v in row.items() if k not in {"latitude", "longitude"}},
            })
        for rel in report["spatial_relations"]:
            relations.append({
                "report_id": report["report_id"],
                "hazard": report["hazard"],
                **{f: rel.get(f) for f in RELATION_FIELDS if f not in {"report_id", "hazard"}},
            })

    _write_csv(out / "locations.csv", LOCATION_FIELDS, locations)
    _write_csv(out / "relations.csv", RELATION_FIELDS, relations)
    (out / "locations.geojson").write_text(json.dumps({
        "type": "FeatureCollection", "features": features,
    }, indent=2), encoding="utf-8")
    (out / "unresolved.json").write_text(json.dumps(unresolved, indent=2), encoding="utf-8")

    summary = {
        "reports_processed": len(results),
        "resolved_place_mentions": len(locations),
        "unresolved_place_mentions": len(unresolved),
        "spatial_relations_extracted": len(relations),
        "reports_by_hazard": dict(Counter(r["hazard"] for r in results)),
        "ner_modes": dict(Counter(r["ner_mode"] for r in results)),
        "warning": "Extracted references are NOT verified disaster locations or impact extents.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if make_map:
        try:
            _write_map(out / "map.html", locations)
            summary["map_created"] = True
        except ImportError:
            summary["map_created"] = False
            print("Folium not installed; skipping map.html. Install: pip install folium")
    else:
        summary["map_created"] = False
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_map(path: Path, rows: list[dict]) -> None:
    import folium

    # Regions/states are references, not point-level incident locations.
    points = [r for r in rows if r["kind"] not in {"state", "country"}]
    center = [sum(x["latitude"] for x in points) / len(points),
              sum(x["longitude"] for x in points) / len(points)] if points else [39.0, -98.0]
    fmap = folium.Map(location=center, zoom_start=4, tiles="OpenStreetMap", control_scale=True)
    colors = {
        "flood": "blue", "wildfire": "orange", "landslide": "brown",
        "earthquake": "purple", "hurricane": "darkred", "storm": "cadetblue",
        "tornado": "red",
    }
    seen = set()
    for row in points:
        key = (row["report_id"], row["place_id"])
        if key in seen:
            continue
        seen.add(key)
        label = (f"Report: {row['report_id']} | Hazard: {row['hazard']} | "
                 f"Referenced place: {row['name']}")
        popup = (f"<b>{html.escape(row['name'])}</b><br>"
                 f"Report: {html.escape(row['report_id'])}<br>"
                 f"Hazard category: {html.escape(row['hazard'])}<br>"
                 f"Feature: {html.escape(row['kind'])}<br>"
                 "<i>Text reference only; not a verified disaster point.</i>")
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=6,
            color=colors.get(row["hazard"], "gray"), fill=True, fill_opacity=0.8,
            tooltip=label, popup=folium.Popup(popup, max_width=270),
        ).add_to(fmap)
    if points:
        latitudes = [p["latitude"] for p in points]
        longitudes = [p["longitude"] for p in points]
        fmap.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])
    fmap.save(str(path))
