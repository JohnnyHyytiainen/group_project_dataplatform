# src/dashboard/components/queries.py

# Ska in i queries.py sen!!!!!


def get_total_engines_query():
    """Hämtar totalt antal unika motorer från Gold-lagret."""
    return "SELECT COUNT(*) as total_engines FROM dim_engine;"


def get_avg_temp_query():
    """Hämtar snitt-temperaturen för hela flottan."""
    return "SELECT ROUND(AVG(engine_temp)::numeric, 1) as avg_temp FROM fact_sensor_reading;"


# Hämta fördelning per stad
def get_machines_per_city_query():
    return "SELECT l.location, COUNT(DISTINCT f.engine_sk) as antal_maskiner FROM fact_sensor_reading f JOIN dim_location l ON f.location_sk = l.location_sk GROUP BY l.location ORDER BY antal_maskiner DESC;"


# Hämta fördelning per maskintyp
def get_machines_per_appliance_query():
    return "SELECT a.appliance_type, COUNT(DISTINCT f.engine_sk) as antal_maskiner FROM fact_sensor_reading f JOIN dim_appliance a ON f.appliance_sk = a.appliance_sk GROUP BY a.appliance_type ORDER BY antal_maskiner DESC;"


# Hämta totalt antal maskiner med minst ett larm (Enkelt och kraftfullt)
def get_total_warnings_query():
    return "SELECT COUNT(DISTINCT engine_sk) as maskiner_med_larm FROM fact_sensor_reading WHERE maintenance_warning = TRUE  OR temp_warning = TRUE  OR rpm_warning = TRUE  OR vibration_warning = TRUE;"
