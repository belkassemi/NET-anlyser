from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50), unique=True, index=True)
    mac = Column(String(50), nullable=True)
    hostname = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    status = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
