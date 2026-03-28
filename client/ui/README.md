# 🖥️ UI — SparkHire AI Desktop Client

PySide6 widgets, design system, and icon library for the candidate-facing interview interface.

---

## Files

| File | Description |
|---|---|
| `stark_theme.py` | Design tokens (`T`) and `StarkTheme` component styles |
| `icons.py` | `StarkIcons` — Lucide SVG icons + Stark logo variants |
| `main_window.py` | `MainWindow` — application shell and all interview logic |
| `interview_widget.py` | `InterviewWidget` — right-side panel (progress, buttons, countdown) |
| `video_player_widget.py` | `VideoPlayerWidget` — HR avatar video display |
| `camera_preview_widget.py` | `CameraPreviewWidget` — webcam PiP overlay with real-time landmark preview |

---

## Design System (`stark_theme.py`)

### Tokens (`T`)

All visual constants are accessible as class attributes on `T`:

| Category | Examples |
|---|---|
| Backgrounds | `T.BG_APP`, `T.BG_CARD`, `T.BG_PAGE` |
| Indigo primary | `T.INDIGO_50` → `T.INDIGO_900` |
| Status colors | `T.GREEN_500`, `T.RED_500`, `T.AMBER_500` |
| Text hierarchy | `T.TEXT_900` (headings) → `T.TEXT_400` (disabled) |
| Typography | `T.FONT`, `T.FONT_MONO`, `T.FONT_BODY` |
| Font sizes | `T.FS_2XS` (9px) → `T.FS_4XL` (44px) |
| Spacing | `T.SP_1` (4px) → `T.SP_12` (48px) — 8px grid |
| Border radius | `T.R_SM` (8px) → `T.R_FULL` (9999px) |

### `StarkTheme` Methods

| Method | Returns |
|---|---|
| `get_button_style(variant)` | QSS string for `primary`, `accent`, `ghost`, `danger`, `record` |
| `progress_style()` | QSS for indigo gradient progress bar |
| `input_style()` | QSS for text input with focus ring |
| `card_style(hover)` | QSS for white card with optional hover |
| `global_stylesheet()` | QSS applied to `QMainWindow`, scrollbars, tooltips, status bar |

---

## `MainWindow`

Central application window using a `QStackedWidget` for navigation:

| Page | Index | Content |
|---|---|---|
| Language selection | 0 | Three `LanguageCard` widgets |
| Session entry | 1 | Session ID input + connect button |
| Interview | — | `VideoPlayerWidget` + `InterviewWidget` (shown by swapping `stacked` visibility) |

### Key Responsibilities

- **WebSocket lifecycle** — connect, receive messages, send audio/video chunks
- **Audio playback** — pygame.mixer receives PCM chunks, assembles WAV, plays back; sends `audio_finished` on completion
- **Recording control** — `AudioRecorder` and `VideoFrameCollector` start/stop synchronized with interview state
- **State machine** — routes WebSocket messages (`welcome`, `question`, `answer_*`, `global_evaluation`, etc.) to UI updates

### Language Cards (`LanguageCard`)

Selectable cards for Arabic / French / English. Selection updates `_language` and passes `?lang=` to the WebSocket URL.

### Status Chip (`StatusChip`)

Header-mounted pill showing connection state: `disconnected` / `validating` / `connected` / `error`.

---

## `InterviewWidget`

Right-side panel displayed during the interview. Fully localized (`ar` / `fr` / `en`), with automatic RTL layout direction for Arabic.

### Sub-components

| Class | Description |
|---|---|
| `_SectionHeader` | Title + animated pulsing dot |
| `_ProgressCard` | Progress bar + question counter + dot indicators |
| `_InfoCard` | Mic icon, status pill, duration badge, countdown |
| `PulseDot` | Animated dot widget (alpha oscillation) |

### Record Button States

| State | Appearance | Enabled |
|---|---|---|
| Waiting for audio | Primary gradient, "Start answering" | ❌ |
| Audio finished | Primary gradient, "Start answering" | ✅ |
| Recording | Red gradient, "Stop recording" | ✅ |
| Countdown at 0 | Auto-stop triggered | — |

### Public API

```python
widget.set_max_recording_seconds(90)
widget.update_question({"current": 1, "total": 3, "percentage": 33})
widget.set_audio_playing()
widget.set_ready_to_answer()
widget.enable_recording(True)   # starts recording immediately
```

---

## `VideoPlayerWidget`

Plays looping HR avatar videos (OpenCV → pygame → QLabel) with a status bar overlay.

| State | Method | Video file |
|---|---|---|
| Idle | `set_idle()` | `assets/videos/rh_idle.mp4` |
| Speaking | `set_speaking()` | `assets/videos/rh_speaking.mp4` |
| Listening | `set_listening()` | `assets/videos/rh_listening.mp4` |

If a video file is missing, a styled gradient placeholder is displayed. The frame rate is ~30 fps via `QTimer`.

**Camera PiP overlay** — `CameraPreviewWidget` is embedded as a child widget, positioned in the bottom-left corner and repositioned on `resizeEvent`.

---

## `CameraPreviewWidget`

Fixed-size (204 × 174 px) PiP overlay for the candidate's webcam feed.

- Displays JPEG frames via `on_frame(bytes)` slot
- Shows an animated `● REC` badge during recording (`set_recording(True)`)
- Runs lightweight **real-time MediaPipe FaceMesh** analysis in a background thread for local preview only (yaw, EAR, eye contact, smile, brow raise)
- Client-side metrics are **never sent to the server** — only raw JPEG frames are transmitted

> The MediaPipe import at module level uses the same protobuf stub injection pattern as the backend to prevent TensorFlow conflicts on Windows Python 3.11.

---

## `StarkIcons`

SVG icon library with two categories:

### Lucide Icons

Stroke-only SVGs rendered at configurable sizes. Available icons include:
`microphone`, `microphone_off`, `headphones`, `volume_2`, `radio`, `message_circle`, `stop_circle`, `power`, `log_out`, `activity`, `circle_check`, `circle_alert`, `wifi`, `wifi_off`, `arrow_left`, `chevron_right`, `check`, `x_circle`, `user_check`, `user_circle`, `briefcase`, `file_text`, `clipboard_list`, `shield_check`, `lock`, `key_round`, `zap`, `help_circle`, `settings`, `square`

### Stark Logos

Premium SVG badge variants using `textPath` arcs:
- `logo_stark(size)` — hexagonal badge with arc text
- `logo_stark_compact(size)` — circular compact badge
- `logo_stark_banner(size)` — horizontal banner with hex + title
- `logo_stark_badge(size)` — circular seal with perimeter text