import mysql.connector
from config.settings import DB_CONFIG

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

