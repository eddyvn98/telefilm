@echo off
set PYTHONPATH=%cd%
uvicorn backend.main:app --host 127.0.0.1 --port 9999 --no-server-header
pause
