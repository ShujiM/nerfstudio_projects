# 2DGS - 2D Gaussian Splatting
# Geometrically Accurate Radiance Fields
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="${CUDA_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}"

WORKDIR /opt

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    python3-dev \
    libglew-dev \
    libassimp-dev \
    libboost-all-dev \
    libgtk-3-dev \
    libopencv-dev \
    libglfw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set CUDA build environment
ENV FORCE_CUDA=1
ENV TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6;8.9;9.0"
ENV MAX_JOBS=4

# Install Python packages
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install \
    torch==2.0.0+cu118 \
    torchvision==0.15.0+cu118 \
    torchaudio==2.0.0+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# Clone 2DGS repository
RUN git clone --recursive https://github.com/hbb1/2d-gaussian-splatting.git /opt/2dgs

WORKDIR /opt/2dgs

# Install 2DGS dependencies
RUN python3 -m pip install \
    open3d==0.18.0 \
    mediapy==1.1.2 \
    lpips==0.1.4 \
    scikit-image==0.21.0 \
    tqdm==4.66.2 \
    trimesh==4.3.2 \
    plyfile \
    opencv-python \
    matplotlib \
    numpy==1.24.4

# Install diff-surfel-rasterization and simple-knn
RUN cd submodules/diff-surfel-rasterization && \
    python3 -m pip install --no-build-isolation . && \
    cd /opt/2dgs && \
    cd submodules/simple-knn && \
    python3 -m pip install --no-build-isolation .

WORKDIR /workspace

CMD ["/bin/bash"]
