# Dissertation/Project Report

## DisasterGeo: An NLP-Based Geographical Information Extraction System for Disaster Management

**Subject area:** Natural Language Processing (NLP), Geographic Information Systems (GIS), and Disaster Management  
**Implementation language:** Python 3.10+  
**Project type:** Educational research prototype; fully reproducible synthetic-data demonstration

---

## Abstract

Disaster management depends on timely interpretation of reports that often describe hazards and locations using free-form language. Such descriptions may contain city and region names, natural features, and relative references such as “near the river” or “north of the city.” Converting these expressions into GIS-compatible information can support indexing, situational-awareness dashboards, and subsequent human analysis. This project implements a reproducible Python pipeline for geographical information extraction from disaster-related text. The pipeline comprises text preprocessing, geographic named entity recognition, toponym disambiguation, coordinate lookup, extraction of spatial relationships, and generation of GIS outputs. A curated offline gazetteer enables deterministic execution without web services; optional spaCy named entity recognition discovers further candidate location expressions. The prototype exports JSON, CSV, GeoJSON, and a Folium web map. In a functional demonstration using 14 **fictional** disaster reports, the system resolved 33 place mentions, left one ambiguous mention unresolved, and extracted 20 spatial relations. All nine automated functional tests passed. These counts indicate prototype operation, **not measured precision, recall, or operational reliability**. Further evaluation with annotated, real-world, multilingual reports is required before any operational use.

**Keywords:** Geographical Information Extraction, Disaster Management, Geoparsing, Named Entity Recognition, Toponym Disambiguation, Geocoding, GIS, spaCy, Python.

## 1. Introduction

Floods, wildfires, storms, landslides, and earthquakes are described in news reports, emergency communications, and community observations. These sources contain geographical information that may not already be stored in structured geospatial databases. For instance, “Roads near the Chattahoochee River were closed” contains a named geographical feature and a spatial relation. A geographic information extraction system helps transform such narrative references into structured records so analysts can explore them geographically.

**Geoparsing** generally includes recognizing geographic names and grounding them to locations. Disaster-report analysis also benefits from identifying spatial relations and explicitly recording uncertainty. The central challenge is not merely finding a capitalized place name: names can be ambiguous, relationships can be relative, and mentioned places may not coincide with actual damaged areas.

## 2. Problem statement

Unstructured disaster reports create four interconnected problems:

1. Geographic mentions may be buried inside long natural-language narratives.
2. Place names can be ambiguous: “Paris” or “Springfield” refers to multiple real-world locations.
3. Relative expressions such as “north of Miami” do not provide exact event coordinates.
4. Traditional GIS software expects structured coordinates or geometries rather than free-form text.

The aim is to build a transparent prototype that addresses these challenges while preserving uncertainty instead of creating unjustified exact incident locations.

## 3. Aim and objectives

### Aim

Develop a Python-based geographical information extraction and GIS visualization workflow for disaster-related text.

### Specific objectives

- Preprocess unstructured disaster text and segment it into sentences.
- Detect mentions of cities, states, countries, counties, and named natural features.
- Resolve ambiguous toponyms with contextual administrative and geographic clues.
- Assign WGS84 latitude and longitude coordinates to supported gazetteer entries.
- Extract basic spatial relationships from narrative sentences.
- Produce structured, interoperable GIS data and an exploratory HTML map.
- Create automated tests and outline a defensible real-world evaluation protocol.

## 4. Research questions

1. How can a deterministic NLP pipeline transform disaster narratives into GIS-compatible records?
2. How can contextual locations such as administrative regions and rivers help resolve ambiguous place names?
3. Which spatial relations can be obtained with explainable rule-based methods, and what are their limitations?
4. How should an extraction system distinguish between a *place mentioned in text* and an *actual verified disaster location*?

## 5. Scope of the project

The prototype processes English-language reports stored in a CSV file. Its mini gazetteer contains 22 reference locations spanning select US places and France. Inputs and coordinates are illustrative. Hazard classes are assigned using simple keywords. The work emphasizes the **information extraction pipeline**, not live data collection, damage assessment, flood modeling, casualty prediction, route optimization, hazard forecasting, or emergency dispatch.

## 6. System architecture

```text
          Disaster reports (CSV)
                     |
                     v
           1. Text preprocessing
       (normalization, segmentation)
                     |
                     v
           2. Geographic NER
      (offline gazetteer + optional spaCy)
                     |
                     v
       3. Toponym disambiguation
      (same-sentence context matching)
                     |
                     v
          4. Geocoding lookup
          (local WGS84 gazetteer)
                     |
                     v
      5. Spatial relation extraction
      (north of, near, along, in...)
                     |
                     v
      6. Structured GIS information
         (JSON / CSV / GeoJSON)
                     |
                     v
             Exploratory map
                 (Folium)
```

Geocoding is conceptually part of the toponym resolution/geocoding stage but is separated in this diagram to show the coordinate lookup explicitly.

## 7. Methodology and implementation

### 7.1 Data input and preprocessing

**Input:** `data/reports.csv`, containing `report_id`, `source`, `published_date`, and `text`. Reports are fictional and intentionally include ambiguous examples. **Module:** `disaster_geo/preprocessing.py`.

The preprocessing module normalizes Unicode, collapses irregular whitespace, and divides text into sentences while maintaining character offsets. Offsets associate each extracted mention with its source sentence and help avoid using unrelated context from another sentence. It is intentionally a lightweight segmenter; a production system should handle abbreviations and more complex punctuation.

### 7.2 Geographical named entity recognition

**Module:** `disaster_geo/gazetteer.py` and `disaster_geo/extractor.py`.

The default recognizer performs dictionary-backed mention detection using case-insensitive, boundary-aware regular expressions generated from the place gazetteer. For example, it recognizes `Atlanta`, `Georgia`, and `Chattahoochee River`. An optional spaCy `en_core_web_sm` model adds candidate `GPE`, `LOC`, and `FAC` named entities that do not overlap with a gazetteer match. Out-of-gazetteer spaCy mentions are recorded as unresolved rather than invented coordinates.

The gazetteer-only default is a valid **gazetteer-based NER method**, but coverage is intentionally restricted. The optional spaCy model improves candidate discovery, not grounding completeness.

### 7.3 Toponym disambiguation

**Module:** `disaster_geo/disambiguation.py`.

Every location mention is associated with candidate gazetteer records. One-candidate matches are resolved directly. Ambiguous mentions are assigned a context compatibility score using resolved places in the same sentence. The heuristic rewards agreement in administrative region and country; larger scores arise when a candidate city matches a nearby state or country mention. It iterates to use context that has already become unambiguous. If the best candidate does not receive distinctive positive support, the location remains **ambiguous**, with all candidates retained for review.

**Examples:**

- `Paris, Texas` → Paris, Texas, US.
- `Paris near the Seine River` → Paris, France.
- `Springfield` → unresolved because the sample gazetteer contains at least two possible Springfields.
- `Atlanta, Georgia` → Georgia, US state, because the city provides contextual evidence.

This is an interpretable heuristic, **not** a learned classifier, and its score is not a calibrated confidence probability. It can select an incorrect match when the reference gazetteer is incomplete or text context is misleading.

### 7.4 Geocoding

**Module:** `disaster_geo/pipeline.py`, in coordination with `disaster_geo/gazetteer.py`.

After a place is resolved to a unique gazetteer ID, its stored latitude and longitude are attached to the result. Coordinates follow WGS84 geographic conventions; GeoJSON uses the coordinate order `[longitude, latitude]`. No external geocoding API, API key, internet access, or quota is necessary. The local gazetteer is a proof-of-concept; its coordinates for rivers and administrative areas represent reference points, **not complete geometries**.

### 7.5 Spatial relationship extraction

**Module:** `disaster_geo/relations.py`.

The system detects a curated list of expressions: `north of`, `south of`, `east of`, `west of`, `near`, `along`, `within`, `around`, `between`, `toward`, `from`, `in`, and `at`. It matches the following resolved location to the expression. When a suitable preceding resolved geographical entity exists, it is recorded as a source; otherwise, a short narrative phrase is retained as the subject. For example:

| Sentence | Extracted relation | Important interpretation |
|---|---|---|
| “A wildfire north of Miami, Florida” | `north_of → Miami` | Miami is the reference place, not the wildfire coordinate |
| “Roads near the Chattahoochee River” | `near → Chattahoochee River` | Relative relation, not verified road geometry |
| “The storm moved from Miami toward Tampa” | `from → Miami`; `Miami — toward → Tampa` | A textual movement claim, not a validated storm track |

This rule-based approach does **not** perform full syntactic parsing or complex reasoning. It does not convert vague relations to invented coordinates or directions.

### 7.6 Structured geographical data and mapping

**Module:** `disaster_geo/outputs.py`.

Each input report produces a record with the original text, a simple hazard label, extracted entity spans, candidate IDs, chosen place IDs (where known), geocoding method, and spatial relationships. Outputs include `results.json`, `locations.csv`, `relations.csv`, `locations.geojson`, and `unresolved.json`. An optional Folium HTML map shows city, county, and natural-feature references. State and country centroids are **not plotted as individual disaster sites**. Tooltips explicitly describe map points as text references rather than verified event locations.

GeoJSON can be loaded into GIS software such as QGIS for inspection or joining against additional validated datasets.

## 8. Technologies and dependencies

| Technology | Role |
|---|---|
| Python 3.10+ | Core application and testing |
| `re`, `json`, `csv`, `unicodedata` | Preprocessing and structured export |
| Local gazetteer (JSON) | Location reference records and coordinates |
| spaCy (optional) | Additional learned NER location candidates |
| Folium (optional) | HTML/Leaflet-based interactive map |
| QGIS (external desktop software, optional) | Downstream viewing and geospatial analysis of GeoJSON |

There are no secret credentials, web API dependencies, or live disaster feeds in the baseline prototype.

## 9. Algorithm outline

```text
For each report:
    Normalize the text and identify sentence boundaries.
    Find gazetteer place-name mentions.
    If enabled, add nonoverlapping spaCy geographic entity mentions.
    Assign candidates from the local gazetteer.
    Resolve unique matches and ambiguous names with sentence context.
    For resolved places, look up latitude and longitude.
    Identify spatial prepositions and link them to nearby resolved entities.
    Assign a basic hazard keyword category.
    Store raw text, evidence, candidate IDs, outcomes, and relations.
After all reports:
    Write results.json, locations.csv, relations.csv and unresolved.json.
    Export resolved references as locations.geojson.
    Optionally generate map.html.
    Print aggregate counts and unresolved cases.
```

## 10. Results and functional demonstration

A run on the **14 supplied synthetic documents** produced the following outcomes:

| Measurement | Prototype result |
|---|---:|
| Reports processed | 14 |
| Resolved place mentions | 33 |
| Unresolved / ambiguous place mentions | 1 |
| Spatial relationship records | 20 |
| Reports categorized as flood | 7 |
| Reports categorized as storm | 5 |
| Reports categorized as wildfire | 1 |
| Reports categorized as landslide | 1 |
| Automated tests passed | 9 / 9 |

The system intentionally preserves an ambiguous `Springfield` rather than assigning a coordinate. Other example reports demonstrate `Paris, Texas`, `Paris, France`, and directional relations. The hazard classifier prioritizes keyword patterns rather than sophisticated event semantics; its output is only a coarse analytical label.

**Interpretation:** These are **counts of output records and passing fixture tests**, not accuracy rates. A successful software run does not establish scientific validity, sensitivity to false reports, or suitability for emergency decisions.

## 11. Proposed scientific evaluation

Create a held-out, independently annotated dataset containing diverse types of disaster narrative, document sources, and geographically ambiguous locations. Annotators should label: exact location mention spans; accepted canonical place ID; actual/unknown grounding status; place type; whether location is associated with the event or merely mentioned; spatial relation type and participants; and negation, uncertainty, and timing where relevant.

### Quantitative measures

1. **Named entity recognition precision:** `TP / (TP + FP)` for location spans.
2. **Named entity recognition recall:** `TP / (TP + FN)` for location spans.
3. **Named entity recognition F1:** `2 × precision × recall / (precision + recall)`.
4. **Toponym accuracy:** Correctly selected place IDs divided by the number of eligible annotated mentions; report unresolved/abstention rates separately.
5. **Relation extraction precision, recall, F1:** Exact matching of relation label and grounded arguments.
6. **Geocoding error:** Spatial distance (e.g. median great-circle kilometers) where reference coordinates are meaningful, with clearly defined representative-point conventions.
7. **Operational review:** Fraction of extracted candidate sites requiring human correction, by hazard category and source type.

### Baselines and experimental comparisons

- Gazeteer-only NER versus gazetteer plus pretrained spaCy NER.
- Contextual disambiguation versus trivial fixed-candidate lookup (with abstention tracked).
- Relation rules versus a separately trained and evaluated relation extraction model.
- Small local gazetteer versus a larger authoritative gazetteer, including unseen locations.

Use document-level train/test splits and separate geographic holdouts. Include errors related to ambiguous entities, out-of-gazetteer locations, text negation, rumors, abbreviations, multilingual and code-switched reports, and expressions such as “50 km northwest of city X.” Reproducible results require logging dataset versions and annotation criteria.

## 12. Limitations

- **Limited world coverage:** Only 22 example gazetteer entries. Globally unique names cannot be inferred from local uniqueness.
- **Textual mention vs incident:** The system maps references, not independently confirmed damaged or affected areas.
- **Missing exact footprints:** “North of Miami” and “near a river” cannot be geocoded to an exact event point without extra evidence.
- **Centroid limitations:** Rivers and administrative regions require geometry, not one representative point, in full GIS analyses.
- **Rule-based relation extraction:** Can misinterpret syntax, qualifiers, movement, proximity, or nested clauses.
- **No event verification:** Headlines, hoaxes, hypothetical examples, negation (“no flooding”), and old events may be misinterpreted.
- **Simplified NER and hazards:** The optional off-the-shelf spaCy English model and regex-based hazard classifier are not disaster-domain validated.
- **No real-time data:** The prototype does not monitor news or emergency feeds and never makes automated emergency-response decisions.

## 13. Ethical considerations and responsible deployment

Disaster dashboards can affect public perception and emergency actions. This prototype must not be mistaken for a trusted alert service. Real implementations should (a) retain source and timestamp for every claim, (b) distinguish unverified mentions from official confirmations, (c) preserve unresolved alternatives, (d) support human review, (e) protect precise private locations, (f) avoid misleading map symbology, and (g) evaluate performance across regions, languages, and communities before any deployment.

## 14. Future enhancements

1. Integrate an authoritative geographic gazetteer with robust alternate spellings, multilingual names, and historical administrative records.
2. Train/evaluate domain-tuned transformer NER and entity-linking models using annotated disaster corpora.
3. Add distance and directional reasoning, geospatial geometries, and uncertainty zones using Shapely/GeoPandas.
4. Extract time expressions, event status, source credibility, negation, and uncertainty.
5. Integrate verified situation reports using appropriate permissions and source provenance.
6. Compare methods quantitatively on held-out real datasets and publish a reproducible evaluation.

## 15. Conclusion

The completed DisasterGeo prototype demonstrates a modular and explainable workflow for turning disaster-related natural-language documents into geographical references and GIS-compatible datasets. Its six central stages—preprocessing, geographical entity recognition, toponym resolution/geocoding, relation extraction, structured output, and mapping—are implemented in Python. The system preserves ambiguous names and avoids claiming that geographical references represent exact disaster incidents. The prototype provides a foundation for academic experiments, with the explicit requirement that larger gazetteers, domain-aware NLP, validation data, and human verification be added before operational disaster-management applications.

## References and implementation resources

- spaCy. *Models and Languages.* <https://spacy.io/usage/models>
- Python documentation. *Regular expression operations.* <https://docs.python.org/3/library/re.html>
- Folium documentation. *Folium: Python data, Leaflet.js maps.* <https://python-visualization.github.io/folium/latest/>
- Butler et al. *The GeoJSON Format*, IETF RFC 7946 (2016). <https://www.rfc-editor.org/rfc/rfc7946>
- GeoNames. *Geographical Database.* <https://www.geonames.org/> (potential future gazetteer; the included data is illustrative, not an export from GeoNames)
