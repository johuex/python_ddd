from pydantic import BaseSettings


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


def get_postgres_uri():
    host = db_settings.host
    port = db_settings.port
    password = db_settings.password
    user = db_settings.user
    db_name = db_settings.db_name
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = "localhost"
    port = 8000
    return f"http://{host}:{port}"
