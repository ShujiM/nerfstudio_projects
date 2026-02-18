#!/bin/bash
# ============================================
# Nerfstudio Docker Helper Script
# ============================================

set -e

case "${1}" in
  build)
    echo "🔨 Building Nerfstudio Docker image..."
    docker compose build
    ;;
  up)
    echo "🚀 Starting Nerfstudio container..."
    docker compose up -d
    echo "✅ Container started."
    echo "   - Web UI: http://localhost:8501"
    echo "   - Viewer: http://localhost:7007"
    ;;
  web)
    echo "🌐 Starting Web UI..."
    docker compose exec nerfstudio streamlit run app.py --server.address=0.0.0.0
    ;;
  shell)
    echo "🐚 Opening shell in Nerfstudio container..."
    docker compose exec nerfstudio bash
    ;;
  train)
    if [ -z "${2}" ]; then
      echo "Usage: ./start.sh train <method> [options]"
      echo "Example: ./start.sh train splatfacto --data /workspace/data/nerfstudio/poster"
      exit 1
    fi
    echo "🏋️ Starting training with: ns-train ${@:2}"
    docker compose exec nerfstudio ns-train "${@:2}"
    ;;
  process)
    if [ -z "${2}" ]; then
      echo "Usage: ./start.sh process <path-to-images>"
      echo "Example: ./start.sh process /workspace/data/nerfstudio/poster/images"
      exit 1
    fi
    echo "📸 Processing data: ns-process-data images --data ${2} --output-dir ${3:-/workspace/data/processed}"
    docker compose exec nerfstudio ns-process-data images --data "${2}" --output-dir "${3:-/workspace/data/processed}"
    ;;
  export)
    if [ -z "${2}" ]; then
      echo "Usage: ./start.sh export <config-path>"
      exit 1
    fi
    echo "📦 Exporting: ns-export ${@:2}"
    docker compose exec nerfstudio ns-export "${@:2}"
    ;;
  gpu)
    echo "🖥️ Checking GPU status..."
    docker compose exec nerfstudio nvidia-smi
    ;;
  down)
    echo "⏹️ Stopping Nerfstudio container..."
    docker compose down
    ;;
  logs)
    docker compose logs -f nerfstudio
    ;;
  *)
    echo "Nerfstudio Docker Helper"
    echo "========================"
    echo "Usage: ./start.sh <command>"
    echo ""
    echo "Commands:"
    echo "  build    - Build Docker image"
    echo "  up       - Start container in background"
    echo "  shell    - Open bash shell in container"
    echo "  train    - Run ns-train (e.g., ./start.sh train splatfacto --data ...)"
    echo "  process  - Run ns-process-data"
    echo "  export   - Run ns-export"
    echo "  gpu      - Check GPU status (nvidia-smi)"
    echo "  down     - Stop container"
    echo "  logs     - View container logs"
    ;;
esac
