# Team Git Workflow (Hur vi bygger kod tillsammans)

Syfte: En steg-för-steg guide för hur vi samarbetar i repot utan att skriva över varandras kod. 

## Den Heliga Regeln

**Vi jobbar ALDRIG direkt på `main`.**

`main`-branchen är vår färdiga, fungerande produkt. Allt arbete sker i egna arbetskopior (så kallade "branches"). När vi är klara, ber vi om tillåtelse att slå ihop vår kod med `main` via en **Pull Request (PR)**.

---

## Det Dagliga Arbetsflödet (Step by step)

### 1. Börja dagen med att synka

- Innan du skriver en enda rad kod, måste du se till att du har de senaste ändringar.

```bash
git checkout main
git pull origin main
```

### 2. Skapa din arbetskopia (Branch)

Skapa en egen "bubbla" att jobba i. Ge den ett namn som beskriver vad du ska göra.

```bash
# Exempel: git checkout -b feat/add-kafka-producer

git checkout -b <typ>/<kort-beskrivning>

```

- (Nu kan du koda bäst du vill! Om allt kraschar, har du inte förstört `main`.)

### 3. Spara ditt arbete (Stage & Commit)

När du har skrivit kod som fungerar, är det dags att spara den i Git.
Gör det till en vana att **alltid** titta vad du har ändrat innan du sparar:

```bash
git status
```

**Steg A: Stage (Lägg till filerna för att göra dom redo)**

Använd **ALDRIG** `git add .` (det är så hemliga lösenord råkar hamna på nätet!). Lägg istället till specifika filer:

```bash
git add src/min_nya_fil.py

```

**Steg B: Commit (Gör dom redo att skickas iväg)**
Skriv ett kort meddelande om vad din kod gör.

```bash
git commit -m "feat(api): created new search endpoint"

```
*(Tips: Du kan göra flera commits i din branch medan du jobbar!)*

### 4. Skicka din branch till GitHub (Push)

När du känner dig klar för dagen, skicka upp din branch till molnet.

```bash
git push -u origin <ditt-branch-namn>

```

---

## Hur vi får in koden i `main` (Pull Requests)

När din kod är redo att användas av resten av gruppen:

1. Gå till vårt repo på GitHub.

2. Klicka på **"New Pull Request"**.

3. Be om en "Review" från en projektet (de kollar snabbt att koden ser okej ut).

### Magin med "Squash and Merge"

När din PR blir godkänd klickar vi på den gröna knappen **"Squash and merge"**.

**Varför "Squash"?**

Medan du jobbade i din branch kanske du gjorde 5 olika commits (t.ex. "fixade bugg", "glömde ett komma", "nu funkar det"). 

Vi vill inte smutsa ner `main` med alla dessa småsteg. "Squash" trycker ihop alla dina 5 commits till **en enda, snygg commit** innan den läggs på `main`. Det håller vår gemensamma historik ren och professionell!

### Efter en Merge (Städa upp)

När din kod ligger på `main`, går du tillbaka till din terminal, går till `main`, hämtar den nya koden och raderar din gamla arbetskopia:

```bash
git checkout main
git pull origin main
git branch -d <ditt-gamla-branch-namn>

```

---

## Panik-akuten (Vanliga misstag)

* **Jag vet inte vilken branch jag är på!**
Kör `git status` eller `git branch`.

* **Git säger "Everything up-to-date" fast jag har skrivit ny kod!**
Du har glömt att göra `git add` och `git commit`. Koden är sparad på din dator, men Git känner inte till den än.

* **Jag råkade börja koda direkt på `main`!**
Gör ingen commit! Skapa bara en ny branch direkt, så följer dina osparade ändringar med dit:
`git checkout -b fix/oops-fel-branch`
