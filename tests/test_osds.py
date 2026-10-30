import unittest
from retrieval import search_osds

class Response:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): pass
    def json(self): return self.payload

class Session:
    def __init__(self, payload): self.payload = payload
    def post(self, url, **kwargs):
        self.request = kwargs
        return Response(self.payload)

class OSDSTests(unittest.TestCase):
    def test_requires_real_endpoint(self):
        with self.assertRaises(ValueError): search_osds("query", "")
    def test_official_passages_keep_corpus_identity(self):
        session = Session({"results": {"passages": ["evidence"], "pes2o IDs": [123]}})
        result = search_osds("query", "http://localhost:9000/search", session=session)
        self.assertEqual(result[0]["corpus_id"], "123")
        self.assertEqual(result[0]["url"], "")
        self.assertEqual(session.request["json"]["domains"], "pes2o")
    def test_mismatched_ids_fail_instead_of_misattributing(self):
        session = Session({"results": {"passages": ["evidence"], "pes2o IDs": []}})
        with self.assertRaises(ValueError):
            search_osds("query", "http://localhost:9000/search", session=session)
    def test_unsupported_year_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            search_osds("query", "http://localhost:9000/search", "2026")

if __name__ == "__main__": unittest.main()
