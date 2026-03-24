import streamlit as st

st.set_page_config(
    page_title="Maskinpark Analytics",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Maskinpark Analytics Dashboard")
st.caption("Grupparbete – Data Engineering 2025 · STI · Grupp 6")
st.markdown("---")

st.markdown(
    """
Välkommen till vår dashboard för analys av IoT-sensorer från en flotta av vitvaror.
Datan flödar genom vår **Medallion-pipeline** (Bronze → Silver → Gold) och visualiseras här.
"""
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Vad kan du se här?")
    st.markdown(
        """
    Översiktssidan innehåller:
    - 📈 Fleet KPIs – motorer, mätningar, larm
    - ⚠️ Varningar per maskintyp
    - 🔧 Underhållsstatus (körtimmar)
    - 🗺️ Geografisk fördelning per stad
    - 📉 Tidsserie – temperatur och larm
    - 🔍 Sensorkorrelationer (Pearson)
    - 🏆 Topp 20 motorer med flest larm
    - 🚨 Felanalys per stad och maskintyp
    """
    )

with col2:
    st.subheader("🏗️ Vår pipeline")
    st.markdown(
        """
    Så här flödar datan genom vårt system:
    """
    )
    st.code(
        """
🥉 Bronze  →  Producer genererar syntetisk IoT-data
               Consumer validerar med Pydantic
               Raw JSON sparas i staging_sensor_data
               Korrupt data → Dead Letter Queue (DLQ)

🥈 Silver  →  Batch ETL-jobb tvättar datan (cleaner.py)
               Strippar whitespace, standardiserar namn
               Sätter is_valid-flagga (ej grindvakt!)
               Laddar till silver_sensor_data

🥇 Gold    →  ETL bygger Star Schema
               Dim-tabeller + fact_sensor_reading
               Affärslogik: larmflaggor beräknas här
               Aggregeras till fact_engine_daily

⚡ FastAPI  →  Servar Silver-data med pagination
               Connection pooling + SQL injection-skydd

📊 Dashboard → Du är här!
    """,
        language="text",
    )

st.markdown("---")

st.subheader("🛠️ Tech Stack")

tc1, tc2, tc3, tc4 = st.columns(4)
tc1.info("🐍 Python 3.12\nDatagenerering, ETL, API")
tc2.info("📨 Apache Kafka\nMessage broker, event streaming")
tc3.info("🐘 PostgreSQL\nBronze + Silver + Gold tabeller")
tc4.info("🐳 Docker Compose\nOrkestrerar hela systemet")

tc5, tc6, tc7, tc8 = st.columns(4)
tc5.info("⚡ FastAPI\nREST API med Swagger docs")
tc6.info("📊 Streamlit\nDen här dashboarden")
tc7.info("✅ Pydantic\nSchema-validering i Bronze")
tc8.info("🧹 Pandas\nETL-tvätt i Silver-lagret")

st.markdown("---")
st.caption(
    "Navigera med menyn till vänster. All data läses från Gold-lagret i realtid."
)
