# src/dashboard/pages/01_overview.py
# Main overview page — layout and logic only.
# All queries live in components/queries.py
# All charts live in components/charts.py

import streamlit as st
from components.queries import (
    get_fleet_summary,
    get_warnings_by_appliance,
    get_city_stats,
    get_maintenance_distribution,
    get_run_hours_histogram,
    get_temp_trend,
    get_warning_volume_all_time,
    get_top_engines,
    get_sensor_scatter,
    get_error_types,
    get_errors_by_city,
    get_error_rate_by_city,
    get_error_timeline,
    get_daily_fleet_health,
    get_latest_day_snapshot,
)
from components.charts import (
    warning_pie_chart,
    warnings_by_appliance_bar,
    warning_rate_bar,
    maintenance_donut,
    run_hours_histogram,
    engines_per_city_bar,
    warnings_per_city_bar,
    city_scatter,
    temp_and_warnings_timeseries,
    warning_volume_area,
    sensor_scatter,
    correlation_heatmap,
    top_engines_bar,
    error_rate_bar,
    error_timeline_line,
    daily_health_chart,
)

st.set_page_config(page_title="Översikt", page_icon="📊", layout="wide")


# ── CONNECTION ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return st.connection("postgresql", type="sql")


conn = get_conn()


# ── CACHED DATA ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    return {
        "summary": get_fleet_summary(conn),
        "warn_app": get_warnings_by_appliance(conn),
        "city_stats": get_city_stats(conn),
        "maint_dist": get_maintenance_distribution(conn),
        "hist_df": get_run_hours_histogram(conn),
        "temp_trend": get_temp_trend(conn),
        "warn_time": get_warning_volume_all_time(conn),
        "top_eng": get_top_engines(conn),
        "scatter": get_sensor_scatter(conn),
        "daily": get_daily_fleet_health(conn),
        "snapshot": get_latest_day_snapshot(conn),
    }


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Översikt")
    st.caption("Välj en sektion att utforska.")
    st.divider()
    section = st.radio(
        "Sektion",
        [
            "📊 Fleet KPIs",
            "⚠️ Varningar per maskintyp",
            "🔧 Underhållsstatus",
            "🗺️ Geografisk fördelning",
            "📈 Tidsserie",
            "🔍 Sensorkorrelationer",
            "🏆 Topp 20 motorer",
            "📅 Daglig hälsa",
            "🚨 Felanalys",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("🔄 Uppdatera data"):
        st.cache_data.clear()
        st.rerun()

# ── LOAD ──────────────────────────────────────────────────────────────────────
try:
    data = load_all()
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen: {e}")
    st.stop()

s = data["summary"].iloc[0]
warn_app = data["warn_app"]
city_stats = data["city_stats"]
maint_dist = data["maint_dist"]
hist_df = data["hist_df"]
temp_trend = data["temp_trend"]
warn_time = data["warn_time"]
top_eng = data["top_eng"]
scatter_df = data["scatter"]

st.title("📊 Flottan – Översikt")
st.caption("Explorativ analys av Gold-lagret · Medallion Architecture")
st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# 1 — FLEET KPIs
# ═══════════════════════════════════════════════════════════════════════════════
if "Fleet KPIs" in section:
    st.subheader("Nyckeltal för hela flottan")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Motorer", f"{int(s['total_engines']):,}")
    c2.metric("Mätningar", f"{int(s['total_events']):,}")
    c3.metric("Snitt temp", f"{s['avg_temp']} °C")
    c4.metric("Max temp", f"{s['max_temp']} °C")
    c5.metric("Snitt RPM", f"{s['avg_rpm']}")
    c6.metric("Totalt larm", f"{int(s['total_warning_events']):,}")

    st.divider()
    st.subheader("Larmtyper")

    wc1, wc2, wc3, wc4 = st.columns(4)

    def warn_pct(x):
        return f"{100 * x / max(s['total_events'], 1):.1f}% av mätningar"

    wc1.metric(
        "🔧 Underhåll", f"{int(s['maint_warnings']):,}", warn_pct(s["maint_warnings"])
    )
    wc2.metric(
        "🌡️ Temperatur", f"{int(s['temp_warnings']):,}", warn_pct(s["temp_warnings"])
    )
    wc3.metric("⚙️ RPM", f"{int(s['rpm_warnings']):,}", warn_pct(s["rpm_warnings"]))
    wc4.metric(
        "📳 Vibration", f"{int(s['vib_warnings']):,}", warn_pct(s["vib_warnings"])
    )

    st.plotly_chart(warning_pie_chart(s), use_container_width=True)
    st.info(
        f"Totalt {100*s['total_warning_events']/max(s['total_events'],1):.1f}% av alla mätningar "
        f"triggar minst ett larm. Högsta temp: {s['max_temp']}°C. Max körtid: {s['max_run_hours']}h."
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 2 — VARNINGAR PER MASKINTYP
# ═══════════════════════════════════════════════════════════════════════════════
elif "Varningar" in section:
    st.subheader("⚠️ Varningar per maskintyp")

    if not warn_app.empty:
        st.plotly_chart(warnings_by_appliance_bar(warn_app), use_container_width=True)

        warn_app["larm_procent"] = (
            100 * warn_app["total_warnings"] / warn_app["total_events"].replace(0, 1)
        ).round(2)
        st.plotly_chart(warning_rate_bar(warn_app), use_container_width=True)

        st.dataframe(
            warn_app.rename(
                columns={
                    "appliance_type": "Maskintyp",
                    "maintenance": "Underhåll",
                    "temperature": "Temperatur",
                    "rpm": "RPM",
                    "vibration": "Vibration",
                    "total_warnings": "Totalt larm",
                    "total_events": "Totalt mätningar",
                    "larm_procent": "Larm %",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 3 — UNDERHÅLLSSTATUS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Underhåll" in section:
    st.subheader("🔧 Underhållsstatus för flottan")

    col_a, col_b = st.columns(2)
    with col_a:
        if not maint_dist.empty:
            st.plotly_chart(maintenance_donut(maint_dist), use_container_width=True)
    with col_b:
        if not maint_dist.empty:
            st.dataframe(
                maint_dist.rename(
                    columns={"health_band": "Status", "engine_count": "Antal motorer"}
                ),
                use_container_width=True,
                hide_index=True,
            )
            total = maint_dist["engine_count"].sum()
            crit_df = maint_dist[maint_dist["health_band"].str.startswith("Critical")]
            crit_n = int(crit_df["engine_count"].iloc[0]) if not crit_df.empty else 0
            st.warning(
                f"⚠️ {crit_n} motorer ({100*crit_n/max(total,1):.1f}%) är kritiska (≥5000h)."
            )

    st.subheader("Fördelning av körtimmar (topp 500 motorer)")
    if not hist_df.empty:
        st.plotly_chart(run_hours_histogram(hist_df), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 4 — GEOGRAFISK
# ═══════════════════════════════════════════════════════════════════════════════
elif "Geografisk" in section:
    st.subheader("🗺️ Geografisk fördelning")

    if not city_stats.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(engines_per_city_bar(city_stats), use_container_width=True)
        with c2:
            st.plotly_chart(warnings_per_city_bar(city_stats), use_container_width=True)

        city_stats["larm_procent"] = (
            100 * city_stats["warnings"] / city_stats["events"].replace(0, 1)
        ).round(2)
        st.plotly_chart(city_scatter(city_stats), use_container_width=True)

        st.dataframe(
            city_stats.rename(
                columns={
                    "city": "Stad",
                    "engines": "Motorer",
                    "events": "Mätningar",
                    "warnings": "Larm",
                    "avg_temp": "Snitt temp °C",
                    "avg_run_hours": "Snitt körtid",
                    "larm_procent": "Larm %",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 5 — TIDSSERIE
# ═══════════════════════════════════════════════════════════════════════════════
elif "Tidsserie" in section:
    st.subheader("📈 Temperatur och larm (senaste 90 dagarna)")

    if not temp_trend.empty:
        st.plotly_chart(
            temp_and_warnings_timeseries(temp_trend), use_container_width=True
        )
    else:
        st.info("Ingen data för de senaste 90 dagarna.")

    st.subheader("Hela historiken – dagliga larm")
    if not warn_time.empty:
        st.plotly_chart(warning_volume_area(warn_time), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 6 — SENSORKORRELATIONER
# ═══════════════════════════════════════════════════════════════════════════════
elif "Sensorkorrelationer" in section:
    st.subheader("🔍 Sensorkorrelationer")
    st.caption("Slumpmässigt urval av 2 000 mätningar från fact_sensor_reading")

    if not scatter_df.empty:
        color_by = st.selectbox("Färgkoda efter", ["appliance_type", "location"])
        clean = scatter_df.dropna(subset=["rpm", "engine_temp", "vibration_hz"]).copy()
        clean["vibration_hz"] = clean["vibration_hz"].clip(lower=0.01)

        st.plotly_chart(sensor_scatter(clean, color_by), use_container_width=True)
        st.subheader("Korrelationsmatris (Pearson)")
        st.plotly_chart(correlation_heatmap(clean), use_container_width=True)
        st.info(
            "Värden nära +1 = stark positiv korrelation, -1 = omvänd, 0 = inget samband. "
            "Hög korrelation mellan run_hours och engine_temp tyder på att äldre motorer körs varmare."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 7 — TOPP 20 MOTORER
# ═══════════════════════════════════════════════════════════════════════════════
elif "Topp 20" in section:
    st.subheader("🏆 Topp 20 motorer med flest larm")

    if not top_eng.empty:
        st.plotly_chart(top_engines_bar(top_eng), use_container_width=True)
        st.dataframe(
            top_eng.rename(
                columns={
                    "engine_id": "Motor-ID",
                    "appliance_type": "Maskintyp",
                    "city": "Stad",
                    "max_run_hours": "Max körtid (h)",
                    "total_warnings": "Totalt larm",
                    "peak_temp": "Max temp °C",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.info(
            "Korsreferera med underhållsstatusen för att se om hög larmmängd "
            "sammanfaller med höga körtimmar – ett viktigt signal för prediktivt underhåll."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 8 — DAGLIG HÄLSA
# ═══════════════════════════════════════════════════════════════════════════════
elif "Daglig hälsa" in section:
    st.subheader("📅 Daglig flottahälsa (senaste 30 dagarna)")
    st.caption(
        "Baserat på fact_engine_daily — kör daily_aggregator.py för att uppdatera."
    )

    df_daily = data["daily"]
    df_snapshot = data["snapshot"]

    if not df_snapshot.empty:
        snap = df_snapshot.iloc[0]
        st.markdown(f"**Senast aggregerad dag: {snap['date']}**")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Aktiva motorer", f"{int(snap['active_engines']):,}")
        s2.metric("Snitt max temp", f"{snap['avg_max_temp']} °C")
        s3.metric("Totala larm", f"{int(snap['total_warnings']):,}")
        s4.metric("Motorer med larm", f"{int(snap['engines_with_warnings']):,}")

    st.divider()

    if not df_daily.empty:
        st.plotly_chart(daily_health_chart(df_daily), use_container_width=True)
        st.info(
            "Tryck 🔄 Uppdatera data efter att ha kört daily_aggregator.py för att se nya siffror."
        )
    else:
        st.info("Ingen daglig data hittades. Kör daily_aggregator.py först.")

# ═══════════════════════════════════════════════════════════════════════════════
# 9 — FELANALYS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Felanalys" in section:
    st.subheader("🚨 Felanalys")

    try:
        df_types = get_error_types(conn)
        df_by_city = get_errors_by_city(conn)
        df_rate = get_error_rate_by_city(conn)
        df_timeline = get_error_timeline(conn)
    except Exception as e:
        st.error(f"Kunde inte ladda feldata: {e}")
        st.stop()

    ec1, ec2, ec3, ec4 = st.columns(4)
    ec1.metric("🌡️ Temp-fel", int(df_types.iloc[0]["temp_errors"]))
    ec2.metric("⚙️ RPM-fel", int(df_types.iloc[0]["rpm_errors"]))
    ec3.metric("📳 Vibrations-fel", int(df_types.iloc[0]["vibration_errors"]))
    ec4.metric("🔧 Underhåll-fel", int(df_types.iloc[0]["maintenance_errors"]))

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Fel per stad & maskintyp")
        if not df_by_city.empty:
            pivot_df = df_by_city.pivot(
                index="location", columns="appliance_type", values="total_errors"
            ).fillna(0)
            st.bar_chart(pivot_df)
        else:
            st.info("Inga fel hittades.")
    with col_r:
        st.subheader("Rådata")
        st.dataframe(df_by_city, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Andel mätningar som är larm per stad (%)")
    if not df_rate.empty:
        st.plotly_chart(error_rate_bar(df_rate), use_container_width=True)

    st.divider()

    st.subheader("Tidslinje: Fel per stad (2016 – Idag)")
    if not df_timeline.empty:
        cities = df_timeline["location"].unique()
        tabs = st.tabs([str(c) for c in cities])
        for i, city in enumerate(cities):
            with tabs[i]:
                city_df = df_timeline[df_timeline["location"] == city]
                st.plotly_chart(
                    error_timeline_line(city_df, city), use_container_width=True
                )
    else:
        st.info("Ingen tidslinje-data hittades.")
