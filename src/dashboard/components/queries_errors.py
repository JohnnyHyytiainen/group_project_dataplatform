# Script for querying errors for our IoT sensors

# --- Sektion 1: Feltyper ---
# Error typer
def get_error_types_query():
    """Räknar totala antalet av varje specifik feltyp."""
    return """
        SELECT
            COUNT(*) FILTER (WHERE temp_warning) AS temp_errors,
            COUNT(*) FILTER (WHERE rpm_warning) AS rpm_errors,
            COUNT(*) FILTER (WHERE vibration_warning) AS vibration_errors,
            COUNT(*) FILTER (WHERE maintenance_warning) as maintenance_errors
        FROM fact_sensor_reading;
    """


# --- Sektion 2: Fel per Stad och Maskin ---
# Error per stad
def get_errors_by_city_query():
    """Räknar ut toala antalet fel (alla typer) per stad OCH maskintyp."""
    return """
        SELECT 
            l.location,
            a.appliance_type,
            COUNT(*) FILTER (WHERE f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning) as total_errors
        FROM fact_sensor_reading f
        JOIN dim_location l ON f.location_sk = l.location_sk
        JOIN dim_appliance a ON f.appliance_sk = a.appliance_sk
        GROUP BY l.location, a.appliance_type
        HAVING COUNT(*) FILTER (WHERE f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning) > 0
        ORDER BY total_errors DESC;
    """


# --- Sektion 4: Fel procent per stad ---
# Error % per stad
def get_error_rate_by_city_query():
    """Räknar ut andelen(i procent) av maskinerna i en stad som har larm."""
    return """
        SELECT 
            l.location,
            COUNT(DISTINCT f.engine_sk) AS total_machines,
            COUNT(DISTINCT CASE WHEN f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning THEN f.engine_sk END) AS machines_with_errors,
            ROUND((COUNT(DISTINCT CASE WHEN f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning THEN f.engine_sk END) * 100.0) / NULLIF(COUNT(DISTINCT f.engine_sk), 0), 1) AS error_percentage
        FROM fact_sensor_reading f
        JOIN dim_location l ON f.location_sk = l.location_sk
        GROUP BY l.location
        ORDER BY error_percentage DESC;
    """


# --- Sektion 4: Tidslinje (Timeline) per stad ---
# Error över en timeline
def get_error_timeline_query():
    """Hämtar en tidslinje över NÄR felen sker per stad."""
    return """
        SELECT 
            d.calendar_date,
            l.location,
            COUNT(*) FILTER (WHERE f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning) as daily_errors
        FROM fact_sensor_reading f
        JOIN dim_date d ON f.date_sk = d.date_sk
        JOIN dim_location l ON f.location_sk = l.location_sk
        WHERE f.temp_warning OR f.rpm_warning OR f.vibration_warning OR f.maintenance_warning
        GROUP BY d.calendar_date, l.location
        ORDER BY d.calendar_date ASC;
    """
