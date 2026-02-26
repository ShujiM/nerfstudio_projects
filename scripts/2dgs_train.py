#!/usr/bin/env python3
"""
2DGS Training Pipeline Script
Runs inside the 2DGS Docker container.
Pipeline: Train 2DGS → Extract mesh → Export PLY

Usage:
  python3 2dgs_train.py --data /workspace/data/nerfstudio/<project> \
                        --output /workspace/outputs/<project>/2dgs
"""

import argparse
import os
import sys
import subprocess


def run_cmd(cmd, desc=""):
    """Run a command and stream output."""
    print(f"\n{'='*60}")
    print(f"[2DGS] {desc}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in process.stdout:
        print(line, end='')
    process.wait()

    if process.returncode != 0:
        print(f"\n[ERROR] Command failed with return code {process.returncode}")
        return False
    return True


def prepare_data(data_path, output_path):
    """
    Prepare data directory for 2DGS training.
    2DGS expects COLMAP-style directory structure.
    """
    colmap_sparse = os.path.join(data_path, "colmap", "sparse", "0")
    if not os.path.exists(colmap_sparse):
        print(f"[ERROR] COLMAP sparse data not found at: {colmap_sparse}")
        return False

    os.makedirs(output_path, exist_ok=True)

    # Symlink images
    src_images = os.path.join(data_path, "images")
    dst_images = os.path.join(output_path, "images")
    if not os.path.exists(dst_images):
        os.symlink(src_images, dst_images)

    # Symlink sparse
    src_sparse = os.path.join(data_path, "colmap", "sparse")
    dst_sparse = os.path.join(output_path, "sparse")
    if not os.path.exists(dst_sparse):
        os.symlink(src_sparse, dst_sparse)

    return True


def main():
    parser = argparse.ArgumentParser(description="2DGS Training Pipeline")
    parser.add_argument("--data", required=True, help="Path to nerfstudio processed data")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--iterations", type=int, default=30000,
                        help="Training iterations (default: 30000)")
    parser.add_argument("--depth-ratio", type=float, default=0.0,
                        help="Depth ratio for regularization (default: 0.0)")
    parser.add_argument("--lambda-normal", type=float, default=0.05,
                        help="Normal consistency loss weight (default: 0.05)")
    args = parser.parse_args()

    dgs_dir = "/opt/2dgs"

    # Prepare data
    scene_path = os.path.join(args.output, "scene")
    if not prepare_data(args.data, scene_path):
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    model_output = os.path.join(args.output, "model")

    # Step 1: 2DGS Training
    print("\n" + "="*60)
    print("[2DGS Pipeline] Step 1/2: 2DGS Training")
    print("="*60)

    train_cmd = [
        "python3", os.path.join(dgs_dir, "train.py"),
        "-s", scene_path,
        "-m", model_output,
        "--iterations", str(args.iterations),
        "--depth_ratio", str(args.depth_ratio),
        "--lambda_normal", str(args.lambda_normal),
    ]
    if not run_cmd(train_cmd, "2DGS Training"):
        sys.exit(1)

    # Step 2: Mesh Extraction (TSDF Fusion)
    print("\n" + "="*60)
    print("[2DGS Pipeline] Step 2/2: Mesh Extraction (TSDF)")
    print("="*60)

    render_cmd = [
        "python3", os.path.join(dgs_dir, "render.py"),
        "-s", scene_path,
        "-m", model_output,
        "--depth_ratio", str(args.depth_ratio),
    ]
    if not run_cmd(render_cmd, "Rendering depth maps"):
        print("[WARNING] Rendering had issues.")

    # TSDF mesh extraction
    mesh_output = os.path.join(args.output, "mesh")
    os.makedirs(mesh_output, exist_ok=True)

    tsdf_cmd = [
        "python3", os.path.join(dgs_dir, "scripts", "tsdf_fusion.py" if os.path.exists(os.path.join(dgs_dir, "scripts", "tsdf_fusion.py")) else "extract_mesh.py"),
        "-m", model_output,
        "-o", mesh_output,
    ]
    run_cmd(tsdf_cmd, "TSDF Mesh Extraction")

    # Summary
    print("\n" + "="*60)
    print("[2DGS Pipeline] Complete!")
    print(f"Output directory: {args.output}")
    print("="*60)

    for root, dirs, files in os.walk(args.output):
        for f in files:
            if f.endswith(('.ply', '.obj', '.glb')):
                filepath = os.path.join(root, f)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"  {filepath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
