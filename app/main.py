from fastapi import FastAPI
from faker import Faker
from kafka import KafkaProducer
import random
import json
import datetime

app = FastAPI()
faker = Faker()

# Kafka config
KAFKA_TOPIC = "iot-stream"
KAFKA_BROKER = "localhost:9092"

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

@app.get("/iot-data")
def get_iot_data():
    data = {
        "device_id": faker.uuid4(),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "temperature": round(random.uniform(20, 40), 2),
        "humidity": round(random.uniform(30, 80), 2)
    }
    producer.send(KAFKA_TOPIC, value=data)
    producer.flush()
    return {"status": "sent to kafka", "data": data}

# uvicorn main:app --reload