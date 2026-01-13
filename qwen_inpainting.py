import modal
import subprocess

qwen_inpainting_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "nano", "curl")
    .pip_install("comfy-cli==1.3.5")
    # Force complete rebuild - FRESH START 2025-01-11
    .run_commands(
        "rm -rf /root/comfy || true",
        "comfy --skip-prompt install --nvidia",
    )
    .run_commands(
        # Qwen Image Inpainting Models
        # Text Encoders
        "comfy --skip-prompt model download --url https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors --relative-path models/text_encoders",
        
        # VAE
        "comfy --skip-prompt model download --url https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors --relative-path models/vae",
        
        # LoRA for Lightning (correct model from workflow)
        "comfy --skip-prompt model download --url https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-fp32.safetensors --relative-path models/loras",
        
        # UNET Model (BF16 safetensors - 40.9 GB - the one actually used in workflow)
        "comfy --skip-prompt model download --url https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors --relative-path models/diffusion_models",
    )
    .run_commands(
        # Install missing custom nodes using correct GitHub repositories
        "comfy node install https://github.com/kijai/ComfyUI-KJNodes",
        "comfy node install https://github.com/lrzjason/Comfyui-QwenEditUtils", 
        "comfy node install https://github.com/ltdrdata/was-node-suite-comfyui",
        "comfy node install https://github.com/city96/ComfyUI-GGUF",
        "comfy node install https://github.com/kael558/ComfyUI-GGUF-FantasyTalking",
    )
)

app = modal.App(name="qwen-image-inpainting", image=qwen_inpainting_image)

@app.function(
    max_containers=1,
    scaledown_window=300,
    timeout=3200,
    gpu="A100-40GB",
)
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=60)
def ui():
    # Reset ComfyUI database to fix SQLite errors
    subprocess.run("rm -f /root/comfy/ComfyUI/comfyui.db || true", shell=True)
    subprocess.run("rm -rf /root/comfy/ComfyUI/userdata/__pycache__ || true", shell=True)
    
    # Start ComfyUI with proper settings
    subprocess.Popen([
        "comfy", "launch", "--", 
        "--listen", "0.0.0.0", 
        "--port", "8000",
        "--disable-auto-launch",
        "--disable-metadata"
    ], shell=False)
