import psycopg2
import os

DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS boxes(
id SERIAL PRIMARY KEY,
nombre TEXT,
tipo TEXT,
canal_id BIGINT,
dueno_id BIGINT,
staff_id BIGINT,
miembros TEXT,
inicio TIMESTAMP,
fin TIMESTAMP
)
""")

conn.commit()