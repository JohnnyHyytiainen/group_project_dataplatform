# Unit tests for src/silver/cleaner.py
# Run with: uv run pytest tests/test_cleaner.py -v

from src.silver.cleaner import clean_event


# Reusable base event representing a normal, fully valid sensor row
def base_event(**overrides):
    event = {
        "engine_id": "abc-123",
        "appliance_type": "washing_machine",
        "timestamp": "2024-01-01T12:00:00",
        "run_hours": 312.0,
        "location": "Stockholm",
        "rpm": 1200.0,
        "engine_temp": 72.4,
        "vibration_hz": 8.1,
    }
    event.update(overrides)
    return event


# --- Happy path ---
def test_valid_event_is_valid():
    """A completely normal row should pass through with is_valid = True."""
    result = clean_event(base_event())
    assert result["is_valid"] is True
