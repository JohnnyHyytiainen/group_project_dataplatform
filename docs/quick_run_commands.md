# Quick run commands som är bra att ha: 


Det här är en snabbguide för att starta projektet lokalt med Docker + köra producer/consumer/API.

**Tips:** Kör kommandon från repo root (samma nivå som `docker-compose.yml`)


## 0) Förutsättningar
- Docker Desktop är igång
- Du har `.env` på plats (fråga teamet om du saknar den)
- `uv` är installerat (Då vi använder uv i projektet)

## 0.5) Ladda ner alla nödvändiga python dependencies(EN GÅNG RÄCKER)
- `uv sync`
---

## 1) Starta Docker-miljön (Postgres + Kafka + pgAdmin)
Starta containers i bakgrunden:
```bash
docker compose up -d
````

Kolla att allt är uppe:

```bash
docker compose ps
```

Se loggar (om något strular):

```bash
docker compose logs -f
# eller bara en service:
docker compose logs -f postgres
docker compose logs -f kafka
docker compose logs -f pgadmin
```

Stäng ner (behåller data/volymer):

```bash
docker compose down
```

---

## 2) Kör producer / consumer (viktigt: kör som modul)

### Varför -m?

Om du kör en fil direkt, t.ex:

```bash
uv run src/consumer/consumer.py
```

…kan Python få fel "start" mapp och då hittar den inte `src` som paket.

Kör därför som modul (rekommenderat):

```bash
uv run python -m src.producer.producer
uv run python -m src.consumer.consumer
```

> Notera: med `-m` använder Python repo root som utgångspunkt och importerna fungerar stabilt.
(Repo root = där vi har vår `README.md`, vår `docker-compose.yml`)

---

## 3) Kör API (FastAPI/Uvicorn)

Starta API-servern:

```bash
uv run uvicorn src.api.main:app --reload
```

Du ska se något i stil med:

* `Uvicorn running on http://127.0.0.1:8000`

`--reload` betyder att servern startar om automatiskt när du sparar kodändringar.

---

## 4) Öppna pgAdmin (för att titta i databasen)

**Kan skriva guide för detta med. Säg bara till / Johnny**

---

## 5) Snabbkoll: 'kommer data in i Kafka?'

### Lyssna på events (inne i Kafka-containern)

Öppna terminal i kafka-containern:

```bash
docker exec -it group_kafka bash
```

Lista topics:

```bash
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

Lyssna på topic:

```bash
/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic sensor_data_stream \
  --from-beginning
```

> Obs: Sökvägen `/kafka/bin/...` kan skilja mellan images. Om kommandot inte hittas, kör `ls` och leta efter `kafka-console-consumer.sh`.

---

## 6) **NUKE & rebuild** (om du vill börja från helt tom databas)

VARNING: detta tar bort all sparad data i volymer.

```bash
docker compose down -v
docker compose up -d
```

---

## Vanliga fel & snabba fixar

### A) Port is already allocated (t.ex. 9092)

Det betyder att en annan process redan använder porten.

* Byt host-port i `docker-compose.yml` (ex: 19092)
* Eller stäng den andra processen/containern som använder porten

Snabbkoll på running containers:

```bash
docker ps
```

### B) "ModuleNotFoundError: No module named 'src'"

Kör som modul:

```bash
uv run python -m src.consumer.consumer
```

### C) "Nothing happens" i consumer

* Kontrollera att producer faktiskt kör
* Kolla loggar:

```bash
docker compose logs -f kafka
docker compose logs -f postgres
```

## OM du ej klarar CI pipens check. Kan du alltid gå in och se VAD som är felet.
Enkel lösning: Gå in i VScode igen och skriv denna rad:

`uv run ruff check --fix .`

Du kommer nu se t.ex detta i terminalen:

```bash
$ uv run ruff check --fix .
Found 3 errors (3 fixed, 0 remaining).
```

Så som hände mig nyss. Ser felen i github trädet vid sidan, committar filerna och gör ändringarna. KLART