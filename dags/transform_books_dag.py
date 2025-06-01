from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pandas as pd
import pyodbc

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

server = 'yourservername'
database = 'yourdbname'
username = 'yourusername'
password = 'yourpassword'
driver = '{ODBC Driver 17 for SQL Server}'


def transform_books_data():
    conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = conn.cursor()

    # Load books data
    df = pd.read_sql("SELECT * FROM books", con=conn)

    print("Problematic rating values:")
    print(df[~df['averageRating'].apply(lambda x: isinstance(x, (int, float)))])
    df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')  # Converts invalid entries to NaN
    df['averageRating'] = df['averageRating'].fillna(0.0)
    # Transform
    df = df.dropna(subset=['title', 'authors'])
    df['title'] = df['title'].str.title()
    df['authors'] = df['authors'].str.title()
    df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')
    df['averageRating'].fillna(df['averageRating'].mean(), inplace=True)

    # Create output table if not exists
    cursor.execute("""
        IF OBJECT_ID('books_transformed', 'U') IS NULL
        CREATE TABLE books_transformed (
            id NVARCHAR(255),
            title NVARCHAR(MAX),
            authors NVARCHAR(MAX),
            genre NVARCHAR(255),
            publishedDate NVARCHAR(255),
            description NVARCHAR(MAX),
            averageRating FLOAT
        )
    """)
    conn.commit()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO books_transformed (id, title, authors, genre, publishedDate, description, averageRating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, row['id'], row['title'], row['authors'], row['genre'], row['publishedDate'], row['description'], row['averageRating'])

    conn.commit()
    cursor.close()
    conn.close()

with DAG(
    dag_id='transform_books_data',
    default_args=default_args,
    description='Transform books data and store in a new table',
    schedule_interval=None,
    start_date=datetime(2025, 5, 14),
    catchup=False,
    tags=['books', 'transformation'],
) as dag:

    transform_task = PythonOperator(
        task_id='transform_books',
        python_callable=transform_books_data
    )

    transform_task
