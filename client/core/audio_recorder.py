import pyaudio
import numpy as np
from PySide6.QtCore import QObject, Signal, QTimer
from client.config import settings

class AudioRecorder(QObject):
    """Enregistreur audio avec PyAudio"""
    
    audio_chunk_ready = Signal(bytes)
    recording_started = Signal()
    recording_stopped = Signal()
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.buffer = bytearray()
    
    def start_recording(self):
        """Démarrer l'enregistrement"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=settings.CHANNELS,
                rate=settings.SAMPLE_RATE,
                input=True,
                frames_per_buffer=settings.CHUNK_SIZE,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            self.recording_started.emit()
        
        except Exception as e:
            self.error_occurred.emit(f"Recording error: {e}")
    
    def stop_recording(self):
        """Arrêter l'enregistrement"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.recording_stopped.emit()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback pour chaque chunk audio"""
        if self.is_recording:
            self.buffer.extend(in_data)
            self.audio_chunk_ready.emit(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def get_recorded_audio(self) -> bytes:
        """Récupérer tout l'audio enregistré"""
        audio_bytes = bytes(self.buffer)
        self.buffer.clear()
        return audio_bytes
    
    def cleanup(self):
        """Nettoyer les ressources"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()