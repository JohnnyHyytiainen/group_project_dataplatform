## 1. Vad är Data Lineage? (Spårbarheten)
*Skriven 14/03-2026*


Data Lineage handlar *inte* om att databasen ska styra sig själv, utan om **revision och spårbarhet (Audit Trail)**.
Tänk att en analytiker tittar på vår Streamlit dashboard och säger: *"Vänta nu, den 14 mars klockan 14:10 hade en motor i Stockholm en temperatur på 500 grader? Det måste vara ett fel!"*

---
Tack vare vår Lineage kan vi felsöka det på sekunder genom:

1. Vi tittar i Gold (`FACT_SENSOR_READING`) och ser det orimliga värdet. Längst ut till höger på den raden står det `silver_id = 1042`. (Det här är en ledtråd)

2. Vi går till Silver (`silver_sensor_data`) och letar upp `silver_id = 1042`. HÄR ser vi exakt hur datan såg ut efter att vår `cleaner.py` tvättade den. Kanske gick det fel i tvätten?

3. I Silver ser vi vilken `timestamp` raden hade. Då kan vi gå hela vägen tillbaka till Bronze (`staging_sensor_data`) och titta på den råa, oredigerade Kafka-JSON strängen för att se om sensorn faktiskt skickade "500" eller om det var ett nätverksfel.
---

**Lineage är ledtrådar som låter oss gå baklänges i tiden**
---

### 2. Varför vi undviker `ON DELETE CASCADE` i våra tables för projektet

I en traditionell relationsdatabas (OLTP, typ en webbshop) är `ON DELETE CASCADE` grymt att ha! Om en användare raderar sitt konto, vill vi att databasen automatiskt raderar alla deras sparade varukorgar.

Men i ett Data Warehouse / Medallion-arkitektur (OLAP) är regeln nästan alltid: **Vi raderar aldrig data. Vi är "Append-Only"**

* **Risken med Cascade:** Tänk om någon råkar köra en `DELETE` på en motor i `DIM_ENGINE` av misstag. Om vi hade `ON DELETE CASCADE`, skulle Postgres blixtsnabbt radera **alla** historiska mätvärden för den motorn i faktatabellen! Plötsligt försvinner tre års KPI-historik i vår dashboard, och företaget tappar all sin finansiella sta§tistik för den maskinen (BIG PROBLEM!!!)

* **Soft Deletes:** Istället för att radera en motor som skrotas, lägger man ofta till en kolumn i dimensionen som heter `is_active = False` (Här är en liknelse med logiken med varför vi använder `is_valid` och varför vi använder oss av `is_valid =` flaggan). Då bevaras historiken för rapporterna, men maskinen dyker inte upp som ett val i nya sökningar.

* **Mer förklaring kring `is_active` och `is_valid`:**
    - `is_active` (Dimensioner): Används när en riktig fysisk motor skrotas. Motorn var bra, men används inte längre. (Detta kallas Slowly Changing Dimensions - SCD)  

    - `is_valid` (Fakta/Silver): Används när en motor skickar trasig data eller saknar ID.

### 3. Så hur rensar vi tabellerna i development läge?

* när vi är i "Development mode" och leker och utvecklar vår MvP kommer vi ibland vilja tömma hela Gold-lagret och börja om. Men vi bygger inte in raderingslogik i *tabellens struktur*. **Vi gör det explicit med ett kommando.**

* När du vill blåsa rent databasen (i PgAdmin eller via ett Python script), använder du `TRUNCATE` med `CASCADE`-flaggan på kommandot, *inte* på tabellen:

```sql
TRUNCATE TABLE dim_engine, dim_location, dim_appliance, dim_date, fact_sensor_reading CASCADE;
```

* Då säger du: *"Jag vet vad jag gör, töm tabellerna och strunta i Foreign Key-varningarna just för denna operation."*


### Sammanfattning

Vår design är solid och byggd för att följa klassisk medalion arkitektur.

* Våra Foreign Keys (`REFERENCES`) skyddar oss så att vi inte kan lägga in en fakta-rad om en motor som inte existerar i dimensionen (Referential Integrity)

* Avsaknaden av `ON DELETE CASCADE` skyddar våra analytiker(oss) från att förlora historisk data av misstag.

* Vårat `silver_id` ger oss perfekt Data Lineage för felsökning.

* Vi kan med säkerhet vara nöjda och glada över att vi följer 'bransch praxis' i hur `Data Warehouse / Medallion-arkitektur (OLAP)` byggs och bör se ut.