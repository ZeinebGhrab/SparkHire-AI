# 🧠 AI Services — SparkHire AI

This module groups the four artificial intelligence services that form the core of the pipeline: **ASR**, **TTS**, **LLM**, and **Facial Analysis**.

---

## Overview

```
backend/services/
├── asr_service.py           ← Speech recognition (Whisper GPU / Vosk)
├── tts_service.py           ← Speech synthesis (Edge-TTS + gTTS fallback)
├── edge_tts_engine.py       ← Edge-TTS engine with network retry
├── llm_service.py           ← LLM evaluation (Ollama + Llama 3.2)
├── facial_analysis_service.py ← Behavioral analysis (MediaPipe + HSEmotion)
└── avatar_service.py        ← Avatar provider (simple / D-ID)
```

---

## Files
 
| File | Description |
|---|---|
| `asr_service.py` | Speech recognition (Whisper GPU / Vosk offline) |
| `tts_service.py` | Speech synthesis (Edge-TTS primary + gTTS fallback) |
| `edge_tts_engine.py` | Edge-TTS engine with network retry logic |
| `llm_service.py` | LLM evaluation via Ollama + Llama 3.2 |
| `facial_analysis_service.py` | Behavioral analysis (MediaPipe + HSEmotion) |
| `avatar_service.py` | Avatar video provider (simple / D-ID stub) |
 
---

## 1. ASR — Speech Recognition

**File:** `asr_service.py`

### Architecture

```
WhisperASR (faster-whisper)     ← primary engine (GPU recommended)
VoskASR                         ← offline fallback (Arabic only)
ASRService                      ← unified facade
```

### How It Works

1. Receives audio bytes (PCM or WAV).
2. Writes to a temporary WAV file if necessary.
3. Calls `WhisperModel.transcribe()` with integrated VAD.
4. Returns the transcript as a string.

### Key Parameters

| Parameter | Recommended Value | Description |
|---|---|---|
| `model_size` | `medium` | Precision/speed trade-off |
| `device` | `cuda` | GPU if available, else `cpu` |
| `compute_type` | `float16` (GPU) / `int8` (CPU) | Quantization type |
| `vad_filter` | `true` | Voice Activity Detection filter |
| `min_silence_duration_ms` | 500 | Minimum detected silence |

### Supported Languages

`ar` (Arabic) · `fr` (French) · `en` (English)

### Performance

| Model | Size | CPU | GPU (RTX 4050) |
|---|---|---|---|
| tiny | 75 MB | ~2 s | ~0.5 s |
| medium | 1.5 GB | 5–10 s | ~1–3 s |
| large-v3 | 3.1 GB | — | ~2–5 s (GPU 6 GB+) |

### Usage

```python
from backend.services import get_asr_service

asr = get_asr_service()
transcript = asr.transcribe(wav_bytes, language="fr")
```

---

## 2. TTS — Speech Synthesis

**Files:** `tts_service.py` · `edge_tts_engine.py`

### Architecture

```
EdgeEngine (Edge-TTS 7.x)   ← primary (Microsoft neural TTS)
    └── retry × 3 on 403 / network timeout
GoogleEngine (gTTS)         ← automatic fallback
TTSService                  ← MD5 cache + engine selection
```

### Configured Voices

| Language | Edge-TTS Voice |
|---|---|
| Arabic | `ar-LB-LaylaNeural` |
| French | `fr-FR-DeniseNeural` |
| English | `en-US-AriaNeural` |

### Cache

The service computes an MD5 hash of `(text, language, voice)` and stores the WAV in `uploads/tts_cache/`. Fixed questions (welcome, transitions) are synthesized only once.

### Prefetch

While the candidate answers question N, the backend pre-generates audio for question N+1. Perceived latency between questions is reduced to ~0 s.

### MP3 → WAV Conversion

Edge-TTS produces MP3. `pydub` (via FFmpeg) converts to 16-bit PCM WAV before transmission.

### Usage

```python
from backend.services import get_tts_service

tts = get_tts_service()
audio_bytes = tts.synthesize("Hello, welcome.", language="en")
```

---

## 3. LLM — Answer Evaluation

**File:** `llm_service.py`

### Architecture

```
OllamaLLMService
├── evaluate_answer()              ← standard evaluation
├── evaluate_with_followup()       ← evaluation + follow-up decision
├── evaluate_final_with_followup() ← evaluation after follow-up
├── evaluate_with_facial()         ← enriched evaluation (facial + duration)
└── generate_global_summary()      ← summary + hiring recommendation
```

### Strict Grading Scale (injected into system prompt)

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Precise, structured, concrete examples, technical mastery |
| 7–8 | Very Good | Good but lacks depth or examples |
| 5–6 | Acceptable | Superficial or vague |
| 3–4 | Insufficient | Errors or partial understanding |
| 0–2 | Poor | Off-topic, empty, or incorrect |

### Multilingual Prompts

Three distinct prompt sets (ar / fr / en) ensure the LLM responds in the interview language. The returned JSON is always parsed with robust regex extraction.

### Duration Integration

The service injects into the prompt:
- Actual answer duration
- Maximum allowed duration for the question
- Usage ratio (%)

Impact on score:
- `< 20%` of allotted time → penalty −1 to −2 pts if content is poor
- `40–90%` → neutral
- `> 90%` with rich content → possible bonus +0.5 pt

### Facial Data Integration

When facial metrics are available and reliable (`face_detection_rate ≥ 0.3`), additional context is added to the system prompt with confidence, stress, and engagement scores. Verbal content carries 80% weight; non-verbal behavior 20%.

### JSON Output Format (per answer)

```json
{
  "score": 7.5,
  "verdict": "Very Good",
  "strengths": ["Good clarity", "Concrete example"],
  "improvements": ["Lacks technical depth"],
  "feedback": "Clear response but not deeply elaborated.",
  "needs_followup": false,
  "followup_question": ""
}
```

### Global Summary Output

```json
{
  "recommendation": "Hire",
  "decision_reason": "Weighted average 7.2/10 across 3 questions.",
  "key_strengths": ["Communication", "Python"],
  "key_improvements": ["ML depth"],
  "summary": "Strong candidate, recommended for hiring."
}
```

### Usage

```python
from backend.services.llm_service import get_llm_service

llm = get_llm_service()
result = await llm.evaluate_with_facial(
    question="Tell me about yourself.",
    answer=transcript,
    language="en",
    position_title="Data Scientist",
    facial_metrics=metrics,
    duration_seconds=45.0,
    max_duration_seconds=90.0,
)
```

---

## 4. Facial Analysis

**File:** `facial_analysis_service.py`

### Detection Pipeline

```
JPEG Frames (2 fps from client)
    │
    ├─► MediaPipe FaceMesh (478 landmarks + iris)
    │     EAR → blink detection (threshold 0.22)
    │     iris offset → eye contact
    │     solvePnP → yaw / pitch / roll (normalized)
    │     lip corners → smile
    │     brow raise / frown → Action Units AU1/2/4
    │
    └─► Emotion backend (decreasing priority)
          1. HSEmotion EfficientNet-B0   ~82%   ← active
          2. DeepFace VGG CNN            ~73%   ← fallback 1
          3. FACS heuristics             ~60%   ← fallback 2
```

### Emotion Backends

#### HSEmotion EfficientNet-B0 (Priority 1)
- Models: `enet_b0_8_best_afew` → `enet_b2_8_best_vgaf`
- Accuracy: ~82% (AffectNet8 + AFEW)
- Dependencies: `timm==0.9.2`, `efficientnet_pytorch`, `hsemotion`
- Batch GPU inference via PyTorch (no TensorFlow)

#### DeepFace VGG (Priority 2)
- Accuracy: ~73% (AffectNet)
- Warm-up at startup to avoid latency on first call
- Dependencies: `deepface`, `tf-keras`

#### FACS Heuristics (Priority 3)
- Pure geometric computation from MediaPipe landmarks
- No additional ML dependency
- ~60% accuracy, always available

### Computed Metrics

| Metric | Range | Formula |
|---|---|---|
| `eye_contact_ratio` | 0–1 | Fraction of frames with camera gaze |
| `head_stability` | 0–1 | `1 − (yaw_std + pitch_std) / 60` |
| `smile_ratio` | 0–1 | Fraction of frames with detected smile |
| `blink_rate` | bpm | Estimated blinks (min 5 frames) |
| `confidence_score` | 0–10 | Eye contact + stability + emotions |
| `stress_score` | 0–10 | Frowning + instability + fear/anger |
| `engagement_score` | 0–10 | Eye contact + expressiveness + smile |

### Batch Optimization

1. Automatic sampling: max 25 frames analyzed (from all received)
2. Sequential CPU MediaPipe on 25 frames
3. Face crop from landmarks
4. HSEmotion **batch** inference on GPU → single PyTorch call

### Installation Prerequisites

```bash
# Mandatory order
pip install timm==0.9.2
pip install efficientnet_pytorch
pip install hsemotion
pip install mediapipe==0.10.14
pip install "protobuf>=4.25.3,<5.0.0"
```

### Verification

```bash
python -c "
from hsemotion.facial_emotions import HSEmotionRecognizer
fer = HSEmotionRecognizer(model_name='enet_b0_8_best_afew', device='cpu')
print('HSEmotion OK:', fer)
"
```

### Usage

```python
from backend.services.facial_analysis_service import get_facial_service

svc = get_facial_service()
frame_results = svc.analyze_frames_batch(frames_bgr)
metrics = svc.compute_metrics(frame_results)
print(metrics.confidence_score, metrics.dominant_emotion)
```

---

## 5. Avatar

**File:** `avatar_service.py`

Two providers are defined:

| Provider | Description |
|---|---|
| `simple` | Reads static videos from `assets/videos/` (default) |
| `did` | D-ID API stub (not implemented → falls back to simple) |

Configurable via `AVATAR_PROVIDER=simple` in `.env`.

---

## Singleton Pattern

Each service exposes a `get_*_service()` function returning a unique instance initialized once (module-level cache). Services are instantiated in `main.py` via the FastAPI `lifespan`, ensuring availability before the first WebSocket call.

---

## Diagrams

### Activity A1 — Facial Analysis Pipeline

<p align="center">
  <img src="../../docs/A1. Facial Analysis Pipeline.png" width="50%" alt="Facial Analysis Pipeline"/>
</p>

### Activity A2 — ASR + LLM Evaluation

<p align="center">
  <img src="../../docs/A2. ASR + LLM Evaluation.png" width="50%" alt="ASR + LLM Evaluation"/>
</p>

### Activity A3 — TTS Synthesis

<p align="center">
  <img src="../../docs/A3. TTS Synthesis.png" width="40%" alt="TTS Synthesis"/>
</p>