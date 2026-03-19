# Faker scriptet
# Timedelta behövs för att kunna "spola fram tiden" i vår "flotta" av sensorer
import json
from datetime import datetime, timedelta
import time
import random
import os
from faker import Faker
from confluent_kafka import Producer

# 1. Hämta adressen från Docker (eller använd localhost om vi kör utanför Docker)
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
# Konfigurera Faker och vår Kafka klient
fake = Faker()
# Berätta för producern vart vägen börjar (Localhost eftersom skriptet körs på min dator)
conf = {"bootstrap.servers": KAFKA_BROKER}
producer = Producer(conf)
# Filen där vi sparar vår Source of Truth (Cold Storage)
TOPIC_NAME = "sensor_data_stream"
RAW_DATA_FILE = "data/raw/raw_sensor_data.jsonl"


# Callback funktion (Kvitto på 'posten')
# Kafka är asynkront(ASYNC). Den här funktionen anropas automatiskt i bakgrunden utan att vi behöver tänka
# när Kafka-servern bekräftar "Jag har tagit emot ditt meddelande!"
def delivery_report(err, msg):
    if err is not None:
        print(f"Failed to send message: {err}")
    else:
        val = json.loads(msg.value().decode("utf-8"))
        print(
            f"Kafka: {val.get('sensor_type', 'UNKNOWN').upper()} | Partition: {msg.partition()}"
        )


print(
    f"Starting transmition!\n Saving source of Truth locally to: {RAW_DATA_FILE}\nPress CTRL+C to abort.\n"
)

# ==========
# 1) Bygger vår flotta av motorer vi väljer (Så kallad 'Stateful data')
# ==========
NUM_MACHINES = 1000  # Antal unika motorer i vår flotta
fleet = []
print(f"Building our fleet of {NUM_MACHINES}..")

# Iterera över vår flotta av motorer i olika maskiner
for x in range(NUM_MACHINES):
    fleet.append(
        {
            "engine_id": fake.uuid4(),
            "appliance_type": random.choice(
                ["washing_machine", "dryer", "dishwasher", "drying_cabinet"]
            ),
            "location": fake.city(),
            # Ger våra maskiner(motorer) en starttid i det förflutna. Våra sensorer började mäta 2006.
            "current_time": fake.date_time_between(
                start_date=datetime(2006, 1, 1), end_date=datetime.now()
            ),
            # Genererar en slumpmässig mätarställning från start
            "run_hours": round(random.uniform(10.0, 500.0), 1),
        }
    )

try:
    # Öppnar filen med "a" (append) läge för att lägga till nya rows
    with open(RAW_DATA_FILE, "a", encoding="utf-8") as file:
        while True:
            # ==========
            # 2) Väljer EN maskin(motor) och spolar fram tiden
            # ==========
            machine = random.choice(fleet)
            # Säkerställer satt maskin(motor) har varit igång mellan 1-20 timmar sedan förra mätningen
            hours_passed = random.uniform(1.0, 12.0)
            # Uppdaterar maskinens INBYGGDA state
            machine["current_time"] += timedelta(hours=hours_passed)
            machine["run_hours"] += hours_passed

            # Bygger eventet
            event = {
                "engine_id": machine["engine_id"],
                "appliance_type": machine["appliance_type"],
                "timestamp": machine["current_time"].isoformat(),
                "run_hours": round(machine["run_hours"], 1),
                "location": machine["location"],
                "rpm": round(random.uniform(0.0, 1600.0), 2),
                "engine_temp": round(random.uniform(10.0, 100.0), 2),
                "vibration_hz": round(random.uniform(0.1, 15), 2),
            }

            # ==========
            # 3) Kaos generator(Här smutsar jag ner genererad data med FLIT!)
            # ==========
            if random.random() < 0.20:
                error_type = random.choice(
                    [
                        "extreme_temp",
                        "extreme_rpm",
                        "extreme_vibration",
                        "null_value",
                        "sensor_offline",
                        "missing_id",
                        "format_noise",  # NY! Siffror(floats) som fula str.
                        "category_noise",  # NY! Fula namn på maskinerna. CAPS, fel format etc.
                    ]
                )

                if error_type == "extreme_temp":
                    event["engine_temp"] = round(random.uniform(101.0, 150.0), 2)
                elif error_type == "extreme_rpm":
                    event["rpm"] = round(random.uniform(1601.0, 5000.0), 2)
                elif error_type == "extreme_vibration":
                    event["vibration_hz"] = round(random.uniform(16.0, 50.0), 2)

                elif error_type == "null_value":
                    broken_sensor = random.choice(
                        ["rpm", "engine_temp", "vibration_hz"]
                    )
                    event[broken_sensor] = None

                elif error_type == "sensor_offline":
                    broken_sensor = random.choice(
                        ["rpm", "engine_temp", "vibration_hz"]
                    )
                    event[broken_sensor] = "SENSOR_OFFLINE"

                elif error_type == "missing_id":
                    if "engine_id" in event:
                        del event["engine_id"]

                # --- NYTT - ETL SMUTS ---
                elif error_type == "format_noise":
                    # Slumpa vilket värde som blir en smutsig sträng med whitespaces(mellanslag)
                    noisy_sensor = random.choice(
                        ["rpm", "engine_temp", "vibration_hz", "run_hours"]
                    )
                    event[noisy_sensor] = f"   {event[noisy_sensor]}   "

                elif error_type == "category_noise":
                    # Gör om normala namn mot något som kräver .str.lower() i Pandas / .str.lower() i etl script.
                    messy_names = {
                        "washing_machine": [
                            "WASHING MACHINE",
                            "washing-machine",
                            " Washing_Machine ",
                        ],
                        "dryer": [" DRYER ", "Dryer", "dryer "],
                        "dishwasher": ["DishWasher", "dish washer", "DISHWASHER"],
                        "drying_cabinet": [
                            "DryingCabinet",
                            "drying cabinet",
                            " DRYING_CABINET",
                        ],
                    }
                    event["appliance_type"] = random.choice(
                        messy_names[event["appliance_type"]]
                    )
                print(f"Seeding errors with error type: {error_type}")

            # Spara och skicka till raw fil. Source of Truth
            file.write(json.dumps(event) + "\n")
            file.flush()

            # Skicka till kafka
            json_payload = json.dumps(event).encode("utf-8")
            producer.produce(TOPIC_NAME, value=json_payload, callback=delivery_report)
            producer.poll(0)
            # Tidsintervall för att kontrollera hur snabbt data ska genereras
            time.sleep(30)

except KeyboardInterrupt:
    print("\nTurning off...")

finally:
    producer.flush()
    print("Closed.")
