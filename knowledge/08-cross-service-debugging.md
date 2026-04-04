# Cross-Service Debugging Pipeline

**Tags:** `debugging` `docker` `gateway` `observability`

## Concept
Trace errors layer-by-layer: `gateway -> app -> upstream`.

## When to use
- UI works but stream fails
- Intermittent 499/500/403

## When NOT to use
- Single-process local app with no proxy/upstream

## Quick commands
```powershell
# Gateway stream status
docker logs --since 10m discordvip-cinema-web-gateway-1

# App errors
docker logs --since 10m discordvip-cinema-app-server-1

# Upstream service (telefilm)
Get-Content D:\telefilm\uvicorn.err.log -Tail 200
```
