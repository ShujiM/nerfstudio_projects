import streamlit as st
import os
import subprocess
import signal
import time
import glob
import shutil
from PIL import Image

# Configuration
UPLOAD_DIR = "/workspace/data/uploads"
DATA_DIR = "/workspace/data/nerfstudio"
OUTPUT_DIR = "/workspace/outputs"
EXPORT_DIR = "/workspace/exports"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

st.set_page_config(layout="wide", page_title="Nerfstudio Web UI", page_icon="🎥")

# Session State Initialization
if "process" not in st.session_state:
    st.session_state.process = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "pid" not in st.session_state:
    st.session_state.pid = None
if "current_project" not in st.session_state:
    st.session_state.current_project = ""

def run_command(command, log_placeholder):
    """Run a command and capture output in real-time"""
    st.session_state.logs = []
    
    # Stop existing process if any
    if st.session_state.process:
        try:
            os.kill(st.session_state.pid, signal.SIGTERM)
        except:
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
            st.session_state.logs.append(output.strip())
            # Keep only last 1000 lines
            if len(st.session_state.logs) > 1000:
                st.session_state.logs.pop(0)
            
            # Update log view every few lines
            if len(st.session_state.logs) % 2 == 0 or len(st.session_state.logs) < 20:
                log_str = "\n".join(st.session_state.logs[-50:]) # Show last 50 lines in preview
                log_placeholder.code(log_str)
            
    return process.poll()

def stop_process():
    if st.session_state.process:
        st.session_state.process.terminate()
        st.session_state.process = None
        st.error("Process stopped")

# Sidebar
st.sidebar.title("Nerfstudio Web UI")
page = st.sidebar.radio("Navigation", ["1. Upload Data", "2. Process Data", "3. Train Model", "4. View & Export"])

st.sidebar.markdown("---")
if st.session_state.current_project:
    st.sidebar.success(f"Project: {st.session_state.current_project}")
else:
    st.sidebar.info("No project selected")

# ==========================================
# 1. Upload Data
# ==========================================
if page == "1. Upload Data":
    st.header("📂 Data Upload")
    
    project_name = st.text_input("Project Name (no spaces)", value="my_project")
    if project_name:
        st.session_state.current_project = project_name
    
    upload_type = st.radio("Data Type", ["Video (.mp4)", "Images (folder)"])
    
    if upload_type == "Video (.mp4)":
        uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"])
        if uploaded_file and project_name:
            save_path = os.path.join(UPLOAD_DIR, f"{project_name}.mp4")
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Video saved to: {save_path}")
            st.video(save_path)
            
    else: # Images
        uploaded_files = st.file_uploader("Upload Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        if uploaded_files and project_name:
            save_dir = os.path.join(UPLOAD_DIR, project_name)
            os.makedirs(save_dir, exist_ok=True)
            for uploaded_file in uploaded_files:
                with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Saved {len(uploaded_files)} images to: {save_dir}")

# ==========================================
# 2. Process Data
# ==========================================
elif page == "2. Process Data":
    st.header("⚙️ Process Data (COLMAP)")
    
    project_name = st.text_input("Project Name", value=st.session_state.current_project)
    
    # Check if input exists
    video_path = os.path.join(UPLOAD_DIR, f"{project_name}.mp4")
    images_path = os.path.join(UPLOAD_DIR, project_name)
    
    data_type = "video" if os.path.exists(video_path) else "images"
    input_path = video_path if data_type == "video" else images_path
    
    if not os.path.exists(input_path):
        st.warning(f"Input data not found for project '{project_name}'. Please go to '1. Upload Data' first.")
    else:
        st.info(f"Input: {input_path} ({data_type})")
        output_path = os.path.join(DATA_DIR, project_name)
        st.info(f"Output Directory: {output_path}")

        # Processing Options
        num_frames = st.number_input("Number of Frames (for video)", value=300, min_value=10)
        
        if st.button("Start Processing"):
            cmd = ["ns-process-data", data_type, "--data", input_path, "--output-dir", output_path]
            
            if data_type == "video":
                cmd.extend(["--num-frames-target", str(num_frames)])
            
            # Additional flags to be more robust?
            # cmd.extend(["--verbose"])

            st.write(f"Running: {' '.join(cmd)}")
            log_area = st.empty()
            ret = run_command(cmd, log_area)
            
            # Verify result
            transforms_file = os.path.join(output_path, "transforms.json")
            if ret == 0 and os.path.exists(transforms_file):
                st.success(f"Processing Complete! transforms.json created at {transforms_file}")
            else:
                st.error("Processing Failed or Incomplete. Check logs above.")
                if not os.path.exists(transforms_file):
                    st.warning("⚠️ transforms.json was not created. COLMAP might have failed.")

# ==========================================
# 3. Train Model
# ==========================================
elif page == "3. Train Model":
    st.header("🏋️ Train Model")
    
    project_name = st.text_input("Project Name", value=st.session_state.current_project)
    model_type = st.selectbox("Model", ["splatfacto", "nerfacto"])
    
    data_path = os.path.join(DATA_DIR, project_name)
    transforms_file = os.path.join(data_path, "transforms.json")
    
    # Validation
    if not os.path.exists(data_path):
        st.error(f"❌ Data directory not found: {data_path}")
        st.stop()
        
    if not os.path.exists(transforms_file):
        st.error(f"❌ transforms.json not found in {data_path}")
        st.warning("👉 Please go to '2. Process Data' and run processing first.")
        st.stop()
        
    st.success(f"✅ Found processed data at: {data_path}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Training"):
            # timestamp for unique output
            timestamp = time.strftime("%Y-%m-%d_%H%M%S")
            cmd = [
                "ns-train", model_type, 
                "--data", data_path, 
                "--viewer.quit-on-train-completion", "False",
                "--viewer.websocket-port", "7007",
                "--project-name", project_name,
                "--timestamp", timestamp,
                "--vis", "viewer"
            ]
            st.write(f"Running: {' '.join(cmd)}")
            
            st.info("Training started... Logs will stream below.")
            st.info("Viewer will be available at http://localhost:7007")
            
            log_area = st.empty()
            run_command(cmd, log_area)
            
    with col2:
        if st.button("Stop Training"):
            stop_process()

    st.markdown("### Viewer")
    st.markdown("Access the [Nerfstudio Viewer](http://localhost:7007) separately if the iframe doesn't load.")
    try:
        st.components.v1.iframe("http://localhost:7007", height=600)
    except:
        st.warning("Viewer not loaded.")

# ==========================================
# 4. View & Export
# ==========================================
elif page == "4. View & Export":
    st.header("📦 Export & Download")
    
    projects = []
    if os.path.exists(OUTPUT_DIR):
        projects = [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
    
    selected_project = st.selectbox("Select Project", projects, index=projects.index(st.session_state.current_project) if st.session_state.current_project in projects else 0)
    
    config_path = None
    if selected_project:
        base_path = os.path.join(OUTPUT_DIR, selected_project)
        # Search for config.yml recursively
        configs = glob.glob(os.path.join(base_path, "**", "config.yml"), recursive=True)
        configs.sort(key=os.path.getmtime, reverse=True)
        
        if configs:
            config_path = st.selectbox("Select Checkpoint", configs)
        else:
            st.warning("No checkpoints found.")
            
    export_format = st.selectbox("Export Format", ["gaussian-splat", "pointcloud", "mesh"])
    
    if config_path and st.button("Export PLY"):
        output_name = f"{selected_project}_{int(time.time())}"
        export_out_dir = os.path.join(EXPORT_DIR, output_name)
        
        cmd = ["ns-export", export_format, "--load-config", config_path, "--output-dir", export_out_dir]
        st.write(f"Running: {' '.join(cmd)}")
        log_area = st.empty()
        run_command(cmd, log_area)
        
        # Check for ply file
        ply_files = glob.glob(os.path.join(export_out_dir, "**", "*.ply"), recursive=True)
        
        if ply_files:
            st.success(f"Export created at {export_out_dir}")
            for ply in ply_files:
                file_name = os.path.basename(ply)
                with open(ply, "rb") as f:
                    st.download_button(
                        label=f"Download {file_name}",
                        data=f,
                        file_name=file_name,
                        mime="application/octet-stream"
                    )
        else:
            st.warning("Export command finished but no PLY found. Check logs.")

# ==========================================
# Logs Footer
# ==========================================
st.markdown("---")
with st.expander("Full Process Logs", expanded=True):
    st.code("\n".join(st.session_state.logs))
