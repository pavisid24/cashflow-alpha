import sqlite3
import pandas as pd
from pathlib import Path

DB = Path("cashflow_alpha.db")

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY, company TEXT, score INTEGER, classification TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def save_watchlist(symbol, company, score, classification):
    with sqlite3.connect(DB) as con:
        con.execute("INSERT OR REPLACE INTO watchlist(symbol,company,score,classification) VALUES(?,?,?,?)",
                    (symbol, company, int(score), classification))

def load_watchlist():
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query("SELECT * FROM watchlist ORDER BY score DESC", con)

def remove_watchlist(symbol):
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))
