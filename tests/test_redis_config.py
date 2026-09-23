import os
import subprocess
import sys
import unittest

from app.core.config import Settings


class RedisTLSConfigTests(unittest.TestCase):
    def _settings(self, redis_url: str) -> Settings:
        return Settings(
            DATABASE_URL="postgresql://db",
            REDIS_URL=redis_url,
            CELERY_BROKER_URL=redis_url,
            CELERY_RESULT_BACKEND=redis_url,
            QDRANT_URL="https://qdrant",
            SECRET_KEY="secret",
        )

    def test_secure_redis_urls_require_certificate_validation(self):
        settings = self._settings("rediss://user:password@redis.example.com:6380/0")

        self.assertTrue(settings.REDIS_URL.endswith("?ssl_cert_reqs=required"))
        self.assertTrue(settings.CELERY_BROKER_URL.endswith("?ssl_cert_reqs=required"))
        self.assertTrue(settings.CELERY_RESULT_BACKEND.endswith("?ssl_cert_reqs=required"))

    def test_existing_secure_redis_options_are_preserved(self):
        settings = self._settings(
            "rediss://redis.example.com/0?socket_timeout=5&ssl_cert_reqs=optional"
        )

        self.assertIn("socket_timeout=5", settings.CELERY_BROKER_URL)
        self.assertIn("ssl_cert_reqs=optional", settings.CELERY_BROKER_URL)

    def test_plain_redis_url_is_unchanged(self):
        url = "redis://localhost:6379/0"

        settings = self._settings(url)

        self.assertEqual(settings.REDIS_URL, url)
        self.assertEqual(settings.CELERY_BROKER_URL, url)
        self.assertEqual(settings.CELERY_RESULT_BACKEND, url)

    def test_celery_keeps_secure_redis_tls_query_from_environment(self):
        secure_url = "rediss://user:password@redis.example.com:6380/0"
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "postgresql://db",
                "REDIS_URL": secure_url,
                "CELERY_BROKER_URL": secure_url,
                "CELERY_RESULT_BACKEND": secure_url,
                "QDRANT_URL": "https://qdrant",
                "SECRET_KEY": "secret",
            }
        )
        command = (
            "from urllib.parse import urlsplit, parse_qsl; "
            "from app.worker.celery_app import celery_app; "
            "print(dict(parse_qsl(urlsplit(celery_app.conf.broker_url).query))"
            ".get('ssl_cert_reqs')); "
            "print(dict(parse_qsl(urlsplit(celery_app.conf.result_backend).query))"
            ".get('ssl_cert_reqs'))"
        )

        result = subprocess.run(
            [sys.executable, "-c", command],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.stdout.splitlines(), ["required", "required"])


if __name__ == "__main__":
    unittest.main()
