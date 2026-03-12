"""
Gestionnaire de connexions WebSocket
"""

import asyncio
import logging
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestionnaire de connexions WebSocket"""

    def __init__(self):
        # Dict[session_id, WebSocket]
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accepter une nouvelle connexion"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connecté: {session_id}")

    def disconnect(self, session_id: str):
        """Déconnecter un client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket déconnecté: {session_id}")

    async def send_json(self, session_id: str, data: dict):
        """
        Envoyer un message JSON.
        Lève WebSocketDisconnect si le client s'est déconnecté,
        afin que le handler puisse interrompre proprement son exécution.
        """
        if session_id not in self.active_connections:
            logger.warning(f"Tentative d'envoi vers session inconnue: {session_id}")
            raise WebSocketDisconnect(code=1006, reason="Client non connecté")

        websocket = self.active_connections[session_id]
        try:
            await websocket.send_json(data)
        except WebSocketDisconnect:
            logger.warning(f"Client déconnecté lors de l'envoi: {session_id}")
            self.disconnect(session_id)
            raise  # Propage au handler pour interrompre l'entretien
        except Exception as e:
            logger.error(f"Erreur envoi message vers {session_id}: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.disconnect(session_id)
            # Convertir en WebSocketDisconnect pour une gestion uniforme dans le handler
            raise WebSocketDisconnect(code=1006, reason=str(e)) from e

    async def send_heartbeat_during(
        self,
        session_id: str,
        coro,
        interval: float = 15.0,
    ):
        """
        Exécute `coro` (coroutine ou future) tout en envoyant des heartbeats
        périodiques au client pour maintenir la connexion ouverte.

        Utilisé quand Coqui TTS peut prendre plusieurs minutes pour générer
        de l'audio — sans ça la connexion WebSocket timeout côté client/proxy.

        Args:
            session_id: ID de la session WebSocket active
            coro: coroutine à attendre (ex: synthesis task)
            interval: intervalle entre heartbeats en secondes (défaut 15s)

        Returns:
            Le résultat de `coro`
        """
        result_container = {}

        async def _heartbeat_loop():
            while True:
                await asyncio.sleep(interval)
                if session_id not in self.active_connections:
                    break
                try:
                    await self.send_json(session_id, {"type": "heartbeat"})
                    logger.debug(f"Heartbeat → {session_id}")
                except Exception:
                    break

        task = asyncio.ensure_future(coro)
        heartbeat = asyncio.ensure_future(_heartbeat_loop())

        try:
            result = await task
        finally:
            heartbeat.cancel()
            try:
                await heartbeat
            except (asyncio.CancelledError, Exception):
                pass

        return result

    async def broadcast(self, message: dict):
        """Diffuser à tous les clients connectés"""
        for session_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Erreur broadcast vers {session_id}: {e}")
                self.disconnect(session_id)

    def is_connected(self, session_id: str) -> bool:
        """Vérifier si un client est connecté"""
        return session_id in self.active_connections

    def get_connection_count(self) -> int:
        """Nombre de connexions actives"""
        return len(self.active_connections)


# Instance globale
manager = ConnectionManager()