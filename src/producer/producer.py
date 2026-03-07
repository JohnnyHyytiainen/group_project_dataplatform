# Faker scriptet
import json
from datetime import datetime
import time
import random
import os
from faker import Faker
from confluent_kafka import Producer

# 1) Konfigurera Faker och vår Kafka klient
fake = Faker()
# Berätta för producern vart vägen börjar (Localhost eftersom skriptet körs på din dator)
conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
TOPIC_NAME = "sensor_data_stream"

# Filen där vi sparar vår Source of Truth (Cold Storage)
RAW_DATA_FILE = "data/raw/raw_sensor_data.jsonl"


# Callback funktion (Kvitto  på posten)
# Kafka är asynkront(ASYNC). Den här funktionen anropas automatiskt i bakgrunden utan att vi behöver tänka
# när Kafka-servern bekräftar "Jag har tagit emot ditt meddelande!"
def delivery_report(err, msg):
    if err is not None:
        print(f"Failed to send message: {err}")
    else:
        val = json.loads(msg.value().decode('utf-8'))
        print(f"Kafka: {val.get('sensor_type', 'UNKNOWN').upper()} | Partition: {msg.partition()}")

print(f"Starting transmition!\n Saving source of Truth locally to: {RAW_DATA_FILE}\nPress CTRL+C to abort.\n")

# Öppnar filen med "a" (append) läge för att lägga till nya rows
try:
    with open(RAW_DATA_FILE, "a", encoding="utf-8") as file:
        while True:
            # Definiera våra maskiner
            appliance = random.choice(["washing_machine", "dryer", "dishwasher", "drying_cabinet"])

            # Bygg våra events för motorerna. Alla sensorer i samma payload
            event = {
                "engine_id": fake.uuid4(),
                "appliance_type": appliance,
                "timestamp": fake.date_time_between(start_date=datetime(2006, 1, 1), end_date="now").isoformat(),
                "run_hours": round(random.uniform(10.0, 10500.0), 1),
                "location": fake.city(),
                # Maskinernas aktuella status för alla sensorer samtidigt
                "rpm": round(random.uniform(0.0, 1600.0), 2),
                "engine_temp": round(random.uniform(10.0, 100.0), 2),
                "vibration_hz": round(random.uniform(0.1, 10), 2)
            }

            # HÄR börjar kaoset. Vi genererar 5% fel överallt så vi får med missvisande data (MED FLIT!)
            # HÄR styr vi vad för typ av fel vi genererar. Vi kan välja exakt vad för typ av fel vi vill generera
            if random.random() < 0.20:
                error_type = random.choice([
                    "extreme_temp",         # Överhettad
                    "extreme_rpm",          # För hög RPM
                    "extreme_vibration",    # Skakar sönder
                    "null_value",           # Sensorfel
                    "sensor_offline",       # Nätverksfel
                    "missing_id"            # Databasfel
                ])

                if error_type == "extreme_temp":
                    event["engine_temp"] = round(random.uniform(101.0, 150.0), 2)
                elif error_type == "extreme_rpm":
                    event["rpm"] = round(random.uniform(1601.0, 5000.0), 2)
                elif error_type == "extreme_vibration":
                    event["vibration_hz"] = round(random.uniform(11.0, 50.0), 2)

                # Slumpa vilken sensor som skickar null values
                elif error_type == "null_value":
                    broken_sensor = random.choice(["rpm", "engine_temp", "vibration_hz"])
                    event[broken_sensor] = None
                
                # Slumpa vilken sensor som skickar text istället för siffror
                elif error_type == "sensor_offline":
                    broken_sensor = random.choice(["rpm", "engine_temp", "vibration_hz"])
                    event[broken_sensor] = "SENSOR_OFFLINE"
                
                elif error_type == "missing_id":
                    if "engine_id" in event:
                        del event["engine_id"]


                print(f"\n Seeding errors with error type: {error_type}")

            # SPARA TILL SOURCE OF TRUTH (JSONL)
            # Gör om till en JSON-sträng, lägg till en radbrytning (\n) och skriv till filen
            file.write(json.dumps(event) + "\n")
            file.flush() # Tvingar Python att spara till hårddisken direkt

            # SKICKA TILL KAFKA (Samma som förut)
            json_payload = json.dumps(event).encode('utf-8')
            producer.produce(TOPIC_NAME, value=json_payload, callback=delivery_report)
            producer.poll(0)

            # Skriver varje 2 sekunder. Vi kontrollerar hur snabbt vi genererar datan
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nTurning off...")

finally:
    producer.flush()
    print("Closed.")