from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from backend.media.models import MediaUploadResponse
from backend.auth.security import get_current_recruiter
from backend.config import settings
from pathlib import Path
import shutil
import uuid
from typing import Optional

router = APIRouter(prefix="/media", tags=["Media"])

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_file(
    file: UploadFile = File(...),
    entity_type: Optional[str] = Query(None, description="Type d'entité (interview, candidate, position)"),
    entity_id: Optional[str] = Query(None, description="ID de l'entité associée"),
    _: str = Depends(get_current_recruiter)
):
    """Upload un fichier média (audio, vidéo, image)"""
    
    # Vérifier le type de fichier
    allowed_types = {
        "audio": ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac"],
        "video": ["video/mp4", "video/webm", "video/ogg"],
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"]
    }
    
    content_type = file.content_type
    file_category = None
    
    for category, types in allowed_types.items():
        if content_type in types:
            file_category = category
            break
    
    if not file_category:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non autorisé: {content_type}"
        )
    
    # Générer un nom de fichier unique
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Créer le dossier de destination
    upload_dir = settings.UPLOAD_DIR / file_category
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / unique_filename
    
    # Sauvegarder le fichier
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}")
    
    # Obtenir la taille du fichier
    file_size = file_path.stat().st_size
    
    # Générer l'URL du fichier
    file_url = f"/uploads/{file_category}/{unique_filename}"
    
    return MediaUploadResponse(
        file_id=str(uuid.uuid4()),
        filename=file.filename,
        file_path=str(file_path),
        file_url=file_url,
        size_bytes=file_size,
        mime_type=content_type
    )

@router.get("/download/{category}/{filename}")
async def download_media_file(
    category: str,
    filename: str,
    _: str = Depends(get_current_recruiter)
):
    """Télécharger un fichier média"""
    
    file_path = settings.UPLOAD_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.delete("/{category}/{filename}")
async def delete_media_file(
    category: str,
    filename: str,
    _: str = Depends(get_current_recruiter)
):
    """Supprimer un fichier média"""
    
    file_path = settings.UPLOAD_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    try:
        file_path.unlink()
        return {"message": "Fichier supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")