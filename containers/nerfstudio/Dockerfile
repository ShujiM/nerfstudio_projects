# Nerfstudio Docker Image (restructured)
# Based on official nerfstudio image with CUDA + PyTorch + COLMAP
FROM ghcr.io/nerfstudio-project/nerfstudio:latest

# Set working directory
WORKDIR /workspace

# Install additional utilities + Docker CLI + GLOMAP build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    htop \
    git \
    ca-certificates \
    curl \
    gnupg \
    ninja-build \
    wget \
    build-essential \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsqlite3-dev \
    libglew-dev \
    libceres-dev \
    libcgal-dev \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Install cmake 3.30 (GLOMAP requires >= 3.28 for FetchContent)
RUN wget -q https://github.com/Kitware/CMake/releases/download/v3.30.1/cmake-3.30.1-linux-x86_64.tar.gz \
    && tar xf cmake-3.30.1-linux-x86_64.tar.gz --strip-components=1 -C /usr/local \
    && rm cmake-3.30.1-linux-x86_64.tar.gz

# Clone GLOMAP
RUN git clone https://github.com/colmap/glomap.git /opt/glomap

# Configure GLOMAP (cmake)
RUN cd /opt/glomap && mkdir build && cd build && \
    cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release \
    -DFETCH_COLMAP=ON -DFETCH_POSELIB=ON

# Build GLOMAP (ninja) - separated to capture exact errors
RUN cd /opt/glomap/build && ninja -j2 2>&1 | tail -100 && ninja install

# Clean up build files
RUN rm -rf /opt/glomap

# Install Streamlit for Web UI + trimesh for PLY→GLB conversion
RUN python3 -m pip install streamlit watchdog trimesh pyglet

# Default command: start interactive bash
CMD ["/bin/bash"]
