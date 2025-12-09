import mysql.connector
from flask import g

# Database configuration
# UPDATE THESE VALUES WITH YOUR LOCAL MYSQL CONFIGURATION
DB_CONFIG = {
    'user': 'root',
    'password': 'root',  # Change this to your MySQL password
    'host': 'localhost',
    'database': 'flytau',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
        # Disable ONLY_FULL_GROUP_BY to allow non-aggregated columns in SELECT list
        cursor = g.db.cursor()
        cursor.execute("SET sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''))")
        cursor.close()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query, args)
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        db.rollback()
        raise e
    finally:
        cursor.close()
