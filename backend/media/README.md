# 🗂️ Media — SparkHire AI Backend

File upload and download management for audio, video, and image assets. Files are stored in the `uploads/` directory organized by category.

---

## Files

| File | Description |
|---|---|
| `models.py` | `MediaFile`, `MediaUploadResponse` Pydantic models |
| `routes.py` | Upload, download, and delete endpoints |

---

## API Endpoints

All routes require `Authorization: Bearer <token>`.

### `POST /media/upload`

Uploads a file and returns its metadata and access URL.

**Query parameters:**

| Parameter | Description |
|---|---|
| `entity_type` | `interview` / `candidate` / `position` (optional) |
| `entity_id` | ID of the related entity (optional) |

**Accepted MIME types:**

| Category | Types |
|---|---|
| `audio` | `audio/wav`, `audio/mpeg`, `audio/mp3`, `audio/ogg`, `audio/flac` |
| `video` | `video/mp4`, `video/webm`, `video/ogg` |
| `image` | `image/jpeg`, `image/png`, `image/gif`, `image/webp` |

**Response (`MediaUploadResponse`):**

```json
{
  "file_id": "<uuid>",
  "filename": "original_name.wav",
  "file_path": "/abs/path/on/server",
  "file_url": "/uploads/audio/<uuid>.wav",
  "size_bytes": 48320,
  "mime_type": "audio/wav",
  "message": "Fichier uploadé avec succès"
}
```

---

### `GET /media/download/{category}/{filename}`

Downloads a file as `application/octet-stream`.

**Path parameters:**
- `category` — `audio`, `video`, or `image`
- `filename` — UUID-based filename returned at upload time

Returns `404` if the file does not exist.

---

### `DELETE /media/{category}/{filename}`

Deletes a file from disk.

Returns `404` if the file does not exist, `500` if deletion fails.

---

## Storage Layout

```
uploads/
├── audio/      ← WAV/MP3/OGG files uploaded via this endpoint
├── video/      ← MP4/WebM files
├── image/      ← JPEG/PNG/GIF/WebP files
└── tts_cache/  ← TTS synthesis cache (managed by TTSService, not this module)
```

Static file serving is configured in `main.py`:

```python
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR))
```

Files uploaded here are accessible at `http://localhost:8000/uploads/{category}/{filename}`.

---

## Notes

- Filenames are UUID-generated to avoid collisions
- The `entity_type` / `entity_id` parameters are accepted but not yet persisted in a `media_files` collection — they serve as metadata hints for future extensions
- Audio files recorded during WebSocket interviews are saved directly by `InterviewHandler` and bypass this endpoint