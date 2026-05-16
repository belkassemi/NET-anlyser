from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionResponse(BaseModel):
    id: int
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: str
    bytes: int
    packets: int
    duration: float
    start_time: datetime
    end_time: Optional[datetime]
    layer7_category: Optional[str]

    model_config = {"from_attributes": True}
