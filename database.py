import os
from datetime import datetime

import libsql
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    return libsql.connect(
        database=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )


def create_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_expense(user_id, username, amount, description):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses (user_id, username, amount, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, amount, description))

    conn.commit()
    conn.close()


def get_expenses():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, amount, description
        FROM expenses
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_balance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, SUM(amount)
        FROM expenses
        GROUP BY user_id, username
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def create_users_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, username)
        VALUES (?, ?)
    """, (user_id, username))

    conn.commit()
    conn.close()


def get_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username
        FROM users
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_settlement_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            users.user_id,
            users.username,
            COALESCE(SUM(expenses.amount), 0)
        FROM users
        LEFT JOIN expenses
        ON users.user_id = expenses.user_id
        GROUP BY users.user_id, users.username
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def clear_expenses():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses")

    conn.commit()
    conn.close()


def create_archive_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archive_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id TEXT,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


def archive_and_clear_expenses():
    conn = get_connection()
    cursor = conn.cursor()

    period_id = datetime.now().strftime("%d.%m.%Y %H:%M")

    cursor.execute("""
        SELECT user_id, username, amount, description
        FROM expenses
    """)

    expenses = cursor.fetchall()

    for user_id, username, amount, description in expenses:
        cursor.execute("""
            INSERT INTO archive_expenses
            (period_id, user_id, username, amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            period_id,
            user_id,
            username,
            amount,
            description
        ))

    cursor.execute("DELETE FROM expenses")

    conn.commit()
    conn.close()

    return period_id


def get_archive():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT period_id, username, amount, description
        FROM archive_expenses
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows

def clear_all_expense_data():
    conn = libsql.connect(
        database=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"]
    )

    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM archive_expenses")

    conn.commit()
    conn.close()