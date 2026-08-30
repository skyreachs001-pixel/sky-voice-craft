import os
import sys
import json
import base64
import time
import wave
import re
import subprocess
import shutil
import urllib.request
import urllib.error

# 25+ Curated Google AI Studio Gemini Voices
GEMINI_VOICES = {
    "🌌 Enceladus (Deep, Epic & Cinematic - Male)": "Charon",
    "🎙️ Charon (Classic Narrator & Documentary - Male)": "Charon",
    "🔥 Puck (Energetic, Youthful & Viral Hook - Male)": "Puck",
    "⚡ Sirius (Bright, High-Energy & Dynamic - Male)": "Puck",
    "🚀 Altair (Crisp & High-Paced - Male)": "Puck",
    "🎧 Castor (Storyteller & Podcast Host - Male)": "Puck",
    "🎙️ Arcturus (Warm, Engaging Storyteller - Male)": "Puck",
    "🌸 Kore (Calm, Soft & Soothing - Female)": "Kore",
    "🌙 Selene (Mysterious, Whispering & Soft - Female)": "Kore",
    "✨ Vega (Bright, Cheerful & Dynamic - Female)": "Kore",
    "🌺 Capella (Polite, Tender & Gentle - Female)": "Kore",
    "⚡ Fenrir (Bold, Authoritative & Dramatic - Male)": "Fenrir",
    "👑 Orus (Commanding, Regal & Powerful - Male)": "Fenrir",
    "🏆 Pollux (Inspiring, Heroic & Motivational - Male)": "Fenrir",
    "🌟 Algieba (Rich & Resonant Deep Voice - Male)": "Fenrir",
    "🎵 Aoede (Warm, Melodious & Expressive - Female)": "Aoede",
    "💼 Leda (Professional News Anchor - Female)": "Aoede",
    "💖 Lyra (Emotional, Tender & Expressive - Female)": "Aoede",
    "💎 Bellatrix (Crisp, Modern & Direct - Female)": "Aoede",
    "🎶 Spica (Melodic, Friendly & Cheerful - Female)": "Aoede",
    "🌬️ Zephyr (Smooth, Gentle & Flowing - Male)": "Charon",
    "☀️ Helios (Warm, Friendly & Clear - Male)": "Charon",
    "📖 Alcor (Documentary & Educational Explainer - Male)": "Charon",
    "🎬 Canopus (Epic Trailer Narrator - Male)": "Charon",
    "🌌 Deneb (Atmospheric, Deep & Cosmic - Male)": "Charon",
}

VOICE_TONES = [
    "🔥 Energetic & Excited (Reels Viral Hook)",
    "🎬 Dramatic & Cinematic Storyteller",
    "✨ Natural & Conversational (Casual Hindi/English)",
    "🧘 Calm, Soft & Soothing (Meditation / Relaxing)",
    "💼 Professional & News Anchor (Formal)",
    "⚡ Fast-Paced & Urgent (Breaking / Trending)",
    "📖 Expressive Book & Audio Story Narrator",
    "👻 Mystery, Dark & Thriller (Suspense)",
    "😂 Fun, Humorous & Playful",
    "❤️ Emotional & Heart-touching",
]

LANGUAGES = [
    "Hindi (Natural Indian Accent)",
    "Hinglish (Casual YouTube / Social Media Style)",
    "English (Indian Accent)",
    "English (US Accent)",
    "English (UK Accent)",
    "Urdu (Poetic & Elegant)",
    "Bengali (Bangla)",
    "Marathi",
    "Gujarati",
    "Tamil",
    "Telugu",
    "Punjabi",
    "Arabic",
    "Spanish",
    "French",
]

TTS_MODELS = [
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts"
]

VALID_BASE_VOICES = {"Puck", "Charon", "Kore", "Fenrir", "Aoede"}

def clean_voice_id(voice_input: str) -> str:
    """Extract valid Google AI voice identifier (Charon, Puck, Kore, Fenrir, Aoede)."""
    if not voice_input:
        return "Charon"
    if voice_input in GEMINI_VOICES:
        return GEMINI_VOICES[voice_input]
    voice_str = str(voice_input).strip()
    if voice_str in VALID_BASE_VOICES:
        return voice_str
    for v_name in VALID_BASE_VOICES:
        if v_name.lower() in voice_str.lower():
            return v_name
    match = re.search(r'[A-Za-z]+', voice_str)
    if match:
        w = match.group(0)
        for v_name in VALID_BASE_VOICES:
            if v_name.lower() == w.lower():
                return v_name
    return "Charon"

def clean_text_for_tts(text: str) -> str:
    """Strips markdown and normalizes whitespace so narrator speaks cleanly."""
    if not text:
        return ""
    # Strip markdown symbols (*, _, `, ~, #)
    cleaned = re.sub(r'[\*_`~#]', '', text)
    # Replace excessive linebreaks
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def split_text_into_chunks(text: str, max_chars: int = 1200) -> list[str]:
    """Smart sentence chunking on punctuation marks (., !, ?, ।, \n)."""
    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        return []
    if len(cleaned_text) <= max_chars:
        return [cleaned_text]

    sentence_pattern = r'([^.!?।\n]+[.!?।\n]+|[^.!?।\n]+$)'
    raw_sentences = [s.strip() for s in re.findall(sentence_pattern, cleaned_text) if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in raw_sentences:
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            words = sentence.split(" ")
            word_chunk = ""
            for w in words:
                if len(word_chunk) + len(w) + 1 <= max_chars:
                    word_chunk = f"{word_chunk} {w}".strip()
                else:
                    if word_chunk:
                        chunks.append(word_chunk.strip())
                    word_chunk = w
            if word_chunk:
                current_chunk = word_chunk
        elif len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk = f"{current_chunk} {sentence}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def parse_dialogue_script(script_text: str) -> list[dict]:
    """
    Parses a multi-speaker script with character tags into structured lines.
    Supports formats:
    [Narrator]: Dialogue line
    [Rahul]: Dialogue line
    Narrator: Dialogue line
    Rahul: Dialogue line
    """
    if not script_text:
        return []

    lines = script_text.strip().split("\n")
    dialogue_items = []
    current_speaker = "Narrator"
    current_text = []

    speaker_pattern = re.compile(r'^(?:\[([^\]]+)\]|([A-Za-z0-9_\s\u0900-\u097F\-]+))\s*[:：]?\s*(.*)$')

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        match = speaker_pattern.match(line_str)
        if match:
            if current_text:
                dialogue_items.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text).strip()
                })
                current_text = []
            speaker_name = (match.group(1) or match.group(2)).strip()
            current_speaker = speaker_name
            content = match.group(3).strip()
            if content:
                current_text.append(content)
        else:
            current_text.append(line_str)

    if current_text:
        dialogue_items.append({
            "speaker": current_speaker,
            "text": " ".join(current_text).strip()
        })

    return dialogue_items

def detect_characters_in_script(script_text: str) -> list[str]:
    """Extracts unique character names present in the dialogue script."""
    items = parse_dialogue_script(script_text)
    speakers = []
    for it in items:
        sp = it["speaker"]
        if sp not in speakers:
            speakers.append(sp)
    return speakers

def find_ffmpeg_executable() -> str | None:
    """Locate FFmpeg in PATH, system dirs, or local project folder."""
    in_path = shutil.which("ffmpeg")
    if in_path:
        return in_path

    # Check known paths in project hierarchy
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(curr_dir)
    grandparent = os.path.dirname(parent_dir)

    possible_locations = [
        # In VoiceCraft_AI_Studio
        os.path.join(parent_dir, "ffmpeg", "ffmpeg.exe"),
        os.path.join(parent_dir, "ffmpeg.exe"),
        # In sibling video automation directories
        os.path.join(grandparent, "video automation by arsh", "video automation by arsh", "video automation", "ffmpeg", "ffmpeg.exe"),
        os.path.join(grandparent, "ffmpeg", "ffmpeg.exe"),
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for loc in possible_locations:
        if os.path.exists(loc):
            return loc

    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    return None

class VoiceEngine:
    """Speech synthesis engine with Multi-Key Auto-Rotation and zero downtime."""

    def __init__(self, key_vault, output_dir: str):
        self.key_vault = key_vault
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.samples_dir = os.path.join(self.output_dir, "samples")
        os.makedirs(self.samples_dir, exist_ok=True)

    def _fetch_chunk(self, chunk_text: str, voice_base: str, tone: str, language: str) -> bytes:
        """
        Synthesize a chunk with multi-key auto-rotation.
        If a key hits HTTP 429, marks it rate-limited and instantly rotates to the next key.
        """
        style_instructions = f"Speak in {language}. Style & Tone: {tone}. Deliver with natural human expressiveness, clear cadence, and authentic pronunciation."
        final_prompt = f"[System instruction: {style_instructions}]\n\nRead the following narration naturally:\n\"{chunk_text}\""

        payload = {
            "contents": [
                {"parts": [{"text": final_prompt}]}
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_base
                        }
                    }
                }
            }
        }

        # Try up to 4 rounds across candidate keys
        for round_idx in range(4):
            candidates = self.key_vault.get_candidate_keys_for_generation()
            if not candidates:
                raise ValueError("No active API Keys available! Please add at least one Google AI Studio API key in the API Vault tab.")

            for profile in candidates:
                p_id = profile["id"]
                p_key = profile["key"].strip().strip('"\'')
                p_name = profile["name"]

                for model in TTS_MODELS:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={p_key}"
                    try:
                        req = urllib.request.Request(
                            url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=35) as resp:
                            res_data = json.loads(resp.read().decode("utf-8"))
                            candidates_list = res_data.get("candidates", [])
                            if candidates_list:
                                parts = candidates_list[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    if "inlineData" in p and "data" in p["inlineData"]:
                                        raw_b64 = p["inlineData"]["data"]
                                        pcm_data = base64.b64decode(raw_b64)
                                        # Mark key success
                                        self.key_vault.mark_success(p_id)
                                        return pcm_data
                    except urllib.error.HTTPError as http_err:
                        if http_err.code == 429:
                            # Try other models in TTS_MODELS which have separate quota pools
                            continue
                        elif http_err.code in (400, 403):
                            # Invalid key
                            self.key_vault.update_profile(p_id, enabled=False)
                            break
                        else:
                            continue
                    except Exception:
                        continue

                # If loop completed without return, all models on this key were exhausted
                self.key_vault.mark_rate_limited(p_id, cooldown_seconds=18)

            # If all keys are currently cooling down, dynamically wait for cooldown to expire
            rem_wait = 12.0
            try:
                candidates_now = self.key_vault.get_candidate_keys_for_generation()
                if candidates_now:
                    active_now = [c for c in candidates_now if c.get("cooldown_remaining", 0) == 0 and c.get("status") == "ACTIVE"]
                    if not active_now:
                        coolings = [c.get("cooldown_remaining", 0) for c in candidates_now if c.get("cooldown_remaining", 0) > 0]
                        if coolings:
                            rem_wait = min(coolings)
            except Exception:
                pass

            time.sleep(min(rem_wait + 1.0, 20.0))

        raise RuntimeError("All configured API Keys are currently rate-limited. Please wait 20 seconds or add another API key to the Vault.")

    def _save_pcm_to_mp3(self, merged_pcm: bytearray, base_filename: str) -> tuple[str, str, int]:
        """Saves PCM to WAV and converts to HD MP3 with FFmpeg (or WAV fallback)."""
        temp_wav = os.path.join(self.output_dir, f"{base_filename}_temp.wav")
        final_mp3 = os.path.join(self.output_dir, f"{base_filename}.mp3")

        # 1. Save PCM as 24kHz 16-bit Mono WAV
        with wave.open(temp_wav, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(bytes(merged_pcm))

        total_samples = len(merged_pcm) // 2
        duration_sec = max(1, round(total_samples / 24000))

        # 2. Convert to HD MP3 via FFmpeg
        ffmpeg_exe = find_ffmpeg_executable()
        if ffmpeg_exe:
            try:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", temp_wav,
                    "-codec:a", "libmp3lame",
                    "-qscale:a", "2",
                    final_mp3
                ]
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
                if res.returncode == 0 and os.path.exists(final_mp3):
                    os.remove(temp_wav)
                    return final_mp3, f"{base_filename}.mp3", duration_sec
            except Exception:
                pass

        # Fallback to WAV if FFmpeg is unavailable
        final_wav = os.path.join(self.output_dir, f"{base_filename}.wav")
        if os.path.exists(temp_wav):
            if os.path.exists(final_wav):
                os.remove(final_wav)
            os.rename(temp_wav, final_wav)
            return final_wav, f"{base_filename}.wav", duration_sec

        raise RuntimeError("Audio file could not be saved to disk.")

    def synthesize(self, text: str, voice_name: str, tone: str, language: str, custom_filename: str = None, progress_callback = None) -> tuple[str, str, int]:
        """
        Synthesize narration into an HD MP3.
        Supports multi-chunk processing for long-form scripts (15,000+ chars).
        Returns: (file_path, filename, duration_seconds)
        """
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            raise ValueError("Input script text cannot be empty!")

        base_voice = clean_voice_id(voice_name)
        chunks = split_text_into_chunks(clean_text, max_chars=1200)

        # 120ms natural breathing silence gap at 24000Hz 16-bit mono
        silence_bytes = b'\x00' * int(24000 * 2 * 0.12)
        merged_pcm = bytearray()

        for idx, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(idx + 1, len(chunks), f"Synthesizing chunk {idx + 1}/{len(chunks)}...")
            pcm = self._fetch_chunk(chunk, base_voice, tone, language)
            if merged_pcm:
                merged_pcm.extend(silence_bytes)
            merged_pcm.extend(pcm)
            if idx < len(chunks) - 1:
                time.sleep(0.5)

        timestamp = int(time.time())
        snippet = "".join(c for c in clean_text[:20] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        if not snippet:
            snippet = "audio"
        base_filename = custom_filename or f"voice_{timestamp}_{snippet}"
        base_filename = os.path.splitext(base_filename)[0]

        return self._save_pcm_to_mp3(merged_pcm, base_filename)

    def synthesize_dialogue(self, script_text: str, character_voice_map: dict, tone: str, language: str, custom_filename: str = None, progress_callback = None) -> tuple[str, str, int]:
        """
        Synthesizes a multi-speaker / character conversation into a single continuous HD MP3.
        character_voice_map maps character names (e.g. 'Narrator', 'Rahul') to Gemini voices.
        """
        dialogue_items = parse_dialogue_script(script_text)
        if not dialogue_items:
            raise ValueError("No valid dialogue lines detected in script! Format: [Character Name]: Dialogue line")

        # 250ms natural conversational silence gap between speakers
        conversational_silence = b'\x00' * int(24000 * 2 * 0.25)
        merged_pcm = bytearray()

        total_lines = len(dialogue_items)
        for idx, item in enumerate(dialogue_items):
            speaker = item["speaker"]
            line_text = clean_text_for_tts(item["text"])
            if not line_text:
                continue

            voice_for_speaker = character_voice_map.get(speaker) or character_voice_map.get(speaker.lower()) or "Charon"
            base_voice = clean_voice_id(voice_for_speaker)

            if progress_callback:
                progress_callback(idx + 1, total_lines, f"Synthesizing {speaker} ({idx + 1}/{total_lines})...")

            # Split line into chunks if a single character dialogue is exceptionally long
            sub_chunks = split_text_into_chunks(line_text, max_chars=1200)
            for sub_c in sub_chunks:
                pcm = self._fetch_chunk(sub_c, base_voice, tone, language)
                if merged_pcm:
                    merged_pcm.extend(conversational_silence)
                merged_pcm.extend(pcm)
                time.sleep(1.2)

        if not merged_pcm:
            raise ValueError("No audio was generated from the dialogue script.")

        timestamp = int(time.time())
        base_filename = custom_filename or f"dialogue_{timestamp}_podcast"
        base_filename = os.path.splitext(base_filename)[0]

        return self._save_pcm_to_mp3(merged_pcm, base_filename)

    def get_sample(self, voice_name: str) -> str:
        """Returns path to cached 2-second voice sample, creating it if needed."""
        clean_name = clean_voice_id(voice_name)
        safe_key = "".join(c for c in str(voice_name) if c.isalnum() or c in " _-").strip().replace(" ", "_")
        if not safe_key:
            safe_key = clean_name

        sample_mp3 = os.path.join(self.samples_dir, f"sample_{safe_key}.mp3")
        sample_wav = os.path.join(self.samples_dir, f"sample_{safe_key}.wav")

        if os.path.exists(sample_mp3):
            return sample_mp3
        if os.path.exists(sample_wav):
            return sample_wav

        display_name = str(voice_name).split("(")[0].strip()
        sample_text = f"Namaste! Yeh {display_name} voice ka audio sample preview hai."

        out_path, _, _ = self.synthesize(
            text=sample_text,
            voice_name=voice_name,
            tone="✨ Natural & Conversational (Casual Hindi/English)",
            language="Hindi (Natural Indian Accent)",
            custom_filename=os.path.join("samples", f"sample_{safe_key}")
        )
        return out_path
