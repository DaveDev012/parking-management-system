"""
database.py - Database Layer for Smart Parking Management System
Handles SQLite database connection, table creation, and CRUD operations.
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Database file path in the project directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parking.db')


def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    row_factory is set to sqlite3.Row to access columns by name (like dictionaries).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(seed_demo_data=True):
    """
    Initializes the database schema and optionally seeds realistic sample data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: vehicles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL
        );
    """)

    # Table 2: parking_records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            slot_number TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            duration_hours INTEGER,
            parking_fee REAL,
            status TEXT NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        );
    """)

    conn.commit()

    # Seed demo records if database is freshly created and empty
    if seed_demo_data:
        cursor.execute("SELECT COUNT(*) FROM parking_records")
        record_count = cursor.fetchone()[0]
        if record_count == 0:
            _seed_initial_data(conn)

    conn.close()


def _seed_initial_data(conn):
    """
    Helper function to seed realistic sample parking data for viva demo.
    """
    cursor = conn.cursor()
    now = datetime.now()

    # Sample demo vehicles: (vehicle_number, owner_name, vehicle_type)
    demo_vehicles = [
        ('GJ01AB1234', 'Rahul Sharma', 'Car'),
        ('MH12CD5678', 'Priya Patel', 'Car'),
        ('KA03EF9012', 'Amit Verma', 'Bike'),
        ('DL05GH3456', 'Neha Gupta', 'Car'),
        ('TN07JK7890', 'Karthik Raja', 'Bike'),
        ('GJ05LM2345', 'Anjali Desai', 'Car'),
        ('MH02PQ6789', 'Vikas Rao', 'Bike'),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO vehicles (vehicle_number, owner_name, vehicle_type)
        VALUES (?, ?, ?);
    """, demo_vehicles)

    # Fetch vehicle IDs
    cursor.execute("SELECT id, vehicle_number FROM vehicles")
    v_map = {row['vehicle_number']: row['id'] for row in cursor.fetchall()}

    # Format helpers for demo timestamps
    def fmt(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    # Completed demo sessions (earlier today and yesterday)
    completed_sessions = [
        (v_map['GJ05LM2345'], 'A05', fmt(now - timedelta(hours=5)), fmt(now - timedelta(hours=3)), 2, 50.0, 'COMPLETED'),
        (v_map['MH02PQ6789'], 'B03', fmt(now - timedelta(hours=4)), fmt(now - timedelta(hours=2)), 2, 30.0, 'COMPLETED'),
        (v_map['DL05GH3456'], 'A02', fmt(now - timedelta(days=1, hours=4)), fmt(now - timedelta(days=1, hours=1)), 3, 70.0, 'COMPLETED'),
        (v_map['TN07JK7890'], 'B04', fmt(now - timedelta(days=1, hours=3)), fmt(now - timedelta(days=1, hours=2)), 1, 20.0, 'COMPLETED'),
    ]

    # Active PARKED demo sessions
    active_sessions = [
        (v_map['GJ01AB1234'], 'A01', fmt(now - timedelta(hours=2, minutes=15)), None, None, None, 'PARKED'),
        (v_map['MH12CD5678'], 'A04', fmt(now - timedelta(hours=1, minutes=10)), None, None, None, 'PARKED'),
        (v_map['KA03EF9012'], 'B01', fmt(now - timedelta(minutes=45)), None, None, None, 'PARKED'),
    ]

    cursor.executemany("""
        INSERT INTO parking_records 
        (vehicle_id, slot_number, entry_time, exit_time, duration_hours, parking_fee, status)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, completed_sessions + active_sessions)

    conn.commit()


# ==========================================
# VEHICLE OPERATIONS
# ==========================================

def add_or_get_vehicle(vehicle_number, owner_name, vehicle_type):
    """
    Inserts a new vehicle or updates owner/type if it already exists.
    Returns the vehicle ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    vehicle_number = vehicle_number.strip().upper()
    owner_name = owner_name.strip()

    cursor.execute("SELECT id FROM vehicles WHERE vehicle_number = ?", (vehicle_number,))
    existing = cursor.fetchone()

    if existing:
        vehicle_id = existing['id']
        # Update details in case owner or type changed
        cursor.execute("""
            UPDATE vehicles 
            SET owner_name = ?, vehicle_type = ? 
            WHERE id = ?
        """, (owner_name, vehicle_type, vehicle_id))
    else:
        cursor.execute("""
            INSERT INTO vehicles (vehicle_number, owner_name, vehicle_type)
            VALUES (?, ?, ?)
        """, (vehicle_number, owner_name, vehicle_type))
        vehicle_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return vehicle_id


def get_vehicle_by_number(vehicle_number):
    """
    Fetches vehicle details by vehicle number.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_number = ?", (vehicle_number.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ==========================================
# PARKING RECORD OPERATIONS
# ==========================================

def create_parking_record(vehicle_id, slot_number, entry_time):
    """
    Creates a new parking record with status 'PARKED'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parking_records (vehicle_id, slot_number, entry_time, status)
        VALUES (?, ?, ?, 'PARKED')
    """, (vehicle_id, slot_number, entry_time))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_active_record_by_vehicle(vehicle_number):
    """
    Returns active (status = 'PARKED') record for a vehicle, joining vehicle details.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.status,
               v.id AS vehicle_id, v.vehicle_number, v.owner_name, v.vehicle_type
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        WHERE v.vehicle_number = ? AND pr.status = 'PARKED'
        LIMIT 1
    """, (vehicle_number.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_record_by_id(record_id):
    """
    Returns active record by record ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.status,
               v.id AS vehicle_id, v.vehicle_number, v.owner_name, v.vehicle_type
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        WHERE pr.id = ? AND pr.status = 'PARKED'
    """, (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def complete_parking_record(record_id, exit_time, duration_hours, parking_fee):
    """
    Marks an active parking record as 'COMPLETED', recording exit time, duration, and fee.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE parking_records
        SET exit_time = ?, duration_hours = ?, parking_fee = ?, status = 'COMPLETED'
        WHERE id = ? AND status = 'PARKED'
    """, (exit_time, duration_hours, parking_fee, record_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def get_all_active_records():
    """
    Returns all currently parked vehicles with their slot and vehicle info.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.status,
               v.vehicle_number, v.owner_name, v.vehicle_type
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        WHERE pr.status = 'PARKED'
        ORDER BY pr.entry_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_records(limit=5):
    """
    Returns the most recent parking activity records (active or completed).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.exit_time,
               pr.duration_hours, pr.parking_fee, pr.status,
               v.vehicle_number, v.owner_name, v.vehicle_type
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        ORDER BY pr.id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_parking_history(search_query=None):
    """
    Returns parking history, optionally filtered by vehicle number or owner name.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        query_wildcard = f"%{search_query.strip().upper()}%"
        cursor.execute("""
            SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.exit_time,
                   pr.duration_hours, pr.parking_fee, pr.status,
                   v.vehicle_number, v.owner_name, v.vehicle_type
            FROM parking_records pr
            JOIN vehicles v ON pr.vehicle_id = v.id
            WHERE UPPER(v.vehicle_number) LIKE ? OR UPPER(v.owner_name) LIKE ?
            ORDER BY pr.id DESC
        """, (query_wildcard, query_wildcard))
    else:
        cursor.execute("""
            SELECT pr.id AS record_id, pr.slot_number, pr.entry_time, pr.exit_time,
                   pr.duration_hours, pr.parking_fee, pr.status,
                   v.vehicle_number, v.owner_name, v.vehicle_type
            FROM parking_records pr
            JOIN vehicles v ON pr.vehicle_id = v.id
            ORDER BY pr.id DESC
        """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ==========================================
# DASHBOARD & REPORTS AGGREGATIONS
# ==========================================

def get_dashboard_stats(total_slots=20):
    """
    Computes dashboard KPI metrics and today's activity stats.
    All values are dynamically queried from SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Occupied slots count
    cursor.execute("SELECT COUNT(*) FROM parking_records WHERE status = 'PARKED'")
    occupied_slots = cursor.fetchone()[0]

    available_slots = max(0, total_slots - occupied_slots)

    # 2. Today's date string YYYY-MM-DD
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_pattern = f"{today_str}%"

    # 3. Today's revenue: sum of fees from completed sessions exited today
    cursor.execute("""
        SELECT COALESCE(SUM(parking_fee), 0.0)
        FROM parking_records
        WHERE status = 'COMPLETED' AND exit_time LIKE ?
    """, (today_pattern,))
    today_revenue = cursor.fetchone()[0]

    # 4. Vehicles entered today
    cursor.execute("""
        SELECT COUNT(*)
        FROM parking_records
        WHERE entry_time LIKE ?
    """, (today_pattern,))
    today_entered = cursor.fetchone()[0]

    # 5. Vehicles exited today
    cursor.execute("""
        SELECT COUNT(*)
        FROM parking_records
        WHERE status = 'COMPLETED' AND exit_time LIKE ?
    """, (today_pattern,))
    today_exited = cursor.fetchone()[0]

    conn.close()

    return {
        'total_slots': total_slots,
        'occupied_slots': occupied_slots,
        'available_slots': available_slots,
        'today_revenue': round(today_revenue, 2),
        'today_entered': today_entered,
        'today_exited': today_exited
    }


def get_reports_stats():
    """
    Computes analytics and aggregations for the Reports page.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total distinct vehicles registered
    cursor.execute("SELECT COUNT(DISTINCT vehicle_number) FROM vehicles")
    total_vehicles = cursor.fetchone()[0]

    # Total completed sessions
    cursor.execute("SELECT COUNT(*) FROM parking_records WHERE status = 'COMPLETED'")
    completed_sessions = cursor.fetchone()[0]

    # Total all-time revenue
    cursor.execute("SELECT COALESCE(SUM(parking_fee), 0.0) FROM parking_records WHERE status = 'COMPLETED'")
    total_revenue = cursor.fetchone()[0]

    # Average parking duration (in hours)
    cursor.execute("SELECT COALESCE(AVG(duration_hours), 0.0) FROM parking_records WHERE status = 'COMPLETED'")
    avg_duration = cursor.fetchone()[0]

    # Vehicle type breakdown (Car vs Bike)
    cursor.execute("""
        SELECT v.vehicle_type, COUNT(pr.id) AS count
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        GROUP BY v.vehicle_type
    """)
    type_counts = {'Car': 0, 'Bike': 0}
    for row in cursor.fetchall():
        type_counts[row['vehicle_type']] = row['count']

    # Daily revenue for the last 7 days
    # SQLite substr(exit_time, 1, 10) gives YYYY-MM-DD
    cursor.execute("""
        SELECT substr(exit_time, 1, 10) as day, COALESCE(SUM(parking_fee), 0) as daily_total
        FROM parking_records
        WHERE status = 'COMPLETED' AND exit_time IS NOT NULL
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """)
    daily_rows = cursor.fetchall()

    # Reverse so the chart displays chronologically (oldest to newest)
    daily_data = [{'day': row['day'], 'revenue': row['daily_total']} for row in reversed(daily_rows)]

    # If there are fewer than 3 days recorded, ensure today is present
    today_str = datetime.now().strftime('%Y-%m-%d')
    if not any(d['day'] == today_str for d in daily_data):
        daily_data.append({'day': today_str, 'revenue': 0})

    conn.close()

    return {
        'total_vehicles': total_vehicles,
        'completed_sessions': completed_sessions,
        'total_revenue': round(total_revenue, 2),
        'avg_duration': round(avg_duration, 1),
        'car_count': type_counts.get('Car', 0),
        'bike_count': type_counts.get('Bike', 0),
        'daily_revenue': daily_data
    }
