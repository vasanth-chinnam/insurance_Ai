"""
Run the Day 1 multi-tenant SQL migration against the live Supabase database.

Usage:
    python scratch/migrate_tenants.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    sys.exit(1)

import psycopg2

url = DATABASE_URL
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]

print(f"Connecting to: {url[:50]}...")
conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

MIGRATION_SQL = [
    # 1. Tenants table
    """
    CREATE TABLE IF NOT EXISTS tenants (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name          TEXT NOT NULL,
        logo_url      TEXT,
        primary_color TEXT DEFAULT '#2563EB',
        domain        TEXT UNIQUE,
        created_at    TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # 2. Add tenant_id to users
    """
    DO $$ BEGIN
        ALTER TABLE users ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 3. Add tenant_id to policies
    """
    DO $$ BEGIN
        ALTER TABLE policies ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 4. Add tenant_id to claims
    """
    DO $$ BEGIN
        ALTER TABLE claims ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 5. Add tenant_id to fraud_checks
    """
    DO $$ BEGIN
        ALTER TABLE fraud_checks ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 6. Add tenant_id to risk_profiles
    """
    DO $$ BEGIN
        ALTER TABLE risk_profiles ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 7. Add tenant_id to renewal_history
    """
    DO $$ BEGIN
        ALTER TABLE renewal_history ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 8. Add role column to users (for RBAC in Day 2)
    """
    DO $$ BEGIN
        ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer';
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$
    """,
    # 9. Default tenant for existing data
    """
    INSERT INTO tenants (id, name, primary_color)
    VALUES ('00000000-0000-0000-0000-000000000001', 'InsureAI Default', '#2563EB')
    ON CONFLICT DO NOTHING
    """,
    # 10. Update existing rows to use default tenant
    "UPDATE users          SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
    "UPDATE policies       SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
    "UPDATE claims         SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
    "UPDATE fraud_checks   SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
    "UPDATE risk_profiles  SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
    "UPDATE renewal_history SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL",
]

print("Running multi-tenant migration...")
for i, stmt in enumerate(MIGRATION_SQL, 1):
    try:
        cur.execute(stmt)
        print(f"  [{i}/{len(MIGRATION_SQL)}] OK")
    except Exception as e:
        print(f"  [{i}/{len(MIGRATION_SQL)}] WARN: {e}")

# Verify
cur.execute("SELECT COUNT(*) FROM tenants")
count = cur.fetchone()[0]
print(f"\nVerification: tenants table has {count} row(s)")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'tenant_id'")
has_col = cur.fetchone()
print(f"Verification: users.tenant_id column exists: {bool(has_col)}")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role'")
has_role = cur.fetchone()
print(f"Verification: users.role column exists: {bool(has_role)}")

cur.close()
conn.close()
print("\nMigration complete!")
