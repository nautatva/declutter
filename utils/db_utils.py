import sqlite3
from flask import g

def get_raw_db():
    return sqlite3.connect('photo_manager.db')

def close_db_sqlite(db):
    db.close()

def get_db():
    if 'db' not in g:
        g.db = get_raw_db()
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        close_db_sqlite(db)
