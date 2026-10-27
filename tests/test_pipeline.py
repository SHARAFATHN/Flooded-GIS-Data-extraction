"""Offline, deterministic end-to-end checks: python -m unittest discover -s tests -v"""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from disaster_geo.pipeline import DisasterGeoPipeline, classify_hazard
from disaster_geo.preprocessing import clean_text, split_sentences
from disaster_geo.outputs import write_outputs
from main import read_reports

ROOT = Path(__file__).resolve().parents[1]


class DisasterGeoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = DisasterGeoPipeline(ROOT / "data" / "gazetteer.json")

    def report(self, text):
        return self.pipeline.process({
            "report_id": "TEST", "text": text, "source": "unit_test", "published_date": "2026-01-01",
        })

    def test_preprocessing_and_sentences(self):
        clean = clean_text(" Flooding\n in   Atlanta.  Roads near a river! ")
        self.assertEqual(clean, "Flooding in Atlanta. Roads near a river!")
        sentences = split_sentences(clean)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(clean[sentences[1].start:sentences[1].end], "Roads near a river!")

    def test_ner_geocoding_and_spatial_relations(self):
        r = self.report("Flooding in Atlanta, Georgia. Roads near the Chattahoochee River were closed.")
        locs = {l["mention"]: l for l in r["locations"]}
        self.assertEqual(locs["Atlanta"]["place_id"], "us_atlanta")
        self.assertEqual(locs["Georgia"]["place_id"], "us_georgia")
        self.assertAlmostEqual(locs["Atlanta"]["latitude"], 33.749)
        self.assertEqual(locs["Chattahoochee River"]["kind"], "river")
        self.assertTrue(any(x["relation"] == "near" and x["to_place"] == "Chattahoochee River"
                            for x in r["spatial_relations"]))

    def test_disambiguation_with_explicit_region(self):
        r = self.report("Flooding in Paris, Texas, was reported.")
        paris = next(l for l in r["locations"] if l["mention"] == "Paris")
        self.assertEqual(paris["place_id"], "us_paris_tx")
        self.assertEqual(paris["resolution_method"], "contextual_gazetteer_resolution")

    def test_disambiguation_using_nearby_river(self):
        r = self.report("Residents of Paris reported floods near the Seine River.")
        paris = next(l for l in r["locations"] if l["mention"] == "Paris")
        self.assertEqual(paris["place_id"], "fr_paris")
        self.assertEqual(r["hazard"], "flood")

    def test_unresolved_toponym_is_not_guessed(self):
        r = self.report("Flooding affected Springfield.")
        self.assertEqual(r["locations"][0]["status"], "ambiguous")
        self.assertIsNone(r["locations"][0]["latitude"])

    def test_north_of_is_a_relation_not_event_coordinates(self):
        r = self.report("A wildfire started north of Miami, Florida.")
        self.assertEqual(r["hazard"], "wildfire")
        rel = next(x for x in r["spatial_relations"] if x["relation"] == "north_of")
        self.assertIsNone(rel["from_place_id"])
        self.assertEqual(rel["to_place_id"], "us_miami")

    def test_hazard_classifier(self):
        self.assertEqual(classify_hazard("Storm surge affected Tampa"), "storm")
        self.assertEqual(classify_hazard("An earthquake hit the region"), "earthquake")

    def test_export_formats(self):
        results = [self.report("Flooding in Atlanta, Georgia."),
                   self.report("Flooding affected Springfield.")]
        with tempfile.TemporaryDirectory() as directory:
            summary = write_outputs(results, directory, make_map=False)
            out = Path(directory)
            geojson = json.loads((out / "locations.geojson").read_text())
            self.assertEqual(geojson["type"], "FeatureCollection")
            self.assertEqual(geojson["features"][0]["geometry"]["coordinates"], [-84.388, 33.749])
            self.assertEqual(summary["unresolved_place_mentions"], 1)
            with (out / "locations.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertTrue((out / "relations.csv").exists())
            self.assertTrue((out / "results.json").exists())

    def test_csv_input_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.csv"
            path.write_text("id,body\nA,Some text\n")
            with self.assertRaises(ValueError):
                read_reports(path)


if __name__ == "__main__":
    unittest.main()
