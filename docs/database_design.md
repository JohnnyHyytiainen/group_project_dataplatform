# Database module overview:

**Docs och förklaringar om databas designen.**

- Stämmer det att en databas utan relationer (Foreign Keys) är en trasig databas?

    - Svaret är: **Nej, alla tabeller ska inte vara länkade med varandra via Foreign Keys (FK).** 
Här är en kort förklaring om varför det är så:

Inom **Data Engineering och Medallion-arkitektur gäller helt andra regler!**


## 1. Separation of Concerns (Fristående lager)

Tanken med Medallion är att lagren (Bronze, Silver, Gold) ska vara **frikopplade (decoupled)**.
Om du sätter en tvingande Foreign Key från Silver till Bronze t.ex `FOREIGN KEY (bronze_id) REFERENCES staging_sensor_data(id)` så betyder det att du *aldrig kan rensa din Bronze tabell* utan att först radera din Silver-tabell. 

I verkligheten vill man ofta tömma Staging tabeller (Bronze) efter 30 dagar för att spara plats, medan Silver och Gold sparar historik i flera år.

Därför är `bronze_id` i Silver-tabellen bara en **"Soft Link" (Lineage)**. Den säger: *"Jag kom från rad 14 i Bronze"* men det är ingen tvingande databas relation.

## 2. DLQ (`faulty_events`) är en återvändsgränd

Vår `faulty_events`-tabell i Bronze *ska* sitta helt ensam, flytande i rymden. Det är papperskorgen. Ingen annan tabell ska bygga vidare på den, och den har ingen relation till våra Star Schema tabeller. Dess enda syfte är att finnas där så att en tekniker kan titta i den om något går fel.

## 3. Star Schema (Gold) är sitt eget lilla ekosystem

I Gold lager har Vi `DIM_ENGINE`, `DIM_DATE` och `FACT_SENSOR_READING`. **Dessa** tabeller är stenhårt länkade till varandra med Foreign Keys! Fakta-tabellen länkar till dimensionerna. Men Gold-lagret som helhet behöver ingen tvingande FK tillbaka till Silver. Den har bara `silver_id` som spårbarhet (Lineage)

## 4. Behöver vi olika databaser?

Nej, det funkar utmärkt att ha allt i samma PostgreSQL databas! Det finns två vanliga sätt att skilja dem åt i samma databas:

1. **Prefix (Det Vi i grupp 6 gör):** Tabellerna heter `staging_...`, `silver_...`, `dim_...` och `fact_...`. Namnet berättar vilket lager tabellen tillhör.

2. **Schemas (Lite mer avancerat):** Man kan skapa logiska mappar i Postgres (`CREATE SCHEMA bronze;`, `CREATE SCHEMA silver;`) så att tabellerna heter `bronze.sensor_data`, `silver.sensor_data`. 

3. **Prefix VS Schemas:** För denna labb räcker prefix gott och väl för ett bra MvP. Dock så är det värt att nämna *varför* schemas är bättre i större system och det kan sammanfattas till ett ord: **Behörigheter**.

Med `CREATE SCHEMA GOLD; GRANT SELECT ON SCHEMA gold TO analyst_role;` kan man ge analytiker läsrättigheter till Gold utan att de ens kan se `bronze` till exempel. Det kan fungera som ytterligare ett lager av säkerhet både för läckt data men även för att rätt data hamnar hos rätt personer för att kunna utföra så tydliga analyser det bara går.


### Sammanfattning
*Inom Data Engineering bygger vi slussar. Bronze slussar data till Silver, Silver slussar till Gold. De är löskopplade för att vi ska kunna riva eller bygga om ett lager utan att krascha hela databasen. Relationerna (Foreign Keys) använder vi bara inuti Gold-lagret för att bygga vår affärsmodell!*