# Data contracts for the API — Pydantic enforces types and builds /docs automatically
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class SensorData(BaseModel):
    """Mirrors the silver_sensor_data table —> one row per sensor event."""

    silver_id: int
    engine_id: Optional[str] = None
    appliance_type: Optional[str] = None
    timestamp: Optional[datetime] = None
    # must be 0 or above, A machine cannot have negative run hours.
    run_hours: Optional[float] = Field(None, ge=0)
    location: Optional[str] = "Unknown Location"  #  instead of returning null
    rpm: Optional[float] = None
    engine_temp: Optional[float] = None
    vibration_hz: Optional[float] = None
    is_valid: bool
    silver_processed_at: datetime


class PaginationMetadata(BaseModel):
    """Describes the current page —> how many rows, where we started, what filters were used."""

    total_returned: int
    skip: int
    limit: int
    filters_applied: dict[str, Any]


class PaginatedSensorResponse(BaseModel):
    """Full API response —> metadata about the page + the actual data rows."""

    metadata: PaginationMetadata
    data: List[SensorData]
