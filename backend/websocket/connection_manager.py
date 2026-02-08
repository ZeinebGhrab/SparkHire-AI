"""
Gestionnaire de connexions WebSocket
"""

import logging
from typing import Dict
from fastapi import WebSocket

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
        """Envoyer un message JSON"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Erreur envoi message: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        """Diffuser à tous les clients"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Erreur broadcast vers {session_id}: {e}")
    
    def is_connected(self, session_id: str) -> bool:
        """Vérifier si un client est connecté"""
        return session_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Nombre de connexions actives"""
        return len(self.active_connections)


# Instance globale
manager = ConnectionManager()