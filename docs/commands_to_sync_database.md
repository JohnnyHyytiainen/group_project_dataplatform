# Quick run commands för att synka din data.

## Synka databasen:
Steg för steg guide i hur du synkar databasen så vi alla får exakt samma data lokalt.
```bash
Eftersom Kafka inte sparar data för evigt lokalt och vi vill att alla i teamet ska ha exakt samma data när vi utvecklar och testar har vi en "Source of Truth" fil:

(raw_sensor_data.jsonl)
```

**Genom att köra vår `replayer.py` så "skjuter vi in" historiken från filen rakt in i Kafka igen så att din lokala databas fylls med det officiella datasetet** 

**Steg för steg guide:**

0) Hämta senaste koden.
    - `git checkout main`
    - `git pull origin main`

1) Nuke & Rebuild (Börja med en clean slate)
- För att garantera att du inte har gammal skräpdata blandat med den nya, nollställ din lokala databas (**VARNING:** Detta raderar din nuvarande lokala Docker-data).
- Du kan även gå in i PGAdmin GUI och rensa dina tables i bronze layer också. Gör det du känner är enklast.
    - `docker compose down -v`
    - `docker compose up -d`

2) Starta Consumer.
- Öppna en terminal och starta consumer scriptet. Detta script måste vara igång för att ta emot datan vi ska skicka in.
    - `uv run python -m src.consumer.worker`

3) Kör replayer scriptet.
- Öppna en **NY** terminal. Nu ska du läsa från vår .jsonl fil och skicka in det i Kafka kön.
    `uv run python -m src.producer.replayer`

*Nu kommer du se i din första terminal (Consumern) hur den frenetiskt börjar tugga i sig all data och spara ner det i din Postgres databas (Bronze lagret)* 
