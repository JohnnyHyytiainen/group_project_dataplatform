import streamlit as st

st.set_page_config(page_title="Anomalies", layout="wide")
st.title("Anomalier & Datakvalitet")

# Initiera databaskopplingen
conn = st.connection("postgresql", type="sql")


# @st.cache_data gör att resultatet sparas i minnet.
# ttl=60 betyder att den hämtar ny data från databasen max en gång i minuten.
@st.cache_data(ttl=60)
def get_invalid_data_stats():
    query = """
    SELECT 
        a.appliance_type,
        COUNT(f.reading_id) AS total_events,
        SUM(CASE WHEN f.is_valid = FALSE THEN 1 ELSE 0 END) AS invalid_events
    FROM FACT_SENSOR_READING f
    JOIN DIM_ENGINE e ON f.engine_sk = e.engine_sk
    JOIN DIM_APPLIANCE a ON e.appliance_sk = a.appliance_sk
    GROUP BY a.appliance_type;
    """
    # conn.query returnerar en Pandas DataFrame automatiskt!
    return conn.query(query)


st.write(
    "Här analyserar vi sensorernas tillförlitlighet och hur ofta vi tappar data (is_valid = FALSE)."
)

# Hämta datan via vår cachade funktion
df_anomalies = get_invalid_data_stats()

# Skapa en ny kolumn för procentuell felfrekvens
df_anomalies["error_rate_%"] = (
    df_anomalies["invalid_events"] / df_anomalies["total_events"]
) * 100

# Visa datan i layouten (två spalter)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Rådata")
    st.dataframe(df_anomalies, use_container_width=True)

with col2:
    st.subheader("Felfrekvens per maskintyp")
    # Streamlit har inbyggda grafer som är superenkla att använda
    st.bar_chart(data=df_anomalies, x="appliance_type", y="error_rate_%")
