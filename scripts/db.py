import sqlite3
from utils import script_source_dir


def init_db(db_path):
    with sqlite3.connect(db_path) as conn:
        db_schema_path = script_source_dir() / 'sql' / 'txs_schema.sql'
        schema = open(db_schema_path, 'r').read()
        conn.executescript(schema)

def import_txs(db_path, txs: dict):
    """ Import pending transactions into their own SQLite database."""
    q = """
    INSERT INTO txs (name, recipient, amount, bucket)
    VALUES (:name, :recipient, :amount, :bucket)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany(q, txs)

def query_all(db_path, query):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query)
        return cur.fetchall()

def update_txid(db_path, id_, txid):
    q = """
    UPDATE txs SET txid = :txid WHERE id = :id
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(q, {'id': id_, 'txid': txid})
        conn.commit()

def mark_tx_as_successful(db_path, id_):
    q = """
    UPDATE txs SET success = 1 WHERE id = :id
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(q, {'id': id_})
        conn.commit()

def mark_tx_for_retry(db_path, id_):
    q = """
    UPDATE txs SET success = 0, txid = NULL WHERE id = :id
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(q, {'id': id_})
        conn.commit()
