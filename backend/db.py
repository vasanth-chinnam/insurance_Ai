import os
import sqlite3
import logging
import json
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ── Database backend detection ────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith("postgres")

DB_PATH = Path("data/insureai.db")  # SQLite fallback


def _pg_connect():
    """Create a PostgreSQL connection using psycopg2."""
    import psycopg2
    import psycopg2.extras
    url = DATABASE_URL
    # Supabase gives postgres:// but psycopg2 needs postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    conn = psycopg2.connect(url)
    conn.autocommit = False
    return conn


def _sqlite_to_pg_sql(sql: str) -> str:
    """
    Translate SQLite-flavour SQL into PostgreSQL-compatible SQL.
    - Replace ? placeholders with %s
    - Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
    - Replace INSERT OR REPLACE with INSERT ... ON CONFLICT ... DO UPDATE
    """
    # Replace placeholders
    translated = sql.replace("?", "%s")

    upper = translated.upper().strip()

    # INSERT OR IGNORE → ON CONFLICT DO NOTHING
    if "INSERT OR IGNORE" in upper:
        translated = translated.replace("INSERT OR IGNORE", "INSERT", 1)
        translated = translated.replace("insert or ignore", "INSERT", 1)
        translated = translated.replace("Insert Or Ignore", "INSERT", 1)
        # Append ON CONFLICT DO NOTHING before any trailing whitespace
        translated = translated.rstrip().rstrip(";")
        translated += " ON CONFLICT DO NOTHING"

    # INSERT OR REPLACE → use ON CONFLICT (primary key) DO UPDATE
    elif "INSERT OR REPLACE" in upper:
        translated = translated.replace("INSERT OR REPLACE", "INSERT", 1)
        translated = translated.replace("insert or replace", "INSERT", 1)
        translated = translated.replace("Insert Or Replace", "INSERT", 1)
        # Extract table name and columns for ON CONFLICT ... DO UPDATE
        translated = _build_upsert(translated)

    return translated


def _build_upsert(sql: str) -> str:
    """
    Convert a simple INSERT INTO <table> (cols...) VALUES (...) statement
    into PostgreSQL INSERT ... ON CONFLICT (pk) DO UPDATE SET col=EXCLUDED.col, ...
    """
    import re
    # Match: INSERT INTO tablename (col1, col2, ...) VALUES (...)
    match = re.match(
        r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
        sql.strip(),
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        # Fallback — can't parse, just return as-is
        return sql

    table = match.group(1)
    cols_str = match.group(2)
    vals_str = match.group(3)

    cols = [c.strip() for c in cols_str.split(",")]

    # Determine the primary key column (first column by convention in our schema)
    pk = cols[0]

    # Build SET clause for all non-PK columns
    update_cols = [c for c in cols if c != pk]
    if update_cols:
        set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
        conflict = f" ON CONFLICT ({pk}) DO UPDATE SET {set_clause}"
    else:
        conflict = f" ON CONFLICT ({pk}) DO NOTHING"

    return f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str}){conflict}"


class PgRowDict(dict):
    """Dict subclass that supports both dict[key] and dict['key'] access like sqlite3.Row."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


@contextmanager
def get_conn():
    """
    Yield a database connection.
    - If DATABASE_URL is set: PostgreSQL (Supabase)
    - Otherwise: local SQLite
    """
    if USE_POSTGRES:
        conn = _pg_connect()
        try:
            yield _PgConnWrapper(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class _PgConnWrapper:
    """
    Wraps a psycopg2 connection to provide an interface compatible with
    sqlite3.Connection: .execute(), .cursor(), etc., while translating SQL.
    """

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=None):
        translated = _sqlite_to_pg_sql(sql)
        import psycopg2.extras
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(translated, params or ())
        return _PgCursorWrapper(cur)

    def cursor(self):
        import psycopg2.extras
        return _PgCursorProxy(
            self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        )

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


class _PgCursorProxy:
    """Proxy around psycopg2 cursor that auto-translates SQL."""

    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql: str, params=None):
        translated = _sqlite_to_pg_sql(sql)
        self._cur.execute(translated, params or ())
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return PgRowDict(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [PgRowDict(r) for r in rows]


class _PgCursorWrapper:
    """Wraps a single execute result for .fetchone() / .fetchall() compat."""

    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return PgRowDict(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [PgRowDict(r) for r in rows]


# ── Schema initialisation ─────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist. Call this on startup."""
    if USE_POSTGRES:
        _init_pg()
    else:
        _init_sqlite()


def _init_sqlite():
    """SQLite schema — original behaviour."""
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT,
                phone       TEXT,
                password_hash TEXT,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        try:
            c.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                policy_id            TEXT PRIMARY KEY,
                user_id              TEXT NOT NULL,
                insurance_type       TEXT NOT NULL,
                provider             TEXT,
                sum_insured          REAL,
                annual_premium       REAL,
                years_with_provider  INTEGER DEFAULT 0,
                claim_free_years     INTEGER DEFAULT 0,
                created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id     TEXT PRIMARY KEY,
                policy_id    TEXT NOT NULL,
                amount       REAL,
                covered_amount REAL,
                status       TEXT DEFAULT 'pending',
                description  TEXT,
                claim_date   TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS fraud_checks (
                check_id     TEXT PRIMARY KEY,
                claim_id     TEXT NOT NULL,
                score        INTEGER,
                verdict      TEXT,
                reasons      TEXT,
                checked_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS risk_profiles (
                profile_id      TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                insurance_type  TEXT,
                score           INTEGER,
                category        TEXT,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS renewal_history (
                renewal_id   TEXT PRIMARY KEY,
                policy_id    TEXT NOT NULL,
                old_premium  REAL,
                new_premium  REAL,
                savings      REAL,
                new_provider TEXT,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
            )
        """)

        logger.info("SQLite database initialized at %s", DB_PATH)


def _init_pg():
    """PostgreSQL schema — Supabase compatible."""
    conn = _pg_connect()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT,
                phone         TEXT,
                password_hash TEXT,
                created_at    TIMESTAMP DEFAULT NOW()
            )
        """)

        # Safe column migration
        cur.execute("""
            DO $$
            BEGIN
                ALTER TABLE users ADD COLUMN password_hash TEXT;
            EXCEPTION WHEN duplicate_column THEN
                NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                policy_id            TEXT PRIMARY KEY,
                user_id              TEXT NOT NULL REFERENCES users(user_id),
                insurance_type       TEXT NOT NULL,
                provider             TEXT,
                sum_insured          DOUBLE PRECISION,
                annual_premium       DOUBLE PRECISION,
                years_with_provider  INTEGER DEFAULT 0,
                claim_free_years     INTEGER DEFAULT 0,
                created_at           TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id       TEXT PRIMARY KEY,
                policy_id      TEXT NOT NULL REFERENCES policies(policy_id),
                amount         DOUBLE PRECISION,
                covered_amount DOUBLE PRECISION,
                status         TEXT DEFAULT 'pending',
                description    TEXT,
                claim_date     TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fraud_checks (
                check_id     TEXT PRIMARY KEY,
                claim_id     TEXT NOT NULL REFERENCES claims(claim_id),
                score        INTEGER,
                verdict      TEXT,
                reasons      TEXT,
                checked_at   TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS risk_profiles (
                profile_id      TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(user_id),
                insurance_type  TEXT,
                score           INTEGER,
                category        TEXT,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS renewal_history (
                renewal_id   TEXT PRIMARY KEY,
                policy_id    TEXT NOT NULL REFERENCES policies(policy_id),
                old_premium  DOUBLE PRECISION,
                new_premium  DOUBLE PRECISION,
                savings      DOUBLE PRECISION,
                new_provider TEXT,
                created_at   TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        logger.info("PostgreSQL database initialized (Supabase)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Write helpers ──────────────────────────────────────────────────────

def create_user(user_id: str, name: str, email: str = "", phone: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name, email, phone) VALUES (?, ?, ?, ?)",
            (user_id, name, email, phone)
        )


def create_policy(
    policy_id: str, user_id: str, insurance_type: str,
    provider: str = "", sum_insured: float = 0,
    annual_premium: float = 0, years_with_provider: int = 0,
    claim_free_years: int = 0,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO policies
            (policy_id, user_id, insurance_type, provider, sum_insured,
             annual_premium, years_with_provider, claim_free_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (policy_id, user_id, insurance_type, provider, sum_insured,
              annual_premium, years_with_provider, claim_free_years))


def save_claim(
    claim_id: str, policy_id: str, amount: float,
    covered_amount: float = 0, status: str = "pending",
    description: str = "",
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO claims
            (claim_id, policy_id, amount, covered_amount, status, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (claim_id, policy_id, amount, covered_amount, status, description))


def save_fraud_check(
    check_id: str, claim_id: str, score: int,
    verdict: str, reasons: list[str] = None,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO fraud_checks
            (check_id, claim_id, score, verdict, reasons)
            VALUES (?, ?, ?, ?, ?)
        """, (check_id, claim_id, score, verdict, json.dumps(reasons or [])))


def save_risk_profile(
    profile_id: str, user_id: str, insurance_type: str,
    score: int, category: str,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO risk_profiles
            (profile_id, user_id, insurance_type, score, category)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, user_id, insurance_type, score, category))


def save_renewal(
    renewal_id: str, policy_id: str, old_premium: float,
    new_premium: float, savings: float, new_provider: str,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO renewal_history
            (renewal_id, policy_id, old_premium, new_premium, savings, new_provider)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (renewal_id, policy_id, old_premium, new_premium, savings, new_provider))


# ── Read helpers ───────────────────────────────────────────────────────

def get_policy_by_number(policy_number: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM policies WHERE policy_id = ?", (policy_number,)
        ).fetchone()
        return dict(row) if row else None


def get_claims_for_policy(policy_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM claims WHERE policy_id = ? ORDER BY claim_date DESC",
            (policy_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_user_context(user_id: str | None = None, policy_number: str | None = None) -> dict:
    """
    THE key function — returns everything known about a user/policy
    so every agent (fraud, risk, renewal) can use REAL history
    instead of hardcoded defaults.
    """
    with get_conn() as conn:
        policy = None
        if policy_number:
            row = conn.execute(
                "SELECT * FROM policies WHERE policy_id = ?", (policy_number,)
            ).fetchone()
            policy = dict(row) if row else None
            if policy:
                user_id = policy["user_id"]

        user = None
        if user_id:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            user = dict(row) if row else None

        claims = []
        if policy:
            rows = conn.execute(
                "SELECT * FROM claims WHERE policy_id = ? ORDER BY claim_date DESC",
                (policy["policy_id"],)
            ).fetchall()
            claims = [dict(r) for r in rows]

        risk_profile = None
        if user_id:
            row = conn.execute(
                "SELECT * FROM risk_profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            risk_profile = dict(row) if row else None

        fraud_checks = []
        for claim in claims:
            rows = conn.execute(
                "SELECT * FROM fraud_checks WHERE claim_id = ?",
                (claim["claim_id"],)
            ).fetchall()
            fraud_checks.extend([dict(r) for r in rows])

        return {
            "user":           user,
            "policy":         policy,
            "claims":         claims,
            "previous_claims_count": len(claims),
            "risk_profile":   risk_profile,
            "fraud_checks":   fraud_checks,
        }
