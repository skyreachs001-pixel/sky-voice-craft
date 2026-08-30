import os
import sys
import json
import time
import socket

# Reconfigure stdout/stderr for Windows console compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.key_vault import KeyVaultManager
from core.voice_engine import (
    VoiceEngine, GEMINI_VOICES, VOICE_TONES, LANGUAGES,
    detect_characters_in_script, parse_dialogue_script
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
HISTORY_FILE = os.path.join(BASE_DIR, "data", "history.json")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

# Initialize Key Vault and Voice Engine
key_vault = KeyVaultManager()
voice_engine = VoiceEngine(key_vault, OUTPUTS_DIR)

app = FastAPI(title="Sky Voice Craft", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_local_ip() -> str:
    """Find local network IP address (e.g. 192.168.1.5) for phone access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_history() -> list[dict]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history: list[dict]):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

# ── Pydantic Request Models ───────────────────────────────────────────────────
class ProfileCreateRequest(BaseModel):
    name: str
    key: str
    validate_key: bool = True

class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    key: str | None = None
    enabled: bool | None = None

class AutoSwitchRequest(BaseModel):
    enabled: bool

class SampleRequest(BaseModel):
    voice_name: str

class GenerateRequest(BaseModel):
    text: str
    voice_name: str
    tone: str
    language: str

class DialogueDetectRequest(BaseModel):
    script: str

class DialogueGenerateRequest(BaseModel):
    script: str
    character_voices: dict[str, str] = {}
    tone: str = "🎭 Dramatic & Cinematic Storyteller"
    language: str = "Hindi (Natural Indian Accent)"

# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "local_ip": get_local_ip(),
        "port": 8000,
        "metrics": key_vault.get_metrics()
    }

@app.get("/api/profiles")
def get_profiles():
    return {
        "metrics": key_vault.get_metrics(),
        "profiles": key_vault.get_all_profiles()
    }

@app.post("/api/profiles")
def add_profile(req: ProfileCreateRequest):
    success, msg, profile = key_vault.add_profile(req.name, req.key, validate=req.validate_key)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "profile": profile, "metrics": key_vault.get_metrics()}

@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: str, req: ProfileUpdateRequest):
    success, msg = key_vault.update_profile(profile_id, name=req.name, key=req.key, enabled=req.enabled)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "metrics": key_vault.get_metrics()}

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: str):
    success, msg = key_vault.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    return {"message": msg, "metrics": key_vault.get_metrics()}

@app.post("/api/profiles/{profile_id}/test")
def test_profile(profile_id: str):
    valid, msg = key_vault.test_profile(profile_id)
    return {"valid": valid, "message": msg, "metrics": key_vault.get_metrics()}

@app.post("/api/profiles/test-all")
def test_all_profiles():
    results = key_vault.test_all_profiles()
    return {"results": results, "metrics": key_vault.get_metrics()}

@app.post("/api/profiles/auto-switch")
def set_auto_switch(req: AutoSwitchRequest):
    key_vault.set_auto_switch(req.enabled)
    return {"auto_switch_enabled": req.enabled}

@app.get("/api/voices")
def get_voices():
    return {
        "voices": list(GEMINI_VOICES.keys()),
        "tones": VOICE_TONES,
        "languages": LANGUAGES
    }

@app.post("/api/sample")
def generate_sample(req: SampleRequest):
    try:
        sample_path = voice_engine.get_sample(req.voice_name)
        rel_path = os.path.relpath(sample_path, OUTPUTS_DIR).replace("\\", "/")
        return {
            "success": True,
            "voice_name": req.voice_name,
            "audio_url": f"/api/audio/{rel_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def generate_speech(req: GenerateRequest):
    try:
        file_path, filename, duration_sec = voice_engine.synthesize(
            text=req.text,
            voice_name=req.voice_name,
            tone=req.tone,
            language=req.language
        )
        file_size_kb = os.path.getsize(file_path) // 1024

        rel_path = os.path.relpath(file_path, OUTPUTS_DIR).replace("\\", "/")
        audio_url = f"/api/audio/{rel_path}"

        # Record to history
        history_item = {
            "id": filename,
            "filename": filename,
            "audio_url": audio_url,
            "text_snippet": req.text[:120].strip() + ("..." if len(req.text) > 120 else ""),
            "voice": req.voice_name.split("(")[0].strip(),
            "tone": req.tone.split("(")[0].strip(),
            "language": req.language.split("(")[0].strip(),
            "duration_sec": duration_sec,
            "size_kb": file_size_kb,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        history = load_history()
        history.insert(0, history_item)
        save_history(history[:50])  # keep last 50

        return {
            "success": True,
            "item": history_item,
            "metrics": key_vault.get_metrics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dialogue/detect")
def detect_dialogue_speakers(req: DialogueDetectRequest):
    """Detects distinct character names from a dialogue script."""
    try:
        characters = detect_characters_in_script(req.script)
        dialogue_lines = parse_dialogue_script(req.script)
        return {
            "characters": characters,
            "line_count": len(dialogue_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/dialogue/generate")
def generate_dialogue_audio(req: DialogueGenerateRequest):
    """Synthesizes a multi-character dialogue script into a single HD MP3."""
    try:
        file_path, filename, duration_sec = voice_engine.synthesize_dialogue(
            script_text=req.script,
            character_voice_map=req.character_voices,
            tone=req.tone,
            language=req.language
        )

        file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
        history_item = {
            "id": str(int(time.time())),
            "filename": filename,
            "audio_url": f"/api/audio/{filename}",
            "text_snippet": req.script.strip()[:140] + ("..." if len(req.script.strip()) > 140 else ""),
            "voice": f"🎭 Multi-Voice ({len(req.character_voices)} Characters)",
            "tone": req.tone.split("(")[0].strip(),
            "language": req.language.split("(")[0].strip(),
            "duration_sec": duration_sec,
            "size_kb": file_size_kb,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        history = load_history()
        history.insert(0, history_item)
        save_history(history[:50])

        return {
            "success": True,
            "item": history_item,
            "metrics": key_vault.get_metrics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_path:path}")
def get_audio_file(file_path: str):
    abs_path = os.path.abspath(os.path.join(OUTPUTS_DIR, file_path))
    if not abs_path.startswith(os.path.abspath(OUTPUTS_DIR)) or not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    media_type = "audio/mpeg" if abs_path.endswith(".mp3") else "audio/wav"
    return FileResponse(abs_path, media_type=media_type, filename=os.path.basename(abs_path))

@app.get("/api/history")
def get_history():
    history = load_history()
    valid_history = []
    for h in history:
        f_name = h.get("filename")
        if f_name and os.path.exists(os.path.join(OUTPUTS_DIR, f_name)):
            valid_history.append(h)
    return {"history": valid_history}

@app.delete("/api/history/{filename}")
def delete_history_item(filename: str):
    # Path traversal protection: strict parameter validation
    if "/" in filename or "\\" in filename or ".." in filename or not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        raise HTTPException(status_code=400, detail="Invalid filename parameter")

    file_path = os.path.abspath(os.path.join(OUTPUTS_DIR, filename))
    if not file_path.startswith(os.path.abspath(OUTPUTS_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden access")

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    history = [h for h in load_history() if h.get("filename") != safe_filename]
    save_history(history)
    return {"success": True}

# Serve Frontend static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "VoiceCraft Studio server online. Please build static assets."})

if __name__ == "__main__":
    import uvicorn
    local_ip = get_local_ip()
    print("=" * 65)
    print("[*] VOICECRAFT AI STUDIO - SERVER STARTED")
    port = int(os.environ.get("PORT", 8000))
    print(f"[+] Active Port:    {port}")
    print("=" * 65)
    uvicorn.run(app, host="0.0.0.0", port=port)
