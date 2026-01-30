import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="Bloodbank",     # change if your DB name is different
        user="postgres",
        password="root"   # replace with your PostgreSQL password
    )
    return conn
