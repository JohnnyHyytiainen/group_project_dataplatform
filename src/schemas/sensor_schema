from pydantic import BaseModel, Field
from datetime import datetime

class SensorEvent(BaseModel):
    engine_id: str
    appliance_type: str
    sensor_type: str
    run_hours: float = Field(..., ge=0.0)
    value: float = Field(..., ge=-50.0, le=5000.0)
    timestamp: datetime
    location: str


