# src/dashboard/components/queries.py
# All SQL queries for the overview dashboard.
# Each function accepts a Streamlit connection object and returns a DataFrame.


def get_fleet_summary(conn):
    return conn.query(
        """
        SELECT
            COUNT(DISTINCT engine_sk)                            AS total_engines,
            COUNT(*)                                             AS total_events,
            ROUND(AVG(engine_temp)::numeric, 2)                  AS avg_temp,
            ROUND(MAX(engine_temp)::numeric, 2)                  AS max_temp,
            ROUND(AVG(rpm)::numeric, 2)                          AS avg_rpm,
            ROUND(AVG(run_hours)::numeric, 1)                    AS avg_run_hours,
            ROUND(MAX(run_hours)::numeric, 1)                    AS max_run_hours,
            COUNT(*) FILTER (WHERE maintenance_warning = TRUE)   AS maint_warnings,
            COUNT(*) FILTER (WHERE temp_warning = TRUE)          AS temp_warnings,
            COUNT(*) FILTER (WHERE rpm_warning = TRUE)           AS rpm_warnings,
            COUNT(*) FILTER (WHERE vibration_warning = TRUE)     AS vib_warnings,
            COUNT(*) FILTER (WHERE
                maintenance_warning OR temp_warning
                OR rpm_warning OR vibration_warning
            )                                                    AS total_warning_events
        FROM fact_sensor_reading;
    """
    )


def get_warnings_by_appliance(conn):
    return conn.query(
        """
        SELECT
            da.appliance_type,
            COUNT(*) FILTER (WHERE f.maintenance_warning) AS maintenance,
            COUNT(*) FILTER (WHERE f.temp_warning)        AS temperature,
            COUNT(*) FILTER (WHERE f.rpm_warning)         AS rpm,
            COUNT(*) FILTER (WHERE f.vibration_warning)   AS vibration,
            COUNT(*) FILTER (WHERE
                f.maintenance_warning OR f.temp_warning
                OR f.rpm_warning OR f.vibration_warning
            )                                             AS total_warnings,
            COUNT(*)                                      AS total_events
        FROM fact_sensor_reading f
        JOIN dim_appliance da ON f.appliance_sk = da.appliance_sk
        GROUP BY da.appliance_type
        ORDER BY total_warnings DESC;
    """
    )


def get_city_stats(conn):
    return conn.query(
        """
        SELECT
            dl.location                           AS city,
            COUNT(DISTINCT f.engine_sk)           AS engines,
            COUNT(*)                              AS events,
            COUNT(*) FILTER (WHERE
                f.maintenance_warning OR f.temp_warning
                OR f.rpm_warning OR f.vibration_warning
            )                                    AS warnings,
            ROUND(AVG(f.engine_temp)::numeric, 2) AS avg_temp,
            ROUND(AVG(f.run_hours)::numeric, 1)   AS avg_run_hours
        FROM fact_sensor_reading f
        JOIN dim_location dl ON f.location_sk = dl.location_sk
        GROUP BY dl.location
        ORDER BY warnings DESC;
    """
    )


def get_maintenance_distribution(conn):
    return conn.query(
        """
        SELECT
            CASE
                WHEN max_hours >= 5000 THEN 'Critical (5000h+)'
                WHEN max_hours >= 4000 THEN 'Warning (4000-4999h)'
                ELSE 'Healthy (<4000h)'
            END AS health_band,
            COUNT(*) AS engine_count
        FROM (
            SELECT engine_sk, MAX(max_run_hours) AS max_hours
            FROM fact_engine_daily GROUP BY engine_sk
        ) sub
        GROUP BY health_band ORDER BY engine_count DESC;
    """
    )


def get_run_hours_histogram(conn):
    return conn.query(
        """
        SELECT ROUND(MAX(max_run_hours)::numeric, 1) AS max_run_hours
        FROM fact_engine_daily GROUP BY engine_sk
        ORDER BY max_run_hours DESC LIMIT 500;
    """
    )


def get_temp_trend(conn):
    return conn.query(
        """
        SELECT
            dd.calendar_date                             AS date,
            ROUND(AVG(fed.max_engine_temp)::numeric, 2) AS avg_temp,
            ROUND(MAX(fed.max_engine_temp)::numeric, 2) AS peak_temp,
            SUM(fed.warnings_total)                     AS daily_warnings
        FROM fact_engine_daily fed
        JOIN dim_date dd ON fed.date_sk = dd.date_sk
        WHERE dd.calendar_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY dd.calendar_date ORDER BY dd.calendar_date;
    """
    )


def get_warning_volume_all_time(conn):
    return conn.query(
        """
        SELECT dd.calendar_date AS date, SUM(fed.warnings_total) AS total_warnings
        FROM fact_engine_daily fed
        JOIN dim_date dd ON fed.date_sk = dd.date_sk
        GROUP BY dd.calendar_date ORDER BY dd.calendar_date;
    """
    )


def get_top_engines(conn):
    return conn.query(
        """
        SELECT
            de.engine_id,
            da.appliance_type,
            dl.location                                 AS city,
            ROUND(MAX(fed.max_run_hours)::numeric, 1)   AS max_run_hours,
            SUM(fed.warnings_total)                     AS total_warnings,
            ROUND(MAX(fed.max_engine_temp)::numeric, 2) AS peak_temp
        FROM fact_engine_daily fed
        JOIN dim_engine de ON fed.engine_sk = de.engine_sk
        JOIN (
            SELECT DISTINCT ON (engine_sk) engine_sk, location_sk, appliance_sk
            FROM fact_sensor_reading ORDER BY engine_sk, event_ts DESC
        ) latest ON latest.engine_sk = fed.engine_sk
        JOIN dim_location  dl ON latest.location_sk  = dl.location_sk
        JOIN dim_appliance da ON latest.appliance_sk = da.appliance_sk
        GROUP BY de.engine_id, da.appliance_type, dl.location
        ORDER BY total_warnings DESC LIMIT 20;
    """
    )


def get_sensor_scatter(conn):
    return conn.query(
        """
        SELECT f.rpm, f.engine_temp, f.vibration_hz, f.run_hours,
               da.appliance_type, dl.location
        FROM fact_sensor_reading f
        JOIN dim_appliance da ON f.appliance_sk = da.appliance_sk
        JOIN dim_location  dl ON f.location_sk  = dl.location_sk
        WHERE f.rpm IS NOT NULL AND f.engine_temp IS NOT NULL
        ORDER BY RANDOM() LIMIT 2000;
    """
    )


# ── DAILY AGGREGATION ─────────────────────────────────────────────────────────


def get_daily_fleet_health(conn):
    """Daily aggregated health metrics from fact_engine_daily for the last 30 days."""
    return conn.query(
        """
        SELECT
            dd.calendar_date                                    AS date,
            COUNT(DISTINCT fed.engine_sk)                       AS active_engines,
            ROUND(AVG(fed.max_engine_temp)::numeric, 2)         AS avg_max_temp,
            ROUND(AVG(fed.avg_rpm)::numeric, 2)                 AS avg_rpm,
            ROUND(AVG(fed.max_vibration)::numeric, 2)           AS avg_vibration,
            ROUND(AVG(fed.max_run_hours)::numeric, 1)           AS avg_run_hours,
            SUM(fed.warnings_total)                             AS total_warnings
        FROM fact_engine_daily fed
        JOIN dim_date dd ON fed.date_sk = dd.date_sk
        WHERE dd.calendar_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY dd.calendar_date
        ORDER BY dd.calendar_date;
    """
    )


def get_latest_day_snapshot(conn):
    """Single-row snapshot of the most recently aggregated day."""
    return conn.query(
        """
        SELECT
            dd.calendar_date                                    AS date,
            COUNT(DISTINCT fed.engine_sk)                       AS active_engines,
            ROUND(AVG(fed.max_engine_temp)::numeric, 2)         AS avg_max_temp,
            ROUND(AVG(fed.avg_rpm)::numeric, 2)                 AS avg_rpm,
            ROUND(SUM(fed.warnings_total)::numeric, 0)          AS total_warnings,
            COUNT(DISTINCT CASE WHEN fed.warnings_total > 0
                THEN fed.engine_sk END)                         AS engines_with_warnings
        FROM fact_engine_daily fed
        JOIN dim_date dd ON fed.date_sk = dd.date_sk
        WHERE dd.calendar_date = (SELECT MAX(calendar_date) FROM dim_date
                                   WHERE date_sk IN (SELECT date_sk FROM fact_engine_daily))
        GROUP BY dd.calendar_date;
    """
    )


# ── ERROR QUERIES ──────────────────────────────────────────────────────────────


def get_error_types(conn):
    return conn.query(
        """
        SELECT
            COUNT(*) FILTER (WHERE temp_warning)        AS temp_errors,
            COUNT(*) FILTER (WHERE rpm_warning)         AS rpm_errors,
            COUNT(*) FILTER (WHERE vibration_warning)   AS vibration_errors,
            COUNT(*) FILTER (WHERE maintenance_warning) AS maintenance_errors
        FROM fact_sensor_reading;
    """
    )


def get_errors_by_city(conn):
    return conn.query(
        """
        SELECT l.location, a.appliance_type,
            COUNT(*) FILTER (WHERE
                f.temp_warning OR f.rpm_warning
                OR f.vibration_warning OR f.maintenance_warning
            ) AS total_errors
        FROM fact_sensor_reading f
        JOIN dim_location l  ON f.location_sk  = l.location_sk
        JOIN dim_appliance a ON f.appliance_sk = a.appliance_sk
        GROUP BY l.location, a.appliance_type
        HAVING COUNT(*) FILTER (WHERE
            f.temp_warning OR f.rpm_warning
            OR f.vibration_warning OR f.maintenance_warning
        ) > 0
        ORDER BY total_errors DESC;
    """
    )


def get_error_rate_by_city(conn):
    return conn.query(
        """
        SELECT l.location,
            COUNT(f.reading_id) AS total_readings,
            COUNT(CASE WHEN f.temp_warning OR f.rpm_warning
                OR f.vibration_warning OR f.maintenance_warning THEN 1 END) AS error_readings,
            ROUND(
                COUNT(CASE WHEN f.temp_warning OR f.rpm_warning
                    OR f.vibration_warning OR f.maintenance_warning THEN 1 END)
                * 100.0 / NULLIF(COUNT(f.reading_id), 0), 1
            ) AS error_percentage
        FROM fact_sensor_reading f
        JOIN dim_location l ON f.location_sk = l.location_sk
        GROUP BY l.location ORDER BY error_percentage DESC;
    """
    )


def get_error_timeline(conn):
    return conn.query(
        """
        SELECT d.calendar_date, l.location,
            COUNT(*) FILTER (WHERE
                f.temp_warning OR f.rpm_warning
                OR f.vibration_warning OR f.maintenance_warning
            ) AS daily_errors
        FROM fact_sensor_reading f
        JOIN dim_date d     ON f.date_sk     = d.date_sk
        JOIN dim_location l ON f.location_sk = l.location_sk
        WHERE f.temp_warning OR f.rpm_warning
            OR f.vibration_warning OR f.maintenance_warning
        GROUP BY d.calendar_date, l.location
        ORDER BY d.calendar_date ASC;
    """
    )
