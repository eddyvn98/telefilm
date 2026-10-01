# Telefilm security deployment

This repository is designed to run behind Cloudflare Tunnel with Uvicorn bound to `127.0.0.1:9999`.

## Required .env settings

Copy the new keys from `.env.example` into the real `.env` file before restarting the application.

- `SECRET_KEY`: generate a random value of at least 32 bytes.
  - Example: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `ALLOWED_TELEGRAM_IDS`: users allowed to open the application.
- `ADMIN_TELEGRAM_IDS`: users allowed to call remote admin APIs.
- `UPLOAD_ROOTS`: comma-separated absolute roots that admin scan/upload may access.
- Keep `SESSION_COOKIE_SECURE=true` and `SESSION_COOKIE_PARTITIONED=true` for the HTTPS Telegram Web / Cloudflare deployment.

If `SECRET_KEY` is missing or looks like an old weak default, the server temporarily falls back to `BOT_TOKEN` for signing. A separate random `SECRET_KEY` is still strongly preferred.

## Upgrade steps

1. Pull the latest `main`.
2. Update the production `.env` with the settings above.
3. Run `python -m pip install -r requirements.txt`.
4. Ensure `ffmpeg` and `cloudflared` are available on PATH (or in the existing expected location).
5. Restart with `start_project.bat` or `run_server.bat`.

The server now listens only on localhost. Do not expose port 9999 directly through Windows Firewall or router port forwarding; Cloudflare Tunnel should be the public entrypoint.

## Authentication model

Telegram `initData` is accepted only by `POST /api/auth/login`. After validation the server creates a Secure, HttpOnly, partitioned session cookie. Catalog, history, media, admin and playback APIs require that session.

Generated thumbnails and backdrops are no longer public static files. Their existing URLs remain compatible, but requests now pass through an authenticated route.

Playback URLs contain a short-lived signed token bound to the current server session. The token contains a hash binding rather than the Telegram ID or raw session ID.

## Database upgrade

Startup enables SQLite foreign keys, WAL, a busy timeout, and a unique user/movie watch-history index. If old duplicate history rows exist, startup keeps the newest row per user/movie before creating the index.

Keep a normal backup of `telegram_film.db` before the first production restart after this upgrade.

## Upload and cleanup behavior

- Scan paths and per-file real paths must remain inside `UPLOAD_ROOTS`; symlink escapes are rejected.
- FFmpeg thumbnail work runs off the async event loop and has a timeout.
- `UPLOAD_SPEED_LIMIT_MB` is enforced by the uploader when greater than zero.
- If Telegram upload succeeds but DB indexing fails, the newly created Telegram message is removed as compensation.
- Delete/duplicate cleanup commits the DB removal first, then performs Telegram/local-file cleanup. A remote cleanup failure therefore leaves an orphan remote message rather than a broken movie row.

## CI gate

Pull requests and pushes to `main` run:
- Python compile checks
- JavaScript syntax checks
- pinned dependency installation
- `pip check`
- backend import
- unit tests for sessions, stream-token binding, path traversal, rate and concurrency limits
- `pip-audit`
