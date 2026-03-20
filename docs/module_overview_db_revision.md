# Module Overview: Database Migrations (Alembic)
*Written 20/03-2026 by Johnny*

Detta dokument förklarar vår strategi och mina tankar för/kring versionshantering av databasen i Gold och Silver lagren. Vi använder oss av Alembic för att hantera Database Migrations. Database migrations är en branschstandard för produktionssatta dataplattformar.

## Alembic teori
Alembic skapar inte en ny databas och flyttar över datan. 

Tänk dig att din databas är ett hus och datan i databasen är dina möbler. Om du behöver ett extra fönster (en ny kolumn) bygger du inte ett helt nytt hus och bär över alla möbler in till det nya huset, det hade varit väldigt dyrt och onödigt.

Du tar istället fram sågen och gör ett hål i väggen där du vill att fönstret du behöver medan möblerna står kvar i huset.

Alembic använder SQL kommandot `ALTER TABLE` under huven. Den modifierar strukturen runt datan, vilket gör att alla dina miljoner rows av data ligger i tryggt förvar medan tabellen byter skepnad.

## Vad är en Database Migration?
Den enklaste förklaringen är att det fungerar som **Git för vår databas.**

Precis som vi *inte* raderar hela vår kodbas och skriver om den från noll varje gång vi vill lägga till en funktion, kan vi inte radera (droppa) våra databastabeller varje gång vi behöver en ny kolumn. Det Alembic gör, är att det skapar en spårbar, sekventiell tidslinje av förändringar så kallade `revisions` som appliceras steg-för-steg på databasen.

## Varför är det här kritiskt och viktigt i branschen? (Affärsvärde)
Att hantera databaser utan migrationsverktyg i ett live system(i produktion) är en tickande bomb. Här är varför Alembic är avgörande:

1. **Noll Dataförlust vid uppdateringar:**  
    - Om verksamheten plötsligt vill att vi ska börja spara `humidity` i vårt Silver-lager, kan vi inte köra `DROP TABLE silver_sensor_data` och radera 10 miljoner historiska rader för att skapa tabellen på nytt. Alembic använder `ALTER TABLE` för att dynamiskt "operera" in den nya kolumnen medan den befintliga datan ligger kvar helt orörd.

2. **Eliminerar "Schema Drift":**  
   - I ett team med flera utvecklare uppstår snabbt kaos om person A lägger till en kolumn lokalt, men glömmer berätta det för person B. Med Alembic måste alla ändringar finnas i koden (en `.py`-fil i `versions/` mappen) När en utvecklare drar ner ny kod och kör `alembic upgrade head`, så synkas deras lokala databas exakt med resten av teamets.

3. **Rollbacks (Ångra-knappen):**  
   - Om vi råkar rulla ut en trasig databasuppdatering till produktion, kan vi på några sekunder köra `alembic downgrade -1`. Systemet backar då bandet, tar bort den felaktiga ändringen och återställer databasen till den tidigare, stabila versionen.

## Edge Cases: Vad händer utan Alembic?  

* **"Deploy Nightmare":** 
- Utan migrations script måste utvecklare manuellt logga in i produktionsdatabasen och skriva SQL kommandon för hand under en release. Skriver man fel, eller glömmer en tabell, kraschar hela plattformen.

* **Inkonsistenta Miljöer:** 
- Vår Sandbox databas, Test databas och Live databas kommer gradvis att se olika ut. Till slut går det inte att veta varför koden fungerar i dev men kraschar i produktion.

## Hur arkitekturen fungerar

När vi kör kommandot `uv run alembic upgrade head` händer följande:

1. Alembic tittar i vår Postgres-databas i en speciell intern tabell som heter `alembic_version`.

2. Den läser av vilket ID som ligger där (ex: `ea79237cf323`).

3. Den tittar i vår lokala kodmapp (`alembic/versions/`) och letar upp skript som är *nyare* än detta ID.

4. Den kör `upgrade()`-funktionen i de nya skripten.

5. Den uppdaterar ID't i `alembic_version` till den allra senaste versionen. 
---

**Databasen och koden är nu 100% in sync med varandra och vi undviker att förstöra någonting som kan orsaka stora problem i produktion eller leda till oväntad downtime vilket kan få stakeholders att bli panikslagna.**

## Men vad händer med datan om vi gör en `upgrade()`?
**Det här är en fråga om att göra ändringar i huset som nämns ovan och och fylla huset med nya möbler.  
(Ändringar på huset är våra tabeller och möblerna är datan i den här kontexten)**

1. När du kör alembic upgrade och lägger till t.ex kolumnen `humidity` via en `ALTER TABLE` så kommer databasen automatiskt ge `NULL` values eller ett förvalt `DEFAULT` värde för den nya kolumnen på alla historiska rader. Databasen säger i princip "Ok, jag har en ny kolumn nu men ingen aning om vad `humidity` var igår så jag lämnar det tomt"

2. Hur kommer då den nya datan in och hur ersätter vi alla `NULL` values? Jo, eftersom att Alembic enbart står för strukturen på databasen. För att faktiskt börja spara data måste hela pipelinen uppdateras. I samma PR där jag skapar min Alembic-revision bör jag även göra följande ändringar i koden.
    - **Producenten/Consumern (Kafka):** Jag uppdaterar scriptet så att sensorerna faktiskt börjar mäta och skicka `"humidity": 35.6`
    - **Bronze/Silver ETL:** Jag uppdaterar `cleaner.py` för att tvätta och validera `humidity` precis som vi gör med `rpm` och `engine_temp`
    - **API & Pydantic:** Vår `api_schemas.py` måste få en ny rad: `humidity: Optional[float] = None` så att API'et vet hur den ska paketera datan och visa den i Swagger UI.

--- 

## Schema vs Data Flow  
Alembic hanterar enbart strukturen (Schema Migrations). När en ny kolumn (t.ex humidity) läggs till, får historisk data värdet NULL. För att populera kolumnen framåt uppdateras plattformens kontrakt (Pydantic modeller) och ETL-script parallellt med Alembic-revisionen.