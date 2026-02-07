import asyncio
import json
import base64
from typing import Callable, Optional
import websockets
from PySide6.QtCore import QObject, Signal, QThread

class WebSocketWorker(QObject):
    """Worker pour WebSocket dans thread séparé"""
    
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.websocket = None
        self.running = False
    
    async def connect(self):
        """Connecter au WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected.emit()
            
            # Boucle de réception
            async for message in self.websocket:
                if not self.running:
                    break
                
                try:
                    data = json.loads(message)
                    self.message_received.emit(data)
                except json.JSONDecodeError as e:
                    self.error_occurred.emit(f"JSON error: {e}")
        
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
        finally:
            self.disconnected.emit()
    
    async def send(self, data: dict):
        """Envoyer message"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(data))
    
    async def close(self):
        """Fermer connexion"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
    
    def run(self):
        """Point d'entrée du worker"""
        self.running = True
        asyncio.run(self.connect())


class WebSocketClient(QObject):
    """Client WebSocket avec interface Qt"""
    
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.worker = WebSocketWorker(url)
        self.thread = QThread()
        
        # Déplacer worker dans thread
        self.worker.moveToThread(self.thread)
        
        # Connecter signaux
        self.thread.started.connect(self.worker.run)
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.message_received.connect(self._on_message)
        self.worker.error_occurred.connect(self._on_error)
    
    def connect_to_server(self):
        """Démarrer connexion"""
        if not self.thread.isRunning():
            self.thread.start()
    
    def send_message(self, data: dict):
        """Envoyer message"""
        asyncio.run_coroutine_threadsafe(
            self.worker.send(data),
            self.worker.loop if hasattr(self.worker, 'loop') else asyncio.get_event_loop()
        )
    
    def disconnect_from_server(self):
        """Déconnecter"""
        asyncio.run_coroutine_threadsafe(
            self.worker.close(),
            self.worker.loop if hasattr(self.worker, 'loop') else asyncio.get_event_loop()
        )
        self.thread.quit()
        self.thread.wait()
    
    def _on_connected(self):
        self.connected.emit()
    
    def _on_disconnected(self):
        self.disconnected.emit()
    
    def _on_message(self, data: dict):
        self.message_received.emit(data)
    
    def _on_error(self, error: str):
        self.error_occurred.emit(error)