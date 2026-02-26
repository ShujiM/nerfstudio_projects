# SuGaR - Surface-Aligned Gaussian Splatting
# Mesh extraction from 3D Gaussian Splatting
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
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
ENV FORCE_CUDA=1
ENV TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6;8.9;9.0"
ENV MAX_JOBS=4

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    torchaudio==2.0.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# Install PyTorch3D from prebuilt wheel (avoids torch import error during source build)
RUN python3 -m pip install --no-build-isolation \
    "git+https://github.com/facebookresearch/pytorch3d.git@stable"

# Clone SuGaR repository
RUN git clone --recursive https://github.com/Anttwo/SuGaR.git /opt/SuGaR

WORKDIR /opt/SuGaR

# Install SuGaR dependencies
RUN python3 -m pip install \
    plyfile \
    open3d \
    trimesh \
    pyglet \
    rich \
    opencv-python \
    lpips \
    scikit-image \
    matplotlib \
    plotly \
    numpy==1.24.4

# Install Gaussian Splatting submodule rasterizer
RUN cd gaussian_splatting/submodules/diff-gaussian-rasterization && \
    python3 -m pip install --no-build-isolation . && \
    cd /opt/SuGaR && \
    cd gaussian_splatting/submodules/simple-knn && \
    python3 -m pip install --no-build-isolation .

WORKDIR /workspace

CMD ["/bin/bash"]
