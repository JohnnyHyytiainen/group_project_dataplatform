"""
Page 2 — Warnings & Anomalies
Temperature trends over time, warnings by city, and top offending engines.
"""

import streamlit as st
from components.queries import (
    get_warnings_by_city_query,
    get_avg_temp_over_time_query,
    get_top_warning_engines_query,
)
from components.charts import (
    warnings_by_city_bar,
    avg_temp_line_chart,
    top_warning_engines_bar,
)

st.set_page_config(page_title="Varningar & Anomalier", page_icon="⚠️", layout="wide")
st.title("⚠️ Varningar & Anomalier")
st.markdown(
    "Temperaturutveckling över tid, geografisk varningsfördelning och de motorer som genererar flest larm."
)

# Koppla upp mot databasen
conn = st.connection("postgresql", type="sql")

# Hämta data
df_temp = conn.query(get_avg_temp_over_time_query())
df_city = conn.query(get_warnings_by_city_query())
df_engines = conn.query(get_top_warning_engines_query())

# ── TEMPERATURE OVER TIME ─────────────────────────────────────────────────────
st.subheader("🌡️ Daglig medeltemperatur (senaste 90 dagarna)")

if not df_temp.empty:
    st.plotly_chart(avg_temp_line_chart(df_temp), use_container_width=True)
else:
    st.info("Ingen temperaturdata tillgänglig för de senaste 90 dagarna.")

st.divider()

# ── WARNINGS BY CITY ──────────────────────────────────────────────────────────
st.subheader("🗺️ Varningshändelser per stad")

if not df_city.empty:
    st.plotly_chart(warnings_by_city_bar(df_city), use_container_width=True)
else:
    st.info("Inga varningshändelser hittades.")

st.divider()

# ── TOP WARNING ENGINES ────────────────────────────────────────────────────────
st.subheader("🔴 Topp 20 motorer efter antal varningar")

if not df_engines.empty:
    st.plotly_chart(top_warning_engines_bar(df_engines), use_container_width=True)
    st.dataframe(
        df_engines.rename(
            columns={
                "engine_id": "Motor-ID",
                "appliance_type": "Maskintyp",
                "city": "Stad",
                "total_warnings": "Totalt varningar",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Ingen motorvarningsdata tillgänglig.")
