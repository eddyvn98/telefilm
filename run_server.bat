@echo off
set PYTHONPATH=%cd%
uvicorn backend.main:app --reload --host 0.0.0.0 --port 9999
pause
