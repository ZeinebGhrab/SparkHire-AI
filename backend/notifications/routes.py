from fastapi import APIRouter, Depends, HTTPException, Query
from backend.notifications.models import Notification, NotificationCreate, NotificationUpdate
from backend.auth.security import get_current_recruiter
from backend.database import db
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/", response_model=Notification)
async def create_notification(
    notification: NotificationCreate,
    _: str = Depends(get_current_recruiter)
):
    """Créer une nouvelle notification"""
    
    notification_dict = notification.model_dump()
    notification_dict["read"] = False
    notification_dict["created_at"] = datetime.utcnow()
    
    result = db.notifications.insert_one(notification_dict)
    notification_dict["_id"] = str(result.inserted_id)
    
    return Notification(**notification_dict)

@router.get("/", response_model=List[Notification])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False, description="Afficher uniquement les non lues"),
    email: str = Depends(get_current_recruiter)
):
    """Lister les notifications pour l'utilisateur connecté"""
    
    query = {"recipient_email": email}
    
    if unread_only:
        query["read"] = False
    
    notifications = list(
        db.notifications.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    
    for notif in notifications:
        notif["_id"] = str(notif["_id"])
    
    return [Notification(**notif) for notif in notifications]

@router.get("/unread-count")
async def get_unread_count(
    email: str = Depends(get_current_recruiter)
):
    """Obtenir le nombre de notifications non lues"""
    
    count = db.notifications.count_documents({
        "recipient_email": email,
        "read": False
    })
    
    return {"unread_count": count}

@router.patch("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    email: str = Depends(get_current_recruiter)
):
    """Mettre à jour une notification (marquer comme lue)"""
    
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="ID invalide")
    
    update_data = notification_update.model_dump(exclude_unset=True)
    
    result = db.notifications.update_one(
        {
            "_id": ObjectId(notification_id),
            "recipient_email": email
        },
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    notification = db.notifications.find_one({"_id": ObjectId(notification_id)})
    notification["_id"] = str(notification["_id"])
    
    return Notification(**notification)

@router.post("/mark-all-read")
async def mark_all_as_read(
    email: str = Depends(get_current_recruiter)
):
    """Marquer toutes les notifications comme lues"""
    
    result = db.notifications.update_many(
        {
            "recipient_email": email,
            "read": False
        },
        {"$set": {"read": True}}
    )
    
    return {
        "message": "Notifications marquées comme lues",
        "updated_count": result.modified_count
    }

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    email: str = Depends(get_current_recruiter)
):
    """Supprimer une notification"""
    
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="ID invalide")
    
    result = db.notifications.delete_one({
        "_id": ObjectId(notification_id),
        "recipient_email": email
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    return {"message": "Notification supprimée"}