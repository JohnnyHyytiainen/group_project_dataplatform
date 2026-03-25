# Streamlit Tools We Used in Our Dashboard

---

## app.py — The Welcome Page

This is just the landing page. Nothing fancy, mostly text and layout stuff.

- `st.set_page_config()` — sets the browser tab title and icon
- `st.title()` / `st.subheader()` — headings
- `st.markdown()` — formatted text, like writing in Notion
- `st.columns()` — puts things side by side
- `st.code()` — shows our pipeline flow as a code block
- `st.info()` — blue boxes for our tech stack cards
- `st.divider()` — just a horizontal line to separate sections

---

## 01_overview.py — The Main Dashboard

This is the big one. All the real logic lives here.

### Connection & Caching

- `@st.cache_resource` — opens the database connection ONCE and reuses it. Without this, every page refresh opens a new connection and eventually crashes the DB.
- `st.connection()` — connects to PostgreSQL using credentials from the secrets config
- `@st.cache_data(ttl=300)` — caches all our query results for 5 minutes. So switching between sections is instant instead of hitting the database every time.
- `st.cache_data.clear()` — busts the cache when you press the refresh button
- `st.rerun()` — forces the page to reload after cache is cleared

### Navigation

- `st.sidebar` — the left panel where we put our navigation
- `st.radio()` — the clickable section buttons (Fleet KPIs, Varningar, etc.)
- `st.button()` — the "🔄 Uppdatera data" button

### Layout

- `st.columns()` — we use this everywhere. 2 columns, 4 columns, 6 columns depending on the section
- `st.tabs()` — the city tabs in Felanalys (Gothenburg, Malmo, etc.)
- `st.divider()` — horizontal lines between sections

### Displaying Data

- `st.metric()` — those KPI cards with the big number and small delta underneath (e.g. "1,534 — 4.8% av mätningar")
- `st.plotly_chart()` — renders all our Plotly charts
- `st.dataframe()` — interactive sortable tables, used with `hide_index=True` so the index column doesn't show
- `st.bar_chart()` — used once in Felanalys for the pivot table. It's Streamlit's built-in chart, simpler than Plotly but no legend.

### Text & Messages

- `st.title()` / `st.subheader()` / `st.caption()` / `st.markdown()` — different sizes of text
- `st.info()` — blue box, used for analytical insights at the bottom of sections
- `st.warning()` — yellow box, shows up when engines are in warning zone (4000-5000h)
- `st.success()` — green box, shows when no critical engines found
- `st.error()` — red box, shows when the database can't connect
- `st.stop()` — stops the page from rendering further if something goes wrong. Prevents a cascade of confusing errors.

### Interactive

- `st.selectbox()` — the dropdown in Sensorkorrelationer where you pick "color by appliance_type or location"

---

## queries.py — Just SQL, No Streamlit

This file has zero Streamlit UI tools. It just takes the `conn` object and runs SQL.

- `conn.query()` — executes SQL and returns a pandas DataFrame. That's it.

We kept all SQL here so `01_overview.py` stays clean and readable.

---

## charts.py — Just Plotly, No Streamlit

This file also has zero Streamlit tools. It takes DataFrames and returns Plotly figures.

The main Plotly stuff we used:

- `px.pie()` — warning type donut chart
- `px.bar()` — most of our bar charts
- `px.scatter()` — sensor correlation scatter
- `px.histogram()` — run hours distribution
- `px.area()` — all-time warning volume
- `px.imshow()` — Pearson correlation heatmap
- `px.line()` — city error timelines
- `make_subplots()` — when we need multiple charts stacked vertically (like in Daglig hälsa)
- `fig.add_hline()` / `fig.add_vline()` — threshold lines (101°C, 1600 RPM, 4000h/5000h)

---

## Why We Split It This Way

`queries.py` → SQL only  
`charts.py` → Plotly only  
`01_overview.py` → layout and orchestration only

This is called Separation of Concerns. If a query breaks, we fix it in `queries.py` without touching the charts. If a chart looks wrong, we fix it in `charts.py` without touching the SQL. Clean and easy to debug.
