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
        
        # Добавляем метаданные
        event_data = {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "reservation_service"
        }
        
        await prod.send_and_wait(
            topic, 
            json.dumps(event_data, default=str).encode("utf-8")
        )
        print(f" Event sent to {topic}: {event_data.get('event_type', 'unknown')}")
    except Exception as e:
        print(f" Failed to send event to {topic}: {e}")

async def send_reservation_event(event_type: str, reservation_data: dict):
    """Отправка события о бронировании"""
    event_data = {
        "event_type": event_type,
        "reservation_id": reservation_data.get("id"),
        "reservation_code": reservation_data.get("reservation_code"),
        "user_id": reservation_data.get("user_id"),
        "table_id": reservation_data.get("table_id"),
        "guests_count": reservation_data.get("guests_count"),
        "reservation_date": reservation_data.get("reservation_date").isoformat() if reservation_data.get("reservation_date") else None,
        "status": reservation_data.get("status"),
        "data": reservation_data
    }
    
    await send_event("reservation.events", event_data)

async def stop_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None