from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PacketIn(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: str
    bytes: int = 0
    timestamp: Optional[datetime] = None
    country: Optional[str] = None
    layer7_category: Optional[str] = None


class TrafficLogResponse(PacketIn):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class LiveMetrics(BaseModel):
    packets_per_sec: float
    bytes_per_sec: float
    active_connections: int
    top_protocols: list[dict]
    top_talkers_src: list[dict]
    top_talkers_dst: list[dict]
    timestamp: datetime
