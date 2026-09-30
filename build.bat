@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1 || (
    echo [-] python was not found. Catalog rebuild skipped.
    exit /b 0
)
if exist tools\build_catalog.py (
    python tools\build_catalog.py
)
exit /b 0
