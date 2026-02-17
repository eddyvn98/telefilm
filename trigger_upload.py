import httpx
path = r"H:\bestpretty\Processed\ADN-057 Tôi muốn được yêu bởi bạn. Ishihara Rina - Miss_highlight.mp4"
try:
    r = httpx.post('http://127.0.0.1:9999/api/admin/upload/scan', json={'path': path}, timeout=30)
    print(r.status_code)
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
