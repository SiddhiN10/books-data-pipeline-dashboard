import requests
import pyodbc
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Azure SQL Connection parameters (replace with Airflow connection if needed)
server = 'openlibraryserver.database.windows.net'
database = 'openlibrarydb'
username = 'openadmin'
password = 'IllumiHisoka@1302'
driver = '{ODBC Driver 17 for SQL Server}'


genres = ["romance", "fantasy", "thriller", "mystery", "science fiction"]

def fetch_and_insert_books():
    conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = conn.cursor()

    total_inserted = 0

    for genre in genres:
        print(f"Fetching genre: {genre}")
        url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{genre}&maxResults=40"
        response = requests.get(url)
        books = response.json().get("items", [])
        print(f"  → Found {len(books)} books")

        for book in books:
            volume_info = book.get("volumeInfo", {})
            book_id = book.get("id")
            title = volume_info.get("title")
            authors = ", ".join(volume_info.get("authors", []))
            publishedDate = volume_info.get("publishedDate")
            description = volume_info.get("description", "")
            rating = volume_info.get("averageRating", None)

            if not book_id or not title:
                continue  # skip incomplete records

            try:
                cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM books WHERE id = ?)
                INSERT INTO books (id, title, authors, genre, publishedDate, description, averageRating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, book_id, book_id, title, authors, genre, publishedDate, description, rating)
                total_inserted += 1
            except Exception as e:
                print(f"  ✘ Failed to insert book '{title}': {e}")
                continue

            cursor.execute("SELECT 1 FROM library WHERE id = ?", (book_id,))
            if cursor.fetchone():
                print(f"Book '{title}' already exists. Skipping...")
                continue

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Total books inserted: {total_inserted}")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 5, 13),
    'retries': 1,
}

with DAG('google_books_to_sql',
         default_args=default_args,
         schedule_interval='@daily',
         catchup=False) as dag:

    extract_and_load = PythonOperator(
        task_id='fetch_books_from_google_api',
        python_callable=fetch_and_insert_books
    )
