# Signed Playback Token

**Tags:** `security` `streaming` `token` `anti-share`

## Concept
Generate short-lived, user-bound token for each playback URL.

## When to use
- Prevent direct link sharing
- Enforce replay/TTL control

## When NOT to use
- Public/open media CDN
- Long-lived static signed URLs requirements

## Minimal pattern
```ts
const token = sign({ itemId, userId, kind: 'full', exp: now + 60 });
const url = `/api/cinema/stream/${itemId}/full?token=${encodeURIComponent(token)}`;

// On request:
const payload = verify(token);
if (payload.userId !== currentUserId || payload.exp < now) throw new Error('Denied');
```
