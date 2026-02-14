"""
Middlewares pour le backend
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger toutes les requêtes"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Début de la requête
        start_time = time.time()
        
        # Log de la requête
        logger.info(f"➡️  {request.method} {request.url.path}")
        
        # Traitement
        response = await call_next(request)
        
        # Durée de traitement
        process_time = time.time() - start_time
        
        # Log de la réponse
        logger.info(
            f"⬅️  {request.method} {request.url.path} "
            f"[{response.status_code}] - {process_time:.3f}s"
        )
        
        # Ajouter header de temps de traitement
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware pour gérer les erreurs globales"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Erreur non gérée: {str(e)}", exc_info=True)
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Erreur interne du serveur",
                    "detail": str(e) if logger.level == logging.DEBUG else "Une erreur est survenue"
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware simple de rate limiting"""
    
    def __init__(self, app, max_requests: int = 100, time_window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obtenir l'IP du client
        client_ip = request.client.host
        current_time = time.time()
        
        # Initialiser ou nettoyer les compteurs
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Nettoyer les anciennes requêtes
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < self.time_window
        ]
        
        # Vérifier la limite
        if len(self.request_counts[client_ip]) >= self.max_requests:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Trop de requêtes",
                    "detail": f"Limite de {self.max_requests} requêtes par {self.time_window}s dépassée"
                }
            )
        
        # Ajouter la requête actuelle
        self.request_counts[client_ip].append(current_time)
        
        # Continuer
        response = await call_next(request)
        
        # Ajouter headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.max_requests - len(self.request_counts[client_ip])
        )
        
        return response