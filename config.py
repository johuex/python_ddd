# TODO переделать под использование с .env
def get_postgres_uri():
    host = "localhost"
    port = 5432
    password = "123456"
    user, db_name = "dev", "default"
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = "localhost"
    port = 8000
    return f"http://{host}:{port}"
