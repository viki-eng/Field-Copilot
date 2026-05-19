"""
SQLite-backed visit outcome logger.
Stores rep visit results and exposes conversion rate queries.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "outcomes.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visit_outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rep_id      TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    visit_date  TEXT NOT NULL,
    outcome     TEXT NOT NULL CHECK(outcome IN ('sale','no_purchase','follow_up')),
    products_sold TEXT,
    qty_sold    INTEGER DEFAULT 0,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with _db() as conn:
        conn.executescript(_SCHEMA)


def log_outcome(
    rep_id: str,
    entity_id: str,
    visit_date: str,
    outcome: str,
    products_sold: Optional[List[str]] = None,
    qty_sold: int = 0,
    notes: str = "",
) -> int:
    """Insert a visit outcome. Returns new row id."""
    import json
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO visit_outcomes
               (rep_id, entity_id, visit_date, outcome, products_sold, qty_sold, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (rep_id, entity_id, visit_date, outcome,
             json.dumps(products_sold or []), qty_sold, notes),
        )
        return cur.lastrowid


def get_conversion_rate(territory_id: str = None, weeks: int = 4) -> dict:
    """Return conversion rate for a territory (or global) over last N weeks."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(weeks=weeks)
    with _db() as conn:
        rows = conn.execute(
            "SELECT outcome, COUNT(*) as cnt FROM visit_outcomes "
            "WHERE visit_date >= ? GROUP BY outcome",
            (cutoff.isoformat(),),
        ).fetchall()
    total = sum(r["cnt"] for r in rows)
    sales = sum(r["cnt"] for r in rows if r["outcome"] == "sale")
    return {
        "total_visits": total,
        "sales": sales,
        "conversion_rate": round(sales / total, 3) if total else 0.0,
        "breakdown": {r["outcome"]: r["cnt"] for r in rows},
    }
