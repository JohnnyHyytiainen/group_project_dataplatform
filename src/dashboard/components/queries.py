"""
SQL queries for the Machine Fleet Analytics Dashboard.
All queries read from the Gold layer (fact_sensor_reading, fact_engine_daily,
dim_engine, dim_location, dim_appliance, dim_date).

Each function returns a plain SQL string.
The page scripts own the connection and call conn.query(get_xxx_query()).
"""

# ── PAGE 1: OVERVIEW ──────────────────────────────────────────────────────────


def get_fleet_summary_query():
    """High-level KPIs for the entire fleet from the Gold fact table."""
    return """
        SELECT
            COUNT(DISTINCT f.engine_sk)                AS total_engines,
            COUNT(*)                                   AS total_events,
            ROUND(AVG(f.engine_temp)::numeric, 1)      AS avg_temp,
            ROUND(AVG(f.rpm)::numeric, 1)              AS avg_rpm,
            COUNT(*) FILTER (WHERE
                f.maintenance_warning = TRUE OR
                f.temp_warning        = TRUE OR
                f.rpm_warning         = TRUE OR
                f.vibration_warning   = TRUE
            )                                          AS total_warning_events
        FROM fact_sensor_reading f;
    """


def get_warnings_by_appliance_query():
    """Warning counts broken down by appliance type."""
    return """
        SELECT
            da.appliance_type                                     AS appliance_type,
            COUNT(*) FILTER (WHERE f.maintenance_warning = TRUE)  AS maintenance,
            COUNT(*) FILTER (WHERE f.temp_warning        = TRUE)  AS temperature,
            COUNT(*) FILTER (WHERE f.rpm_warning         = TRUE)  AS rpm,
            COUNT(*) FILTER (WHERE f.vibration_warning   = TRUE)  AS vibration,
            COUNT(*) FILTER (WHERE
                f.maintenance_warning = TRUE OR
                f.temp_warning        = TRUE OR
                f.rpm_warning         = TRUE OR
                f.vibration_warning   = TRUE
            )                                                     AS total_warnings
        FROM fact_sensor_reading f
        JOIN dim_appliance da ON f.appliance_sk = da.appliance_sk
        GROUP BY da.appliance_type
        ORDER BY total_warnings DESC;
    """


def get_engines_per_city_query():
    """Number of unique engines per city."""
    return """
        SELECT
            l.location,
            COUNT(DISTINCT f.engine_sk) AS engine_count
        FROM fact_sensor_reading f
        JOIN dim_location l ON f.location_sk = l.location_sk
        GROUP BY l.location
        ORDER BY engine_count DESC;
    """


def get_engines_with_any_warning_query():
    """Total unique engines that have triggered at least one warning."""
    return """
        SELECT COUNT(DISTINCT engine_sk) AS engines_with_warnings
        FROM fact_sensor_reading
        WHERE maintenance_warning = TRUE
           OR temp_warning        = TRUE
           OR rpm_warning         = TRUE
           OR vibration_warning   = TRUE;
    """


# ── PAGE 2: WARNINGS & ANOMALIES ──────────────────────────────────────────────


def get_warnings_by_city_query():
    """Number of warning events per city."""
    return """
        SELECT
            dl.location  AS city,
            COUNT(*)     AS total_warnings
        FROM fact_sensor_reading f
        JOIN dim_location dl ON f.location_sk = dl.location_sk
        WHERE (
            f.maintenance_warning = TRUE OR
            f.temp_warning        = TRUE OR
            f.rpm_warning         = TRUE OR
            f.vibration_warning   = TRUE
        )
        GROUP BY dl.location
        ORDER BY total_warnings DESC;
    """


def get_avg_temp_over_time_query():
    """Daily average temperature over the last 90 days."""
    return """
        SELECT
            dd.calendar_date                              AS date,
            ROUND(AVG(fed.max_engine_temp)::numeric, 2)  AS avg_temp
        FROM fact_engine_daily fed
        JOIN dim_date dd ON fed.date_sk = dd.date_sk
        WHERE dd.calendar_date >= CURRENT_DATE - INTERVAL '90 days'
          AND fed.max_engine_temp IS NOT NULL
        GROUP BY dd.calendar_date
        ORDER BY dd.calendar_date;
    """


def get_top_warning_engines_query():
    """Top 20 engines ranked by total number of warning events."""
    return """
        SELECT
            de.engine_id             AS engine_id,
            da.appliance_type        AS appliance_type,
            dl.location              AS city,
            SUM(fed.warnings_total)  AS total_warnings
        FROM fact_engine_daily fed
        JOIN dim_engine de ON fed.engine_sk = de.engine_sk
        JOIN (
            SELECT DISTINCT ON (engine_sk)
                engine_sk, location_sk, appliance_sk
            FROM fact_sensor_reading
            ORDER BY engine_sk, event_ts DESC
        ) latest ON latest.engine_sk = fed.engine_sk
        JOIN dim_location  dl ON latest.location_sk  = dl.location_sk
        JOIN dim_appliance da ON latest.appliance_sk = da.appliance_sk
        GROUP BY de.engine_id, da.appliance_type, dl.location
        ORDER BY total_warnings DESC
        LIMIT 20;
    """


# ── PAGE 3: MAINTENANCE ───────────────────────────────────────────────────────


def get_maintenance_distribution_query():
    """Fleet health distribution based on each engine's max run hours."""
    return """
        SELECT
            CASE
                WHEN max_hours >= 5000 THEN 'Critical (5000h+)'
                WHEN max_hours >= 4000 THEN 'Warning (4000-4999h)'
                ELSE 'Healthy (<4000h)'
            END AS health_band,
            COUNT(*) AS engine_count
        FROM (
            SELECT engine_sk, MAX(max_run_hours) AS max_hours
            FROM fact_engine_daily
            GROUP BY engine_sk
        ) sub
        GROUP BY health_band
        ORDER BY engine_count DESC;
    """


def get_critical_engines_query():
    """Engines at or above 5000 run hours — require immediate service."""
    return """
        SELECT
            de.engine_id                                  AS engine_id,
            da.appliance_type                             AS appliance_type,
            dl.location                                   AS city,
            ROUND(MAX(fed.max_run_hours)::numeric, 1)     AS max_run_hours
        FROM fact_engine_daily fed
        JOIN dim_engine de ON fed.engine_sk = de.engine_sk
        JOIN (
            SELECT DISTINCT ON (engine_sk)
                engine_sk, location_sk, appliance_sk
            FROM fact_sensor_reading
            ORDER BY engine_sk, event_ts DESC
        ) latest ON latest.engine_sk = fed.engine_sk
        JOIN dim_location  dl ON latest.location_sk  = dl.location_sk
        JOIN dim_appliance da ON latest.appliance_sk = da.appliance_sk
        GROUP BY de.engine_id, da.appliance_type, dl.location
        HAVING MAX(fed.max_run_hours) >= 5000
        ORDER BY max_run_hours DESC;
    """


def get_warning_engines_query():
    """Engines between 4000–4999 run hours — service needed soon."""
    return """
        SELECT
            de.engine_id                                  AS engine_id,
            da.appliance_type                             AS appliance_type,
            dl.location                                   AS city,
            ROUND(MAX(fed.max_run_hours)::numeric, 1)     AS max_run_hours
        FROM fact_engine_daily fed
        JOIN dim_engine de ON fed.engine_sk = de.engine_sk
        JOIN (
            SELECT DISTINCT ON (engine_sk)
                engine_sk, location_sk, appliance_sk
            FROM fact_sensor_reading
            ORDER BY engine_sk, event_ts DESC
        ) latest ON latest.engine_sk = fed.engine_sk
        JOIN dim_location  dl ON latest.location_sk  = dl.location_sk
        JOIN dim_appliance da ON latest.appliance_sk = da.appliance_sk
        GROUP BY de.engine_id, da.appliance_type, dl.location
        HAVING MAX(fed.max_run_hours) >= 4000 AND MAX(fed.max_run_hours) < 5000
        ORDER BY max_run_hours DESC;
    """
