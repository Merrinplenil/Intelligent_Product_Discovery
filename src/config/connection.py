import logging

import mysql.connector

from src.config.settings import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


logger = logging.getLogger(__name__)


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
        )

        logger.info("MySQL connection established.")
        return connection

    except mysql.connector.Error as error:
        logger.error("MySQL connection failed: %s", error)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    connection = get_connection()

    if connection.is_connected():
        print("Database connection successful.")
        connection.close()