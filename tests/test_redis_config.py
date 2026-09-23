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


if __name__ == "__main__":
    unittest.main()
