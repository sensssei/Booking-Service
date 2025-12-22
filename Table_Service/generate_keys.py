import os
import sys
import shutil
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_keys():
    """Генерирует RSA ключи для JWT с RS256 и копирует в сервисы"""
    
    print("🔑 Генерация RSA ключей для JWT...")
    
    try:
        # Проверяем существование .env файла
        if not os.path.exists('.env'):
            print("❌ Ошибка: Файл .env не найден!")
            print("   Создайте .env файл с настройками")
            return False
        
        # Читаем текущий .env
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Проверяем и удаляем старые файлы/директории
        key_files = ['private_key.pem', 'public_key.pem']
        for key_file in key_files:
            if os.path.exists(key_file):
                if os.path.isdir(key_file):
                    print(f"⚠️  Удаляю директорию: {key_file}")
                    shutil.rmtree(key_file)
                else:
                    print(f"⚠️  Удаляю старый файл: {key_file}")
                    os.remove(key_file)
        
        # Генерируем приватный ключ
        print("   Генерация приватного ключа...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Получаем публичный ключ
        print("   Генерация публичного ключа...")
        public_key = private_key.public_key()
        
        # Сериализуем приватный ключ
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Сериализуем публичный ключ
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Записываем в файлы (бинарный режим!)
        print("   Сохранение ключей...")
        with open('private_key.pem', 'wb') as f:
            f.write(private_pem)
        
        with open('public_key.pem', 'wb') as f:
            f.write(public_pem)
        
        # Проверяем что файлы созданы
        print("\n✅ Ключи успешно сгенерированы:")
        
        for key_file in key_files:
            if os.path.exists(key_file) and os.path.isfile(key_file):
                size = os.path.getsize(key_file)
                print(f"   📄 {key_file}: {size} байт")
            else:
                print(f"   ❌ {key_file}: ОШИБКА - не создан!")
                return False
        
        # КОПИРУЕМ КЛЮЧИ В СЕРВИСЫ
        print("\n📁 Копирование ключей в сервисы...")
        
        # Директории сервисов
        services = ['auth_service', 'menu_service', 'reservation_service']
        
        for service in services:
            if os.path.exists(service):
                # Для auth_service нужны оба ключа
                if service == 'auth_service':
                    shutil.copy('private_key.pem', os.path.join(service, 'private_key.pem'))
                    shutil.copy('public_key.pem', os.path.join(service, 'public_key.pem'))
                    print(f"   ✅ {service}: private_key.pem, public_key.pem")
                else:
                    # Для остальных только публичный ключ
                    shutil.copy('public_key.pem', os.path.join(service, 'public_key.pem'))
                    print(f"   ✅ {service}: public_key.pem")
            else:
                print(f"   ⚠️  {service}: директория не найдена")
        
        # Обновляем .env чтобы использовать RS256
        print("\n📝 Обновление .env файла для RS256...")
        
        # Убедимся что в .env установлен RS256
        if 'JWT_ALGORITHM=RS256' not in env_content:
            # Заменяем HS256 на RS256 если нужно
            env_content = env_content.replace('JWT_ALGORITHM=HS256', 'JWT_ALGORITHM=RS256')
            env_content = env_content.replace('JWT_ALGORITHM = HS256', 'JWT_ALGORITHM=RS256')
            
            # Добавляем если нет
            if 'JWT_ALGORITHM' not in env_content:
                env_content += '\nJWT_ALGORITHM=RS256'
        
        # Добавляем пути к ключам если их нет
        if 'JWT_PRIVATE_KEY_PATH' not in env_content:
            env_content += '\nJWT_PRIVATE_KEY_PATH=private_key.pem'
        
        if 'JWT_PUBLIC_KEY_PATH' not in env_content:
            env_content += '\nJWT_PUBLIC_KEY_PATH=public_key.pem'
        
        # Сохраняем обновленный .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env файл обновлен для работы с RS256")
        
        # Создаем .env.example
        print("\n📝 Создание .env.example (без паролей)...")
        
        # Маскируем чувствительные данные
        example_content = env_content
        
        # Маскируем пароли
        sensitive_keys = [
            'SMTP_PASSWORD',
            'JWT_SECRET',
            'POSTGRES_PASSWORD_AUTH',
            'POSTGRES_PASSWORD_MENU', 
            'POSTGRES_PASSWORD_RESERVATION',
            'DEFAULT_ADMIN_PASSWORD'
        ]
        
        for key in sensitive_keys:
            patterns = [f'{key}=', f'{key} =']
            for pattern in patterns:
                if pattern in example_content:
                    start_idx = example_content.find(pattern) + len(pattern)
                    end_idx = example_content.find('\n', start_idx)
                    if end_idx == -1:
                        end_idx = len(example_content)
                    
                    old_value = example_content[start_idx:end_idx]
                    example_content = example_content.replace(
                        f'{pattern}{old_value}',
                        f'{pattern}YOUR_{key}_HERE'
                    )
        
        example_content = "# .env.example\n# Копируйте в .env и заполните своими значениями\n\n" + example_content
        
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        print("✅ Создан .env.example")
        
        print("\n" + "=" * 50)
        print("🎉 Ключи успешно созданы и скопированы в сервисы!")
        print("\n📋 Инструкция:")
        print("   1. Убедитесь что в .env установлено: JWT_ALGORITHM=RS256")
        print("   2. Пересоберите образы: docker-compose build --no-cache")
        print("   3. Запустите: docker-compose up -d")
        print("   4. Проверьте: docker-compose logs auth_service")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при генерации ключей: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_env_file():
    """Проверяет наличие и содержание .env файла"""
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("\nСоздайте .env файл с настройками или выполните:")
        print("cp .env.example .env")
        print("# затем отредактируйте .env")
        return False
    
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ Файл .env найден")
    
    # Проверяем JWT алгоритм
    if 'JWT_ALGORITHM=RS256' in content or 'JWT_ALGORITHM = RS256' in content:
        print("   ✓ JWT_ALGORITHM=RS256")
    else:
        print("   ⚠️  JWT_ALGORITHM не RS256, будет использоваться HS256")
    
    return True

if __name__ == "__main__":
    print("🛠️  Генератор RSA ключей для Restaurant Booking System")
    print("=" * 50)
    
    # Проверяем .env файл
    if not check_env_file():
        response = input("\nПродолжить без .env? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Генерируем ключи
    success = generate_keys()
    
    if not success:
        print("\n⚠️  Если не удалось сгенерировать RSA ключи,")
        print("   используйте HS256:")
        print("\n   В .env установите:")
        print("   JWT_ALGORITHM=HS256")
        print("   JWT_SECRET=very_strong_secret_key_here")
    
    if os.name == 'nt':
        input("\nНажмите Enter для выхода...")