# DisasterGeo — Geographic Information Extraction for Disaster Management

An educational, **runnable Python project** that extracts geographical references from disaster-related text and produces machine-readable GIS results and an interactive map. It runs offline with a small included gazetteer. spaCy NER is optional.

> **Important:** All example reports are synthetic. An extracted place name is **not** proof of a disaster at that point. The coordinates for rivers and counties are representative reference points, **not disaster footprints**. This project is not an emergency warning or response system.

## 1. Project objectives

1. Clean and segment unstructured disaster-related text.
2. Identify geographical named entities (cities, states, countries, counties, rivers).
3. Resolve ambiguous toponyms using sentence context.
4. Convert resolved geographical names to coordinates using a local gazetteer.
5. Extract relationships such as **near**, **north of**, **south of**, **along**, **in**, **from**, and **toward**.
6. Export extracted information to **CSV, JSON, GeoJSON**, and **HTML map** for GIS analysis.

## 2. Folder structure

```text
disaster_geo_extraction/
├── main.py                      # Command-line application
├── requirements.txt            # Optional map / NER dependencies
├── README.md                   # Setup and usage
├── PROJECT_REPORT.md           # Full academic-style project write-up
├── data/
│   ├── reports.csv             # 14 fictional disaster reports
│   └── gazetteer.json          # 22 reference locations
├── disaster_geo/
│   ├── preprocessing.py        # Normalization + sentence segmentation
│   ├── gazetteer.py            # Place catalog + dictionary NER
│   ├── extractor.py            # Optional spaCy NER augmentation
│   ├── disambiguation.py       # Context-based place resolution
│   ├── relations.py            # Spatial relation pattern matching
│   ├── pipeline.py             # Orchestration + basic hazard keywords
│   └── outputs.py              # JSON/CSV/GeoJSON/Folium map generation
├── tests/
│   └── test_pipeline.py        # Standard-library unittest suite
└── outputs/                    # Example output artifacts
```

## 3. Installation and execution

Use **Python 3.10 or later**. From the project folder:

```bash
# Create a virtual environment (recommended)
python -m venv .venv

# Activate on macOS/Linux:
source .venv/bin/activate
# OR on Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install visualization and optional NLP library
python -m pip install -r requirements.txt

# Run the default offline extraction pipeline
python main.py

# Run automated tests
python -m unittest discover -s tests -v
```

For spaCy's pretrained English location-entity recognition (optional):

```bash
python -m spacy download en_core_web_sm
python main.py --use-spacy
```

If the spaCy model is missing, `--use-spacy` gracefully continues in gazetteer-only mode. You can run `python main.py --no-map` **without installing any external packages**; the core implementation uses only Python's standard library.

### Custom input files

```bash
python main.py --input my_reports.csv --outdir my_results
python main.py --input my_reports.csv --gazetteer data/gazetteer.json --use-spacy
```

The CSV **must** include `report_id` and `text`; `source` and `published_date` are optional. Store files in UTF-8 encoding:

```csv
report_id,source,published_date,text
EXAMPLE-001,fictional,2026-01-01,"Flash floods were reported in Houston, Texas, near Buffalo Bayou."
```

## 4. The six main steps

| Step | Python implementation | Output |
|---|---|---|
| 1. Text preprocessing | `clean_text`, `split_sentences` | Normalized text and sentence offsets |
| 2. Geographical NER | Gazetteer matching, optional spaCy NER | Mention spans and candidates |
| 3. Toponym disambiguation | Context from states, countries, adjacent named features | Resolved place ID or explicit ambiguity |
| 4. Geocoding | Offline gazetteer latitude/longitude lookup | WGS84 coordinates |
| 5. Spatial relationship extraction | Rule-based preposition patterns | Relation, source place (when known), target place |
| 6. GIS export / mapping | CSV, JSON, GeoJSON, Folium | Structured data and interactive map |

**Note:** Geocoding is the coordinate-lookup portion of Step 3 in some taxonomies; it is listed separately above to make it easier to locate in the code. The core six-stage conceptual pipeline comprises preprocessing, geographical NER, toponym resolution/geocoding, relation extraction, data structuring, and mapping/analysis.

## 5. Example

**Input report**

> Heavy rainfall triggered flooding in Atlanta, Georgia. Roads near the Chattahoochee River were closed.

**Extracted references**

| Mention | Resolved feature | Latitude | Longitude |
|---|---|---:|---:|
| Atlanta | Atlanta city, Georgia, US | 33.7490 | -84.3880 |
| Georgia | Georgia state, US | 32.1656 | -82.9001 |
| Chattahoochee River | River (representative point near Atlanta) | 33.8250 | -84.4540 |

**Detected relationships:** `in → Atlanta` and `near → Chattahoochee River`. These describe **what the text says**; they do not produce a polygon for an inundated area or an exact event location.

### Example: ambiguous place name

- `Flooding in Paris, Texas` → **Paris, Texas, US** (Texas context).
- `Floods in Paris near the Seine River` → **Paris, France** (river context).
- `Flooding in Springfield` → **ambiguous**, excluded from coordinate outputs.

A place that is unique in the *small example gazetteer* is not necessarily unique worldwide.

## 6. Outputs

Running `python main.py` creates:

- `outputs/results.json`: full results per report including resolved/unresolved entities, methods, and relationships.
- `outputs/locations.csv`: flattened **resolved mentions** for tabular analysis.
- `outputs/relations.csv`: relations between mentioned locations or narratives and target places.
- `outputs/locations.geojson`: geocoded text references as GeoJSON point features; usable in QGIS.
- `outputs/unresolved.json`: ambiguous / unknown locations for human review.
- `outputs/summary.json`: processing totals.
- `outputs/map.html`: Folium/Leaflet map of **city, county, and river references**. State/country centroids are intentionally not shown as incident markers.

The HTML map may need internet access to display OpenStreetMap tiles and external JavaScript, although CSV, JSON, GeoJSON, and all extraction steps are fully offline.

## 7. Review and evaluation

```bash
python -m unittest discover -s tests -v
```

There are nine initial functional tests. They check text preprocessing, detection, place resolution, geocoding, spatial relations, exports, and input validation. Passing tests demonstrate the implementation works for its **small synthetic fixtures**, **not** real-world extraction accuracy.

For a research evaluation, manually annotate a separate dataset with location spans, canonical locations, coordinates, relation labels, and whether a disaster location is truly asserted. Then compute location entity precision/recall/F1, disambiguation accuracy, and relation precision/recall/F1, including performance on unseen place names and misleading/negated statements. See `PROJECT_REPORT.md`.

## 8. How to extend

- Replace the mini gazetteer with GeoNames / OpenStreetMap / a national gazetteer and assess licensing/provenance.
- Use a domain-tuned transformer for multilingual geographical NER and negation/uncertainty detection.
- Read disaster-related text from a verified feed with source metadata, timestamps, and deduplication.
- Add geospatial geometry and geodesic operations (Shapely/GeoPandas) for roads, zones, polygons, and geofenced alerts.
- Link a named location to a verified event only after cross-checking with trusted disaster bulletins and human review.

## 9. Safety and ethics

Do not treat this demo as an authoritative hazard map. News articles and social posts can mention *places near* events, historical events, rumors, denial statements, places outside the incident, and generic regional centroids. All outputs should retain source attribution and uncertainty. Avoid ingesting personally identifiable location information without appropriate authorization and protection.
