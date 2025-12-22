import asyncio
import json
import os
import logging
from datetime import datetime
from aiokafka import AIOKafkaConsumer
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPICS = ["user.events", "menu.events", "reservation.events"]

# Настройки SMTP для отправки email
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@restaurant.com")

async def send_email_notification(subject: str, body: str, to_email: str = ADMIN_EMAIL):
    """
    Отправляет email уведомление через SMTP
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not set. Email notifications disabled.")
        return False
    
    logger.info(f"📧 Попытка отправки email на {to_email}")
    
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Добавляем текст письма
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Отправляем email
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: send_sync_email(msg, to_email)
        )
        
        logger.info(f"✅ Email отправлен на {to_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email: {e}")
        return False

def send_sync_email(msg: MIMEMultipart, to_email: str):
    """
    Синхронная отправка email (выполняется в thread pool)
    """
    try:
        logger.info(f"🔧 Подключение к SMTP: {SMTP_SERVER}:{SMTP_PORT}")
        
        # Для порта 465 используем SSL, для 587 - TLS
        if SMTP_PORT == 465:
            # SSL соединение для порта 465 (Mail.ru)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                logger.info(f"🔐 Используем SSL соединение для порта {SMTP_PORT}")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                logger.info("✅ Успешная аутентификация SMTP")
                server.send_message(msg)
                logger.info(f"📤 Сообщение отправлено на {to_email}")
        else:
            # TLS для порта 587 (Gmail и другие)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                logger.info(f"🔐 Используем TLS соединение для порта {SMTP_PORT}")
                server.starttls()  # Шифрование TLS
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                logger.info("✅ Успешная аутентификация SMTP")
                server.send_message(msg)
                logger.info(f"📤 Сообщение отправлено на {to_email}")
                
    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"Ошибка аутентификации SMTP: {e}. Проверьте логин и пароль приложения")
    except smtplib.SMTPException as e:
        raise Exception(f"SMTP ошибка: {e}")
    except Exception as e:
        raise Exception(f"Общая ошибка отправки email: {e}")

async def send_notification(event_data: Dict[str, Any]):
    """
    Отправляет уведомление о событии
    """
    event_type = event_data.get("event_type", "unknown")
    timestamp = event_data.get("timestamp", datetime.utcnow().isoformat())
    service = event_data.get("service", "unknown")
    
    # Формируем сообщение для логов
    log_message = f"""
    🚨 Событие в системе ресторана
    
    📋 Тип события: {event_type}
    ⏰ Время: {timestamp}
    🏢 Сервис: {service}
    
    📊 Данные события:
    {json.dumps(event_data, indent=2, ensure_ascii=False)}
    """
    
    logger.info(f"📩 Уведомление: {event_type}")
    logger.info(log_message)
    
    # Отправляем email уведомление администратору
    email_subject = f"[Restaurant System] {event_type}"
    email_body = f"""
    Restaurant Management System Notification
    
    Event Type: {event_type}
    Time: {timestamp}
    Service: {service}
    
    Event Details:
    {json.dumps(event_data, indent=2, ensure_ascii=False)}
    
    ---
    This is an automated notification from Restaurant Booking System.
    """
    
    await send_email_notification(email_subject, email_body, ADMIN_EMAIL)
    
    # Отправляем специальные уведомления в зависимости от типа события
    if event_type == "user.registered":
        await handle_user_registered(event_data)
    elif event_type == "reservation.created":
        await handle_reservation_created(event_data)
    elif event_type == "reservation.confirmed":
        await handle_reservation_confirmed(event_data)
    elif "menu_item" in event_type:
        await handle_menu_update(event_data)

async def handle_user_registered(event_data: Dict[str, Any]):
    """
    Обработка события регистрации пользователя
    """
    user_email = event_data.get("data", {}).get("email")
    user_name = event_data.get("data", {}).get("full_name", "User")
    
    if user_email:
        subject = f"🎉 Welcome to Our Restaurant, {user_name}!"
        body = f"""
        Dear {user_name},
        
        Thank you for registering with our restaurant booking system!
        
        Your account has been successfully created.
        
        You can now:
        - Browse our menu
        - Make table reservations
        - View your booking history
        
        We look forward to serving you!
        
        Best regards,
        Restaurant Team
        
        ---
        This is an automated welcome email.
        """
        
        await send_email_notification(subject, body, user_email)

async def handle_reservation_created(event_data: Dict[str, Any]):
    """
    Обработка события создания бронирования
    """
    reservation_data = event_data.get("data", {})
    user_email = reservation_data.get("contact_email")
    reservation_code = reservation_data.get("reservation_code")
    
    if user_email and reservation_code:
        subject = f"📅 Your Reservation #{reservation_code} is Pending"
        body = f"""
        Dear Guest,
        
        Thank you for making a reservation with us!
        
        Reservation Details:
        - Code: {reservation_code}
        - Status: Pending Confirmation
        - Date: {reservation_data.get('reservation_date', 'N/A')}
        - Guests: {reservation_data.get('guests_count', 'N/A')}
        
        Our team will review your reservation and confirm it shortly.
        You will receive another email once it's confirmed.
        
        If you have any questions, please contact us.
        
        Best regards,
        Restaurant Team
        
        ---
        This is an automated reservation confirmation email.
        """
        
        await send_email_notification(subject, body, user_email)

async def handle_reservation_confirmed(event_data: Dict[str, Any]):
    """
    Обработка события подтверждения бронирования
    """
    reservation_data = event_data.get("data", {})
    user_email = reservation_data.get("contact_email")
    reservation_code = reservation_data.get("reservation_code")
    
    if user_email and reservation_code:
        subject = f"✅ Your Reservation #{reservation_code} is Confirmed!"
        body = f"""
        Dear Guest,
        
        Great news! Your reservation has been confirmed.
        
        📋 Reservation Confirmation:
        - Code: {reservation_code}
        - Status: CONFIRMED ✅
        - Date: {reservation_data.get('reservation_date', 'N/A')}
        - Guests: {reservation_data.get('guests_count', 'N/A')}
        - Confirmed At: {reservation_data.get('confirmed_at', 'N/A')}
        
        We look forward to welcoming you!
        
        Please arrive 10 minutes before your reservation time.
        If you need to cancel or modify your reservation, please contact us.
        
        Best regards,
        Restaurant Team
        
        ---
        This is an automated reservation confirmation email.
        """
        
        await send_email_notification(subject, body, user_email)

async def handle_menu_update(event_data: Dict[str, Any]):
    """
    Обработка события изменения меню
    """
    # Отправляем уведомление администратору об изменениях в меню
    event_type = event_data.get("event_type", "")
    item_name = event_data.get("name", "Unknown Item")
    
    subject = f"🍽️ Menu Update: {event_type}"
    body = f"""
    Menu has been updated:
    
    Action: {event_type}
    Item: {item_name}
    Price: {event_data.get('price', 'N/A')}
    Updated By: User ID {event_data.get('updated_by', 'N/A')}
    Time: {event_data.get('timestamp', 'N/A')}
    
    Full Event Data:
    {json.dumps(event_data, indent=2, ensure_ascii=False)}
    """
    
    await send_email_notification(subject, body, ADMIN_EMAIL)

async def consume_events():
    """
    Основной потребитель событий Kafka
    """
    consumer = AIOKafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        group_id="notification_group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    await consumer.start()
    logger.info(f"✅ Консьюмер запущен. Подписка на топики: {TOPICS}")
    
    try:
        async for msg in consumer:
            logger.info(f"📥 Получено сообщение:")
            logger.info(f"   Топик: {msg.topic}")
            logger.info(f"   Partition: {msg.partition}")
            logger.info(f"   Offset: {msg.offset}")
            
            # Обрабатываем событие
            await send_notification(msg.value)
            
    except Exception as e:
        logger.error(f"❌ Ошибка в консьюмере: {e}")
    finally:
        await consumer.stop()
        logger.info("🛑 Консьюмер остановлен")

async def health_check():
    """
    Проверка доступности Kafka
    """
    while True:
        try:
            consumer = AIOKafkaConsumer(
                bootstrap_servers=KAFKA_BROKER,
                enable_auto_commit=False
            )
            await consumer.start()
            topics = await consumer.topics()
            await consumer.stop()
            logger.info(f"✅ Kafka доступен. Топики: {list(topics)}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Kafka недоступен: {e}")
            await asyncio.sleep(5)

async def main():
    """
    Основная функция
    """
    logger.info("🚀 Запуск сервиса уведомлений...")
    
    # Проверяем настройки SMTP
    logger.info(f"📧 Проверка SMTP настроек:")
    logger.info(f"   Сервер: {SMTP_SERVER}:{SMTP_PORT}")
    logger.info(f"   Пользователь: {SMTP_USERNAME}")
    logger.info(f"   Пароль: {'установлен' if SMTP_PASSWORD else 'НЕ установлен'}")
    logger.info(f"   From: {FROM_EMAIL}")
    logger.info(f"   Admin: {ADMIN_EMAIL}")
    
    if SMTP_USERNAME and SMTP_PASSWORD:
        # Тестируем SMTP соединение
        try:
            logger.info("🔧 Тестирование SMTP соединения...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: test_smtp_connection()
            )
            logger.info("✅ SMTP соединение успешно протестировано")
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования SMTP: {e}")
            logger.warning("⚠️ Email уведомления могут не работать")
    else:
        logger.warning("⚠️ SMTP не настроен. Email уведомления отключены.")
    
    # Ждем пока Kafka будет готов
    logger.info("⏳ Ожидание подключения к Kafka...")
    await health_check()
    
    try:
        await consume_events()
    except KeyboardInterrupt:
        logger.info("👋 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")

def test_smtp_connection():
    """
    Тестирует SMTP соединение
    """
    try:
        if SMTP_PORT == 465:
            # SSL для порта 465
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
        else:
            # TLS для порта 587
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
        return True
    except Exception as e:
        raise Exception(f"SMTP тестирование не удалось: {e}")

if __name__ == "__main__":
    asyncio.run(main())