import streamlit as st
import httpx
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- Sidkonfiguration ---
st.set_page_config(page_title="IoT Maintenance Dashboard", page_icon="⚙️", layout="wide")

st.title("IoT Appliance Dashboard")
st.caption("Cold Chain - Live sensor data")


# --- Hämta data från API ---
@st.cache_data(ttl=60)
def fetch_sensors(location=None, is_valid=None):
    params = {"limit": 1000}
    if location:
        params["location"] = location
    if is_valid is not None:
        params["is_valid"] = is_valid
    response = httpx.get(f"{API_URL}/api/v1/sensors", params=params)
    return pd.DataFrame(response.json()["data"])


# --- Sidebar-filter ---
st.sidebar.header("Filter")
city = st.sidebar.selectbox(
    "Stad", ["Alla", "Stockholm", "Gothenburg", "Malmo", "Uppsala", "Helsingborg"]
)
show_valid = st.sidebar.radio(
    "Datakvalitet", ["Alla", "Endast valid", "Endast anomalier"]
)

# Översätt filter till API-params
location_param = None if city == "Alla" else city
valid_param = None
if show_valid == "Endast valid":
    valid_param = True
elif show_valid == "Endast anomalier":
    valid_param = False

# --- Ladda data ---
df = fetch_sensors(location=location_param, is_valid=valid_param)

if df.empty:
    st.warning("Ingen data hittades för valda filter.")
    st.stop()

# --- Metric cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Totalt records", len(df))
col2.metric("Unika motorer", df["engine_id"].nunique())
col3.metric("Snitt temp", f"{df['engine_temp'].mean():.1f}°C")
col4.metric("Anomalier", len(df[df["is_valid"] == False]))

st.divider()

# --- Graf: anomalier per appliance ---
st.subheader("Anomalier per maskintyp")
anomalier = df[df["is_valid"] == False]["appliance_type"].value_counts()
st.bar_chart(anomalier)

# --- Rådata ---
st.subheader("Sensordata")
st.dataframe(df, use_container_width=True)
