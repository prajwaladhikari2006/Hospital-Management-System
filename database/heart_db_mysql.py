import hashlib
import mysql.connector
from mysql.connector import Error
from database.db_connection import DB_CONFIG

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
def _conn(): return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heart_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            email VARCHAR(120),
            role ENUM('user','admin') DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heart_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            age INT, sex INT, cp INT, trestbps INT, chol INT,
            fbs INT, restecg INT, thalach INT, exang INT,
            oldpeak FLOAT, slope INT, ca INT, thal INT,
            prediction VARCHAR(60), confidence FLOAT,
            predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES heart_users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """)
    conn.commit()
    cur.execute("SELECT id FROM heart_users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO heart_users (username,password,email,role) VALUES (%s,%s,%s,%s)",
            ("admin", _hash("admin123"), "admin@hospital.com", "admin")
        )
        conn.commit()
    cur.close(); conn.close()

def register_user(username, password, email=""):
    conn = _conn(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO heart_users (username,password,email,role) VALUES (%s,%s,%s,'user')",
            (username.strip(), _hash(password), email.strip())
        )
        conn.commit()
        return True, "Registration successful!"
    except mysql.connector.IntegrityError:
        return False, "Username already exists."
    except Error as e:
        return False, f"Database error: {e}"
    finally:
        cur.close(); conn.close()

def login_user(username, password):
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT * FROM heart_users WHERE username=%s AND password=%s",
            (username.strip(), _hash(password))
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close(); conn.close()

def save_prediction(user_id, inputs, prediction, confidence):
    conn = _conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO heart_predictions
            (user_id,age,sex,cp,trestbps,chol,fbs,restecg,
             thalach,exang,oldpeak,slope,ca,thal,prediction,confidence)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (user_id, inputs["age"], inputs["sex"], inputs["cp"],
              inputs["trestbps"], inputs["chol"], inputs["fbs"],
              inputs["restecg"], inputs["thalach"], inputs["exang"],
              inputs["oldpeak"], inputs["slope"], inputs["ca"],
              inputs["thal"], prediction, confidence))
        conn.commit()
    finally:
        cur.close(); conn.close()

def get_user_predictions(user_id):
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT * FROM heart_predictions WHERE user_id=%s ORDER BY predicted_at DESC",
            (user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

def get_all_predictions():
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT p.*, u.username FROM heart_predictions p
            JOIN heart_users u ON p.user_id=u.id
            ORDER BY p.predicted_at DESC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

def get_all_users():
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,username,email,role,created_at FROM heart_users ORDER BY id")
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()
