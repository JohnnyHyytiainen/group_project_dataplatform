"""
Page 1 — Overview
Fleet-wide KPIs, warning counts by appliance type, and engine distribution by city.
"""

import streamlit as st
from components.queries import (
    get_fleet_summary_query,
    get_warnings_by_appliance_query,
    get_engines_per_city_query,
    get_engines_with_any_warning_query,
)
from components.charts import warning_bar_chart

st.set_page_config(page_title="Översikt", page_icon="📊", layout="wide")
st.title("📊 Flottan – Översikt")
st.markdown(
    "Övergripande nyckeltal och varningssammanställning för hela maskinflottan."
)

# Koppla upp mot databasen
conn = st.connection("postgresql", type="sql")

# ── KPI CARDS ────────────────────────────────────────────────────────────────
st.subheader("Nyckeltal för hela flottan")

summary = conn.query(get_fleet_summary_query())
engines_flagged = conn.query(get_engines_with_any_warning_query())

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Totalt antal motorer", f"{int(summary['total_engines'].iloc[0]):,}")
col2.metric("Totalt antal händelser", f"{int(summary['total_events'].iloc[0]):,}")
col3.metric("Medeltemperatur", f"{summary['avg_temp'].iloc[0]} °C")
col4.metric("Medel-RPM", f"{summary['avg_rpm'].iloc[0]}")
col5.metric(
    "Motorer med varningar",
    f"{int(engines_flagged['engines_with_warnings'].iloc[0]):,}",
)

st.divider()

# ── WARNING BREAKDOWN ─────────────────────────────────────────────────────────
st.subheader("⚠️ Varningar per maskintyp")

warn_df = conn.query(get_warnings_by_appliance_query())

if not warn_df.empty:
    st.plotly_chart(warning_bar_chart(warn_df), use_container_width=True)
    st.dataframe(
        warn_df.rename(
            columns={
                "appliance_type": "Maskintyp",
                "maintenance": "Underhåll",
                "temperature": "Temperatur",
                "rpm": "RPM",
                "vibration": "Vibration",
                "total_warnings": "Totalt varningar",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Ingen varningsdata tillgänglig ännu.")

st.divider()

# ── ENGINES PER CITY ──────────────────────────────────────────────────────────
st.subheader("🗺️ Motorfördelning per stad")

city_df = conn.query(get_engines_per_city_query())

if not city_df.empty:
    st.bar_chart(city_df.set_index("location")["engine_count"])
else:
    st.info("Ingen platsdata tillgänglig ännu.")
