import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "prajwal",
    "database": "hospital_db",
    "port": 3306,
    "autocommit": False,
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
    return None

def run_query(sql, params=None, fetch=False):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.lastrowid
    except Error as e:
        conn.rollback()
        print(f"[QUERY ERROR] {e}")
        return None
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        print("Connected:", cur.fetchone()[0])
        conn.close()
