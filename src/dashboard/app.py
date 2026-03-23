import streamlit as st

# Konfigurera sidans utseende (måste vara första kommandot)
st.set_page_config(page_title="Maskinpark Analytics", layout="wide")

st.title("Maskinpark Analytics Dashboard")
st.markdown("""
Välkommen till vår dashboard för övervakning av maskinparken. 
Använd menyn till vänster för att navigera mellan:
* **Overview:** Övergripande hälsa och volymer.
* **Anomalies:** Identifiering av felaktiga sensorvärden.
* **Maintenance:** Prediktivt underhåll och varningar.
""")

# Testa kopplingen till databasen för att visa att allt fungerar
try:
    conn = st.connection("postgresql", type="sql")
    st.success("Uppkopplad mot Postgres-databasen!")
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen: {e}")
