"""Endpoints called exclusively by the capture service (not exposed to users)."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models.traffic_log import TrafficLog
from app.models.device import Device
from app.schemas.traffic import PacketIn

router = APIRouter()


def verify_internal(x_api_key: str = Header(...)):
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/packet", dependencies=[Depends(verify_internal)])
async def ingest_packet(packet: PacketIn, db: Session = Depends(get_db)):
    log = TrafficLog(
        src_ip=packet.src_ip,
        dst_ip=packet.dst_ip,
        src_port=packet.src_port,
        dst_port=packet.dst_port,
        protocol=packet.protocol,
        bytes=packet.bytes,
        timestamp=packet.timestamp or datetime.utcnow(),
        country=packet.country,
        layer7_category=packet.layer7_category,
    )
    db.add(log)

    # Upsert device
    for ip in (packet.src_ip, packet.dst_ip):
        device = db.query(Device).filter(Device.ip == ip).first()
        if device:
            device.last_seen = datetime.utcnow()
            device.status = True
        else:
            db.add(Device(ip=ip))

    db.commit()
    return {"status": "ok"}


@router.post("/batch", dependencies=[Depends(verify_internal)])
async def ingest_batch(packets: list[PacketIn], db: Session = Depends(get_db)):
    logs = []
    ips = set()
    for p in packets:
        logs.append(TrafficLog(
            src_ip=p.src_ip, dst_ip=p.dst_ip,
            src_port=p.src_port, dst_port=p.dst_port,
            protocol=p.protocol, bytes=p.bytes,
            timestamp=p.timestamp or datetime.utcnow(),
            country=p.country, layer7_category=p.layer7_category,
        ))
        ips.add(p.src_ip)
        ips.add(p.dst_ip)

    db.bulk_save_objects(logs)

    # Bulk upsert devices
    existing_devices = db.query(Device).filter(Device.ip.in_(ips)).all()
    device_map = {d.ip: d for d in existing_devices}
    
    new_devices = []
    now = datetime.utcnow()
    
    for ip in ips:
        if ip in device_map:
            device_map[ip].last_seen = now
            device_map[ip].status = True
        else:
            new_devices.append(Device(ip=ip, first_seen=now, last_seen=now, status=True))
    
    if new_devices:
        db.bulk_save_objects(new_devices)

    db.commit()
    return {"status": "ok", "ingested": len(packets)}
