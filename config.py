import os

class Config:
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))
    RELOAD = os.getenv("RELOAD")
    WORKERS = int(os.getenv("WORKERS"))
    LIMIT_CONCURRENCY = os.getenv("LIMIT_CONCURRENCY")

    # Database Connection Settings
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS"))
    DB_CONNECTION_TIMEOUT = int(os.getenv("DB_CONNECTION_TIMEOUT"))
    DB_READ_TIMEOUT = int(os.getenv("DB_READ_TIMEOUT"))
    DB_WRITE_TIMEOUT = int(os.getenv("DB_WRITE_TIMEOUT"))

    # Redis Connection Settings
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_CONNECTION_TIMEOUT = int(os.getenv("REDIS_CONNECTION_TIMEOUT"))
    REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT"))
    REDIS_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL"))

    # Cache Settings
    CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL"))
    CACHE_MAX_TTL = int(os.getenv("CACHE_MAX_TTL"))

config = Config()

instance_config_path = os.path.join(os.path.dirname(__file__), 'instance', 'config.py')
if os.path.exists(instance_config_path):
    instance_config = {}
    with open(instance_config_path) as f:
        exec(f.read(), instance_config)

    # instance_config에서 Config의 속성을 오버라이드
    for key, value in instance_config.items():
        if hasattr(config, key):
            setattr(config, key, value)