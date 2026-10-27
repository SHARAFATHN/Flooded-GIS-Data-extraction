"""CLI for disaster-focused geographical information extraction.

Usage:
    python main.py --input data/reports.csv --outdir outputs
    python main.py --input data/reports.csv --use-spacy
"""

import argparse
import csv
from pathlib import Path

from disaster_geo.pipeline import DisasterGeoPipeline
from disaster_geo.outputs import write_outputs

ROOT = Path(__file__).resolve().parent


def read_reports(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {"report_id", "text"}.issubset(reader.fieldnames):
            raise ValueError("Input CSV needs at least 'report_id' and 'text' columns")
        return [r for r in reader if (r.get("text") or "").strip()]


def main():
    parser = argparse.ArgumentParser(description="Extract disaster-related geographic references.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "reports.csv")
    parser.add_argument("--gazetteer", type=Path, default=ROOT / "data" / "gazetteer.json")
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs")
    parser.add_argument("--use-spacy", action="store_true",
                        help="Use spaCy NER for extra location candidates if en_core_web_sm is installed")
    parser.add_argument("--no-map", action="store_true", help="Skip optional HTML map")
    args = parser.parse_args()

    pipe = DisasterGeoPipeline(args.gazetteer, use_spacy=args.use_spacy)
    if args.use_spacy and pipe.nlp is None:
        print("spaCy model missing; continuing with the offline gazetteer. "
              "To enable: python -m spacy download en_core_web_sm")
    reports = read_reports(args.input)
    results = [pipe.process(r) for r in reports]
    summary = write_outputs(results, args.outdir, make_map=not args.no_map)

    print(f"Input reports: {summary['reports_processed']}")
    print(f"NER mode: {pipe.ner_mode}")
    print(f"Resolved place mentions: {summary['resolved_place_mentions']}")
    print(f"Unresolved mentions: {summary['unresolved_place_mentions']}")
    print(f"Spatial relations extracted: {summary['spatial_relations_extracted']}")
    print(f"Outputs: {args.outdir.resolve()}")
    if summary["map_created"]:
        print(f"Interactive map: {(args.outdir / 'map.html').resolve()}")
    print("WARNING: These are place references in synthetic text, not live verified incidents.")


if __name__ == "__main__":
    main()
