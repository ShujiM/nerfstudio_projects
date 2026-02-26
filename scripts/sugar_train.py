#!/usr/bin/env python3
"""
SuGaR Training Pipeline Script
Runs inside the SuGaR Docker container.
Pipeline: 3DGS pre-training (7k iter) → SuGaR coarse → SuGaR refined mesh

Usage:
  python3 sugar_train.py --data /workspace/data/nerfstudio/<project> \
                         --output /workspace/outputs/<project>/sugar
"""

import argparse
import os
import sys
import subprocess
import json
import shutil


def run_cmd(cmd, desc=""):
    """Run a command and stream output."""
    print(f"\n{'='*60}")
    print(f"[SuGaR] {desc}")
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


def convert_nerfstudio_to_colmap(data_path, output_path):
    """
    Convert nerfstudio format data to COLMAP format for SuGaR.
    SuGaR expects COLMAP-style directory structure:
      <scene>/
        images/
        sparse/0/
          cameras.bin, images.bin, points3D.bin
    """
    colmap_dir = os.path.join(data_path, "colmap", "sparse", "0")
    if os.path.exists(colmap_dir):
        # Already in COLMAP format, symlink to output
        os.makedirs(output_path, exist_ok=True)
        # Link images
        src_images = os.path.join(data_path, "images")
        dst_images = os.path.join(output_path, "images")
        if not os.path.exists(dst_images):
            os.symlink(src_images, dst_images)
        # Link sparse
        src_sparse = os.path.join(data_path, "colmap", "sparse")
        dst_sparse = os.path.join(output_path, "sparse")
        if not os.path.exists(dst_sparse):
            os.symlink(src_sparse, dst_sparse)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="SuGaR Training Pipeline")
    parser.add_argument("--data", required=True, help="Path to nerfstudio processed data")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--gs-iterations", type=int, default=7000,
                        help="3DGS pre-training iterations (default: 7000)")
    parser.add_argument("--refinement-iterations", type=int, default=15000,
                        help="SuGaR refinement iterations (default: 15000)")
    parser.add_argument("--export-obj", action="store_true", default=True,
                        help="Export OBJ mesh")
    parser.add_argument("--export-ply", action="store_true", default=True,
                        help="Export PLY mesh")
    args = parser.parse_args()

    sugar_dir = "/opt/SuGaR"
    gs_dir = os.path.join(sugar_dir, "gaussian_splatting")

    # Prepare COLMAP-format data
    scene_path = os.path.join(args.output, "scene")
    if not convert_nerfstudio_to_colmap(args.data, scene_path):
        print("[ERROR] Could not find COLMAP data in the nerfstudio directory.")
        print(f"Expected: {args.data}/colmap/sparse/0/")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    gs_output = os.path.join(args.output, "gs_output")

    # Step 1: 3DGS Pre-training (required by SuGaR)
    print("\n" + "="*60)
    print("[SuGaR Pipeline] Step 1/3: 3DGS Pre-training")
    print("="*60)

    gs_train_cmd = [
        "python3", os.path.join(gs_dir, "train.py"),
        "-s", scene_path,
        "-m", gs_output,
        "--iterations", str(args.gs_iterations),
    ]
    if not run_cmd(gs_train_cmd, "3DGS Pre-training"):
        sys.exit(1)

    # Step 2: SuGaR Coarse (extract mesh from 3DGS)
    print("\n" + "="*60)
    print("[SuGaR Pipeline] Step 2/3: SuGaR Coarse Mesh Extraction")
    print("="*60)

    sugar_coarse_cmd = [
        "python3", os.path.join(sugar_dir, "train.py"),
        "-s", scene_path,
        "-c", os.path.join(gs_output, "point_cloud", f"iteration_{args.gs_iterations}", "point_cloud.ply"),
        "-o", args.output,
        "--low_poly", "True",
        "--export_ply", "True" if args.export_ply else "False",
        "--export_obj", "True" if args.export_obj else "False",
    ]
    if not run_cmd(sugar_coarse_cmd, "SuGaR Coarse"):
        print("[WARNING] SuGaR coarse training had issues. Checking outputs...")

    # Step 3: SuGaR Refinement
    print("\n" + "="*60)
    print("[SuGaR Pipeline] Step 3/3: SuGaR Mesh Refinement")
    print("="*60)

    sugar_refine_cmd = [
        "python3", os.path.join(sugar_dir, "refine.py"),
        "-s", scene_path,
        "-c", os.path.join(gs_output, "point_cloud", f"iteration_{args.gs_iterations}", "point_cloud.ply"),
        "-o", args.output,
        "--n_gaussians_per_surface_triangle", "6",
        "--refinement_iterations", str(args.refinement_iterations),
        "--export_ply", "True",
        "--export_obj", "True",
    ]
    run_cmd(sugar_refine_cmd, "SuGaR Refinement")

    # Summary
    print("\n" + "="*60)
    print("[SuGaR Pipeline] Complete!")
    print(f"Output directory: {args.output}")
    print("="*60)

    # List output files
    for root, dirs, files in os.walk(args.output):
        for f in files:
            if f.endswith(('.ply', '.obj', '.glb')):
                filepath = os.path.join(root, f)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"  {filepath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
