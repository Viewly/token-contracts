import sqlite3
from utils import script_source_dir


def init_db(db_path):
    with sqlite3.connect(db_path) as conn:
        db_schema_path = script_source_dir() / 'schema.sql'
        schema = open(db_schema_path, 'r').read()
        conn.executescript(schema)

def import_txs(db_path, txs: dict):
    """ Import pending transactions into their own SQLite database."""
    q = """
    INSERT INTO txs (recipient, amount, bucket)
    VALUES (:recipient, :amount, :bucket)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany(q, txs)
