# 🖥️ Desktop Client — SparkHire AI

**PySide6** (Qt6) application for candidates. It manages the WebSocket connection, TTS audio playback, voice recording, video capture, and the interview interface.

---

## Structure

```
client/
├── main.py                     ← entry point (QApplication)
├── config.py                   ← Settings (Pydantic, loaded from .env)
├── requirements.txt
│
├── core/
│   ├── __init__.py
│   ├── models.py               ← lightweight dataclasses (Question, Answer, Progress…)
│   ├── audio_recorder.py       ← AudioRecorder (PyAudio + callback)
│   ├── video_recorder.py       ← VideoFrameCollector (OpenCV + QTimer)
│   └── websocket_client.py     ← WebSocketClient (QThread + websockets)
│
└── ui/
    ├── __init__.py
    ├── stark_theme.py          ← design tokens (T) + StarkTheme (Qt styles)
    ├── icons.py                ← StarkIcons (Lucide SVG + logos)
    ├── main_window.py          ← MainWindow (main window + logic)
    ├── interview_widget.py     ← InterviewWidget (progress + buttons)
    ├── video_player_widget.py  ← VideoPlayerWidget (avatar video)
    └── camera_preview_widget.py ← CameraPreviewWidget (camera PiP)
```

---

## Running the Client

```bash
python -m client.main
```

---

## Configuration

`.env` file (project root):

```env
API_BASE_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000
FACIAL_ANALYSIS_ENABLED=true
FACIAL_CAPTURE_FPS=2.0
```

---

## User Flow

### 1. Language Selection

The user chooses between **Arabic / French / English** via three interactive cards. The selected language is passed to the server via the `?lang=` WebSocket URL parameter.

### 2. Session ID Entry

The identifier (format `session_xxxxxxxxxxxxx`) is provided by the recruiter. The client validates the format before any connection attempt.

### 3. Voice Interview

- The video avatar delivers questions via audio (chunked PCM streaming).
- The record button is enabled **only after** audio playback ends.
- A countdown displays remaining time (default max 90 s).
- The webcam captures JPEG frames at 2 fps during recording.
- At the end of the interview, the final decision is displayed (`accepted` / `pending` / `rejected`).

---

## Core Modules

### `AudioRecorder`

Uses **PyAudio** in non-blocking callback mode.

- Format: PCM Int16, 16 kHz, mono (configurable via `Settings`)
- Chunk: 1024 frames
- Qt signal: `audio_chunk_ready(bytes)` → connected to WebSocket

```python
recorder = AudioRecorder()
recorder.audio_chunk_ready.connect(on_chunk)
recorder.start_recording()
# ...
recorder.stop_recording()
```

### `VideoFrameCollector`

Uses **OpenCV + QTimer** to capture frames without a dedicated QThread (avoids OpenCV thread-safety issues on Windows).

| Parameter | Default | Description |
|---|---|---|
| `camera_index` | 0 | Webcam index |
| `target_fps` | 2.0 | Capture frequency |
| `jpeg_quality` | 70 | JPEG quality (0–100) |
| `max_width` | 640 | Resize if necessary |

Emitted signal: `frame_captured(bytes)` (raw JPEG, no base64).

```python
collector = VideoFrameCollector(target_fps=2.0)
collector.frame_captured.connect(on_frame)
collector.start_capture()
# ...
collector.stop_capture()
```

### `WebSocketClient`

Wraps `websockets` in a separate **QThread** to avoid blocking the main Qt thread.

- A `WebSocketWorker` runs in the thread and reads messages via `async for`.
- Sending is thread-safe via `asyncio.run_coroutine_threadsafe()`.
- Disconnection is **non-blocking**: `_close()` is scheduled in the asyncio loop and `thread.quit()` is called without `thread.wait()`.

```python
client = WebSocketClient("ws://localhost:8000/ws/interview/session_abc?lang=en")
client.message_received.connect(on_message)
client.connect_to_server()
client.send_message({"type": "audio_finished"})
client.disconnect_from_server()
```

---

## User Interface

### `MainWindow`

Main window organized as a `QStackedWidget`:

| Page | Description |
|---|---|
| 0 — Language | Language selection (3 `LanguageCard` widgets) |
| 1 — Session | Session ID entry + connect |
| Interview | Side container (VideoPlayerWidget + InterviewWidget) |

#### Audio Management

Playback via **pygame.mixer**:
- Receives PCM chunks, assembles them into WAV, writes to a temp file.
- Detects end of playback via `pygame.mixer.music.get_busy()` (200 ms polling).
- Sends `audio_finished` to the server at the end of each audio.

#### Video Management

- JPEG frames are sent to the server via WebSocket (base64).
- In parallel, they are displayed in `CameraPreviewWidget` (PiP).
- Capture starts at `start_recording` and stops at `stop_recording`.

### `InterviewWidget`

Right panel of the interview, localized (ar / fr / en).

| Component | Role |
|---|---|
| `_SectionHeader` | Title + animated dot |
| `_ProgressCard` | Progress bar + indicator dots |
| `_InfoCard` | Central card (mic icon, status, countdown) |
| `record_btn` | Main button (Start / Stop) |
| `end_btn` | Secondary button (End interview) |

Record button states:
- **Disabled** during audio playback
- **Enabled** after `audio_chunk_end` received
- **Red (STOP)** during recording
- **Auto-stop** at 0 s of the countdown

### `VideoPlayerWidget`

Displays the HR avatar video (OpenCV + pygame → QLabel).

| State | Loaded Video | Description |
|---|---|---|
| `set_idle()` | `rh_idle.mp4` | Waiting |
| `set_speaking()` | `rh_speaking.mp4` | Question playing |
| `set_listening()` | `rh_listening.mp4` | Recording in progress |

If the video file is missing, a colored placeholder is displayed.

### `CameraPreviewWidget`

PiP (Picture-in-Picture) overlay in the bottom-left corner of `VideoPlayerWidget`.

- Fixed dimensions: 200 × 170 px
- Animated **REC** badge during recording
- Real-time MediaPipe analysis (yaw, EAR, iris, smile, brows) for local preview only
- Client-side computed metrics are **not sent** to the server (unlike raw frames)

---

## Design System

All styles are centralized in `stark_theme.py`.

### Tokens (`T`)

```python
T.INDIGO_500     # "#6366F1"  — primary color
T.BG_CARD        # "#FFFFFF"  — card background
T.BORDER         # "#E5E7EB"  — standard border
T.TEXT_900       # "#111827"  — title text
T.FONT           # "'DM Sans', 'Inter', sans-serif"
T.R_LG           # 14         — large border-radius
T.SP_4           # 16         — spacing (8px grid)
```

### `StarkTheme`

- `StarkTheme.get_button_style(variant)`: `primary` / `accent` / `ghost` / `danger` / `record`
- `StarkTheme.progress_style()`: indigo progress bar
- `StarkTheme.input_style()`: input field with focus ring
- `StarkTheme.global_stylesheet()`: QMainWindow, QScrollBar, QToolTip styles

---

## Internationalization

The UI is fully localized in **Arabic / French / English** via `TEXTS` dictionaries in each widget. The layout direction automatically switches to `RightToLeft` for Arabic.

---

## Client Dependencies

```
PySide6==6.7
pygame==2.6
pyaudio==0.2.14
opencv-python==4.10.0.84
websockets==13.0.1
pydub==0.25.1
numpy==1.26.4
```

Installation:
```bash
pip install -r client/requirements.txt
```

> **Windows:** if PyAudio fails, use `pipwin install pyaudio`.

---

## Privacy

The client **never displays**:
- LLM scores
- Facial metrics
- Feedback or improvement suggestions

Only flow signals (`answer_evaluated`, `global_evaluation`) are received, without any sensitive data.