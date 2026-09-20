import json
import unittest
from pathlib import Path
from deploy.render_env import render

class ReleaseConfigTests(unittest.TestCase):
    def config(self):
        return dict(DATABASE_URL="postgresql://db", REDIS_URL="redis://redis", QDRANT_URL="https://qdrant", SECRET_KEY="secret", FRONTEND_URL="https://web", DATABASE_SSL=False, GROQ_API_KEY="key")

    def test_literals_and_defaults(self):
        config = self.config()
        config["SECRET_KEY"] = "$literal#hash quotes"
        output = render(json.dumps(config))
        self.assertIn("SECRET_KEY=$literal#hash quotes\n", output)
        self.assertIn("CELERY_BROKER_URL=redis://redis\n", output)
        self.assertIn("DATABASE_SSL=false\n", output)

    def test_rejects_injection(self):
        for char in ("\n", "\r", "\0"):
            config = self.config()
            config["SECRET_KEY"] += char
            with self.assertRaises(ValueError):
                render(json.dumps(config))

    def test_missing_database(self):
        config = self.config()
        del config["DATABASE_URL"]
        with self.assertRaises(ValueError):
            render(json.dumps(config))

    def test_independent_compose_services(self):
        # No dependency can implicitly restart the other service.
        for selected, other in (("api", "worker"), ("worker", "api")):
            text = Path(f"deploy/compose-{selected}.yml").read_text()
            self.assertIn(f"  {selected}:", text)
            self.assertNotIn(f"  {other}:", text)
            self.assertNotIn("depends_on:", text)
            self.assertIn("external: true", text)
