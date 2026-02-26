@echo off
REM ============================================
REM 3DGS Studio Docker Helper Script (Windows)
REM ============================================

if "%1"=="build" (
    echo Building all Docker images...
    docker compose build
    goto :eof
)

if "%1"=="build-ns" (
    echo Building Nerfstudio image only...
    docker compose build nerfstudio
    goto :eof
)

if "%1"=="build-sugar" (
    echo Building SuGaR image...
    docker compose build sugar
    goto :eof
)

if "%1"=="build-2dgs" (
    echo Building 2DGS image...
    docker compose build 2dgs
    goto :eof
)

if "%1"=="up" (
    echo Starting all containers...
    docker compose --profile all up -d
    echo Containers started.
    echo    - Web UI: http://localhost:8501
    echo    - Viewer: http://localhost:7007
    goto :eof
)

if "%1"=="up-ns" (
    echo Starting Nerfstudio container only...
    docker compose up -d nerfstudio
    goto :eof
)

if "%1"=="up-sugar" (
    echo Starting SuGaR container...
    docker compose --profile sugar up -d sugar
    goto :eof
)

if "%1"=="up-2dgs" (
    echo Starting 2DGS container...
    docker compose --profile 2dgs up -d 2dgs
    goto :eof
)

if "%1"=="web" (
    echo Starting Web UI...
    docker compose exec nerfstudio python3 -m streamlit run app.py --server.address=0.0.0.0
    goto :eof
)

if "%1"=="shell" (
    echo Opening shell in Nerfstudio container...
    docker compose exec nerfstudio bash
    goto :eof
)

if "%1"=="shell-sugar" (
    echo Opening shell in SuGaR container...
    docker compose exec sugar bash
    goto :eof
)

if "%1"=="shell-2dgs" (
    echo Opening shell in 2DGS container...
    docker compose exec 2dgs bash
    goto :eof
)

if "%1"=="gpu" (
    echo Checking GPU status...
    docker compose exec nerfstudio nvidia-smi
    goto :eof
)

if "%1"=="down" (
    echo Stopping all containers...
    docker compose down
    goto :eof
)

if "%1"=="logs" (
    docker compose logs -f
    goto :eof
)

if "%1"=="status" (
    docker compose ps
    goto :eof
)

echo 3DGS Studio Docker Helper
echo =========================
echo Usage: start.bat ^<command^>
echo.
echo Commands:
echo   build        - Build ALL Docker images
echo   build-ns     - Build Nerfstudio image only
echo   build-sugar  - Build SuGaR image
echo   build-2dgs   - Build 2DGS image
echo   up           - Start ALL containers
echo   up-ns        - Start Nerfstudio only
echo   up-sugar     - Start SuGaR container
echo   up-2dgs      - Start 2DGS container
echo   web          - Start Web UI (http://localhost:8501)
echo   shell        - Open Nerfstudio shell
echo   shell-sugar  - Open SuGaR shell
echo   shell-2dgs   - Open 2DGS shell
echo   gpu          - Check GPU status
echo   down         - Stop all containers
echo   logs         - View container logs
echo   status       - Show container status
echo.
echo Quick Start:
echo   1. start.bat build-ns    (first time: build nerfstudio)
echo   2. start.bat up-ns       (start nerfstudio container)
echo   3. start.bat web         (start web UI)
echo   4. start.bat build-sugar (when ready for SuGaR)
echo   5. start.bat build-2dgs  (when ready for 2DGS)
