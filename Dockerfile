# Nerfstudio Docker Image
# Based on official nerfstudio image with CUDA + PyTorch + COLMAP
FROM ghcr.io/nerfstudio-project/nerfstudio:latest

# Set working directory
WORKDIR /workspace

# Install additional utilities if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Steamlit for Web UI
RUN pip install streamlit watchdog

# Default command: start interactive bash
CMD ["/bin/bash"]
