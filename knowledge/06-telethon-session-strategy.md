# Telethon Session Strategy (User vs Bot)

**Tags:** `telethon` `telegram` `session` `auth`

## Concept
Use `user_session` when media/channel entity access requires user membership; bot session is not always enough.

## When to use
- Private channels where bot lacks full entity access
- Historical message/file fetch by channel/message ID

## When NOT to use
- Pure bot-only public operations
- When policy forbids user sessions

## Minimal rule
```py
if user_session_exists and user_session_authorized:
    use user session
else:
    fail fast with clear error (or explicit bot fallback if valid for your use case)
```
