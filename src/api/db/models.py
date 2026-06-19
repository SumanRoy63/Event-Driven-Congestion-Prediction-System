from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from src.api.db.database import Base

class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, index=True)
    location = Column(String)
    expected_attendance = Column(Integer, default=0)
    road_closure_probability = Column(Float)
    predicted_severity = Column(String)
    alert_triggered = Column(Boolean, default=False)
