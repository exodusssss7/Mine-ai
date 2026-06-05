import os
import psycopg2
import time

def init_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set.")
        return

    if "sslmode=require" not in db_url:
        if "?" in db_url:
            db_url += "&sslmode=require"
        else:
            db_url += "?sslmode=require"

    max_retries = 10
    for i in range(max_retries):
        try:
            print(f"Attempting to connect to db (Attempt {i+1}/{max_retries})...")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            with open('schema.sql', 'r') as f:
                cur.execute(f.read())

            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Error initializing database: {e}")
            time.sleep(5)

    print("Failed to initialize database after multiple attempts.")

if __name__ == "__main__":
    init_db()
