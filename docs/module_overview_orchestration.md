# Module Overview: Infrastructure & Orchestration (Docker)

## Syfte
För att säkerställa att vår dataplattform är plattformsoberoende, reproducerbar och skalbar, har vi valt att containerisera hela vår arkitektur. Istället för att teammedlemmar (eller lärare) ska behöva installera rätt version av Python och manuellt starta 5-6 olika skript, orkestreras allt via Docker Compose. Detta uppfyller branschens krav på portabilitet och CI/CD-beredskap.

## Arkitektur & Nätverk
Vi använder ett slutet, internt Docker-nätverk där våra tjänster pratar med varandra via DNS (containernamn) istället för `localhost`

### 1. Infrastructure (Officiella Images)

* **`postgres:16-alpine`**: Databasen. Vi använder en dölj volym `live_pg_data` för att datan ska överleva även om containern raderas. Exponeras lokalt via port `5439` för PgAdmin åtkomst.

* **`apache/kafka:latest`**: Vår Message Broker. Körs i KRaft-mode (utan Zookeeper) för en mer lättviktig setup.

### 2. Applikationer (Egenbyggd Image via `Dockerfile`)
Vi använder en enda centraliserad `Dockerfile` (baserad på `python:3.12-slim`) för hela vår kodbas. Den installerar våra dependencies via `uv`. I vår Compose fil snurrar vi sedan upp tre isolerade kopior av denna Image med olika ansvarsområden:

* **`api`**: Startar FastAPI servern. Får sina databas-uppgifter injicerade via miljövariabler.

* **`consumer`**: Lyssnar på Kafka (`kafka:9092`) och skriver till Bronze-lagret.

* **`producer`**: Vår datagenerator. Vi har implementerat en **Bind Mount** `./data:/app/data` så att the Source of Truth `.jsonl`-filen speglas direkt ut till vår lokala disk i realtid, utan att låsas fast inuti containern.

## Hur man kör systemet
För att starta hela Medallion plattformen (Databas, Kafka, Producer, Consumer och API) körs endast ett kommando från roten av projektet:

```bash
docker-compose up -d --build
```
För att stoppa och städa upp miljön:
```bash
docker-compose down
```

## Designbeslut

* **Miljövariabler (`os.getenv`)**: Vår kod är skriven för att vara miljöagnostisk. Skripten letar främst efter Docker-variabler (t.ex `DB_HOST=postgres`) men faller snyggt tillbaka på `localhost` om en utvecklare väljer att köra skriptet löst utanför Docker under felsökning.

