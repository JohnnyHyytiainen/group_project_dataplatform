
# Repo Structure & Pathing Survival Guide

Syfte: En snabbkarta över var filer ska bo och hur vi undviker krascher och git-kaos.

---

## 🛑 1. Den Gyllene Regeln (Vad får finnas i Git?)
**Git är för kod, inte för en datalake.** 

* **✅ TILLÅTET I GIT:** Python-kod, SQL-scheman, dokumentation (Markdown), konfigurationsmallar (`.env.example`) och extremt små, anonymiserade testfiler.

* **❌ FÖRBJUDET I GIT:** Riktig data (GDPR/PII), stora databas-dumpar, och hemligheter (din `.env`-fil).

---

## 2. Mappstrukturen (Kartboken)
Så här ser vårt projekt ut. Håll dig till den här strukturen så hittar alla rätt.

```text
projekt_root/
├── docs/                # Markdown-filer, guider och diagram.
├── src/                 # Vår Python-kod. Inga datafiler här!
│   ├── main.py          # Startpunkt för API/App
│   └── database.py      # Databaskopplingar
├── data/                # IGNORERAS AV GIT! Här lägger du lokala dataset.
├── docker-compose.yml   # Startar vår infrastruktur (t.ex. databas, Kafka)
├── .env.example         # Mall för hemligheter (kopiera till .env)
├── .gitignore           # Vår sköld mot att ladda upp fel saker
└── README.md            # Projektets ansikte utåt.

```

---

## 🚨3. PANIK-SEKTION: "ModuleNotFoundError" (Pathing)🚨

Det absolut vanligaste felet när vi bygger projekt i Python är att koden inte hittar varandra. Följ dessa tre regler slaviskt:

**Regel A: Kör ALLTID från Root-mappen**
Navigera aldrig in i `src/` eller `scripts/` med terminalen. Du ska alltid befinna dig längst upp i projektet (där din `README.md` ligger) när du kör kommandon.

**Regel B: Använd "Absoluta Imports"**
Låtsas att `src` är ett externt bibliotek som du har installerat. Använd aldrig punkter (`.`) för att gissa dig bakåt i mapparna.

* ❌ **Gör inte:** `from .database import get_db` (Går sönder om du flyttar filen)

* ✅ **Gör istället:** `from src.database import get_db` (Fungerar alltid, oavsett var du är)

**Regel C: The Magic Module Flag (`-m`)**
När du kör ett script från root-mappen och använder absoluta imports, måste du berätta för Python att hantera mappen som en modul. Annars förstår den inte vad `src` är.

* ❌ **Kraschar:** `python src/min_fil.py`

* ✅ **Fungerar:** `python -m src.min_fil` (Märk att det *inte* är `.py` på slutet!)

---

## 4. Namnstandard

För att vi ska kunna söka och förstå varandras kod, bör vi alltid `snake_case` för filnamn, tabeller och variabler. Inga mellanslag!

* ❌ `Min Nya Fil.py`, `CamelCaseTable`
* ✅ `min_nya_fil.py`, `job_roles`
