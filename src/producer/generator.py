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
            # Definiera våra maskiner och sensor typer
            appliance = random.choice(["washing_machine", "dryer", "dishwasher", "drying_cabinet"])
            sensor = random.choice(["rpm", "temperature", "vibration"])

            # Rimliga värden för våra sensorer
            if sensor == "rpm":
                simulated_value = round(random.uniform(0.0, 1600.0), 2)
            elif sensor == "temperature":
                # Motor temp 10-100 grader
                simulated_value = round(random.uniform(10.0, 100.0), 2)
            else: 
                # vibration
                simulated_value == round(random.uniform(0.1, 10.0), 2)

            event = {
                "engine_id": fake.uuid4(),
                "appliance_type": appliance,
                "timestamp": fake.date_time_between(start_date=datetime(2006, 1, 1), end_date="now").isoformat(),
                "sensor_type": sensor,
                "run_hours": round(random.uniform(10.0, 10500.0), 1),
                "location": fake.city()
            }

            # HÄR börjar kaoset. Vi genererar 5% fel överallt så vi får med missvisande data (MED FLIT!)
            # HÄR styr vi vad för typ av fel vi genererar. Vi kan välja exakt vad för typ av fel vi vill generera
            if random.random() < 0.05:
                error_type = random.choice(["null_value", "string_in_float", "missing_id", "extreme_rpm"])

                if error_type == "null_value":
                    event["value"] = None # Sätter värdet till Null
                elif error_type == "string_in_float":
                    event["value"] = "SENSOR_OFFLINE"
                elif error_type == "missing_id":
                    if "engine_id" in event:
                        del event["engine_id"]
                elif error_type == "extreme_rpm":
                    event["value"] = 9999.99 # Orimligt värde för RPM

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
            time.sleep(0.02)

except KeyboardInterrupt:
    print("\nTurning off...")

finally:
    producer.flush()
    print("Closed.")