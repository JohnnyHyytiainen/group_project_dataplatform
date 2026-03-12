from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SensorEvent(BaseModel):
    engine_id: str
    appliance_type: str
    timestamp: datetime
    run_hours: float = Field(..., ge=0.0, le=20000.0)
    location: str
    rpm: Optional[float] = Field(None, ge=0.0, le=5000.0)
    engine_temp: Optional[float] = Field(None, ge=10.0, le=150.0)
    vibration_hz: Optional[float] = Field(None, ge=0.0, le=50.0)



