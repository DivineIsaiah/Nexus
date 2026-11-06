import mysql.connector
from config import DB_CONFIG


def get_db_connection():
    """
    Creates and returns a MySQL database connection.
    """
    connection = mysql.connector.connect(**DB_CONFIG)

    return connection