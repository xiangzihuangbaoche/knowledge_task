import unittest
from retrieval import search
from engine import synthesize

class FakeResponse:
    def raise_for_status(self): pass
    def json(self):
        return {"data": [
            {"paperId": "1", "title": "A", "abstract": "Evidence", "year": 2026},
            {"paperId": "1", "title": "A", "abstract": "Evidence"},
            {"paperId": "2", "title": "B", "abstract": None}]}

class FakeSession:
    def get(self, url, **kwargs):
        self.kwargs = kwargs
        return FakeResponse()

class RetrievalTests(unittest.TestCase):
    def test_missing_abstract_and_duplicates_are_excluded(self):
        session = FakeSession()
        results = search("query", year="2025-2026", session=session)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["citation_counts"], 0)
        self.assertEqual(session.kwargs["params"]["year"], "2025-2026")
        self.assertEqual(session.kwargs["timeout"], 45)
    def test_key_is_header_only(self):
        session = FakeSession()
        search("query", key="example", session=session)
        self.assertEqual(session.kwargs["headers"]["x-api-key"], "example")
        self.assertNotIn("example", str(session.kwargs["params"]))
    def test_no_evidence_prevents_generation(self):
        with self.assertRaises(ValueError):
            synthesize("question", [])
if __name__ == "__main__":
    unittest.main()
