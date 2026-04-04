# Anti-Patterns Checklist

**Tags:** `anti-patterns` `quality` `security` `streaming`

## What NOT to do
- Keep auth, stream, HTML, and business logic in one giant file
- Hold DB session open during long streaming response
- Use interactive login in service runtime
- Silent fallback from user session to bot session without capability check
- Use default proxy buffering for large video streams

## Red flags
- Many `499` in gateway logs
- `QueuePool limit reached` in upstream logs
- `Cannot send requests while disconnected`
- `EOF when reading a line` inside server process
