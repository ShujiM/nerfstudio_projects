#!/bin/bash
# ============================================
# 3DGS Studio Docker Helper Script (Linux/Mac)
# ============================================

set -e

case "${1}" in
  build)
    echo "Building all Docker images..."
    docker compose build
    ;;
  build-ns)
    echo "Building Nerfstudio image only..."
    docker compose build nerfstudio
    ;;
  build-sugar)
    echo "Building SuGaR image..."
    docker compose build sugar
    ;;
  build-2dgs)
    echo "Building 2DGS image..."
    docker compose build 2dgs
    ;;
  up)
    echo "Starting all containers..."
    docker compose --profile all up -d
    echo "Containers started."
    echo "   - Web UI: http://localhost:8501"
    echo "   - Viewer: http://localhost:7007"
    ;;
  up-ns)
    echo "Starting Nerfstudio container only..."
    docker compose up -d nerfstudio
    ;;
  up-sugar)
    echo "Starting SuGaR container..."
    docker compose --profile sugar up -d sugar
    ;;
  up-2dgs)
    echo "Starting 2DGS container..."
    docker compose --profile 2dgs up -d 2dgs
    ;;
  web)
    echo "Starting Web UI..."
    docker compose exec nerfstudio python3 -m streamlit run app.py --server.address=0.0.0.0
    ;;
  shell)
    echo "Opening shell in Nerfstudio container..."
    docker compose exec nerfstudio bash
    ;;
  shell-sugar)
    echo "Opening shell in SuGaR container..."
    docker compose exec sugar bash
    ;;
  shell-2dgs)
    echo "Opening shell in 2DGS container..."
    docker compose exec 2dgs bash
    ;;
  gpu)
    echo "Checking GPU status..."
    docker compose exec nerfstudio nvidia-smi
    ;;
  down)
    echo "Stopping all containers..."
    docker compose down
    ;;
  logs)
    docker compose logs -f
    ;;
  status)
    docker compose ps
    ;;
  *)
    echo "3DGS Studio Docker Helper"
    echo "========================="
    echo "Usage: ./start.sh <command>"
    echo ""
    echo "Commands:"
    echo "  build        - Build ALL Docker images"
    echo "  build-ns     - Build Nerfstudio image only"
    echo "  build-sugar  - Build SuGaR image"
    echo "  build-2dgs   - Build 2DGS image"
    echo "  up           - Start ALL containers"
    echo "  up-ns        - Start Nerfstudio only"
    echo "  up-sugar     - Start SuGaR container"
    echo "  up-2dgs      - Start 2DGS container"
    echo "  web          - Start Web UI (http://localhost:8501)"
    echo "  shell        - Open Nerfstudio shell"
    echo "  shell-sugar  - Open SuGaR shell"
    echo "  shell-2dgs   - Open 2DGS shell"
    echo "  gpu          - Check GPU status"
    echo "  down         - Stop all containers"
    echo "  logs         - View container logs"
    echo "  status       - Show container status"
    echo ""
    echo "Quick Start:"
    echo "  1. ./start.sh build-ns    (first time: build nerfstudio)"
    echo "  2. ./start.sh up-ns       (start nerfstudio container)"
    echo "  3. ./start.sh web         (start web UI)"
    echo "  4. ./start.sh build-sugar (when ready for SuGaR)"
    echo "  5. ./start.sh build-2dgs  (when ready for 2DGS)"
    ;;
esac
