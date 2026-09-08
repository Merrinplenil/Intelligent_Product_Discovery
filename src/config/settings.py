import os

from dotenv import load_dotenv


load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(
            f"Missing required environment variable: {name}"
        )

    return value


# Groq
GROQ_API_KEY = get_required_env("GROQ_API_KEY")


# MySQL
MYSQL_HOST = get_required_env("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = get_required_env("MYSQL_DATABASE")
MYSQL_USER = get_required_env("MYSQL_USER")
MYSQL_PASSWORD = get_required_env("MYSQL_PASSWORD")