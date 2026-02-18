@echo off
REM ============================================
REM Nerfstudio Docker Helper Script (Windows)
REM ============================================

if "%1"=="build" (
    echo Building Nerfstudio Docker image...
    docker compose build
    goto :eof
)

if "%1"=="up" (
    echo Starting Nerfstudio container...
    docker compose up -d
    echo Container started. Use 'docker exec -it nerfstudio bash' to enter.
    goto :eof
)

if "%1"=="shell" (
    echo Opening shell in Nerfstudio container...
    docker compose exec nerfstudio bash
    goto :eof
)

if "%1"=="gpu" (
    echo Checking GPU status...
    docker compose exec nerfstudio nvidia-smi
    goto :eof
)

if "%1"=="down" (
    echo Stopping Nerfstudio container...
    docker compose down
    goto :eof
)

if "%1"=="logs" (
    docker compose logs -f nerfstudio
    goto :eof
)

echo Nerfstudio Docker Helper
echo ========================
echo Usage: start.bat ^<command^>
echo.
echo Commands:
echo   build  - Build Docker image
echo   up     - Start container in background
echo   shell  - Open bash shell in container
echo   gpu    - Check GPU status (nvidia-smi)
echo   down   - Stop container
echo   logs   - View container logs
echo.
echo For training/processing, use shell and run commands interactively.
