import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from backend.core import paths, security
from backend.core.limits import ConcurrencyLimiter, SlidingWindowLimiter


class SecurityTokenTests(unittest.TestCase):
    def setUp(self):
        self.old_secret = security.settings.SECRET_KEY
        self.old_bot = security.settings.BOT_TOKEN
        self.old_allowed = security.settings.ALLOWED_TELEGRAM_IDS
        security.settings.SECRET_KEY = "test-secret-key-for-unit-tests-123456"
        security.settings.BOT_TOKEN = "test-bot-token"
        security.settings.ALLOWED_TELEGRAM_IDS = "123,456"

    def tearDown(self):
        security.settings.SECRET_KEY = self.old_secret
        security.settings.BOT_TOKEN = self.old_bot
        security.settings.ALLOWED_TELEGRAM_IDS = self.old_allowed

    def test_session_round_trip(self):
        token = security.create_session_token("123")
        data = security.validate_session_token(token)
        self.assertEqual(data["id"], "123")
        self.assertTrue(data["_session_id"])

    def test_tampered_session_is_rejected(self):
        token = security.create_session_token("123")
        with self.assertRaises(HTTPException):
            security.validate_session_token(token + "x")

    def test_stream_token_is_bound_to_user_and_session(self):
        token = security.create_stream_token(7, "123", "session-a")
        data = security.validate_stream_token(token, 7, "123", "session-a")
        self.assertEqual(data["user_id"], "123")
        with self.assertRaises(HTTPException):
            security.validate_stream_token(token, 7, "456", "session-a")
        with self.assertRaises(HTTPException):
            security.validate_stream_token(token, 7, "123", "session-b")


class PathSafetyTests(unittest.TestCase):
    def setUp(self):
        self.old_roots = paths.settings.UPLOAD_ROOTS
        self.temp = tempfile.TemporaryDirectory()
        paths.settings.UPLOAD_ROOTS = self.temp.name

    def tearDown(self):
        paths.settings.UPLOAD_ROOTS = self.old_roots
        self.temp.cleanup()

    def test_allowed_upload_root(self):
        child = Path(self.temp.name) / "movie.mp4"
        child.write_bytes(b"test")
        self.assertTrue(paths.is_upload_path_allowed(str(child)))

    def test_outside_upload_root_is_rejected(self):
        outside = Path(self.temp.name).parent / "outside.mp4"
        self.assertFalse(paths.is_upload_path_allowed(str(outside)))

    def test_media_traversal_is_rejected(self):
        with self.assertRaises(HTTPException):
            paths.resolve_media_file("thumbnails", "../requirements.txt")


class LimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_sliding_window_limit(self):
        limiter = SlidingWindowLimiter(2, 60)
        await limiter.check("user")
        await limiter.check("user")
        with self.assertRaises(HTTPException):
            await limiter.check("user")

    async def test_concurrency_limit_releases(self):
        limiter = ConcurrencyLimiter(1)
        await limiter.acquire("user")
        with self.assertRaises(HTTPException):
            await limiter.acquire("user")
        await limiter.release("user")
        await limiter.acquire("user")
        await limiter.release("user")


if __name__ == "__main__":
    unittest.main()
