# 🔧 Utils — SparkHire AI Backend

Low-level audio utility functions shared across the backend pipeline.

---

## Files

| File | Description |
|---|---|
| `audio_utils.py` | WAV file I/O, PCM ↔ numpy conversion helpers |

---

## `audio_utils.py`

### `save_audio_wav(audio_bytes, output_path, sample_rate=16000)`

Saves raw PCM bytes as a WAV file.

- Format: mono, 16-bit, configurable sample rate (default 16 kHz)
- Creates the file using Python's `wave` module

```python
save_audio_wav(pcm_bytes, "/tmp/answer.wav", sample_rate=16000)
```

---

### `load_audio_wav(audio_path)`

Loads a WAV file and returns `(audio_float32, sample_rate, channels)`.

- Raw frames are decoded as `int16` then normalized to `float32` in `[-1.0, 1.0]`

```python
audio, sr, ch = load_audio_wav("/tmp/answer.wav")
```

---

### `bytes_to_numpy(audio_bytes)`

Converts raw PCM `int16` bytes to a normalized `float32` numpy array.

```python
arr = bytes_to_numpy(pcm_bytes)   # shape: (n_samples,), dtype: float32
```

---

### `numpy_to_bytes(audio_np)`

Converts a `float32` numpy array back to raw PCM `int16` bytes.

```python
pcm = numpy_to_bytes(arr)
```

---

## Usage Context

These utilities are available as building blocks for audio processing within the backend. In practice, the main audio pipeline in `InterviewHandler` uses the `wave` module directly for WAV construction and the `ASRService` for transcription. These helpers can be imported from `backend.utils.audio_utils` when intermediate numpy processing is needed.