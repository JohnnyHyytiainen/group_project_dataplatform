# Unit tests for src/silver/cleaner.py
# Run with: uv run pytest src/test/test_cleaner.py -v

from src.silver.cleaner import clean_event


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


def test_valid_event_is_valid():
    """A completely normal row should pass through with is_valid = True."""
    result = clean_event(base_event())
    assert result["is_valid"] is True


# --- String cleaning ---
def test_whitespace_string_becomes_float():
    result = clean_event(base_event(rpm="  1200.5  "))
    assert result["rpm"] == 1200.5


def test_whitespace_string_run_hours_becomes_float():
    result = clean_event(base_event(run_hours="   312.0   "))
    assert result["run_hours"] == 312.0


def test_sensor_offline_becomes_none():
    result = clean_event(base_event(rpm="SENSOR_OFFLINE"))
    assert result["rpm"] is None


# --- Validation logic ---
def test_extreme_rpm_sets_is_valid_false():
    result = clean_event(base_event(rpm=9999.0))
    assert result["is_valid"] is False


def test_extreme_vibration_sets_is_valid_false():
    result = clean_event(base_event(vibration_hz=50.0))
    assert result["is_valid"] is False


def test_missing_engine_id_sets_is_valid_false():
    event = base_event()
    del event["engine_id"]
    result = clean_event(event)
    assert result["is_valid"] is False


# --- Appliance type normalization ---
def test_appliance_type_caps_and_spaces_normalized():
    result = clean_event(base_event(appliance_type="WASHING MACHINE"))
    assert result["appliance_type"] == "washing_machine"


# --- Location fallback ---
def test_missing_location_gets_fallback():
    event = base_event()
    del event["location"]
    result = clean_event(event)
    assert result["location"] == "Unknown Location"


# --- Regression test for the bug ---
def test_offline_sensor_does_not_kill_is_valid():
    """
    REGRESSION TEST: rpm=None means the sensor was offline, not that the row is corrupt.
    is_valid must stay True as long as engine_id is present and no extreme values exist.
    If this test fails it means 'and not missing_value' has been added back to line 80.
    """
    result = clean_event(base_event(rpm=None))
    assert result["is_valid"] is True
