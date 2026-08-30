// VoiceCraft Studio — Cyber Purple & Electric Cyan Engine Logic

let currentTab = 'studio';
let currentViewMode = 'desktop';
let audioPlayer = null;
let isAudioPlaying = false;
let animationFrameId = null;

let allVoicesList = [];
let selectedVoiceName = "🌌 Enceladus (Deep, Epic & Cinematic - Male)";
let currentVoiceFilter = 'all';

let currentStudioMode = 'solo'; // 'solo' or 'dialogue'
let detectedCharacters = [];
let characterVoiceMap = {};

// ── Voice Catalog Metadata (ElevenLabs Style) ──────────────────────────────
function parseVoiceMetadata(rawName) {
  const isFemale = rawName.includes('Female');
  const isMale = rawName.includes('Male');
  const gender = isFemale ? 'Female' : 'Male';

  let tag = "Studio Voice";
  if (rawName.includes('Cinematic') || rawName.includes('Epic') || rawName.includes('Trailer')) tag = "🎬 Cinematic";
  else if (rawName.includes('Viral') || rawName.includes('Energetic') || rawName.includes('Hook')) tag = "🔥 Viral Hook";
  else if (rawName.includes('Calm') || rawName.includes('Soothing') || rawName.includes('Whisper')) tag = "🌸 Calm Narration";
  else if (rawName.includes('Storyteller') || rawName.includes('Podcast')) tag = "📖 Storyteller";
  else if (rawName.includes('Bold') || rawName.includes('Dramatic')) tag = "⚡ Bold & Dramatic";
  else if (rawName.includes('News') || rawName.includes('Anchor')) tag = "💼 News Anchor";
  else if (rawName.includes('Melodious') || rawName.includes('Warm')) tag = "🎵 Melodious";

  const cleanTitle = rawName.split('(')[0].replace(/[🎙️🔥🌸⚡🎵🌌🌬️👑💼✨🎧🏆☀️🌙📖💖🌟🌺💎🎬🎶🚀]/g, '').trim();

  return {
    raw: rawName,
    title: cleanTitle,
    gender: gender,
    tag: tag,
    icon: isFemale ? "🌸" : "🎙️"
  };
}

// ── Initialization ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  audioPlayer = document.getElementById('main-audio-player');
  initViewMode();
  setupAudioListeners();
  setupScriptInputListeners();
  loadVoices();
  loadProfiles();
  loadHistory();
  initWaveformCanvas();

  // Poll system status & profiles periodically (every 10s)
  setInterval(() => {
    loadProfiles(false);
  }, 10000);
});

// ── View Mode: Laptop vs Phone ──────────────────────────────────────────────
function initViewMode() {
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view');
  
  if (viewParam === 'mobile' || viewParam === 'phone') {
    setViewMode('mobile');
  } else if (viewParam === 'desktop' || viewParam === 'laptop') {
    setViewMode('desktop');
  } else if (window.innerWidth < 768) {
    setViewMode('mobile');
  } else {
    const saved = localStorage.getItem('voicecraft_view_mode') || 'desktop';
    setViewMode(saved);
  }
}

function setViewMode(mode) {
  currentViewMode = mode;
  localStorage.setItem('voicecraft_view_mode', mode);

  const body = document.getElementById('app-body');
  const modeTag = document.getElementById('view-mode-tag');

  if (mode === 'mobile') {
    body.classList.remove('desktop-view');
    body.classList.add('mobile-view');
    if (modeTag) modeTag.innerText = "PHONE APP";
  } else {
    body.classList.remove('mobile-view');
    body.classList.add('desktop-view');
    if (modeTag) modeTag.innerText = "LAPTOP STUDIO";
  }

  setTimeout(initWaveformCanvas, 100);
}

// ── Tab Navigation ──────────────────────────────────────────────────────────
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.add('hidden');
    tab.classList.remove('active');
  });

  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }

  // Update bottom nav (mobile)
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-400');
    btn.classList.remove('text-cyan-300');
  });
  const activeNavBtn = document.getElementById(`nav-${tabId}`);
  if (activeNavBtn) {
    activeNavBtn.classList.add('active');
    activeNavBtn.classList.remove('text-slate-400');
    activeNavBtn.classList.add('text-cyan-300');
  }

  // Update desktop sidebar items
  ['studio', 'vault', 'history'].forEach(id => {
    const sideBtn = document.getElementById(`side-${id}`);
    if (sideBtn) {
      if (id === tabId) {
        sideBtn.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold transition text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 shadow-lg shadow-cyan-500/10";
      } else {
        sideBtn.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-[#1a1440] transition border border-transparent";
      }
    }
  });

  if (tabId === 'vault') {
    loadProfiles();
  } else if (tabId === 'history') {
    loadHistory();
  }
}

// ── Live Script Telemetry ───────────────────────────────────────────────────
function setStudioMode(mode) {
  currentStudioMode = mode;
  const btnSolo = document.getElementById('mode-btn-solo');
  const btnDialogue = document.getElementById('mode-btn-dialogue');
  const secSoloVoices = document.getElementById('section-solo-voices');
  const secDialogueChars = document.getElementById('section-dialogue-characters');
  const btnGenText = document.getElementById('btn-generate-text');
  const scriptLabel = document.getElementById('script-section-label');
  const chunkBadge = document.getElementById('chunk-info-badge');

  if (mode === 'dialogue') {
    if (btnDialogue) btnDialogue.className = "flex-1 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600/40 to-cyan-600/40 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10";
    if (btnSolo) btnSolo.className = "flex-1 py-2.5 px-4 rounded-xl text-xs font-medium transition flex items-center justify-center gap-2 text-slate-400 hover:text-slate-200 border border-transparent";
    
    if (secSoloVoices) secSoloVoices.classList.add('hidden');
    if (secDialogueChars) secDialogueChars.classList.remove('hidden');
    if (btnGenText) btnGenText.innerText = "GENERATE MULTI-VOICE DIALOGUE";
    if (scriptLabel) scriptLabel.innerText = "DIALOGUE / PODCAST SCRIPT";
    if (chunkBadge) chunkBadge.innerText = "🎭 Multi-Character Voice Synthesis & Conversational Timing";

    const curr = document.getElementById('script-input').value.trim();
    if (!curr.includes('[') && !curr.includes(':')) {
      loadDialogueSample();
    } else {
      refreshDetectedCharacters();
    }
  } else {
    if (btnSolo) btnSolo.className = "flex-1 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600/40 to-cyan-600/40 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10";
    if (btnDialogue) btnDialogue.className = "flex-1 py-2.5 px-4 rounded-xl text-xs font-medium transition flex items-center justify-center gap-2 text-slate-400 hover:text-slate-200 border border-transparent";

    if (secSoloVoices) secSoloVoices.classList.remove('hidden');
    if (secDialogueChars) secDialogueChars.classList.add('hidden');
    if (btnGenText) btnGenText.innerText = "GENERATE HD AI VOICE";
    if (scriptLabel) scriptLabel.innerText = "NARRATION SCRIPT";
    if (chunkBadge) chunkBadge.innerText = "✨ Smart Multi-Chunk Concatenation (15,000+ chars)";
  }
  updateScriptStats();
}

async function refreshDetectedCharacters() {
  const text = document.getElementById('script-input').value.trim();
  const grid = document.getElementById('character-voice-grid');
  if (!grid) return;

  try {
    const res = await fetch('/api/dialogue/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script: text })
    });
    const data = await res.json();
    detectedCharacters = data.characters || [];

    if (detectedCharacters.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full p-4 rounded-xl bg-[#070512]/60 border border-purple-500/20 text-center text-xs text-slate-400 font-mono">
          No character tags found. Use format: <span class="text-cyan-300 font-bold">[Character Name]: Dialogue line</span>
        </div>
      `;
      return;
    }

    // Default voice pool for smart assignment
    const defaultVoicePool = [
      "🌌 Enceladus (Deep, Epic & Cinematic - Male)",
      "🌸 Kore (Calm, Soft & Soothing - Female)",
      "🔥 Puck (High-Energy, Viral Reels & Hook - Male)",
      "🎵 Aoede (Warm, Melodious & Expressive - Female)",
      "⚡ Fenrir (Bold, Authoritative & Dramatic - Male)",
      "💼 Leda (Professional News Anchor - Female)"
    ];

    let html = '';
    detectedCharacters.forEach((charName, idx) => {
      const assignedVoice = characterVoiceMap[charName] || defaultVoicePool[idx % defaultVoicePool.length];
      characterVoiceMap[charName] = assignedVoice;

      let optionsHtml = '';
      allVoicesList.forEach(v => {
        const isSelected = v.raw === assignedVoice;
        optionsHtml += `<option value="${escapeHtml(v.raw)}" ${isSelected ? 'selected' : ''}>${escapeHtml(v.title)} (${escapeHtml(v.gender)} • ${escapeHtml(v.tag)})</option>`;
      });

      html += `
        <div class="p-3 rounded-xl bg-[#070512]/80 border border-purple-500/25 space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600/40 to-cyan-500/40 border border-cyan-500/40 flex items-center justify-center text-xs font-bold text-cyan-300">
                ${idx + 1}
              </div>
              <span class="text-xs font-bold text-slate-100 font-mono">${escapeHtml(charName)}</span>
            </div>
            <span class="text-[10px] font-mono text-purple-300/80">Voice Assigned</span>
          </div>

          <select onchange="updateCharacterVoice('${escapeHtml(charName)}', this.value)" class="cyber-select w-full text-xs p-2">
            ${optionsHtml}
          </select>
        </div>
      `;
    });

    grid.innerHTML = html;

  } catch (err) {
    console.error("Detect characters error:", err);
  }
}

function updateCharacterVoice(charName, voiceName) {
  characterVoiceMap[charName] = voiceName;
  showToast(`Voice updated for ${charName} 🎙️`, "info");
}

function loadDialogueSample() {
  const sample = `[Narrator]: Andheri raat mein Koh-e-Siyah ke darwaze par achanak dastak hui.
[Rahul]: Darwaza mat kholna Priya! Bahar koi khatarnaak ho sakta hai.
[Priya]: Lekin Rahul, ek baar dekhne toh do kaun hai... Shayad kisi ko madad chahiye ho!
[Narrator]: Tabhi darwaza zoor se khula aur ek ajeeb sa saya samne aa gaya.`;
  document.getElementById('script-input').value = sample;
  updateScriptStats();
  refreshDetectedCharacters();
  showToast("Multi-Voice Drama script loaded! 🎭", "success");
}

function setupScriptInputListeners() {
  const input = document.getElementById('script-input');
  input.addEventListener('input', () => {
    updateScriptStats();
    if (currentStudioMode === 'dialogue') {
      refreshDetectedCharacters();
    }
  });
  updateScriptStats();
}

function updateScriptStats() {
  const text = document.getElementById('script-input').value.trim();
  const charCount = text.length;
  const words = text ? text.split(/\s+/).filter(Boolean) : [];
  const wordCount = words.length;

  document.getElementById('char-count').innerText = charCount;
  document.getElementById('word-count').innerText = wordCount;

  let estSeconds = wordCount === 0 ? 0 : Math.max(1, Math.round(wordCount / 2.5));
  let estText = estSeconds < 60 ? `~${estSeconds}s audio` : `~${Math.floor(estSeconds / 60)}m ${estSeconds % 60}s audio`;

  // Estimate chunks if long-form
  const chunksEst = Math.ceil(charCount / 1200);
  if (chunksEst > 1) {
    estText += ` (${chunksEst} chunks)`;
  }

  document.getElementById('est-duration').innerText = estText;

  const badge = document.getElementById('script-stats-badge');
  if (charCount <= 1200) {
    badge.className = "flex items-center gap-1.5 text-cyan-400 font-semibold";
  } else if (charCount <= 5000) {
    badge.className = "flex items-center gap-1.5 text-purple-300 font-semibold";
  } else {
    badge.className = "flex items-center gap-1.5 text-pink-400 font-semibold";
  }
}

function pasteScript() {
  navigator.clipboard.readText().then(text => {
    if (text) {
      document.getElementById('script-input').value = text;
      updateScriptStats();
      showToast("Script pasted successfully! 📋", "info");
    }
  }).catch(() => {
    showToast("Clipboard access denied. Please paste manually.", "error");
  });
}

function loadSampleText() {
  if (currentStudioMode === 'dialogue') {
    loadDialogueSample();
  } else {
    const sample = "Karakoram ke buland pahadon ke daman mein chhota sa qasba Shigar basa tha. Barf ki thandi hawayen khidkiyon se takra rahi theen. Zaid ek jawan archaeologist tha jise purani tareekh aur an-chhooay raazon ka junoon tha. Kaha jata tha ke Koh-e-Siyah mein ek qadeem tehzeeb ka tilismati khazana dafan tha.";
    document.getElementById('script-input').value = sample;
    updateScriptStats();
    showToast("Epic adventure story script loaded! 📄", "success");
  }
}

function clearScript() {
  document.getElementById('script-input').value = '';
  updateScriptStats();
  if (currentStudioMode === 'dialogue') {
    refreshDetectedCharacters();
  }
}

function loadScriptFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById('script-input').value = e.target.result;
    updateScriptStats();
    if (currentStudioMode === 'dialogue') {
      refreshDetectedCharacters();
    }
    showToast(`Loaded ${file.name}`, "success");
  };
  reader.readAsText(file);
}

// ── Voice Catalog & ElevenLabs Style Cards ──────────────────────────────────
async function loadVoices() {
  try {
    const res = await fetch('/api/voices');
    const data = await res.json();

    allVoicesList = data.voices.map(parseVoiceMetadata);
    renderVoiceCards();

    // Tones Dropdown
    const toneSelect = document.getElementById('select-tone');
    toneSelect.innerHTML = '';
    data.tones.forEach((t, idx) => {
      const opt = document.createElement('option');
      opt.value = t;
      opt.innerText = t;
      if (idx === 0) opt.selected = true;
      toneSelect.appendChild(opt);
    });

    // Languages Dropdown
    const langSelect = document.getElementById('select-lang');
    langSelect.innerHTML = '';
    data.languages.forEach((l, idx) => {
      const opt = document.createElement('option');
      opt.value = l;
      opt.innerText = l;
      if (idx === 0) opt.selected = true;
      langSelect.appendChild(opt);
    });

  } catch (err) {
    showToast("Failed to load voices from server", "error");
  }
}

function filterVoices(category) {
  currentVoiceFilter = category;
  document.querySelectorAll('.pill-filter').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`filter-${category}`);
  if (activeBtn) activeBtn.classList.add('active');
  renderVoiceCards();
}

function renderVoiceCards() {
  const grid = document.getElementById('voices-grid');
  if (!grid) return;

  let filtered = allVoicesList;
  if (currentVoiceFilter === 'male') {
    filtered = allVoicesList.filter(v => v.gender === 'Male');
  } else if (currentVoiceFilter === 'female') {
    filtered = allVoicesList.filter(v => v.gender === 'Female');
  } else if (currentVoiceFilter === 'cinematic') {
    filtered = allVoicesList.filter(v => v.tag.includes('Cinematic') || v.tag.includes('Epic'));
  } else if (currentVoiceFilter === 'viral') {
    filtered = allVoicesList.filter(v => v.tag.includes('Viral') || v.tag.includes('Hook'));
  }

  let html = '';
  filtered.forEach(v => {
    const isSelected = v.raw === selectedVoiceName;
    html += `
      <div onclick="selectVoice('${escapeHtml(v.raw)}')" class="voice-card ${isSelected ? 'selected' : ''}">
        <div class="flex items-center gap-3.5 min-w-0">
          <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr ${v.gender === 'Female' ? 'from-pink-600/30 to-purple-600/30 border border-pink-500/40 text-pink-300' : 'from-cyan-600/30 to-purple-600/30 border border-cyan-500/40 text-cyan-300'} flex items-center justify-center text-base font-bold shrink-0 shadow-md">
            ${v.icon}
          </div>
          <div class="min-w-0 space-y-0.5">
            <div class="flex items-center gap-2">
              <h4 class="text-xs sm:text-sm font-bold text-slate-100 truncate">${escapeHtml(v.title)}</h4>
              ${isSelected ? '<span class="text-[9px] font-mono font-bold bg-cyan-400/20 text-cyan-300 px-1.5 py-0.2 rounded border border-cyan-400/40">SELECTED</span>' : ''}
            </div>
            <p class="text-[10px] font-mono ${isSelected ? 'text-cyan-300' : 'text-purple-300/80'} truncate flex items-center gap-1.5">
              <span>${escapeHtml(v.tag)}</span>
              <span class="text-slate-600">•</span>
              <span class="text-[9px] text-slate-400">24kHz HD</span>
            </p>
          </div>
        </div>

        <button onclick="event.stopPropagation(); playVoiceSample('${escapeHtml(v.raw)}')" title="Preview Sample" class="btn-sample-play">
          ▶
        </button>
      </div>
    `;
  });

  grid.innerHTML = html;
}

function selectVoice(rawName) {
  selectedVoiceName = rawName;
  renderVoiceCards();
  const clean = rawName.split('(')[0].trim();
  showToast(`Voice Selected: ${clean} 🎙️`, "info");
}

function setAudioSpeed(speed) {
  if (audioPlayer) {
    audioPlayer.playbackRate = speed;
  }
  ['10', '125', '15'].forEach(s => {
    const btn = document.getElementById(`speed-${s}`);
    if (btn) {
      btn.className = "px-2.5 py-1 rounded-lg transition text-slate-400 hover:text-white";
    }
  });
  const activeKey = speed === 1.0 ? '10' : (speed === 1.25 ? '125' : '15');
  const activeBtn = document.getElementById(`speed-${activeKey}`);
  if (activeBtn) {
    activeBtn.className = "px-2.5 py-1 rounded-lg transition text-cyan-300 font-bold bg-cyan-500/20";
  }
  showToast(`Speed set to ${speed}x ⚡`, "info");
}

// ── Sample Preview Playback ─────────────────────────────────────────────────
async function playVoiceSample(overrideVoice = null) {
  const voice = overrideVoice || selectedVoiceName;
  showToast(`Loading sample preview... ⏳`, "info");

  try {
    const res = await fetch('/api/sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice_name: voice })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Sample preview failed");

    playAudioUrl(data.audio_url, `Sample Preview: ${voice.split('(')[0]}`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ── Full Voice Generation (Supports Solo & Multi-Voice Dialogue) ────────────
async function generateAudio() {
  const text = document.getElementById('script-input').value.trim();
  if (!text) {
    showToast("Please enter or paste your script first!", "error");
    return;
  }

  const tone = document.getElementById('select-tone').value;
  const language = document.getElementById('select-lang').value;

  const btn = document.getElementById('btn-generate-voice');
  const btnText = document.getElementById('btn-generate-text');

  const isDialogue = currentStudioMode === 'dialogue';

  btn.disabled = true;
  btn.classList.add('opacity-75', 'cursor-wait');
  btnText.innerText = isDialogue ? "SYNTHESIZING DIALOGUE CHARACTERS..." : "SYNTHESIZING HD VOICE...";

  try {
    let res;
    if (isDialogue) {
      res = await fetch('/api/dialogue/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: text,
          character_voices: characterVoiceMap,
          tone: tone,
          language: language
        })
      });
    } else {
      res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          voice_name: selectedVoiceName,
          tone: tone,
          language: language
        })
      });
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Voice synthesis failed");

    const item = data.item;
    showToast(isDialogue ? "Multi-Voice Dialogue ready! 🎭" : "HD Voice synthesized successfully! ⚡", "success");

    // Display Player Card
    const playerCard = document.getElementById('player-card');
    playerCard.classList.remove('hidden');

    document.getElementById('player-voice-title').innerText = `${item.voice} • ${item.duration_sec}s (${item.size_kb} KB)`;
    document.getElementById('btn-download-audio').href = item.audio_url;
    document.getElementById('btn-download-audio').setAttribute('download', item.filename);

    playAudioUrl(item.audio_url, item.voice);

    if (data.metrics) updateMetricsUI(data.metrics);
    loadHistory();

  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.classList.remove('opacity-75', 'cursor-wait');
    btnText.innerText = isDialogue ? "GENERATE MULTI-VOICE DIALOGUE" : "GENERATE HD AI VOICE";
  }
}

// ── Audio Player & Waveform Visualizer ──────────────────────────────────────
function playAudioUrl(url, title = "Voice Output") {
  if (!audioPlayer) return;
  audioPlayer.src = url;
  audioPlayer.play().then(() => {
    isAudioPlaying = true;
    updatePlayBtnIcon(true);
    startWaveformAnimation();
  }).catch(e => {
    console.log("Autoplay notice:", e);
  });
}

function setupAudioListeners() {
  audioPlayer.addEventListener('timeupdate', () => {
    const curr = formatTime(audioPlayer.currentTime);
    const total = formatTime(audioPlayer.duration || 0);
    document.getElementById('player-time-label').innerText = `${curr} / ${total}`;
  });

  audioPlayer.addEventListener('ended', () => {
    isAudioPlaying = false;
    updatePlayBtnIcon(false);
    stopWaveformAnimation();
  });

  audioPlayer.addEventListener('pause', () => {
    isAudioPlaying = false;
    updatePlayBtnIcon(false);
    stopWaveformAnimation();
  });

  audioPlayer.addEventListener('play', () => {
    isAudioPlaying = true;
    updatePlayBtnIcon(true);
    startWaveformAnimation();
  });
}

function togglePlayPause() {
  if (!audioPlayer || !audioPlayer.src) return;
  if (audioPlayer.paused) {
    audioPlayer.play();
  } else {
    audioPlayer.pause();
  }
}

function replayAudio() {
  if (!audioPlayer || !audioPlayer.src) return;
  audioPlayer.currentTime = 0;
  audioPlayer.play();
}

function updatePlayBtnIcon(playing) {
  const btn = document.getElementById('btn-toggle-play');
  if (btn) {
    btn.innerHTML = playing ? '⏸' : '▶';
  }
}

function formatTime(seconds) {
  if (isNaN(seconds)) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
}

// ── Canvas Waveform Visualizer (Cyber Purple & Cyan Edition) ────────────────
function initWaveformCanvas() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  canvas.width = canvas.parentElement.clientWidth * 2;
  canvas.height = canvas.parentElement.clientHeight * 2;

  canvas.style.cursor = 'pointer';
  canvas.onclick = function(e) {
    if (!audioPlayer || !audioPlayer.duration) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, clickX / rect.width));
    audioPlayer.currentTime = pct * audioPlayer.duration;
  };

  drawStaticWaveform();
}

function drawStaticWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  const bars = 52;
  const barWidth = w / bars - 4;

  for (let i = 0; i < bars; i++) {
    const barHeight = (Math.sin(i * 0.35) * 0.35 + 0.5) * (h * 0.55);
    const x = i * (barWidth + 4);
    const y = (h - barHeight) / 2;

    const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
    grad.addColorStop(0, 'rgba(139, 92, 246, 0.4)');
    grad.addColorStop(1, 'rgba(6, 182, 212, 0.25)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect(x, y, barWidth, barHeight, 3);
    ctx.fill();
  }
}

function startWaveformAnimation() {
  stopWaveformAnimation();
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let step = 0;

  function render() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const bars = 52;
    const barWidth = w / bars - 4;
    const progress = (audioPlayer && audioPlayer.duration) 
      ? audioPlayer.currentTime / audioPlayer.duration 
      : 0;

    for (let i = 0; i < bars; i++) {
      const isPast = (i / bars) <= progress;
      const wave = Math.sin(step * 0.18 + i * 0.4) * 0.4 + 0.6;
      const barHeight = Math.max(8, wave * (h * 0.8));
      const x = i * (barWidth + 4);
      const y = (h - barHeight) / 2;

      const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
      if (isPast) {
        grad.addColorStop(0, '#00f2fe');
        grad.addColorStop(1, '#8b5cf6');
      } else {
        grad.addColorStop(0, 'rgba(139, 92, 246, 0.5)');
        grad.addColorStop(1, 'rgba(6, 182, 212, 0.25)');
      }

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barHeight, 3);
      ctx.fill();
    }

    step++;
    if (isAudioPlaying) {
      animationFrameId = requestAnimationFrame(render);
    } else {
      drawStaticWaveform();
    }
  }

  render();
}

function stopWaveformAnimation() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  drawStaticWaveform();
}

// ── API Vault & Profiles Management ─────────────────────────────────────────
async function loadProfiles(showLoader = true) {
  try {
    const res = await fetch('/api/profiles');
    const data = await res.json();
    updateMetricsUI(data.metrics);
    renderProfilesList(data.profiles);
  } catch (err) {
    console.error("Profiles fetch notice:", err);
  }
}

function updateMetricsUI(metrics) {
  if (!metrics) return;
  document.getElementById('stat-total-keys').innerText = metrics.total_keys;
  document.getElementById('stat-active-keys').innerText = `${metrics.active_keys} 🟢`;
  document.getElementById('stat-cooling-keys').innerText = `${metrics.cooling_keys} 🔴`;

  const sideActive = document.getElementById('side-stat-active');
  if (sideActive) sideActive.innerText = `${metrics.active_keys} 🟢`;

  const autoSwitchToggle = document.getElementById('toggle-auto-switch');
  if (autoSwitchToggle) {
    autoSwitchToggle.checked = metrics.auto_switch_enabled;
  }

  // Header status pill
  const topText = document.getElementById('top-api-text');
  const topDot = document.getElementById('top-api-dot');

  if (metrics.active_keys > 0) {
    topText.innerText = `${metrics.active_keys} Key${metrics.active_keys > 1 ? 's' : ''} Active 🟢`;
    topText.className = "text-xs font-mono font-medium text-cyan-300";
    topDot.className = "w-2 h-2 rounded-full bg-cyan-400 animate-pulse";
  } else if (metrics.total_keys > 0) {
    topText.innerText = "Keys Cooling 🔴";
    topText.className = "text-xs font-mono font-medium text-pink-400";
    topDot.className = "w-2 h-2 rounded-full bg-pink-400";
  } else {
    topText.innerText = "No Keys! Add ➕";
    topText.className = "text-xs font-mono font-medium text-amber-400";
    topDot.className = "w-2 h-2 rounded-full bg-amber-400";
  }

  fetch('/api/status').then(r => r.json()).then(s => {
    const sideIp = document.getElementById('side-network-ip');
    if (sideIp && s.local_ip) {
      sideIp.innerText = `http://${s.local_ip}:8000`;
    }
  }).catch(() => {});
}

function renderProfilesList(profiles) {
  const container = document.getElementById('profiles-list-container');
  document.getElementById('profile-count').innerText = profiles ? profiles.length : 0;

  if (!profiles || profiles.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-xs text-purple-300/60 font-mono">
        No API keys saved yet. Add your first key above!
      </div>
    `;
    return;
  }

  let html = '';
  profiles.forEach(p => {
    const isCooling = p.cooldown_remaining > 0 || p.status === 'RATE_LIMITED';
    const isError = p.status === 'ERROR';

    let badgeClass = 'text-cyan-300 bg-cyan-500/10 border-cyan-500/30';
    let badgeText = '🟢 ACTIVE (Ready)';

    if (isCooling) {
      badgeClass = 'text-pink-400 bg-pink-500/10 border-pink-500/30';
      badgeText = `🔴 RATE LIMITED (${p.cooldown_remaining}s cooldown)`;
    } else if (isError) {
      badgeClass = 'text-red-400 bg-red-500/10 border-red-500/30';
      badgeText = '🔴 ERROR (Invalid)';
    }

    const pct = Math.min(100, Math.round((p.requests_today / 1500) * 100));

    html += `
      <div class="cyber-card p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${isCooling ? 'border-pink-500/40' : 'border-purple-500/20'}">
        <div class="space-y-1.5 flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <h3 class="text-xs sm:text-sm font-bold text-slate-100 truncate">${escapeHtml(p.name)}</h3>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border ${badgeClass}">
              ${badgeText}
            </span>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400">
            <span class="text-cyan-300 font-semibold">${p.masked_key}</span>
            <span>•</span>
            <span>Used: <span class="text-slate-200 font-semibold">${p.requests_today}</span> / 1500 calls</span>
          </div>
          <!-- Usage Progress Bar -->
          <div class="w-full max-w-xs h-1.5 bg-[#070512] rounded-full overflow-hidden border border-purple-500/20">
            <div class="h-full bg-gradient-to-r from-purple-500 to-cyan-400 rounded-full" style="width: ${Math.max(4, pct)}%"></div>
          </div>
        </div>

        <div class="flex items-center gap-2 self-end sm:self-center shrink-0">
          <button onclick="testSingleProfile('${p.id}')" title="Test Key" class="btn-cyber-ghost text-xs px-2.5 py-1.5 flex items-center gap-1 text-cyan-300">
            <span>⚡</span> Test
          </button>
          <button onclick="deleteProfile('${p.id}')" title="Delete Key" class="btn-cyber-ghost text-xs px-2 py-1.5 text-pink-400 hover:text-pink-300">
            <span>🗑️</span>
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function addApiProfile() {
  const nameInput = document.getElementById('new-profile-name');
  const keyInput = document.getElementById('new-profile-key');
  const btn = document.getElementById('btn-save-key');

  const name = nameInput.value.trim() || "Google AI Studio Key";
  const key = keyInput.value.trim();

  if (!key) {
    showToast("Please enter an API key!", "error");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Verifying with Google... ⏳";

  try {
    const res = await fetch('/api/profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, key: key, validate_key: true })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Validation failed");

    showToast(data.message || "Key saved & verified! 🟢", "success");
    nameInput.value = '';
    keyInput.value = '';

    loadProfiles();
  } catch (err) {
    showToast(`Failed: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>💾</span> Save & Verify API Profile`;
  }
}

async function testSingleProfile(id) {
  showToast("Testing API Key with Google...", "info");
  try {
    const res = await fetch(`/api/profiles/${id}/test`, { method: 'POST' });
    const data = await res.json();
    if (data.valid) {
      showToast("API Key is 100% Active & Ready! 🟢", "success");
    } else {
      showToast(`Notice: ${data.message}`, "error");
    }
    loadProfiles();
  } catch (err) {
    showToast("Test request failed", "error");
  }
}

async function testAllProfiles() {
  showToast("Testing all configured API keys concurrently...", "info");
  try {
    const res = await fetch('/api/profiles/test-all', { method: 'POST' });
    const data = await res.json();
    showToast("All keys tested successfully! ⚡", "success");
    loadProfiles();
  } catch (err) {
    showToast("Test-all failed", "error");
  }
}

async function deleteProfile(id) {
  if (!confirm("Are you sure you want to delete this API profile?")) return;
  try {
    const res = await fetch(`/api/profiles/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("Delete failed");
    showToast("API Profile deleted", "info");
    loadProfiles();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function toggleAutoSwitch(enabled) {
  try {
    await fetch('/api/profiles/auto-switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enabled })
    });
    showToast(`Auto-switch ${enabled ? 'Enabled' : 'Disabled'}`, "info");
  } catch (err) {
    console.error("Auto switch toggle notice:", err);
  }
}

function toggleKeyVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
}

// ── Audio Recordings History ────────────────────────────────────────────────
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    renderHistoryList(data.history);
  } catch (err) {
    console.error("History fetch notice:", err);
  }
}

function renderHistoryList(history) {
  const container = document.getElementById('history-list-container');
  if (!history || history.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-xs text-purple-300/60 font-mono">
        No recent audios generated yet.
      </div>
    `;
    return;
  }

  let html = '';
  history.forEach(item => {
    html += `
      <div class="cyber-card p-3.5 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-cyan-300 font-mono">${escapeHtml(item.voice)}</span>
          <span class="text-[11px] font-mono text-slate-400">${item.timestamp}</span>
        </div>
        <p class="text-xs text-slate-300 font-sans line-clamp-2">"${escapeHtml(item.text_snippet)}"</p>
        <div class="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-400">
          <span>${item.duration_sec}s • ${item.size_kb} KB</span>
          <div class="flex items-center gap-2">
            <button onclick="playAudioUrl('${item.audio_url}', '${escapeHtml(item.voice)}')" class="btn-cyber-ghost px-2.5 py-1 text-cyan-300">
              ▶ Play
            </button>
            <a href="${item.audio_url}" download="${item.filename}" class="btn-cyber-ghost px-2.5 py-1 text-purple-300 hover:text-purple-200">
              ⬇ Download
            </a>
            <button onclick="deleteHistoryItem('${item.filename}')" class="btn-cyber-ghost px-2 py-1 text-pink-400 hover:text-pink-300">
              🗑️
            </button>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function deleteHistoryItem(filename) {
  try {
    await fetch(`/api/history/${filename}`, { method: 'DELETE' });
    loadHistory();
    showToast("Recording removed from history", "info");
  } catch (err) {
    showToast("Could not delete recording", "error");
  }
}

// ── Toast Notifications ─────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  toast.innerText = message;
  toast.className = `fixed bottom-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-2xl text-xs font-mono font-medium shadow-2xl border transition-all duration-300 opacity-100 translate-y-0 toast-${type}`;

  setTimeout(() => {
    toast.className = "fixed bottom-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-2xl text-xs font-mono font-medium shadow-2xl border transition-all duration-300 opacity-0 pointer-events-none translate-y-2";
  }, 3200);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[tag] || tag));
}
