from aiokafka import AIOKafkaProducer
import asyncio
import json
import os
from datetime import datetime

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
producer = None

async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
        await producer.start()
    return producer

async def send_event(topic: str, data: dict):
    """Отправка события в Kafka"""
    try:
        prod = await get_producer()
        
        event_data = {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "menu_service"
        }
        
        await prod.send_and_wait(
            topic, 
            json.dumps(event_data, default=str).encode("utf-8")
        )
        print(f" Menu event sent to {topic}: {event_data.get('event_type', 'unknown')}")
    except Exception as e:
        print(f" Failed to send menu event to {topic}: {e}")

async def stop_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None