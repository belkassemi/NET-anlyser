from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Float
from app.core.database import Base


class NetworkSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    src_ip = Column(String(50), index=True)
    dst_ip = Column(String(50), index=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String(50))
    bytes = Column(BigInteger, default=0)
    packets = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True), nullable=True)
    layer7_category = Column(String(100), nullable=True)
