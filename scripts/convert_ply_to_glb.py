#!/usr/bin/env python3
"""
PLY to GLB Converter
Converts PLY mesh files to GLB format using trimesh.

Usage:
  python3 convert_ply_to_glb.py --input file.ply --output file.glb
"""

import argparse
import os
import sys

try:
    import trimesh
except ImportError:
    print("[ERROR] trimesh not installed. Run: pip install trimesh pyglet")
    sys.exit(1)


def convert_ply_to_glb(input_path, output_path):
    """Convert PLY file to GLB format."""
    print(f"[Converter] Loading: {input_path}")

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return False

    try:
        # Load the PLY file
        mesh = trimesh.load(input_path)

        if isinstance(mesh, trimesh.PointCloud):
            print("[INFO] Input is a point cloud, not a mesh.")
            print("[INFO] Converting point cloud to GLB with vertex colors...")
            # For point clouds, create a simple scene
            scene = trimesh.Scene()
            scene.add_geometry(mesh)
            scene.export(output_path, file_type='glb')
        elif isinstance(mesh, trimesh.Scene):
            print(f"[INFO] Input is a scene with {len(mesh.geometry)} geometries")
            mesh.export(output_path, file_type='glb')
        else:
            print(f"[INFO] Input mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
            mesh.export(output_path, file_type='glb')

        output_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[Converter] Success! Output: {output_path} ({output_size:.1f} MB)")
        return True

    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PLY to GLB Converter")
    parser.add_argument("--input", required=True, help="Input PLY file path")
    parser.add_argument("--output", required=True, help="Output GLB file path")
    args = parser.parse_args()

    # Auto-generate output path if only directory is specified
    if os.path.isdir(args.output):
        basename = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join(args.output, f"{basename}.glb")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    success = convert_ply_to_glb(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
