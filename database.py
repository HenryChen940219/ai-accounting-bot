import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "accounting.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                record_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                image_path TEXT
            )
        """)
        # 舊資料庫遷移：補上 image_path 欄位
        try:
            conn.execute("ALTER TABLE records ADD COLUMN image_path TEXT")
            conn.commit()
        except Exception:
            pass  # 欄位已存在，略過
        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (group_id, user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_owner TEXT NOT NULL,
                debtor_name TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                settled INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def upsert_group_member(group_id: str, user_id: str, display_name: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO group_members (group_id, user_id, display_name, updated_at)
            VALUES (?, ?, ?, ?)
        """, (group_id, user_id, display_name, now))
        conn.commit()


def get_group_members(group_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, display_name FROM group_members WHERE group_id = ? ORDER BY updated_at DESC",
            (group_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_unsettled_groups(owner_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT group_owner FROM group_debts
            WHERE settled = 0 AND group_owner = ?
        """, (owner_id,)).fetchall()
    return [dict(r) for r in rows]


def add_group_debts(owner_id: str, total: float, people: int, description: str, names: list[str]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    per_person = round(total / people)
    with get_conn() as conn:
        for name in names:
            conn.execute(
                "INSERT INTO group_debts (group_owner, debtor_name, amount, description, settled, created_at) VALUES (?, ?, ?, ?, 0, ?)",
                (owner_id, name, per_person, description, now)
            )
        conn.commit()


def get_group_debts(owner_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT debtor_name, SUM(amount) as total, MAX(created_at) as last_date
            FROM group_debts
            WHERE group_owner = ? AND settled = 0
            GROUP BY debtor_name
            ORDER BY total DESC
        """, (owner_id,)).fetchall()
    return [dict(r) for r in rows]


def settle_debt(owner_id: str, debtor_name: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE group_debts SET settled = 1 WHERE group_owner = ? AND debtor_name = ?",
            (owner_id, debtor_name)
        )
        conn.commit()


def get_aa_history(owner_id: str, limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT description, MAX(amount) as per_person, COUNT(*) as people_count, created_at
            FROM group_debts
            WHERE group_owner = ?
            GROUP BY description, created_at
            ORDER BY created_at DESC
            LIMIT ?
        """, (owner_id, limit)).fetchall()
    return [dict(r) for r in rows]


def delete_record(record_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()


def delete_group_aa_event(owner_id: str, description: str, created_at: str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM group_debts WHERE group_owner = ? AND description = ? AND created_at = ?",
            (owner_id, description, created_at)
        )
        conn.commit()


def get_group_member_debts(group_id: str) -> list[dict]:
    members = get_group_members(group_id)
    known_names = {m["display_name"] for m in members}
    result = []
    with get_conn() as conn:
        # 已知成員（曾傳過訊息）
        for m in members:
            row = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_debt
                FROM group_debts
                WHERE group_owner = ? AND debtor_name = ? AND settled = 0
            """, (group_id, m["display_name"])).fetchone()
            result.append({
                "user_id": m["user_id"],
                "display_name": m["display_name"],
                "total_debt": row["total_debt"] if row else 0
            })
        # 補上只在分帳紀錄裡出現（被 @提到）但未傳過訊息的人
        extra = conn.execute("""
            SELECT debtor_name,
                   COALESCE(SUM(CASE WHEN settled=0 THEN amount ELSE 0 END), 0) as total_debt
            FROM group_debts
            WHERE group_owner = ?
            GROUP BY debtor_name
        """, (group_id,)).fetchall()
        for row in extra:
            if row["debtor_name"] not in known_names:
                result.append({
                    "user_id": f"at_{row['debtor_name'][:20]}",
                    "display_name": row["debtor_name"],
                    "total_debt": row["total_debt"]
                })
    return result


def get_aa_event_detail(owner_id: str, description: str, created_at: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT debtor_name, amount, settled
            FROM group_debts
            WHERE group_owner = ? AND description = ? AND created_at = ?
            ORDER BY debtor_name
        """, (owner_id, description, created_at)).fetchall()
    return [dict(r) for r in rows]


def get_member_debt_detail(owner_id: str, debtor_name: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, description, amount, created_at
            FROM group_debts
            WHERE group_owner = ? AND debtor_name = ? AND settled = 0
            ORDER BY created_at DESC
        """, (owner_id, debtor_name)).fetchall()
    return [dict(r) for r in rows]


def add_record(user_id: str, amount: float, category: str, note: str, record_date: str = None, image_path: str = None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date = record_date or datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO records (user_id, amount, category, note, record_date, created_at, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, amount, category, note, date, now, image_path)
        )
        conn.commit()


def get_records(user_id: str, days: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM records
            WHERE user_id = ?
              AND record_date >= date('now', ? || ' days')
            ORDER BY record_date DESC, id DESC
        """, (user_id, f"-{days}")).fetchall()
    return [dict(r) for r in rows]


def get_daily(user_id: str, days: int = 14) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT record_date as date, SUM(amount) as total
            FROM records
            WHERE user_id = ?
              AND record_date >= date('now', ? || ' days')
              AND amount < 0
            GROUP BY record_date
            ORDER BY record_date ASC
        """, (user_id, f"-{days}")).fetchall()
    all_dates = {}
    for i in range(days):
        from datetime import timedelta
        d = (datetime.now() - timedelta(days=days-1-i)).strftime("%Y-%m-%d")
        all_dates[d] = 0.0
    for r in rows:
        all_dates[r["date"]] = r["total"]
    return [{"date": d, "total": v} for d, v in all_dates.items()]


def get_summary(user_id: str, days: int = 7) -> dict:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM records
            WHERE user_id = ?
              AND record_date >= date('now', ? || ' days')
            GROUP BY category
            ORDER BY total DESC
        """, (user_id, f"-{days}")).fetchall()
        total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM records
            WHERE user_id = ?
              AND record_date >= date('now', ? || ' days')
        """, (user_id, f"-{days}")).fetchone()["total"]
    return {
        "days": days,
        "total": total,
        "breakdown": [dict(r) for r in rows]
    }
