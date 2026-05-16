from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeviceResponse(BaseModel):
    id: int
    ip: str
    mac: Optional[str]
    hostname: Optional[str]
    vendor: Optional[str]
    status: bool
    last_seen: datetime
    first_seen: datetime

    model_config = {"from_attributes": True}
