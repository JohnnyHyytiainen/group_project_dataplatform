# src/dashboard/components/charts.py
# All Plotly chart builders for the overview dashboard.
# Each function takes a DataFrame and returns a Plotly Figure.
# No Streamlit imports here — pure chart logic, easy to test and reuse.

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def warning_pie_chart(s) -> go.Figure:
    """Pie chart of warning type distribution. Takes the summary row (Series)."""
    fig = px.pie(
        pd.DataFrame(
            {
                "Larmtyp": ["Underhåll", "Temperatur", "RPM", "Vibration"],
                "Antal": [
                    int(s["maint_warnings"]),
                    int(s["temp_warnings"]),
                    int(s["rpm_warnings"]),
                    int(s["vib_warnings"]),
                ],
            }
        ),
        names="Larmtyp",
        values="Antal",
        hole=0.4,
        color_discrete_sequence=["#e74c3c", "#e67e22", "#3498db", "#9b59b6"],
        title="Fördelning av larmtyper",
    )
    return fig


def warnings_by_appliance_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart — warning counts per appliance type."""
    fig = px.bar(
        df,
        x="appliance_type",
        y=["maintenance", "temperature", "rpm", "vibration"],
        barmode="group",
        color_discrete_map={
            "maintenance": "#e74c3c",
            "temperature": "#e67e22",
            "rpm": "#3498db",
            "vibration": "#9b59b6",
        },
        labels={
            "appliance_type": "Maskintyp",
            "value": "Antal larm",
            "variable": "Larmtyp",
        },
        title="Antal larm per maskintyp",
    )
    return fig


def warning_rate_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart — warning rate % per appliance type."""
    fig = px.bar(
        df.sort_values("larm_procent", ascending=True),
        x="larm_procent",
        y="appliance_type",
        orientation="h",
        color="larm_procent",
        color_continuous_scale="Reds",
        labels={"larm_procent": "Larm %", "appliance_type": ""},
        title="Andel mätningar som är larm per maskintyp (%)",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def maintenance_donut(df: pd.DataFrame) -> go.Figure:
    """Donut chart — fleet health distribution by run-hour band."""
    color_map = {
        "Critical (5000h+)": "#e74c3c",
        "Warning (4000-4999h)": "#e67e22",
        "Healthy (<4000h)": "#2ecc71",
    }
    fig = go.Figure(
        go.Pie(
            labels=df["health_band"],
            values=df["engine_count"],
            hole=0.5,
            marker_colors=[color_map.get(b, "#aaa") for b in df["health_band"]],
        )
    )
    fig.update_layout(title="Flottans hälsostatus (körtimmar)")
    return fig


def run_hours_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram of max run hours with warning/critical threshold lines."""
    fig = px.histogram(
        df,
        x="max_run_hours",
        nbins=30,
        color_discrete_sequence=["#3498db"],
        labels={"max_run_hours": "Max körtimmar"},
        title="Histogram – körtimmar för topp 500 motorer",
    )
    fig.add_vline(
        x=4000,
        line_dash="dash",
        line_color="#e67e22",
        annotation_text="Varning (4000h)",
    )
    fig.add_vline(
        x=5000,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="Kritiskt (5000h)",
    )
    return fig


def engines_per_city_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — engine count per city."""
    fig = px.bar(
        df.sort_values("engines", ascending=True),
        x="engines",
        y="city",
        orientation="h",
        title="Antal motorer per stad",
        labels={"engines": "Motorer", "city": ""},
        color="engines",
        color_continuous_scale="Blues",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def warnings_per_city_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — warning events per city."""
    fig = px.bar(
        df.sort_values("warnings", ascending=True),
        x="warnings",
        y="city",
        orientation="h",
        title="Antal larm per stad",
        labels={"warnings": "Larm", "city": ""},
        color="warnings",
        color_continuous_scale="Reds",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def city_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter — engine count vs warning rate %, bubble = event volume."""
    fig = px.scatter(
        df,
        x="engines",
        y="larm_procent",
        size="events",
        color="avg_temp",
        text="city",
        color_continuous_scale="RdYlGn_r",
        title="Antal motorer vs larm % (bubbelstorlek = antal mätningar)",
        labels={
            "engines": "Motorer",
            "larm_procent": "Larm %",
            "avg_temp": "Snitt temp",
        },
    )
    fig.update_traces(textposition="top center")
    return fig


def temp_and_warnings_timeseries(df: pd.DataFrame) -> go.Figure:
    """Dual-panel chart — avg/peak temp + daily warning count over 90 days."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Snitt- och maxtemperatur (°C)", "Antal larm per dag"),
        vertical_spacing=0.15,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["avg_temp"],
            name="Snitt temp",
            line=dict(color="#3498db", width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["peak_temp"],
            name="Max temp",
            line=dict(color="#e74c3c", width=1.5, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(231,76,60,0.07)",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["daily_warnings"],
            name="Dagliga larm",
            marker_color="#e67e22",
            opacity=0.7,
        ),
        row=2,
        col=1,
    )
    fig.update_layout(height=520, hovermode="x unified")
    return fig


def warning_volume_area(df: pd.DataFrame) -> go.Figure:
    """Area chart — all-time daily warning volume."""
    fig = px.area(
        df,
        x="date",
        y="total_warnings",
        title="Dagliga larm – hela historiken",
        color_discrete_sequence=["#e74c3c"],
        labels={"date": "Datum", "total_warnings": "Antal larm"},
    )
    return fig


def sensor_scatter(df: pd.DataFrame, color_by: str) -> go.Figure:
    """Scatter — RPM vs engine temp, sized by vibration_hz."""
    fig = px.scatter(
        df,
        x="rpm",
        y="engine_temp",
        color=color_by,
        size="vibration_hz",
        opacity=0.6,
        title="RPM vs Motortemperatur (storlek = vibration_hz)",
        labels={"rpm": "RPM", "engine_temp": "Temp (°C)"},
        hover_data=["run_hours", "location", "appliance_type"],
    )
    fig.add_hline(
        y=101,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="Temp-gräns (101°C)",
    )
    fig.add_vline(
        x=1600,
        line_dash="dash",
        line_color="#e67e22",
        annotation_text="RPM-gräns (1600)",
    )
    return fig


def correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Pearson correlation heatmap for the four sensor metrics."""
    corr = df[["rpm", "engine_temp", "vibration_hz", "run_hours"]].corr().round(3)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Pearson-korrelation mellan sensorvärden",
    )
    return fig


def top_engines_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — top 20 engines by warning count."""
    fig = px.bar(
        df.sort_values("total_warnings"),
        x="total_warnings",
        y="engine_id",
        orientation="h",
        color="appliance_type",
        title="Topp 20 motorer – antal larm",
        labels={"total_warnings": "Totalt larm", "engine_id": "Motor-ID"},
        hover_data=["city", "max_run_hours", "peak_temp"],
    )
    fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
    return fig


def error_rate_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — % of readings that are alarms per city."""
    fig = px.bar(
        df.sort_values("error_percentage", ascending=True),
        x="error_percentage",
        y="location",
        orientation="h",
        color="error_percentage",
        color_continuous_scale="Reds",
        labels={"error_percentage": "Fel %", "location": ""},
        title="Andel av alla sensormätningar som är larm – per stad",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def error_timeline_line(df: pd.DataFrame, city: str) -> go.Figure:
    """Line chart — daily errors for a single city."""
    fig = px.line(
        df,
        x="calendar_date",
        y="daily_errors",
        title=f"Dagliga fel – {city}",
        labels={"calendar_date": "Datum", "daily_errors": "Antal fel"},
        color_discrete_sequence=["#e74c3c"],
    )
    return fig


def daily_health_chart(df: pd.DataFrame) -> go.Figure:
    """Multi-line chart showing daily fleet health metrics over last 30 days."""
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Aktiva motorer per dag",
            "Daglig snitt max-temperatur (°C)",
            "Totala larm per dag",
        ),
        vertical_spacing=0.1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["active_engines"],
            name="Aktiva motorer",
            line=dict(color="#3498db", width=2),
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.08)",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["avg_max_temp"],
            name="Snitt max temp",
            line=dict(color="#e74c3c", width=2),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["total_warnings"],
            name="Larm",
            marker_color="#e67e22",
            opacity=0.8,
        ),
        row=3,
        col=1,
    )
    fig.update_layout(height=580, hovermode="x unified", showlegend=False)
    return fig
