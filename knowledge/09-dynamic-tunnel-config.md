# Dynamic Tunnel Base URL

**Tags:** `cloudflare` `tunnel` `configuration` `telegram-webapp`

## Concept
When domain is dynamic (trycloudflare), keep `CINEMA_PUBLIC_BASE_URL` aligned with active tunnel URL.

## When to use
- No fixed domain
- Telegram WebApp button opens dynamic endpoint

## When NOT to use
- Stable production domain with DNS + SSL

## Minimal checklist
- Update env: `CINEMA_PUBLIC_BASE_URL=https://<active-tunnel>`
- Restart app/gateway
- Re-issue WebApp entry from bot
```
docker compose restart app-server web-gateway
```
