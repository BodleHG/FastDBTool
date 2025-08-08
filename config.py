import os

class Config:
    # HOST = "Your Host"
    # PORT = "Your Port"
    # RELOAD = "Your Reload"
    # WORKERS = "Your Workers",
    # LIMIT_CONCURRENCY = "Your Limit Concurrency"
    
    HOST = "0.0.0.0"
    PORT = 28000
    RELOAD = True
    WORKERS = 8,
    LIMIT_CONCURRENCY = 1000
    
    # Database Connection Settings
    DB_HOST = "210.110.250.32"
    DB_PORT = 22465
    DB_USER = "sysailab612"
    DB_PASSWORD = "sysailab@612"
    DB_NAME = "profile"
    DB_MAX_CONNECTIONS = 10
    DB_CONNECTION_TIMEOUT = 30
    DB_READ_TIMEOUT = 30
    DB_WRITE_TIMEOUT = 30
    
    # Redis Connection Settings
    REDIS_HOST = "10.109.237.71"
    REDIS_PORT = 6379
    REDIS_PASSWORD = "sysailab@612"
    REDIS_CONNECTION_TIMEOUT = 10
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_HEALTH_CHECK_INTERVAL = 30
    
    # Cache Settings
    CACHE_DEFAULT_TTL = 30  # seconds
    CACHE_MAX_TTL = 3600    # 1 hour

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