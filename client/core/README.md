# ⚙️ Core — SparkHire AI Desktop Client

Non-UI logic for the PySide6 client: data models, WebSocket communication, audio recording, and video frame capture. All components are designed to run safely alongside Qt's event loop.

---

## Files

| File | Description |
|---|---|
| `models.py` | Lightweight dataclasses for client-side state |
| `websocket_client.py` | Thread-safe WebSocket client (`QThread` + `websockets`) |
| `audio_recorder.py` | Microphone capture via PyAudio callbacks |
| `video_recorder.py` | Webcam frame capture via OpenCV + QTimer |

---

## `models.py`

Simple dataclasses used to represent interview state on the client side (no MongoDB, no validation). These are not synced with the backend models — they hold just enough data to drive the UI.

| Class | Fields |
|---|---|
| `Question` | `order`, `question_ar`, `question_en`, `max_duration_seconds` |
| `Answer` | `question_order`, `question_text`, `transcript`, `duration_seconds` |
| `InterviewSession` | `session_id`, `candidate_id`, `job_position_id`, `language`, `status`, `current_question_index`, `answers` |
| `Progress` | `current`, `total`, `percentage` |

---

## `websocket_client.py`

### Architecture

```
MainWindow (Qt main thread)
    │
    └── WebSocketClient (QObject)
            │
            └── WebSocketWorker (QObject, runs in QThread)
                    └── asyncio event loop
                            └── websockets connection
```

### `WebSocketClient` — Public API

| Method | Description |
|---|---|
| `connect_to_server()` | Starts the QThread and opens the WebSocket |
| `send_message(data: dict)` | Thread-safe send via `run_coroutine_threadsafe` |
| `disconnect_from_server()` | Non-blocking close — schedules `_close()` in asyncio loop, calls `thread.quit()` |

### Qt Signals

| Signal | Emitted when |
|---|---|
| `connected` | WebSocket handshake succeeded |
| `disconnected(int, str)` | Connection closed (code, reason) |
| `message_received(dict)` | JSON message received |
| `error_occurred(str)` | Connection or parse error |

### Thread Safety

`disconnect_from_server()` is non-blocking by design — it does **not** call `thread.wait()`. This avoids deadlocking the Qt main thread during `closeEvent`.

---

## `audio_recorder.py`

### `AudioRecorder`

Uses PyAudio in **non-blocking callback mode** for zero-latency streaming.

| Parameter | Value |
|---|---|
| Format | PCM Int16 |
| Sample rate | 16 kHz (from `settings.SAMPLE_RATE`) |
| Channels | Mono (from `settings.CHANNELS`) |
| Chunk size | 1024 frames |

### Qt Signals

| Signal | Emitted when |
|---|---|
| `audio_chunk_ready(bytes)` | Each callback chunk is ready |
| `recording_started` | Stream opened |
| `recording_stopped` | Stream closed |
| `error_occurred(str)` | PyAudio failure |

### Usage

```python
recorder = AudioRecorder()
recorder.audio_chunk_ready.connect(on_chunk)
recorder.start_recording()
# ...
recorder.stop_recording()
recorder.cleanup()   # must be called before exit
```

---

## `video_recorder.py`

### `VideoFrameCollector`

Captures webcam frames at a configurable rate without a separate QThread (OpenCV is called from the Qt main thread via `QTimer.timeout`).

| Parameter | Default | Range |
|---|---|---|
| `camera_index` | 0 | any |
| `target_fps` | 2.0 | 0.5–10 |
| `jpeg_quality` | 70 | 0–100 |
| `max_width` | 640 | any |

Frames larger than `max_width` are automatically downscaled. The OpenCV buffer is set to size 1 (`CAP_PROP_BUFFERSIZE`) to always capture the most recent frame.

### Qt Signals

| Signal | Emitted when |
|---|---|
| `frame_captured(bytes)` | JPEG frame ready (raw bytes, no base64) |
| `camera_ready(bool)` | Camera opened (`True`) or failed (`False`) |
| `camera_error(str)` | Error message |

### Usage

```python
collector = VideoFrameCollector(target_fps=2.0)
collector.frame_captured.connect(on_frame)
collector.start_capture()
# ...
collector.stop_capture()
collector.cleanup()   # release camera
```

> The caller is responsible for base64-encoding frames before sending via WebSocket.