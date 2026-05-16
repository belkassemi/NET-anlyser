from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.device import Device
from app.schemas.device import DeviceResponse

router = APIRouter()


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db), 
    _=Depends(get_current_user)
):
    return db.query(Device).order_by(Device.last_seen.desc()).offset(offset).limit(limit).all()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    from fastapi import HTTPException
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
