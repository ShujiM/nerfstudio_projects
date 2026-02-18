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
            
            # Update log view every few lines or roughly
            log_str = "\n".join(st.session_state.logs[-20:]) # Show last 20 lines in preview
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

# ==========================================
# 1. Upload Data
# ==========================================
if page == "1. Upload Data":
    st.header("📂 Data Upload")
    
    project_name = st.text_input("Project Name (no spaces)", value="my_project")
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
    data_type = st.selectbox("Input Type", ["video", "images"])
    
    input_path = ""
    if data_type == "video":
        input_path = os.path.join(UPLOAD_DIR, f"{project_name}.mp4")
    else:
        input_path = os.path.join(UPLOAD_DIR, project_name)
        
    output_path = os.path.join(DATA_DIR, project_name)
    
    st.info(f"Input: {input_path}")
    st.info(f"Output: {output_path}")
    
    if st.button("Start Processing"):
        cmd = ["ns-process-data", data_type, "--data", input_path, "--output-dir", output_path]
        if data_type == "images":
            # For images, the command is slightly different: ns-process-data images --data ...
            pass 
            
        st.write(f"Running: {' '.join(cmd)}")
        log_area = st.empty()
        ret = run_command(cmd, log_area)
        
        if ret == 0:
            st.success("Processing Complete!")
        else:
            st.error("Processing Failed.")

# ==========================================
# 3. Train Model
# ==========================================
elif page == "3. Train Model":
    st.header("🏋️ Train Model")
    
    project_name = st.text_input("Project Name", value=st.session_state.current_project)
    model_type = st.selectbox("Model", ["splatfacto", "nerfacto"])
    
    data_path = os.path.join(DATA_DIR, project_name)
    
    if not os.path.exists(data_path):
        st.warning(f"Data directory not found: {data_path}")
    else:
        st.success(f"Found data at: {data_path}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Training"):
            cmd = ["ns-train", model_type, "--data", data_path, "--viewer.quit-on-train-completion", "False"]
            st.write(f"Running: {' '.join(cmd)}")
            
            # Start in separate process so we don't block UI entirely? 
            # Ideally stream logs.
            log_area = st.empty()
            
            # Hint to user
            st.info("Training started. Viewer running at http://localhost:7007")
            
            run_command(cmd, log_area)
            
    with col2:
        if st.button("Stop Training"):
            stop_process()

    st.markdown("### Viewer")
    st.markdown("Access the [Nerfstudio Viewer](http://localhost:7007) separately if the iframe doesn't load.")
    st.components.v1.iframe("http://localhost:7007", height=600)

# ==========================================
# 4. View & Export
# ==========================================
elif page == "4. View & Export":
    st.header("📦 Export & Download")
    
    # List available configs
    # Configs are usually in outputs/{project_name}/{model}/{timestamp}/config.yml
    
    projects = []
    if os.path.exists(OUTPUT_DIR):
        projects = [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
    
    selected_project = st.selectbox("Select Project", projects)
    
    config_path = None
    if selected_project:
        # Find latest config
        # Assuming structure: outputs/project/splatfacto/timestamp/config.yml
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
        # ns-export gaussian-splat --load-config ... --output-dir ...
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
with st.expander("Full Process Logs", expanded=False):
    st.code("\n".join(st.session_state.logs))
