# Range-Aware Stream Proxy

**Tags:** `streaming` `http-range` `proxy` `video`

## Concept
Proxy video while preserving `Range` behavior for seek/resume.

## When to use
- Browser/video player requests partial content
- Upstream media source must stay hidden

## When NOT to use
- Small file downloads only
- No seeking needed

## Minimal pattern
```ts
const upstreamHeaders: Record<string, string> = {};
if (req.headers.range) upstreamHeaders.range = String(req.headers.range);

const upstream = await fetch(upstreamUrl, { headers: upstreamHeaders });
res.status(upstream.status);
for (const h of ['content-type','content-length','content-range','accept-ranges']) {
  const v = upstream.headers.get(h);
  if (v) res.setHeader(h, v);
}
Readable.fromWeb(upstream.body as any).pipe(res);
```
