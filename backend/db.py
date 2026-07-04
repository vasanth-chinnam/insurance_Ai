import os
import uuid
import sqlite3
import logging
import json
import contextvars
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ── Multi-Tenant Constants ────────────────────────────────────────────
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

# ContextVar to store request-scoped tenant_id
tenant_context = contextvars.ContextVar("tenant_id", default=DEFAULT_TENANT_ID)

# ── Database backend detection ────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith("postgres")

DB_PATH = Path("data/insureai.db")  # SQLite fallback


def _pg_connect():
    """Create a PostgreSQL connection using psycopg2."""
    import psycopg2
    import psycopg2.extras
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    
    url = DATABASE_URL
    # Supabase gives postgres:// but psycopg2 needs postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
        
    # Clean pgbouncer parameter to prevent psycopg2 from throwing DSN parsing errors
    try:
        parsed = urlparse(url)
        qparams = dict(parse_qsl(parsed.query))
        if "pgbouncer" in qparams:
            qparams.pop("pgbouncer", None)
            new_query = urlencode(qparams)
            url = urlunparse(parsed._replace(query=new_query))
    except Exception as parse_err:
        logger.warning("Could not parse or clean DATABASE_URL: %s", parse_err)
        
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

def seed_default_users(conn):
    """Seed default users for all RBAC roles in the default tenant."""
    pwd_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"  # password123
    default_users = [
        ("U-ADMIN-999", "System Admin", "admin@insureai.com", "admin", pwd_hash),
        ("U-MANAGER-999", "System Manager", "manager@insureai.com", "manager", pwd_hash),
        ("U-AGENT-999", "System Agent", "agent@insureai.com", "agent", pwd_hash),
        ("U-INVEST-999", "System Investigator", "investigator@insureai.com", "fraud_investigator", pwd_hash),
        ("U-CUST-999", "System Customer", "customer@insureai.com", "customer", pwd_hash),
    ]
    cur = conn.cursor()
    for uid, name, email, role, phash in default_users:
        cur.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,))
        if not cur.fetchone():
            cur.execute("SELECT 1 FROM users WHERE LOWER(email) = ?", (email.lower(),))
            if not cur.fetchone():
                conn.execute(
                    "INSERT INTO users (user_id, name, email, phone, password_hash, role, tenant_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, name, email, "", phash, role, DEFAULT_TENANT_ID)
                )

def init_db():
    """Create all tables if they don't exist. Call this on startup."""
    if USE_POSTGRES:
        _init_pg()
    else:
        _init_sqlite()


def _init_sqlite():
    """SQLite schema — with multi-tenant support."""
    with get_conn() as conn:
        c = conn.cursor()

        # Create tenants table
        c.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                logo_url      TEXT,
                primary_color TEXT DEFAULT '#2563EB',
                domain        TEXT UNIQUE,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed default tenant
        c.execute("""
            INSERT OR IGNORE INTO tenants (id, name, primary_color)
            VALUES (?, 'InsureAI Default', '#2563EB')
        """, (DEFAULT_TENANT_ID,))

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT,
                phone         TEXT,
                password_hash TEXT,
                role          TEXT DEFAULT 'customer',
                tenant_id     TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)

        # Add columns if migrating existing SQLite DB
        for col, col_type in [("password_hash", "TEXT"), ("role", "TEXT DEFAULT 'customer'"), ("tenant_id", "TEXT")]:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
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
                tenant_id            TEXT,
                created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE policies ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id       TEXT PRIMARY KEY,
                policy_id      TEXT NOT NULL,
                amount         REAL,
                covered_amount REAL,
                status         TEXT DEFAULT 'pending',
                description    TEXT,
                tenant_id      TEXT,
                claim_date     TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES policies(policy_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE claims ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS fraud_checks (
                check_id     TEXT PRIMARY KEY,
                claim_id     TEXT NOT NULL,
                score        INTEGER,
                verdict      TEXT,
                reasons      TEXT,
                tenant_id    TEXT,
                checked_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE fraud_checks ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS risk_profiles (
                profile_id      TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                insurance_type  TEXT,
                score           INTEGER,
                category        TEXT,
                tenant_id       TEXT,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE risk_profiles ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS renewal_history (
                renewal_id   TEXT PRIMARY KEY,
                policy_id    TEXT NOT NULL,
                old_premium  REAL,
                new_premium  REAL,
                savings      REAL,
                new_provider TEXT,
                tenant_id    TEXT,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES policies(policy_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE renewal_history ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS role_requests (
                request_id     TEXT PRIMARY KEY,
                user_id        TEXT NOT NULL,
                requested_role TEXT NOT NULL,
                company_name   TEXT,
                employee_id    TEXT,
                license_number TEXT,
                additional_info TEXT,
                status         TEXT DEFAULT 'pending',
                tenant_id      TEXT,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        try:
            c.execute("ALTER TABLE role_requests ADD COLUMN tenant_id TEXT")
        except sqlite3.OperationalError:
            pass

        # Backfill default tenant for SQLite
        for table in ["users", "policies", "claims", "fraud_checks", "risk_profiles", "renewal_history", "role_requests"]:
            c.execute(f"UPDATE {table} SET tenant_id = ? WHERE tenant_id IS NULL", (DEFAULT_TENANT_ID,))

        seed_default_users(conn)

        logger.info("SQLite database initialized at %s with multi-tenant support", DB_PATH)


def _init_pg():
    """PostgreSQL schema — Supabase compatible, with multi-tenant support."""
    conn = _pg_connect()
    try:
        cur = conn.cursor()

        # ── Tenants table (must be first — other tables reference it) ──
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name          TEXT NOT NULL,
                logo_url      TEXT,
                primary_color TEXT DEFAULT '#2563EB',
                domain        TEXT UNIQUE,
                created_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Seed default tenant
        cur.execute("""
            INSERT INTO tenants (id, name, primary_color)
            VALUES (%s, 'InsureAI Default', '#2563EB')
            ON CONFLICT DO NOTHING
        """, (DEFAULT_TENANT_ID,))

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT,
                phone         TEXT,
                password_hash TEXT,
                role          TEXT DEFAULT 'customer',
                tenant_id     UUID REFERENCES tenants(id),
                created_at    TIMESTAMP DEFAULT NOW()
            )
        """)

        # Safe column migrations for existing tables
        for col, default in [("password_hash", "TEXT"), ("role", "TEXT DEFAULT 'customer'"), ("tenant_id", "UUID REFERENCES tenants(id)")]:
            cur.execute(f"""
                DO $$
                BEGIN
                    ALTER TABLE users ADD COLUMN {col} {default};
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
                tenant_id            UUID REFERENCES tenants(id),
                created_at           TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE policies ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id       TEXT PRIMARY KEY,
                policy_id      TEXT NOT NULL REFERENCES policies(policy_id),
                amount         DOUBLE PRECISION,
                covered_amount DOUBLE PRECISION,
                status         TEXT DEFAULT 'pending',
                description    TEXT,
                tenant_id      UUID REFERENCES tenants(id),
                claim_date     TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE claims ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fraud_checks (
                check_id     TEXT PRIMARY KEY,
                claim_id     TEXT NOT NULL REFERENCES claims(claim_id),
                score        INTEGER,
                verdict      TEXT,
                reasons      TEXT,
                tenant_id    UUID REFERENCES tenants(id),
                checked_at   TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE fraud_checks ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS risk_profiles (
                profile_id      TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(user_id),
                insurance_type  TEXT,
                score           INTEGER,
                category        TEXT,
                tenant_id       UUID REFERENCES tenants(id),
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE risk_profiles ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS renewal_history (
                renewal_id   TEXT PRIMARY KEY,
                policy_id    TEXT NOT NULL REFERENCES policies(policy_id),
                old_premium  DOUBLE PRECISION,
                new_premium  DOUBLE PRECISION,
                savings      DOUBLE PRECISION,
                new_provider TEXT,
                tenant_id    UUID REFERENCES tenants(id),
                created_at   TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE renewal_history ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_requests (
                request_id     TEXT PRIMARY KEY,
                user_id        TEXT NOT NULL REFERENCES users(user_id),
                requested_role TEXT NOT NULL,
                company_name   TEXT,
                employee_id    TEXT,
                license_number TEXT,
                additional_info TEXT,
                status         TEXT DEFAULT 'pending',
                tenant_id      UUID REFERENCES tenants(id),
                created_at     TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE role_requests ADD COLUMN tenant_id UUID REFERENCES tenants(id);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)

        # Backfill: set default tenant on any rows missing tenant_id
        for table in ["users", "policies", "claims", "fraud_checks", "risk_profiles", "renewal_history", "role_requests"]:
            cur.execute(f"UPDATE {table} SET tenant_id = %s WHERE tenant_id IS NULL", (DEFAULT_TENANT_ID,))

        seed_default_users(_PgConnWrapper(conn))

        conn.commit()
        logger.info("PostgreSQL database initialized with multi-tenant support (Supabase)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Write helpers ──────────────────────────────────────────────────────

def create_user(user_id: str, name: str, email: str = "", phone: str = "",
                role: str = "customer", tenant_id: str | None = None) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name, email, phone, role, tenant_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, email, phone, role, tenant_id)
        )


def create_policy(
    policy_id: str, user_id: str, insurance_type: str,
    provider: str = "", sum_insured: float = 0,
    annual_premium: float = 0, years_with_provider: int = 0,
    claim_free_years: int = 0, tenant_id: str | None = None,
) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO policies
            (policy_id, user_id, insurance_type, provider, sum_insured,
             annual_premium, years_with_provider, claim_free_years, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (policy_id, user_id, insurance_type, provider, sum_insured,
              annual_premium, years_with_provider, claim_free_years, tenant_id))


def save_claim(
    claim_id: str, policy_id: str, amount: float,
    covered_amount: float = 0, status: str = "pending",
    description: str = "", tenant_id: str | None = None,
) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO claims
            (claim_id, policy_id, amount, covered_amount, status, description, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (claim_id, policy_id, amount, covered_amount, status, description, tenant_id))


def save_fraud_check(
    check_id: str, claim_id: str, score: int,
    verdict: str, reasons: list[str] = None,
    tenant_id: str | None = None,
) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO fraud_checks
            (check_id, claim_id, score, verdict, reasons, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (check_id, claim_id, score, verdict, json.dumps(reasons or []), tenant_id))


def save_risk_profile(
    profile_id: str, user_id: str, insurance_type: str,
    score: int, category: str, tenant_id: str | None = None,
) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO risk_profiles
            (profile_id, user_id, insurance_type, score, category, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (profile_id, user_id, insurance_type, score, category, tenant_id))


def save_renewal(
    renewal_id: str, policy_id: str, old_premium: float,
    new_premium: float, savings: float, new_provider: str,
    tenant_id: str | None = None,
) -> None:
    if tenant_id is None:
        tenant_id = tenant_context.get()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO renewal_history
            (renewal_id, policy_id, old_premium, new_premium, savings, new_provider, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (renewal_id, policy_id, old_premium, new_premium, savings, new_provider, tenant_id))


# ── Tenant helpers ─────────────────────────────────────────────────────

def get_tenant_by_domain(domain: str) -> dict | None:
    """Look up a tenant by their custom domain/subdomain."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tenants WHERE domain = ?", (domain,)
        ).fetchone()
        return dict(row) if row else None


def get_tenant_by_id(tenant_id: str) -> dict | None:
    """Look up a tenant by their UUID."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tenants WHERE id = ?", (tenant_id,)
        ).fetchone()
        return dict(row) if row else None


def create_tenant(name: str, domain: str = None,
                  logo_url: str = "", primary_color: str = "#2563EB") -> dict:
    """Create a new tenant and return its record."""
    tenant_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO tenants (id, name, domain, logo_url, primary_color)
            VALUES (?, ?, ?, ?, ?)
        """, (tenant_id, name, domain, logo_url, primary_color))
    return {"id": tenant_id, "name": name, "domain": domain}


def tenant_query(conn, sql: str, params: tuple,
                 tenant_id: str = DEFAULT_TENANT_ID) -> list:
    """
    Automatically appends tenant_id filter to any SELECT query.
    Use this instead of raw queries to enforce tenant isolation.
    """
    if "WHERE" in sql.upper():
        sql += " AND tenant_id = ?"
    else:
        sql += " WHERE tenant_id = ?"
    return conn.execute(sql, params + (tenant_id,)).fetchall()


# ── Read helpers ───────────────────────────────────────────────────────

def get_policy_by_number(policy_number: str) -> dict | None:
    tenant_id = tenant_context.get()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM policies WHERE policy_id = ? AND tenant_id = ?", (policy_number, tenant_id)
        ).fetchone()
        return dict(row) if row else None


def get_claims_for_policy(policy_id: str) -> list[dict]:
    tenant_id = tenant_context.get()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM claims WHERE policy_id = ? AND tenant_id = ? ORDER BY claim_date DESC",
            (policy_id, tenant_id)
        ).fetchall()
        return [dict(r) for r in rows]


def get_user_context(user_id: str | None = None, policy_number: str | None = None) -> dict:
    """
    THE key function — returns everything known about a user/policy
    so every agent (fraud, risk, renewal) can use REAL history
    instead of hardcoded defaults.
    """
    tenant_id = tenant_context.get()
    with get_conn() as conn:
        policy = None
        if policy_number:
            row = conn.execute(
                "SELECT * FROM policies WHERE policy_id = ? AND tenant_id = ?", (policy_number, tenant_id)
            ).fetchone()
            policy = dict(row) if row else None
            if policy:
                user_id = policy["user_id"]

        user = None
        if user_id:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND tenant_id = ?", (user_id, tenant_id)
            ).fetchone()
            user = dict(row) if row else None

        claims = []
        if policy:
            rows = conn.execute(
                "SELECT * FROM claims WHERE policy_id = ? AND tenant_id = ? ORDER BY claim_date DESC",
                (policy["policy_id"], tenant_id)
            ).fetchall()
            claims = [dict(r) for r in rows]

        risk_profile = None
        if user_id:
            row = conn.execute(
                "SELECT * FROM risk_profiles WHERE user_id = ? AND tenant_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id, tenant_id)
            ).fetchone()
            risk_profile = dict(row) if row else None

        fraud_checks = []
        for claim in claims:
            rows = conn.execute(
                "SELECT * FROM fraud_checks WHERE claim_id = ? AND tenant_id = ?",
                (claim["claim_id"], tenant_id)
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
