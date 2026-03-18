# Module Overview: CI/CD Pipeline (GitHub Actions)
*Written 18/03-2026 by Johnny*

## Vad är vår CI-Pipeline?
I ett dataplattformsprojekt med flera utvecklare är kodens stabilitet ytterst viktig eller rättare sagt: KRITISK. Vår Continuous Integration (CI) pipeline är en automatiserad "dörrvakt" (skapad via GitHub Actions) som triggas varje gång någon av oss i gruppen försöker pusha kod till eller skapa en Pull Request mot vår `main` branch.

Syftet med CI pipelinen är enkelt förklarat att eliminera *"Det fungerade på min maskin"* problematiken och säkerställa att all kod som når produktion(vår main branch) håller högsta kvalitet. Du kan dra en liknande parallell med vad vi gjorde med docker tidigare. Just nu i skrivande stund så har vi 5x sessions som kör samtidigt i bakgrunden i vår Docker container, Vår API, vår consumer, Kafka, vår Postgres DB och vår producer.

## Arkitektur & Flöde
Pipelinen körs på en isolerad Ubuntu-server i molnet `runs-on: ubuntu-latest` och utför följande steg sekventiellt (Fail-Fast-metodik):

1. **Miljöuppsättning (Setup):** 
- Checkar ut koden.
- Installerar pakethanteraren `uv` (uv är kodat i rust och är EXTREMT snabbt. Snabbare än pip) och sätter upp Python 3.12.

2. **Beroendehantering:** 
- Kör `uv sync` för att installera en exakt spegelbild av projektets beroenden(våra dependencies(deps)) som består av bl.a FastAPI, Psycopg, Pytest, Ruff etc.

3. **Kodgranskning (Linting & Formatting):** 
- Kör `Ruff` (en extremt snabb linter/formaterare skriven i Rust som nämndes ovan)

- Den analyserar koden efter anti-patterns, oanvända imports och type errors.

- Den verifierar att koden följer projektets formateringsstandard (PEP 8). Om koden är ful, avbryts pipelinen(Så var snäll att högerklicka på scripten, välj format document with... Sedan välj din formatter. Helst Ruff eller autopep8, men Black och Prettier BÖR fungera)

4. **Enhetstestning (Unit Testing):** 
- Om koden passerar Ruff, körs `Pytest` mot mappen `src/test/`. Här exekveras våra Pydantic valideringar och mockade API-tester.
- En notering om detta. Det kommer fungera bättre ju mer unit tests vi utvecklar och skriver. Just nu testar den enbart mot vår API och mock DB. Ju mer tester vi gör == desto bättre kommer vår CI pipe att hjälpa oss undvika huvudvärk.

## Varför detta är avgörande och vad för "Affärsvärde" ger det.

* **Psykologisk trygghet:** 
- Utvecklare(Noviser som vi) vågar koda snabbare eftersom pipen/roboten fångar misstagen vi kan tänkas göra. Man(vi) behöver inte vara rädd för att "råka" krascha main branchen utan kan applicera "learn by doing / learn by breaking it just to fix it" principen. 

* **Tidseffektivitet:** 
- Code Reviews (PR granskningar) kan fokusera på *affärslogik* istället för att leta efter missade kommatecken eller oanvända imports. Vår CI pipeline/roboten gör det tråkiga jobbet.
- Som nämndes ovan i Enhetstestning. Ju mer vi utvecklar tester desto mindre tid behöver vi lägga på att scanna igenom varje tecken i koden för att se typos eller missade semikolon.

* **Idempotens & Kvalitetsgaranti:** 
- Eftersom miljön byggs upp från noll varje gång, bevisar vi att vår kod är fullt containeriserbar och inte beroende av dolda lokala miljövariabler.