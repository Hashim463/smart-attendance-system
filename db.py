import mysql.connector
from mysql.connector import pooling
from config import Config

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="attendance_pool",
            pool_size=5,
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
        )
    return _pool

def get_connection():
    return get_pool().get_connection()

def query(sql, params=None, fetch=False, fetchone=False, commit=False):
    """Small helper to avoid repeating boilerplate everywhere."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        if commit:
            conn.commit()
            result = cursor.lastrowid
        return result
    finally:
        cursor.close()
        conn.close()