# VIP WebApp Gating

**Tags:** `telegram` `webapp` `auth` `vip` `access-control`

## Concept
Only VIP users can open and use web cinema routes.

## When to use
- Paid/private content
- You need hard server-side access checks

## When NOT to use
- Public catalog pages
- Marketing pages that must be indexable/shareable

## Minimal pattern
```ts
app.get('/api/cinema/session/me', (req, res) => {
  const session = requireVip(req); // throws or returns null
  if (!session) return res.status(403).json({ error: 'VIP required' });
  res.json({ isVip: true, expiresAt: session.expiresAt });
});
```
