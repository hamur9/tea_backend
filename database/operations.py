import mysql.connector
from config import Config
from datetime import datetime, timedelta
from mysql.connector import Error
import subprocess

def start_mysql_server():
    try:
        result = subprocess.run(["brew", "services", "start", "mysql"], capture_output=True, text=True)
        if result.returncode == 0:
            print("MySQL-сервер успешно запущен.")
            print(result.stdout)
        else:
            print("Ошибка при запуске MySQL-сервера:")
            print(result.stderr)
    except Exception as e:
        print(f"Ошибка: {e}")

def stop_mysql_server():
    try:
        result = subprocess.run(["brew", "services", "stop", "mysql"], capture_output=True, text=True)
        if result.returncode == 0:
            print("MySQL-сервер успешно остановлен.")
            print(result.stdout)
        else:
            print("Ошибка при остановке MySQL-сервер:")
            print(result.stderr)
    except Exception as e:
        print(f"Ошибка: {e}")

def get_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

def create_database(connection):
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        print(f"База данных '{Config.MYSQL_DB}' успешно создана или уже существует.")
    except Error as err:
        print(f"Ошибка при создании базы данных: {err}")

def init_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            leaves INT DEFAULT 0,
            `rank` INT DEFAULT 0,
            xp INT DEFAULT 50,
            lvl INT DEFAULT 1,
            daily_reward_timer DATETIME DEFAULT NULL,
            clan TEXT DEFAULT NULL,
            rewards INT DEFAULT 0,
            achievements TEXT DEFAULT NULL,
            wheel DATETIME DEFAULT NULL,
            avatar INT DEFAULT 0
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def start_db():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        print("Подключение к MySQL-серверу успешно установлено.")
        create_database(connection)
        connection.close()
        connection = get_connection()
        print("Подключение к базе данных успешно установлено.")
        init_table()
        connection.close()
    except Error as err:
        print(f"Ошибка: {err}")

def get_account(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, leaves, `rank`, xp, lvl, daily_reward_timer, clan, rewards, achievements, wheel, avatar FROM accounts WHERE username = %s", (username,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    return account

def create_account(username, leaves=0, rank=0, xp=50, lvl=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
    if cursor.fetchall():
        conn.commit()
        cursor.close()
        return False
    else:
        cursor.execute("INSERT INTO accounts (username, leaves, `rank`, xp, lvl) VALUES (%s, %s, %s, %s, %s)", (username, leaves, rank, xp, lvl))
        conn.commit()
        cursor.close()
        return True

def update_account_leaves(username, leaves_increment):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET leaves = leaves + %s WHERE username = %s", (leaves_increment, username))
    conn.commit()
    cursor.close()
    conn.close()

def recalc_user_rank(username):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM accounts WHERE leaves > (SELECT leaves FROM accounts WHERE username = %s)"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    rank = result[0] + 1
    cursor.execute("UPDATE accounts SET `rank` = %s WHERE username = %s", (rank, username))
    conn.commit()
    cursor.close()
    conn.close()
    return rank

def set_daily_reward_timer_operation(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT daily_reward_timer FROM accounts WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if not result:
            return 1
        timer_end = result['daily_reward_timer']
        current_time = datetime.utcnow()  # Use UTC
        if timer_end is None or (current_time - timer_end) >= timedelta(hours=24):
            new_timer_end = current_time
            update_query = "UPDATE accounts SET daily_reward_timer = %s WHERE username = %s"
            cursor.execute(update_query, (new_timer_end, username))
            conn.commit()
            cursor.close()
            conn.close()
            return 0
        else:
            cursor.close()
            conn.close()
            return 2
    except Exception as e:
        return e

def set_wheel_timer_operation(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT wheel FROM accounts WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if not result:
            return 1
        last_spin_time = result['wheel']
        current_time = datetime.utcnow()  # Use UTC
        if last_spin_time is None or (current_time - last_spin_time) >= timedelta(minutes=30):
            update_query = "UPDATE accounts SET wheel = %s WHERE username = %s"
            cursor.execute(update_query, (current_time, username))
            conn.commit()
            cursor.close()
            conn.close()
            return 0
        else:
            cursor.close()
            conn.close()
            return 2
    except Exception as e:
        return e

def set_avatar_event(username, avatar_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET avatar = %s WHERE username = %s", (avatar_id, username))
    conn.commit()
    cursor.close()
    conn.close()

def xp_update(username, xp):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT xp FROM accounts WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    current_xp = result['xp'] if result and 'xp' in result else 0
    new_level = (current_xp + xp) // 1000 + 1
    update_query = """
    UPDATE accounts
    SET xp = xp + %s,
        lvl = %s
    WHERE username = %s
    """
    values = (xp, new_level, username)
    cursor.execute(update_query, values)
    conn.commit()
    cursor.close()
    conn.close()

def players_leaderboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
            SELECT username, leaves, clan
            FROM accounts
            ORDER BY leaves DESC
            LIMIT 20
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data
