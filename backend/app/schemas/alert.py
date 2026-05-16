from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertResponse(BaseModel):
    id: int
    type: str
    severity: str
    message: str
    src_ip: Optional[str]
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    resolved: bool
