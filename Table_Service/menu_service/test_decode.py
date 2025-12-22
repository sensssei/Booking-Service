import jwt
import os
import sys

# Установите переменные
os.environ['JWT_PUBLIC_KEY_PATH'] = '/app/public_key.pem'
os.environ['JWT_ALGORITHM'] = 'RS256'

JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "/app/public_key.pem")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

print(f"=== Тестирование декодирования JWT ===")
print(f"JWT_PUBLIC_KEY_PATH: {JWT_PUBLIC_KEY_PATH}")
print(f"JWT_ALGORITHM: {JWT_ALGORITHM}")

# Загрузите ключ
try:
    with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
        JWT_PUBLIC_KEY = f.read()
    print(f"✅ Ключ загружен, длина: {len(JWT_PUBLIC_KEY)}")
except Exception as e:
    print(f"❌ Ошибка загрузки ключа: {e}")
    sys.exit(1)

# Ваш токен
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjYzNzc3NTQsImlhdCI6MTc2NjM3MDU1NCwiaXNzIjoiYXV0aF9zZXJ2aWNlIiwiYXVkIjoicmVzdGF1cmFudF9zZXJ2aWNlcyJ9.ZrISyYKna4_BSYe_ADWlQYwNxNq6PFTVTHyguNFqLryPRqp-9bxG2aOdbved3zwSHyUIm7OyASEmj77RpKHTaCbaH8bhI1tphN-sbMkYX0J0miCGWmsZG9Uo92V0Ict-DFDEHVRgC-U1b1DlOi-Ob29hv2ktAAq767X4rTbFPSKpLbQz2lIXn-G6CLnyBnLULQHMTOOTvyqvhWHbkgBFG1ytragm6ivY0iElSe7SXlIOhzlfDwmuZBmPbwh9x-VRRNUtNJvkx0G_UHyYxs69NKtV946XjdCQHGT55UX4sLG5JpM96s2MJyXd0KzaeCnOR9xY-yNY7VSYwPM0yqkzhA"

print(f"\n=== Анализ токена ===")
try:
    header = jwt.get_unverified_header(token)
    print(f"Заголовок токена: {header}")
    print(f"Алгоритм в токене: {header.get('alg')}")
    print(f"Тип токена: {header.get('typ')}")
except Exception as e:
    print(f"❌ Ошибка чтения заголовка: {e}")

print(f"\n=== Тест 1: Декодирование с RS256 ===")
try:
    payload = jwt.decode(
        token,
        JWT_PUBLIC_KEY,
        algorithms=["RS256"],
        issuer="auth_service",
        audience="restaurant_services"
    )
    print(f"✅ Успешно с RS256!")
    print(f"   user_id: {payload.get('user_id')}")
    print(f"   role: {payload.get('role')}")
except jwt.InvalidAlgorithmError as e:
    print(f"❌ InvalidAlgorithmError: {e}")
except Exception as e:
    print(f"❌ Другая ошибка: {type(e).__name__}: {e}")

print(f"\n=== Тест 2: Декодирование с RS256 (без issuer/audience) ===")
try:
    payload = jwt.decode(
        token,
        JWT_PUBLIC_KEY,
        algorithms=["RS256"]
    )
    print(f"✅ Успешно с RS256 без issuer/audience!")
    print(f"   user_id: {payload.get('user_id')}")
    print(f"   role: {payload.get('role')}")
except Exception as e:
    print(f"❌ Ошибка: {type(e).__name__}: {e}")

print(f"\n=== Тест 3: Проверка доступных алгоритмов в PyJWT ===")
import jwt.algorithms as jwt_algorithms
print(f"Доступные алгоритмы: {jwt_algorithms.get_default_algorithms()}")

print(f"\n=== Тест 4: Проверка версии PyJWT ===")
print(f"PyJWT версия: {jwt.__version__}")