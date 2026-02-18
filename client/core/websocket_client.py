"""
Client WebSocket avec Interface Qt
VERSION CORRIGÉE - Fermeture propre sans bloquer le thread Qt
"""

import asyncio
import json
from PySide6.QtCore import QObject, Signal, QThread


class WebSocketWorker(QObject):
    """Worker WebSocket dans un thread séparé."""

    connection_established = Signal()
    connection_closed = Signal(int, str)   # (code, reason)
    message_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.websocket = None
        self.running = False
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect_to_server(self):
        try:
            import websockets
            self.websocket = await websockets.connect(self.url)
            self.connection_established.emit()

            async for message in self.websocket:
                if not self.running:
                    break
                try:
                    data = json.loads(message)
                    self.message_received.emit(data)
                except json.JSONDecodeError as e:
                    self.error_occurred.emit(f"JSON error: {e}")

        except Exception as e:
            import websockets.exceptions as _wse
            if isinstance(e, _wse.ConnectionClosedError):
                self.connection_closed.emit(e.code, e.reason)
            else:
                self.error_occurred.emit(f"Connection error: {e}")
                self.connection_closed.emit(0, str(e))

    async def send(self, data: dict):
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(data))

    async def _close(self):
        """Ferme proprement le websocket depuis l'asyncio loop."""
        self.running = False
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close()
            except Exception:
                pass

    def run(self):
        """Point d'entrée du thread."""
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect_to_server())
        finally:
            # Nettoyer toutes les tâches en attente AVANT de fermer le loop
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass
            self.loop.close()
            self.loop = None


class WebSocketClient(QObject):
    """Client WebSocket thread-safe avec interface Qt."""

    connected = Signal()
    disconnected = Signal(int, str)   # (code, reason)
    message_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.worker = WebSocketWorker(url)
        self.thread = QThread()

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.connection_established.connect(self._on_connected)
        self.worker.connection_closed.connect(self._on_disconnected)
        self.worker.message_received.connect(self._on_message)
        self.worker.error_occurred.connect(self._on_error)

    def connect_to_server(self):
        if not self.thread.isRunning():
            self.thread.start()

    def send_message(self, data: dict):
        loop = self.worker.loop
        if loop and not loop.is_closed() and self.worker.running:
            asyncio.run_coroutine_threadsafe(self.worker.send(data), loop)

    def disconnect_from_server(self):
        """
        Ferme la connexion de façon NON-BLOQUANTE.

        On schedule _close() dans l'asyncio loop du worker.
        Quand le websocket se ferme, le 'async for' dans connect_to_server()
        se termine, le loop asyncio s'arrête, le thread se termine tout seul.
        On ne bloque PAS le thread Qt principal avec thread.wait().
        """
        self.worker.running = False
        loop = self.worker.loop
        if loop and not loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(self.worker._close(), loop)
            except Exception:
                pass
        # Demander au thread Qt de quitter dès que le worker.run() retourne
        self.thread.quit()
        # PAS de thread.wait() → ne bloque pas le thread principal Qt

    def _on_connected(self):
        self.connected.emit()

    def _on_disconnected(self, code: int, reason: str):
        self.disconnected.emit(code, reason)

    def _on_message(self, data: dict):
        self.message_received.emit(data)

    def _on_error(self, error: str):
        self.error_occurred.emit(error)