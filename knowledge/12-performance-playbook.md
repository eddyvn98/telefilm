# Performance Playbook (Streaming WebApp)

**Tags:** `performance` `streaming` `nginx` `telethon`

## Common bottlenecks
- Reverse proxy buffering to disk
- Cold first stream request
- DB pool contention in upstream service
- Reconnect churn in Telegram client

## Practical optimizations
- Stream endpoint with buffering off (Nginx)
- Lazy-load lists (first N items)
- Query metadata then close DB session before stream
- Reconnect + single retry for Telegram client

## Quick validation metrics
- Stream endpoint returns `206`
- `content-range` present
- No repeated `500` under sequential playback
- `499` rate drops after proxy tuning
