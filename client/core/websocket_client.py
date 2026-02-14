import asyncio
import json
import base64
from typing import Callable, Optional
import websockets
from PySide6.QtCore import QObject, Signal, QThread

class WebSocketWorker(QObject):
    """Worker pour WebSocket dans thread séparé"""
    
    # Renommer le signal pour éviter le conflit avec la méthode connect()
    connection_established = Signal()
    connection_closed = Signal(int, str)  
    message_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.websocket = None
        self.running = False
        self.loop = None
    
    async def connect_to_server(self):
        """Connecter au WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connection_established.emit()
            
            # Boucle de réception
            async for message in self.websocket:
                if not self.running:
                    break
                
                try:
                    data = json.loads(message)
                    self.message_received.emit(data)
                except json.JSONDecodeError as e:
                    self.error_occurred.emit(f"JSON error: {e}")
        
        except websockets.exceptions.ConnectionClosedError as e:
            # ✅ NOUVEAU: Capturer la fermeture avec code et raison
            self.connection_closed.emit(e.code, e.reason)
            
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
            self.connection_closed.emit(0, str(e))
    
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
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_server())


class WebSocketClient(QObject):
    """Client WebSocket avec interface Qt"""
    
    connected = Signal()
    disconnected = Signal(int, str)  # ✅ NOUVEAU: code et raison
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
        self.worker.connection_established.connect(self._on_connected)
        self.worker.connection_closed.connect(self._on_disconnected)
        self.worker.message_received.connect(self._on_message)
        self.worker.error_occurred.connect(self._on_error)
    
    def connect_to_server(self):
        """Démarrer connexion"""
        if not self.thread.isRunning():
            self.thread.start()
    
    def send_message(self, data: dict):
        """Envoyer message"""
        if self.worker.loop and self.worker.running:
            asyncio.run_coroutine_threadsafe(
                self.worker.send(data),
                self.worker.loop
            )
    
    def disconnect_from_server(self):
        """Déconnecter"""
        if self.worker.loop and self.worker.running:
            asyncio.run_coroutine_threadsafe(
                self.worker.close(),
                self.worker.loop
            )
        self.thread.quit()
        self.thread.wait()
    
    def _on_connected(self):
        self.connected.emit()
    
    def _on_disconnected(self, code: int, reason: str):
        self.disconnected.emit(code, reason)
    
    def _on_message(self, data: dict):
        self.message_received.emit(data)
    
    def _on_error(self, error: str):
        self.error_occurred.emit(error)