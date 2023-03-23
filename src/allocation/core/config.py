from pydantic import BaseSettings


class AppSettings(BaseSettings):
    api_url: str
    api_port: int = 8000
    redis_url: str
    redis_port: int = 6379
    bus_init_need: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "app_"


class DatabaseSettings(BaseSettings):
    db_name: str
    user: str
    password: str
    host: str
    scheme: str
    port: int = 5432

    class Config:
        env_file = ".env"
        env_prefix = "postgres_"


db_settings = DatabaseSettings()
app_settings = AppSettings()


def get_postgres_uri():
    host = db_settings.host
    port = db_settings.port
    password = db_settings.password
    user = db_settings.user
    db_name = db_settings.db_name
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = app_settings.api_url
    port = app_settings.api_port
    return f"http://{host}:{port}"


def get_redis_host_and_port():
    host = app_settings.redis_url
    port = app_settings.redis_port
    return dict(host=host, port=port)
