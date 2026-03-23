import streamlit as st

# Konfigurera sidans utseende (måste vara första kommandot)
st.set_page_config(page_title="Maskinpark Analytics", layout="wide")

st.title("Maskinpark Analytics Dashboard")
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("**Overview**\n\nFå en översikt över hela maskinparkens hälsa och volymer.")
with col2:
    st.warning(
        "**Anomalies**\n\nIdentifiera sensorer som skickar extremvärden eller smutsig data."
    )
with col3:
    st.error(
        "**Maintenance**\n\nDyk djupt i specifika orsaker för prediktivt underhåll."
    )
with col4:
    st.error("**Errors**\n\nDyk djupt i typer av fel maskinerna råkar ut för.")

# Testa kopplingen till databasen för att visa att allt fungerar
try:
    conn = st.connection("postgresql", type="sql")
    st.success("Uppkopplad mot Postgres-databasen!")
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen: {e}")
