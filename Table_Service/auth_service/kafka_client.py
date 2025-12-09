from aiokafka import AIOKafkaProducer
import asyncio
import json
import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

producer = None

async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
        await producer.start()
    return producer

async def send_event(topic: str, data: dict):
    prod = await get_producer()
    await prod.send_and_wait(topic, json.dumps(data).encode("utf-8"))

async def stop_producer():
    global producer
    if producer:
        await producer.stop()
