# 🔌 WebSocket Protocol — SparkHire AI

The WebSocket is the main real-time channel between the PySide6 client and the backend. It routes PCM audio, video frames, session commands, and evaluation signals.

---

## Connection

```
ws://localhost:8000/ws/interview/{session_id}?lang=en
```

| Parameter | Description |
|---|---|
| `session_id` | Session identifier (format `session_xxx…`) |
| `lang` | Interview language: `ar` / `fr` / `en` |

The server validates the session at connection time. If invalid, expired, or cancelled, it sends an `error` message then closes the connection (code 4003).

---

## Files

```
backend/websocket/
├── connection_manager.py   ← ConnectionManager (active connection management)
└── interview_handler.py    ← InterviewHandler (interview business logic)
```

---

## `ConnectionManager`

Global singleton (`manager`) managing the `session_id → WebSocket` dictionary.

### Key Methods

| Method | Description |
|---|---|
| `connect(session_id, ws)` | Accepts and registers the connection |
| `disconnect(session_id)` | Removes the connection from the dictionary |
| `send_json(session_id, data)` | Sends a JSON message (raises `WebSocketDisconnect` if client is gone) |
| `send_heartbeat_during(session_id, coro)` | Runs a coroutine while sending heartbeats every 15 s |
| `is_connected(session_id)` | Checks if the client is still connected |

Heartbeats are used during TTS synthesis (which can take several seconds) to prevent proxy-side timeouts.

---

## Session Flow (Happy Path)

```
Client                              Server
  │                                   │
  │── [WS connection] ───────────────►│ validate_session_access()
  │                                   │
  │◄── welcome (chunked audio) ───────│ _send_welcome()
  │── audio_finished ────────────────►│
  │                                   │ update_status("in_progress")
  │                                   │
  │◄── question_loading ──────────────│
  │◄── question (chunked audio) ──────│ _send_current_question()
  │── audio_finished ────────────────►│
  │                                   │ prefetch audio Q+1
  │── audio_chunk × N ───────────────►│ collect PCM
  │── video_frame × M ───────────────►│ collect JPEG
  │── answer_complete ───────────────►│
  │                                   │ asyncio.gather(ASR, Facial)
  │                                   │ LLM evaluate_with_facial()
  │◄── answer_saved ──────────────────│
  │                                   │ [if score < 8]
  │◄── followup_incoming ─────────────│
  │◄── followup_question (audio) ─────│
  │── audio_finished ────────────────►│
  │── audio_chunk × N ───────────────►│
  │── answer_complete ───────────────►│
  │                                   │ LLM evaluate_final_with_followup()
  │◄── answer_followup_completed ─────│
  │                                   │
  │◄── interview_completed (audio) ───│ update_status("completed")
  │── audio_finished ────────────────►│
  │                                   │ _run_global_evaluation() [async]
  │◄── global_evaluation ─────────────│
```

### Reconnection

If the candidate reconnects on an `in_progress` session, the server sends `welcome_back` instead of `welcome` and resumes at the current question.

---

## Server → Client Messages

### `welcome`

```json
{
  "type": "welcome",
  "data": {
    "audio_mode": "chunked",
    "total_questions": 3,
    "position_title": "Data Scientist",
    "candidate_name": "Ahmed Ben Ali",
    "expires_at": "2026-03-26T10:30:00",
    "language": "en",
    "facial_analysis_enabled": true,
    "sample_rate": 22050,
    "channels": 2,
    "bits_per_sample": 16,
    "total_chunks": 12
  }
}
```

### `welcome_back`

Same as `welcome` with additional fields:
- `current_question_index`: index of the current question
- `is_reconnection: true`

### `question`

```json
{
  "type": "question",
  "data": {
    "order": 2,
    "weight": 2.0,
    "max_duration": 90,
    "progress": { "current": 2, "total": 3, "percentage": 67 },
    "language": "en",
    "audio_mode": "chunked",
    "total_chunks": 8
  }
}
```

### `audio_chunk_data`

```json
{
  "type": "audio_chunk_data",
  "data": {
    "chunk_index": 0,
    "total": 8,
    "data": "<base64 PCM>"
  }
}
```

### `audio_chunk_end`

```json
{ "type": "audio_chunk_end", "data": { "msg_type": "question" } }
```

### `answer_saved`

```json
{
  "type": "answer_saved",
  "data": {
    "duration": 42.5,
    "question_order": 2,
    "saved": true,
    "evaluation": "processing"
  }
}
```

### `answer_evaluated`

```json
{
  "type": "answer_evaluated",
  "data": {
    "question_order": 2,
    "had_followup": false,
    "is_initial": true
  }
}
```

> ⚠️ No score, feedback, or facial metric is sent to the client.

### `followup_incoming`

```json
{
  "type": "followup_incoming",
  "data": {
    "question_order": 2,
    "initial_score": 5.5,
    "followup_text": "Can you give a concrete example?"
  }
}
```

### `answer_followup_completed`

```json
{
  "type": "answer_followup_completed",
  "data": { "question_order": 2, "had_followup": true }
}
```

### `global_evaluation`

```json
{
  "type": "global_evaluation",
  "data": {
    "decision": "accepted",
    "decision_label": "Accepted",
    "decision_color": "#10B981",
    "candidate_name": "Ahmed Ben Ali",
    "position_title": "Data Scientist",
    "total_questions": 3,
    "answered_questions": 3
  }
}
```

> `average_score` is **not** sent to the client.

### `interview_completed`

```json
{
  "type": "interview_completed",
  "data": {
    "total_questions": 3,
    "total_answers": 3,
    "position_title": "Data Scientist",
    "candidate_name": "Ahmed Ben Ali"
  }
}
```

### `error`

```json
{
  "type": "error",
  "data": {
    "message": "Session expired 15 minutes ago.",
    "error_type": "SESSION_INVALID"
  }
}
```

---

## Client → Server Messages

### `audio_chunk`

```json
{
  "type": "audio_chunk",
  "audio_data": "<base64 PCM Int16 16kHz mono>"
}
```

### `video_frame`

```json
{
  "type": "video_frame",
  "data": { "frame": "<base64 JPEG>" }
}
```

### `answer_complete`

```json
{ "type": "answer_complete" }
```

### `audio_finished`

```json
{ "type": "audio_finished" }
```

Signals that the client has finished audio playback. The server waits for this signal before enabling the recording button.

### `end_interview`

```json
{ "type": "end_interview" }
```

Voluntary cancellation by the candidate. The session switches to `cancelled`.

---

## Audio Format

Audio is transmitted as **raw PCM** (Int16, 16 kHz, mono) split into **64 KB chunks** encoded in base64. The client receives metadata (sample_rate, channels, bits_per_sample) in the initial message to configure the audio mixer.

---

## Asynchronous Answer Processing

```python
# ASR and facial analysis run in parallel
transcript, facial_metrics = await asyncio.gather(
    _transcribe_audio(wav_bytes),
    _analyze_facial_frames(frames_b64),
)

# LLM evaluation with facial context + duration
result = await llm.evaluate_with_facial(
    question=question_text,
    answer=transcript,
    facial_metrics=facial_metrics,
    duration_seconds=duration,
    max_duration_seconds=question.max_duration_seconds,
)
```

Video frames and audio chunks are collected simultaneously during recording, then processed in parallel after `answer_complete`.

---

## Executors

Four dedicated `ThreadPoolExecutor` instances prevent blocking the asyncio event loop:

| Executor | Workers | Usage |
|---|---|---|
| `_tts_executor` | 1 | TTS synthesis (synchronous) |
| `_llm_executor` | 2 | Ollama calls (httpx async, reserved) |
| `_asr_executor` | 2 | Whisper transcription (synchronous) |
| `_facial_executor` | 1 | MediaPipe + HSEmotion analysis (synchronous) |

---

## Diagrams

### Flow 1 — Session Access Validation

<p align="center">
  <img src="../docs/1.3 Session Access Validation.png" width="50%" alt="Session Access Validation"/>
</p>

### Flow 2 — Real-Time Interview

<p align="center">
  <img src="../docs/2.3 Real-Time Interview.png" width="60%" alt="Real-Time Interview"/>
</p>