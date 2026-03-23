"""
Plotly chart builders for the Machine Fleet Analytics Dashboard.
Each function takes a DataFrame and returns a Plotly Figure.
No Streamlit imports here — pure chart logic, easy to test and reuse.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def warning_bar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart showing warning counts per appliance type.
    Expects columns: appliance_type, maintenance, temperature, rpm, vibration.
    """
    fig = px.bar(
        df,
        x="appliance_type",
        y=["maintenance", "temperature", "rpm", "vibration"],
        barmode="group",
        labels={
            "appliance_type": "Appliance Type",
            "value": "Warning Count",
            "variable": "Warning Type",
        },
        color_discrete_map={
            "maintenance": "#e74c3c",
            "temperature": "#e67e22",
            "rpm": "#3498db",
            "vibration": "#9b59b6",
        },
        title="Warnings by Appliance Type",
    )
    fig.update_layout(legend_title_text="Warning Type")
    return fig


def warnings_by_city_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart showing total warning events per city.
    Expects columns: city, total_warnings.
    """
    fig = px.bar(
        df,
        x="total_warnings",
        y="city",
        orientation="h",
        labels={"total_warnings": "Total Warnings", "city": "City"},
        color="total_warnings",
        color_continuous_scale="Reds",
        title="Warning Events by City",
    )
    fig.update_layout(
        coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"}
    )
    return fig


def avg_temp_line_chart(df: pd.DataFrame) -> go.Figure:
    """
    Line chart showing daily average engine temperature over time.
    Expects columns: date, avg_temp.
    """
    fig = px.line(
        df,
        x="date",
        y="avg_temp",
        labels={"date": "Date", "avg_temp": "Avg Temperature (°C)"},
        title="Daily Average Engine Temperature (Last 90 Days)",
    )
    fig.update_traces(line_color="#e74c3c", line_width=2)
    fig.update_layout(hovermode="x unified")
    return fig


def top_warning_engines_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart for the top 20 engines by warning count.
    Expects columns: engine_id, total_warnings, appliance_type.
    """
    fig = px.bar(
        df,
        x="total_warnings",
        y="engine_id",
        orientation="h",
        color="appliance_type",
        labels={
            "total_warnings": "Total Warnings",
            "engine_id": "Engine ID",
            "appliance_type": "Appliance Type",
        },
        title="Top 20 Engines by Warning Count",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=True)
    return fig


def maintenance_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing fleet health distribution by run-hour band.
    Expects columns: health_band, engine_count.
    """
    color_map = {
        "Critical (5000h+)": "#e74c3c",
        "Warning (4000-4999h)": "#f39c12",
        "Healthy (<4000h)": "#2ecc71",
    }
    colors = [color_map.get(band, "#95a5a6") for band in df["health_band"]]

    fig = go.Figure(
        go.Pie(
            labels=df["health_band"],
            values=df["engine_count"],
            hole=0.45,
            marker_colors=colors,
        )
    )
    fig.update_layout(title="Fleet Health Distribution by Run Hours")
    return fig


def run_hours_histogram(
    df: pd.DataFrame, title: str, color: str = "#3498db"
) -> go.Figure:
    """
    Histogram of max run hours for a subset of engines.
    Expects column: max_run_hours.
    """
    fig = px.histogram(
        df,
        x="max_run_hours",
        nbins=20,
        labels={"max_run_hours": "Max Run Hours"},
        title=title,
        color_discrete_sequence=[color],
    )
    fig.update_layout(bargap=0.05)
    return fig
