# 1. Hämta en minimal "Linux burk" med Python 3.12 installerat
FROM python:3.12-slim
# 2. Sätt en miljövariabel som tvingar Python att skriva loggar direkt till terminalen
# (Annars kan Docker ibland "hålla" på loggarna vilket gör felsökning svårare för oss)
ENV PYTHONUNBUFFERED=1
# 3. Bestämmer att vi ska jobba i en mapp som heter /app inuti containern
WORKDIR /app
# 4. Installerar uv i Linux-datorn
RUN pip install uv
# 5. CACHE: Kopierar in dependency-filer FÖRST.
# Om du ändrar i din Python kod (src), men inte installerar nya paket,
# slipper Docker ladda ner alla paket på nytt. Den återanvänder cachen.
COPY pyproject.toml uv.lock ./
# 6. Installera alla paket från pyproject.toml globalt inuti containern
RUN uv pip install --system -r pyproject.toml
# 7. Kopiera in resten av din kod (din src-mapp, .env etc)
COPY . .
# Vi anger INGET ENTRYPOINT eller CMD här. 
# Varför? För att vi kommer berätta för Docker Compose vad som ska köras.