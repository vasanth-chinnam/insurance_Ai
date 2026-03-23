import os
import sqlite3

MOCK_DB_DIR = os.path.join(os.path.dirname(__file__), "mock_db")

def setup_flights_db():
    db_path = os.path.join(MOCK_DB_DIR, "flights.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_number TEXT PRIMARY KEY,
            status TEXT,
            delay_minutes INTEGER
        )
    """)
    # Insert mock data
    flights = [
        ("AI-101", "On Time", 0),
        ("6E-202", "Delayed", 180),
        ("SG-303", "Canceled", 0),
        ("UK-404", "On Time", 0),
    ]
    cursor.executemany("INSERT OR REPLACE INTO flights VALUES (?, ?, ?)", flights)
    conn.commit()
    conn.close()
    print("flights.db setup complete.")

def setup_hospitals_db():
    db_path = os.path.join(MOCK_DB_DIR, "hospitals.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_name TEXT PRIMARY KEY,
            is_blacklisted INTEGER,
            average_billing_multiplier REAL
        )
    """)
    hospitals = [
        ("City General Hospital", 0, 1.0),
        ("Apollo Care Center", 0, 1.2),
        ("Shady Pines Clinic", 1, 2.5),  # Blacklisted
        ("Apex Wellness", 0, 1.1),
    ]
    cursor.executemany("INSERT OR REPLACE INTO hospitals VALUES (?, ?, ?)", hospitals)
    conn.commit()
    conn.close()
    print("hospitals.db setup complete.")

def setup_workshops_db():
    db_path = os.path.join(MOCK_DB_DIR, "workshops.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workshops (
            workshop_name TEXT PRIMARY KEY,
            is_blacklisted INTEGER,
            average_repair_cost REAL
        )
    """)
    workshops = [
        ("AutoFix Garage", 0, 5000),
        ("Premium Motors Repair", 0, 8000),
        ("Shady Mechanics", 1, 15000),  # Blacklisted
        ("Quick Fix Auto", 0, 4000),
    ]
    cursor.executemany("INSERT OR REPLACE INTO workshops VALUES (?, ?, ?)", workshops)
    conn.commit()
    conn.close()
    print("workshops.db setup complete.")

if __name__ == "__main__":
    os.makedirs(MOCK_DB_DIR, exist_ok=True)
    setup_flights_db()
    setup_hospitals_db()
    setup_workshops_db()
    print("All mock databases generated successfully.")
