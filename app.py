import streamlit as st
import os
import subprocess
import signal
import time
import glob
import shutil
import json
import re

# ==========================================
# Configuration
# ==========================================
UPLOAD_DIR = "/workspace/data/uploads"
DATA_DIR = "/workspace/data/nerfstudio"
OUTPUT_DIR = "/workspace/outputs"
EXPORT_DIR = "/workspace/exports"

# Nerfstudio model categories
NERFSTUDIO_MODELS = {
    "🎯 Gaussian Splatting (推奨)": {
        "splatfacto": "3DGS標準 - バランスの良い品質と速度",
        "splatfacto-big": "3DGS大規模 - より高品質、VRAMを多く使用",
        "splatfacto-w": "3DGS Wild - 屋外/不統一な写真向け",
    },
    "🔬 NeRF (高品質レンダリング)": {
        "nerfacto": "NeRF標準 - 汎用的な高品質レンダリング",
        "nerfacto-big": "NeRF大規模 - 複雑なシーン向け",
        "nerfacto-huge": "NeRF超大規模 - 最高品質",
        "instant-ngp": "Instant NGP - 超高速トレーニング",
    },
    "📐 幾何精度 (メッシュ生成)": {
        "neus-facto": "NeuS-facto - 高精度メッシュ生成",
        "neus": "NeuS - 神経表面再構成",
    },
    "🎬 動的シーン": {
        "dnerf": "D-NeRF - 動的シーン",
        "nerfplayer-nerfacto": "NeRFPlayer - 動画再生",
    },
    "⚡ その他": {
        "tensorf": "TensoRF - テンソル分解ベース",
        "zipnerf": "Zip-NeRF - アンチエイリアス",
        "volinga": "Volinga - WebGLエクスポート対応",
    },
}

# Export formats
EXPORT_FORMATS = {
    "gaussian-splat": "Gaussian Splat (.ply) - SuperSplat対応",
    "pointcloud": "点群 (.ply)",
    "poisson": "Poissonメッシュ (.ply)",
    "marching-cubes": "Marching Cubesメッシュ (.ply)",
    "tsdf": "TSDFメッシュ (.ply)",
}

# Ensure directories exist
for d in [UPLOAD_DIR, DATA_DIR, OUTPUT_DIR, EXPORT_DIR]:
    os.makedirs(d, exist_ok=True)

st.set_page_config(layout="wide", page_title="3DGS Studio", page_icon="🎥")

# ==========================================
# Session State
# ==========================================
if "process" not in st.session_state:
    st.session_state.process = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "pid" not in st.session_state:
    st.session_state.pid = None
if "current_project" not in st.session_state:
    st.session_state.current_project = ""

# ==========================================
# Helper Functions
# ==========================================
def run_command(command, log_placeholder, progress_bar=None, progress_config=None):
    """Run a command and capture output with optional progress bar.
    
    progress_config: dict with keys:
        - 'type': 'steps' | 'iterations' | 'pattern'
        - 'total_steps': int (for 'steps' type)
        - 'step_patterns': list of str (for 'steps' type - regex patterns that advance the step)
        - 'total_iterations': int (for 'iterations' type)
        - 'iteration_pattern': str (regex with group(1) as current iteration)
        - 'pattern': str (regex with group(1) as numerator, group(2) as denominator)
    """
    st.session_state.logs = []
    current_step = 0

    if st.session_state.process:
        try:
            os.kill(st.session_state.pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        st.session_state.process = None

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    st.session_state.process = process
    st.session_state.pid = process.pid

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            line = output.strip()
            st.session_state.logs.append(line)
            if len(st.session_state.logs) > 1000:
                st.session_state.logs.pop(0)

            # Update progress bar if configured
            if progress_bar and progress_config:
                ptype = progress_config.get('type', '')
                try:
                    if ptype == 'steps':
                        for i, pat in enumerate(progress_config.get('step_patterns', [])):
                            if re.search(pat, line, re.IGNORECASE):
                                current_step = max(current_step, i + 1)
                                total = progress_config.get('total_steps', len(progress_config['step_patterns']))
                                progress_bar.progress(min(current_step / total, 1.0),
                                    text=f"ステップ {current_step}/{total}: {line[:80]}")
                                break

                    elif ptype == 'iterations':
                        pat = progress_config.get('iteration_pattern', '')
                        m = re.search(pat, line)
                        if m:
                            current_iter = int(m.group(1))
                            total_iter = progress_config.get('total_iterations', 30000)
                            progress_bar.progress(min(current_iter / total_iter, 1.0),
                                text=f"イテレーション {current_iter:,}/{total_iter:,}")

                    elif ptype == 'pattern':
                        pat = progress_config.get('pattern', '')
                        m = re.search(pat, line)
                        if m:
                            num = int(m.group(1))
                            den = int(m.group(2))
                            if den > 0:
                                progress_bar.progress(min(num / den, 1.0),
                                    text=f"{num}/{den}")
                except (ValueError, IndexError, AttributeError):
                    pass

            # Update log display
            if len(st.session_state.logs) % 2 == 0 or len(st.session_state.logs) < 20:
                log_str = "\n".join(st.session_state.logs[-50:])
                log_placeholder.code(log_str)

    # Mark complete
    if progress_bar:
        progress_bar.progress(1.0, text="✅ 完了")

    return process.poll()


def run_docker_command(container, command):
    """Run a command in a specific Docker container via docker compose exec."""
    full_cmd = ["docker", "compose", "exec", "-T", container] + command
    return full_cmd


def stop_process():
    """Stop the current running process."""
    if st.session_state.process:
        st.session_state.process.terminate()
        st.session_state.process = None
        st.error("プロセスを停止しました")


def check_container_status(container_name):
    """Check if a Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "true"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_image_exists(container_name):
    """Check if a Docker image for a container exists (by checking if container was ever created)."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.Image}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def get_container_status_emoji(container_name):
    """Get status emoji for a container."""
    if check_container_status(container_name):
        return "🟢"  # Running
    elif check_image_exists(container_name):
        return "🟡"  # Built but not running
    else:
        return "🔴"  # Not installed


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 30.0  # fallback to 30 seconds


def find_ply_files(directory):
    """Find all PLY files recursively."""
    return glob.glob(os.path.join(directory, "**", "*.ply"), recursive=True)


def find_glb_files(directory):
    """Find all GLB files recursively."""
    return glob.glob(os.path.join(directory, "**", "*.glb"), recursive=True)


def find_obj_files(directory):
    """Find all OBJ files recursively."""
    return glob.glob(os.path.join(directory, "**", "*.obj"), recursive=True)


def convert_ply_to_glb(ply_path, glb_path):
    """Convert PLY to GLB using trimesh."""
    try:
        import trimesh
        mesh = trimesh.load(ply_path)
        if isinstance(mesh, trimesh.Scene):
            mesh.export(glb_path, file_type='glb')
        elif isinstance(mesh, trimesh.PointCloud):
            scene = trimesh.Scene()
            scene.add_geometry(mesh)
            scene.export(glb_path, file_type='glb')
        else:
            mesh.export(glb_path, file_type='glb')
        return True
    except Exception as e:
        st.error(f"GLB変換エラー: {e}")
        return False


# ==========================================
# Sidebar
# ==========================================
st.sidebar.title("🎥 3DGS Studio")
st.sidebar.markdown("*Gaussian Splatting統合プラットフォーム*")

page = st.sidebar.radio("Navigation", [
    "1. 📂 データアップロード",
    "2. ⚙️ データ前処理",
    "3. 🏋️ トレーニング",
    "4. 📦 エクスポート",
])

st.sidebar.markdown("---")
if st.session_state.current_project:
    st.sidebar.success(f"🗂️ Project: {st.session_state.current_project}")
else:
    st.sidebar.info("プロジェクト未選択")

# Framework status (dynamic)
st.sidebar.markdown("---")
st.sidebar.markdown("### フレームワーク状態")
ns_status = get_container_status_emoji("nerfstudio")
sg_status = get_container_status_emoji("sugar")
dgs_status = get_container_status_emoji("2dgs")
st.sidebar.markdown(f"{ns_status} **Nerfstudio** (splatfacto, nerfacto等)")
st.sidebar.markdown(f"{sg_status} **SuGaR** (メッシュ抽出)")
st.sidebar.markdown(f"{dgs_status} **2DGS** (高品質レンダリング)")
st.sidebar.caption("🟢 Running  🟡 Built (停止中)  🔴 未ビルド")


# ==========================================
# Page 1: Upload Data
# ==========================================
if page == "1. 📂 データアップロード":
    st.header("📂 データアップロード")

    project_name = st.text_input("プロジェクト名 (スペースなし)", value="my_project")
    if project_name:
        st.session_state.current_project = project_name

    upload_type = st.radio("データタイプ", ["動画 (.mp4)", "画像 (複数ファイル)"])

    if upload_type == "動画 (.mp4)":
        uploaded_file = st.file_uploader("動画をアップロード", type=["mp4", "mov", "avi"])
        if uploaded_file and project_name:
            save_path = os.path.join(UPLOAD_DIR, f"{project_name}.mp4")
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ 保存先: {save_path}")
            st.video(save_path)
    else:
        uploaded_files = st.file_uploader(
            "画像をアップロード", type=["jpg", "png", "jpeg"],
            accept_multiple_files=True
        )
        if uploaded_files and project_name:
            save_dir = os.path.join(UPLOAD_DIR, project_name)
            os.makedirs(save_dir, exist_ok=True)
            for uploaded_file in uploaded_files:
                with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"✅ {len(uploaded_files)} 枚を保存: {save_dir}")


# ==========================================
# Page 2: Process Data (COLMAP)
# ==========================================
elif page == "2. ⚙️ データ前処理":
    st.header("⚙️ データ前処理")

    project_name = st.text_input("プロジェクト名", value=st.session_state.current_project)

    video_path = os.path.join(UPLOAD_DIR, f"{project_name}.mp4")
    images_path = os.path.join(UPLOAD_DIR, project_name)

    data_type = "video" if os.path.exists(video_path) else "images"
    input_path = video_path if data_type == "video" else images_path

    if not os.path.exists(input_path):
        st.warning(f"⚠️ 入力データが見つかりません: '{project_name}'")
        st.info("👉 '1. データアップロード' でデータをアップロードしてください")
    else:
        st.info(f"📁 入力: {input_path} ({data_type})")
        output_path = os.path.join(DATA_DIR, project_name)
        st.info(f"📁 出力: {output_path}")

        # SfM Engine selection
        sfm_engine = st.radio(
            "🔧 SfMエンジン",
            ["COLMAP (標準)", "GLOMAP (高速 ⚡)"],
            help="GLOMAPはCOLMAPの10-100倍高速なグローバルSfMです"
        )

        num_frames = st.number_input("フレーム数 (動画の場合)", value=300, min_value=10)

        if "GLOMAP" in sfm_engine:
            st.info("💡 GLOMAPパイプライン: 特徴抽出 → マッチング → GLOMAP Mapper")

            if st.button("🚀 前処理開始 (GLOMAP)"):
                progress_bar = st.progress(0, text="準備中...")
                log_area = st.empty()

                # Step 1: Extract frames from video (if video)
                if data_type == "video":
                    progress_bar.progress(0.05, text="Step 1/5: フレーム抽出...")
                    os.makedirs(os.path.join(output_path, "images"), exist_ok=True)
                    duration = get_video_duration(input_path)
                    extract_fps = max(num_frames / duration, 1)
                    ffmpeg_cmd = [
                        "ffmpeg", "-i", input_path,
                        "-vf", f"fps={extract_fps:.4f}",
                        "-q:v", "1",
                        os.path.join(output_path, "images", "frame_%05d.jpg")
                    ]
                    run_command(ffmpeg_cmd, log_area)

                images_dir = os.path.join(output_path, "images") if data_type == "video" else input_path
                db_path = os.path.join(output_path, "database.db")
                sparse_path = os.path.join(output_path, "sparse")
                os.makedirs(sparse_path, exist_ok=True)

                # Step 2: Feature extraction
                progress_bar.progress(0.2, text="Step 2/5: COLMAP特徴抽出...")
                cmd_feat = [
                    "colmap", "feature_extractor",
                    "--image_path", images_dir,
                    "--database_path", db_path
                ]
                ret = run_command(cmd_feat, log_area)
                if ret != 0:
                    st.error("❌ 特徴抽出に失敗しました")
                    st.stop()

                # Step 3: Matching
                progress_bar.progress(0.4, text="Step 3/5: COLMAPマッチング...")
                cmd_match = [
                    "colmap", "exhaustive_matcher",
                    "--database_path", db_path
                ]
                ret = run_command(cmd_match, log_area)
                if ret != 0:
                    st.error("❌ マッチングに失敗しました")
                    st.stop()

                # Step 4: GLOMAP Mapper
                progress_bar.progress(0.6, text="Step 4/5: GLOMAP Mapper (グローバルSfM)...")
                cmd_glomap = [
                    "glomap", "mapper",
                    "--database_path", db_path,
                    "--image_path", images_dir,
                    "--output_path", sparse_path
                ]
                ret = run_command(cmd_glomap, log_area)
                if ret != 0:
                    st.error("❌ GLOMAP Mapperに失敗しました")
                    st.stop()

                # Step 5: Convert to nerfstudio format
                progress_bar.progress(0.8, text="Step 5/5: Nerfstudio形式に変換...")
                cmd_convert = [
                    "ns-process-data", "images",
                    "--data", images_dir,
                    "--output-dir", output_path,
                    "--skip-colmap",
                    "--colmap-model-path", os.path.join(sparse_path, "0"),
                ]
                ret = run_command(cmd_convert, log_area)

                progress_bar.progress(1.0, text="✅ 完了")
                transforms_file = os.path.join(output_path, "transforms.json")
                if ret == 0 and os.path.exists(transforms_file):
                    st.success("✅ GLOMAP前処理完了！")
                    st.balloons()
                else:
                    st.error("❌ 前処理に失敗しました")
        else:
            # Standard COLMAP via ns-process-data
            if st.button("🚀 前処理開始 (COLMAP)"):
                progress_bar = st.progress(0, text="COLMAP処理中...")
                progress_config = {
                    'type': 'steps',
                    'total_steps': 4,
                    'step_patterns': [
                        r'(?:extracting|feature)',
                        r'(?:matching|exhaustive)',
                        r'(?:mapper|triangulat|reconstruct)',
                        r'(?:undistort|export|transform)',
                    ]
                }
                cmd = ["ns-process-data", data_type, "--data", input_path, "--output-dir", output_path]
                if data_type == "video":
                    cmd.extend(["--num-frames-target", str(num_frames)])
                st.write(f"実行: `{' '.join(cmd)}`")
                log_area = st.empty()
                ret = run_command(cmd, log_area, progress_bar, progress_config)

                transforms_file = os.path.join(output_path, "transforms.json")
                if ret == 0 and os.path.exists(transforms_file):
                    st.success("✅ 前処理完了！")
                    st.balloons()
                else:
                    st.error("❌ 前処理に失敗しました")


# ==========================================
# Page 3: Train Model
# ==========================================
elif page == "3. 🏋️ トレーニング":
    st.header("🏋️ トレーニング")

    project_name = st.text_input("プロジェクト名", value=st.session_state.current_project)
    data_path = os.path.join(DATA_DIR, project_name)
    transforms_file = os.path.join(data_path, "transforms.json")

    # Validate data exists
    if not os.path.exists(data_path):
        st.error(f"❌ データが見つかりません: {data_path}")
        st.stop()
    if not os.path.exists(transforms_file):
        st.error(f"❌ transforms.json が見つかりません")
        st.warning("👉 '2. データ前処理' を実行してください")
        st.stop()

    st.success(f"✅ 処理済みデータ: {data_path}")

    # ==========================================
    # Framework Selection
    # ==========================================
    st.markdown("---")
    framework = st.selectbox("🔧 フレームワーク選択", [
        "Nerfstudio (splatfacto, nerfacto等)",
        "SuGaR (メッシュ抽出)",
        "2DGS (2D Gaussian Splatting)",
    ])

    # ------------------------------------------
    # Nerfstudio Training
    # ------------------------------------------
    if "Nerfstudio" in framework:
        st.subheader("Nerfstudio トレーニング")

        # Model selection by category
        all_models = {}
        for category, models in NERFSTUDIO_MODELS.items():
            all_models.update(models)

        category = st.selectbox("カテゴリ", list(NERFSTUDIO_MODELS.keys()))
        models_in_cat = NERFSTUDIO_MODELS[category]
        model_type = st.selectbox(
            "モデル",
            list(models_in_cat.keys()),
            format_func=lambda x: f"{x} — {models_in_cat[x]}"
        )

        # Advanced options
        with st.expander("⚙️ 詳細設定"):
            max_iterations = st.number_input("最大イテレーション", value=30000, min_value=1000, step=1000)
            viewer_enabled = st.checkbox("Viewer有効化", value=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 トレーニング開始"):
                timestamp = time.strftime("%Y-%m-%d_%H%M%S")
                cmd = [
                    "ns-train", model_type,
                    "--data", data_path,
                    "--viewer.quit-on-train-completion", "False",
                    "--viewer.websocket-port", "7007",
                    "--viewer.websocket-host", "0.0.0.0",
                    "--project-name", project_name,
                    "--timestamp", timestamp,
                    "--max-num-iterations", str(max_iterations),
                ]
                if viewer_enabled:
                    cmd.extend(["--vis", "viewer"])
                else:
                    cmd.extend(["--vis", "tensorboard"])

                st.write(f"実行: `{' '.join(cmd)}`")
                st.info("🔄 トレーニング中... ログは下に表示されます")
                if viewer_enabled:
                    st.info("🖥️ Viewer: http://localhost:7007")

                progress_bar = st.progress(0, text="トレーニング開始...")
                progress_config = {
                    'type': 'iterations',
                    'iteration_pattern': r'(?:Step|step|Iter).*?(\d+).*?/.*?(\d+)',
                    'total_iterations': max_iterations,
                }
                log_area = st.empty()
                run_command(cmd, log_area, progress_bar, progress_config)

        with col2:
            if st.button("⏹️ トレーニング停止"):
                stop_process()

        # Viewer iframe
        if st.checkbox("Viewerを表示", value=True):
            st.markdown("### Viewer")
            st.markdown("[Nerfstudio Viewer](http://localhost:7007) (別タブで開く)")
            try:
                st.components.v1.iframe("http://localhost:7007", height=600)
            except Exception:
                st.warning("Viewerが読み込めません。トレーニングを開始してください。")

    # ------------------------------------------
    # SuGaR Training
    # ------------------------------------------
    elif "SuGaR" in framework:
        st.subheader("🧊 SuGaR トレーニング (メッシュ抽出)")
        st.markdown("""
        **SuGaRパイプライン:**
        1. 3DGS事前学習 (7,000イテレーション)
        2. SuGaRメッシュ抽出 (粗いメッシュ)
        3. メッシュ精密化 (テクスチャ付きメッシュ)

        > ⏱️ 所要時間: 約15-30分 (RTX 4070)
        """)

        with st.expander("⚙️ 詳細設定"):
            gs_iterations = st.number_input("3DGS事前学習イテレーション", value=7000, min_value=1000, step=1000)
            refine_iterations = st.number_input("精密化イテレーション", value=15000, min_value=5000, step=5000)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 SuGaRトレーニング開始"):
                if not check_container_status("sugar"):
                    st.error("❌ SuGaRコンテナが起動していません")
                    st.info("💡 ホストで実行: `scripts\\start.bat build-sugar` → `docker compose --profile sugar up -d`")
                    st.stop()
                output_path = os.path.join(OUTPUT_DIR, project_name, "sugar")
                cmd = [
                    "docker", "exec", "sugar",
                    "python3", "/workspace/scripts/sugar_train.py",
                    "--data", data_path,
                    "--output", output_path,
                    "--gs-iterations", str(gs_iterations),
                    "--refinement-iterations", str(refine_iterations),
                ]
                st.write(f"実行: `{' '.join(cmd)}`")
                st.info("SuGaRコンテナで実行中...")
                progress_bar = st.progress(0, text="SuGaRパイプライン開始...")
                progress_config = {
                    'type': 'steps',
                    'total_steps': 5,
                    'step_patterns': [
                        r'(?:pre.?train|3dgs.*train|gaussian.*train)',
                        r'(?:coarse|mesh.*extract)',
                        r'(?:refin|refinement)',
                        r'(?:export|saving|output)',
                        r'(?:done|complete|finish)',
                    ]
                }
                log_area = st.empty()
                run_command(cmd, log_area, progress_bar, progress_config)

        with col2:
            if st.button("⏹️ 停止"):
                stop_process()

    # ------------------------------------------
    # 2DGS Training
    # ------------------------------------------
    elif "2DGS" in framework:
        st.subheader("🎨 2DGS トレーニング (2D Gaussian Splatting)")
        st.markdown("""
        **2DGSパイプライン:**
        1. 2D Gaussian Splatting 学習
        2. 深度マップレンダリング
        3. TSDFメッシュ抽出

        > ⏱️ 所要時間: 約20-40分 (RTX 4070)
        """)

        with st.expander("⚙️ 詳細設定"):
            dgs_iterations = st.number_input("トレーニングイテレーション", value=30000, min_value=5000, step=5000)
            depth_ratio = st.slider("深度比率", 0.0, 1.0, 0.0)
            lambda_normal = st.slider("法線一貫性重み", 0.0, 0.5, 0.05)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 2DGSトレーニング開始"):
                if not check_container_status("2dgs"):
                    st.error("❌ 2DGSコンテナが起動していません")
                    st.info("💡 ホストで実行: `scripts\\start.bat build-2dgs` → `docker compose --profile 2dgs up -d`")
                    st.stop()
                output_path = os.path.join(OUTPUT_DIR, project_name, "2dgs")
                cmd = [
                    "docker", "exec", "2dgs",
                    "python3", "/workspace/scripts/2dgs_train.py",
                    "--data", data_path,
                    "--output", output_path,
                    "--iterations", str(dgs_iterations),
                    "--depth-ratio", str(depth_ratio),
                    "--lambda-normal", str(lambda_normal),
                ]
                st.write(f"実行: `{' '.join(cmd)}`")
                st.info("2DGSコンテナで実行中...")
                progress_bar = st.progress(0, text="2DGSトレーニング開始...")
                progress_config = {
                    'type': 'iterations',
                    'iteration_pattern': r'(?:iteration|iter|step)\s*(\d+)',
                    'total_iterations': dgs_iterations,
                }
                log_area = st.empty()
                run_command(cmd, log_area, progress_bar, progress_config)

        with col2:
            if st.button("⏹️ 停止 "):
                stop_process()


# ==========================================
# Page 4: Export & Download
# ==========================================
elif page == "4. 📦 エクスポート":
    st.header("📦 エクスポート & ダウンロード")

    # Find available projects
    projects = []
    if os.path.exists(OUTPUT_DIR):
        projects = [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]

    if not projects:
        st.warning("トレーニング済みプロジェクトがありません")
        st.stop()

    default_idx = projects.index(st.session_state.current_project) if st.session_state.current_project in projects else 0
    selected_project = st.selectbox("プロジェクト選択", projects, index=default_idx)

    # ==========================================
    # Tab layout for different export types
    # ==========================================
    tab_ns, tab_sugar, tab_2dgs, tab_convert = st.tabs([
        "🎯 Nerfstudio Export",
        "🧊 SuGaR Export",
        "🎨 2DGS Export",
        "🔄 PLY→GLB 変換",
    ])

    # ------------------------------------------
    # Nerfstudio Export
    # ------------------------------------------
    with tab_ns:
        st.subheader("Nerfstudio エクスポート")

        # Find config files
        base_path = os.path.join(OUTPUT_DIR, selected_project)
        configs = glob.glob(os.path.join(base_path, "**", "config.yml"), recursive=True)
        configs.sort(key=os.path.getmtime, reverse=True)

        if configs:
            config_path = st.selectbox("チェックポイント", configs, key="ns_config")
            export_format = st.selectbox(
                "エクスポート形式",
                list(EXPORT_FORMATS.keys()),
                format_func=lambda x: EXPORT_FORMATS[x]
            )

            if st.button("📦 Nerfstudioエクスポート"):
                output_name = f"{selected_project}_ns_{int(time.time())}"
                export_out_dir = os.path.join(EXPORT_DIR, output_name)
                cmd = ["ns-export", export_format, "--load-config", config_path, "--output-dir", export_out_dir]
                st.write(f"実行: `{' '.join(cmd)}`")
                log_area = st.empty()
                run_command(cmd, log_area)

                ply_files = find_ply_files(export_out_dir)
                if ply_files:
                    st.success(f"✅ エクスポート完了: {export_out_dir}")
                    for ply in ply_files:
                        file_name = os.path.basename(ply)
                        file_size = os.path.getsize(ply) / (1024 * 1024)
                        st.write(f"📄 {file_name} ({file_size:.1f} MB)")
                        with open(ply, "rb") as f:
                            st.download_button(
                                label=f"⬇️ {file_name} をダウンロード",
                                data=f,
                                file_name=file_name,
                                mime="application/octet-stream",
                                key=f"dl_{file_name}"
                            )
                else:
                    st.warning("PLYファイルが見つかりませんでした")
        else:
            st.warning("トレーニング済みチェックポイントがありません")

    # ------------------------------------------
    # SuGaR Export
    # ------------------------------------------
    with tab_sugar:
        st.subheader("SuGaR エクスポート")
        sugar_path = os.path.join(OUTPUT_DIR, selected_project, "sugar")

        if os.path.exists(sugar_path):
            ply_files = find_ply_files(sugar_path)
            obj_files = find_obj_files(sugar_path)
            all_files = ply_files + obj_files

            if all_files:
                st.success(f"✅ {len(all_files)} ファイルが見つかりました")
                for filepath in all_files:
                    file_name = os.path.basename(filepath)
                    file_size = os.path.getsize(filepath) / (1024 * 1024)
                    st.write(f"📄 {file_name} ({file_size:.1f} MB)")
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {file_name}",
                            data=f,
                            file_name=file_name,
                            mime="application/octet-stream",
                            key=f"sugar_dl_{file_name}"
                        )
            else:
                st.info("SuGaRの出力ファイルがまだありません")
        else:
            st.info("SuGaRトレーニングが実行されていません")

    # ------------------------------------------
    # 2DGS Export
    # ------------------------------------------
    with tab_2dgs:
        st.subheader("2DGS エクスポート")
        dgs_path = os.path.join(OUTPUT_DIR, selected_project, "2dgs")

        if os.path.exists(dgs_path):
            ply_files = find_ply_files(dgs_path)
            if ply_files:
                st.success(f"✅ {len(ply_files)} ファイルが見つかりました")
                for filepath in ply_files:
                    file_name = os.path.basename(filepath)
                    file_size = os.path.getsize(filepath) / (1024 * 1024)
                    st.write(f"📄 {file_name} ({file_size:.1f} MB)")
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {file_name}",
                            data=f,
                            file_name=file_name,
                            mime="application/octet-stream",
                            key=f"2dgs_dl_{file_name}"
                        )
            else:
                st.info("2DGSの出力ファイルがまだありません")
        else:
            st.info("2DGSトレーニングが実行されていません")

    # ------------------------------------------
    # PLY → GLB Conversion
    # ------------------------------------------
    with tab_convert:
        st.subheader("🔄 PLY → GLB 変換")
        st.markdown("PLYメッシュをGLBに変換します。GLBはPlayCanvasやWebブラウザで表示可能です。")

        # Find all exported PLY files
        all_plys = find_ply_files(EXPORT_DIR) + find_ply_files(OUTPUT_DIR)

        if all_plys:
            selected_ply = st.selectbox("変換するPLYファイル", all_plys)
            if st.button("🔄 GLBに変換"):
                glb_path = selected_ply.rsplit('.', 1)[0] + ".glb"
                with st.spinner("変換中..."):
                    if convert_ply_to_glb(selected_ply, glb_path):
                        glb_size = os.path.getsize(glb_path) / (1024 * 1024)
                        st.success(f"✅ 変換完了: {glb_path} ({glb_size:.1f} MB)")
                        with open(glb_path, "rb") as f:
                            st.download_button(
                                label="⬇️ GLBをダウンロード",
                                data=f,
                                file_name=os.path.basename(glb_path),
                                mime="model/gltf-binary"
                            )
                    else:
                        st.error("変換に失敗しました")
        else:
            st.info("エクスポート済みのPLYファイルがありません")

    # ==========================================
    # External Editor Links
    # ==========================================
    st.markdown("---")
    st.markdown("### 🔗 外部エディタ")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### SuperSplat Editor")
        st.markdown("PLYファイルをドラッグ＆ドロップで編集")
        st.markdown("[🔗 SuperSplat を開く](https://superspl.at/editor)")
        st.caption("💡 上でダウンロードしたPLYファイルをエディタにドラッグ＆ドロップしてください")

    with col2:
        st.markdown("#### PlayCanvas Editor")
        st.markdown("GLBファイルをドラッグ＆ドロップで使用")
        st.markdown("[🔗 PlayCanvas を開く](https://playcanvas.com/editor/project/1466228)")
        st.caption("💡 上でダウンロードしたGLBファイルをアセットパネルにドラッグ＆ドロップしてください")


# ==========================================
# Logs Footer
# ==========================================
st.markdown("---")
with st.expander("📋 プロセスログ", expanded=False):
    st.code("\n".join(st.session_state.logs))
