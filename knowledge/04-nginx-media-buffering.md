# Nginx for Media Streaming

**Tags:** `nginx` `streaming` `devops` `performance`

## Concept
Disable buffering for media endpoints to reduce temp-file bottlenecks.

## When to use
- Reverse proxying large video streams
- Clients show delayed start or repeated aborts

## When NOT to use
- Small JSON APIs (buffering often helpful)

## Minimal config
```nginx
location ~ ^/api/cinema/stream/ {
  proxy_pass http://app-server:3000;
  proxy_buffering off;
  proxy_request_buffering off;
  proxy_max_temp_file_size 0;
  proxy_read_timeout 3600s;
  proxy_send_timeout 3600s;
}
```
