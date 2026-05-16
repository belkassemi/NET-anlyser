from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    src_ip = Column(String(50), index=True)
    dst_ip = Column(String(50), index=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String(50))
    bytes = Column(BigInteger, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    country = Column(String(100), nullable=True)
    layer7_category = Column(String(100), nullable=True)
    processed = Column(Boolean, default=False, server_default="0", index=True)
