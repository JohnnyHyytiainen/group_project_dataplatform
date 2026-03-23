import streamlit as st
from components.queries_errors import (
    get_error_types_query,
    get_errors_by_city_query,
    get_error_timeline_query,
    get_error_rate_by_city_query,
)

st.set_page_config(page_title="Maskinfel", layout="wide")
st.title("Maskinfelanalys")
st.markdown("Analys av fysiska maskinfel och larm (Vibration, Temp, RPM, Underhåll)")

# Koppla upp mot databasen
conn = st.connection("postgresql", type="sql")

# Hämta data
df_types = conn.query(get_error_types_query())
df_city_appliance = conn.query(get_errors_by_city_query())
df_timeline = conn.query(get_error_timeline_query())


# --- Sektion 1: Feltyper ---
st.subheader("Totala feltyper i nuvarande flotta")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Temp Errors", df_types.iloc[0]["temp_errors"])
col2.metric("RPM Errors", df_types.iloc[0]["rpm_errors"])
col3.metric("Vibration Errors", df_types.iloc[0]["vibration_errors"])
col4.metric("Underhåll behövs", df_types.iloc[0]["maintenance_errors"])

st.divider()


# --- Sektion 2: Fel per Stad och Maskin ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Fel per Stad & Maskintyp")
    if not df_city_appliance.empty:
        # Pivotera datan så Streamlit kan bygga en "Stacked Bar Chart"
        pivot_df = df_city_appliance.pivot(
            index="location", columns="appliance_type", values="total_errors"
        ).fillna(0)
        st.bar_chart(pivot_df)
    else:
        st.info("Inga fel hittades.")

with col_right:
    st.subheader("Rådata: Fel per Stad")
    st.dataframe(df_city_appliance, use_container_width=True)

st.divider()


# --- Sektion 4: Fel procent per stad ---
st.subheader("Vilken stad har sjukast maskinpark? (Felprocent)")
df_error_rate = conn.query(get_error_rate_by_city_query())
if not df_error_rate.empty:
    st.bar_chart(df_error_rate.set_index("location")["error_percentage"])


# --- Sektion 4: Tidslinje (Timeline) per stad ---
st.subheader("Tidslinje: Fel över tid per stad (2016 - Idag)")

if not df_timeline.empty:
    # Hitta alla unika städer i vårt dataset
    cities = df_timeline["location"].unique()

    # Skapa en flik (tab) för varje stad dynamiskt
    tabs = st.tabs([str(city) for city in cities])

    # Loopa igenom varje stad och rita en separat graf i rätt flik
    for index, city in enumerate(cities):
        with tabs[index]:
            # Filtrera fram bara den här stadens data
            city_df = df_timeline[df_timeline["location"] == city]

            # Sätt kalenderdatumet som Index (Streamlit använder Index som X-axel)
            city_chart_data = city_df.set_index("calendar_date")["daily_errors"]

            # Rita linjegrafen
            st.line_chart(city_chart_data)
else:
    st.info("Ingen tidslinje-data hittades.")
