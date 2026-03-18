# This is a replayer script.
# It reads the already-saved raw_sensor_data.jsonl file and replays everything back into Kafka.
# Normal producer -> generates NEW fake data -> saves to JSONL -> sends to Kafka
# Replayer -> reads EXISTING JSONL -> sends to Kafka (no new data generated)

# Used for the small delay between messages to avoid overwhelming local Kafka.
import time

# The Kafka client library
from confluent_kafka import Producer
import os

# Configuration
# 1. Hämta adressen från Docker (eller använd localhost om vi kör utanför Docker)
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
conf = {"bootstrap.servers": KAFKA_BROKER}
TOPIC_NAME = "sensor_data_stream"
RAW_DATA_FILE = "data/raw/raw_sensor_data.jsonl"


# Callback function that Kafka calls automatically after each message is sent
def delivery_report(err, msg):
    if err is not None:
        print(f"Failed to send : {err}")


# The main function that does all the work.
def replay_data():
    print(f"Starting Kafka Replayer from: {RAW_DATA_FILE}")
    conf = {"bootstrap.servers": KAFKA_BROKER}
    producer = Producer(conf)
    lines_sent = 0

    try:
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                # We send the raw JSON string from the file straight into Kafka
                producer.produce(
                    TOPIC_NAME,
                    value=line.strip().encode(  # converts the string to bytes because Kafka only accepts bytes.
                        "utf-8"
                    ),
                    callback=delivery_report,
                )
                # Poll to handle callbacks
                producer.poll(0)
                lines_sent += 1
                # A pause so we don't overload local Kafka right away
                time.sleep(0.01)

    except FileNotFoundError:
        print(f"Couldn't find the file! Is it really there? {RAW_DATA_FILE}?")
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    finally:  # always runs no matter what
        print("Waiting for the final messages to be sent...")
        producer.flush()
        print(f"Replay ready! Sent {lines_sent} events to Kafka.")


# Only runs when you run the file directly
if __name__ == "__main__":
    replay_data()
