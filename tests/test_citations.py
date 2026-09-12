"""Citation payload regressions without model downloads or external services."""
import json
import unittest
from uuid import uuid4

from app.services.citations import build_citations


class CitationTests(unittest.TestCase):
    def test_order_matches_prompt_numbers_and_preserves_multiple_excerpts(self):
        document_id = uuid4()
        context = [
            {"document_id": document_id, "source": "user", "text": "Revenue rose.",
             "metadata": {"filename": "Annual report.pdf", "chunk_id": 0}},
            {"document_id": document_id, "source": "user", "text": "Costs fell.",
             "metadata": {"filename": "Annual report.pdf", "chunk_id": 1}},
            {"document_id": uuid4(), "source": "system", "text": "Sector context.",
             "metadata": {"filename": "Sector report.pdf"}},
        ]
        sources = build_citations(context)
        self.assertEqual([s["citation_id"] for s in sources], [1, 2, 3])
        self.assertEqual(sources[0]["document_id"], str(document_id))
        self.assertEqual(sources[1]["text"], "Costs fell.")
        self.assertEqual(sources[2]["source"], "system")
        self.assertEqual(sources[0]["metadata"]["chunk_id"], "0")
        # This is the JSON roundtrip used by SSE and persisted JSONB metadata.
        self.assertEqual(json.loads(json.dumps(sources, allow_nan=False)), sources)

    def test_missing_filename_does_not_invent_a_title_or_page(self):
        sources = build_citations([
            {"document_id": "abc", "metadata": {"filename": "unknown"}},
            {"text": "Legacy excerpt"},
        ])
        self.assertEqual(sources[0]["filename"], "Document abc")
        self.assertEqual(sources[1]["filename"], "Source 2")
        self.assertNotIn("page", sources[0])

    def test_internal_payload_is_not_exposed(self):
        source = build_citations([{
            "text": "Safe excerpt", "metadata": {
                "filename": "report.pdf", "file_path": "/private/uploads/report.pdf",
                "user_id": "internal-user", "api_key": "test-only",
            },
        }])[0]
        self.assertEqual(set(source["metadata"]), {"filename", "chunk_id"})
        self.assertNotIn("private/uploads", json.dumps(source))

    def test_nonfinite_or_invalid_scores_are_json_safe(self):
        sources = build_citations([{"score": score} for score in [float("nan"), float("inf"), None, "bad"]])
        self.assertEqual([s["score"] for s in sources], [0.0] * 4)
        json.dumps(sources, allow_nan=False)

    def test_no_context_means_no_citations(self):
        self.assertEqual(build_citations([]), [])


if __name__ == "__main__":
    unittest.main()
