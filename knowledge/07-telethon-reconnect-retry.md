# Telethon Reconnect & Retry

**Tags:** `telethon` `resilience` `retry` `network`

## Concept
Reconnect before critical calls; retry once for transient disconnect.

## When to use
- Long-running service with intermittent Telegram disconnects

## When NOT to use
- Stateless short scripts
- Fail-fast workflows where retry is harmful

## Minimal pattern
```py
await client.connect()
if not client.is_connected():
    raise ConnectionError('reconnect failed')

try:
    msg = await client.get_messages(channel_id, ids=message_id)
except ConnectionError:
    await client.connect()
    msg = await client.get_messages(channel_id, ids=message_id)
```
