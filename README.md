# 🎙️ Sky Voice Craft

A high-fidelity, luxury **Text-to-Speech (TTS)** web and mobile application powered by **Google AI Studio (Gemini 2.5 TTS)**. Designed by **Skyreachs Media** for YouTubers, video creators, podcasters, and storytellers.

---

## 🌟 Key Features

1. **25+ Gemini Studio Voices**:
   - Deep & Epic Narrators (Enceladus, Charon, Deneb)
   - High-Energy Viral Hooks (Puck, Sirius, Altair)
   - Calm & Soothing (Kore, Selene, Capella)
   - Bold & Dramatic (Fenrir, Orus, Pollux)
   - Melodic & Warm (Aoede, Lyra, Spica)
2. **10+ Vocal Tones & Emotions**:
   - Reels Viral Hook, Dramatic Storyteller, Natural Conversational, Mystery/Thriller, Emotional, etc.
3. **16+ Languages & Accents**:
   - Hindi (Natural Indian Accent), Hinglish (Casual YouTube), Indian English, US/UK English, Urdu, Punjabi, etc.
4. **Smart API Key Vault & Unlimited Auto-Rotation**:
   - Add unlimited Google AI Studio free API keys with custom profile names.
   - **Zero Downtime Fallback**: If a key hits HTTP 429 rate limit, it automatically rotates to the next active key in milliseconds.
   - Real-time status monitoring (Active 🟢, Cooling Down 🔴, Requests handled today).
5. **Smart Auto-Chunking & Natural Silence**:
   - Automatically handles long scripts (5,000+ words) without sentence cuts.
   - Inserts natural 120ms human breathing pauses between chunks.
6. **In-App Waveform Player & Direct MP3 Download**:
   - Animated visualizer, instant seek, 1-click download directly into your phone/PC storage.

---

## 🚀 How to Run on Laptop / PC (1-Click)

- **For Full Studio Workstation**: Double-click `Laptop_Version.bat`.
- **For Standalone Mobile Phone Window**: Double-click `Phone_Version.bat`.

---

## 📱 How to Use on Your Smartphone (Android & iPhone)

### Method 1: Local Wi-Fi (No Hosting Required, 0 Cost)
1. Ensure your laptop and phone are connected to the **same Wi-Fi network** (or phone hotspot).
2. Start `Laptop_Version.bat` or `Phone_Version.bat` on your laptop.
3. Look at the left sidebar — it displays your local phone access link, for example:
   ```
   📱 Phone Access: http://192.168.1.5:8000
   ```
4. Open that URL on your phone's Chrome or Safari browser.
5. In your mobile browser menu, tap **"Add to Home Screen"**.
6. The app will now appear on your phone's home screen like a native mobile app!

---

## 💼 How to Deliver to Clients

### Option A: Direct Standalone ZIP Package (Easiest & Complete Control)
1. Right-click the `VoiceCraft_AI_Studio` folder and select **Compress to ZIP file**.
2. Rename the zip file to `Sky_Voice_Craft_v1.0.zip`.
3. Send this zip file to your client (via Google Drive, WeTransfer, Telegram, or WhatsApp).
4. The client simply extracts the zip and double-clicks `Laptop_Version.bat` (or `Phone_Version.bat`).
5. It opens instantly on their PC!

### Option B: 24/7 Cloud Hosted Web Link (0 Client Setup - Recommended for Mobile Clients)
1. Create a free account at [Hugging Face](https://huggingface.co) or [Render](https://render.com).
2. Deploy this repository as a **Docker** or **Python Space** (100% free forever).
3. Send your client the live public URL (e.g. `https://sky-voicecraft.hf.space`).
4. The client can open the link on their phone or laptop without installing anything! They tap "Add to Home Screen" and it functions as a native mobile app.
