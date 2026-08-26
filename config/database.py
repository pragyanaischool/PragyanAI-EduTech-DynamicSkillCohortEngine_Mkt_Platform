"""
Database configuration and SQLite schema definitions for PragyanAI DemandX.
Updated with EOI tracking and payment exception fields.
"""

import os
import sqlite3
from typing import Optional
from config.settings import settings


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or settings.DATABASE_PATH
    if target_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Users & RBAC
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT CHECK(role IN ('student', 'college', 'expert', 'coordinator')) NOT NULL,
        phone TEXT NOT NULL DEFAULT '',
        email TEXT NOT NULL DEFAULT '',
        institution TEXT,
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Expert Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expert_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        token TEXT UNIQUE NOT NULL,
        industry_vertical TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        skills TEXT NOT NULL,
        sessions_completed INTEGER DEFAULT 0,
        rating REAL DEFAULT 5.0,
        hourly_rate_inr REAL NOT NULL,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 3. Student Demand Pool
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_demands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        dream_job_role TEXT NOT NULL,
        target_skills TEXT NOT NULL,
        duration_hours INTEGER NOT NULL,
        budget_inr REAL NOT NULL,
        cluster_id TEXT,
        status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'CLUSTERED', 'LOCKED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 4. Institutional Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutional_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        college_id INTEGER NOT NULL,
        spoc_name TEXT NOT NULL,
        spoc_phone TEXT NOT NULL,
        spoc_email TEXT NOT NULL,
        program_type TEXT CHECK(program_type IN ('FDP', 'STP', 'Workshop', 'Guest Lecture')) NOT NULL,
        scope_description TEXT NOT NULL,
        delivery_mode TEXT CHECK(delivery_mode IN ('Online', 'Offline', 'Hybrid')) NOT NULL,
        budget_inr REAL NOT NULL,
        compiled_syllabus TEXT,
        selected_expert_id INTEGER,
        status TEXT DEFAULT 'DRAFT' CHECK(status IN ('DRAFT', 'BIDDING', 'PAYMENT_PENDING', 'COORDINATION', 'COMPLETED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (college_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (selected_expert_id) REFERENCES expert_profiles(id) ON DELETE SET NULL
    );
    """)

    # 5. Compiled Programs / Live Cohorts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compiled_programs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id TEXT UNIQUE NOT NULL,
        source_type TEXT CHECK(source_type IN ('B2C_CROWD', 'B2B_COLLEGE')) NOT NULL,
        title TEXT NOT NULL,
        duration_hours INTEGER NOT NULL,
        ticket_price_inr REAL NOT NULL,
        target_quorum INTEGER NOT NULL,
        enrolled_count INTEGER DEFAULT 0,
        syllabus_json TEXT NOT NULL,
        expert_id INTEGER,
        coordinator_id INTEGER,
        status TEXT DEFAULT 'PLEDGE_OPEN' CHECK(status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING', 'COORDINATION', 'LIVE', 'COMPLETED')),
        whatsapp_group_link TEXT DEFAULT '',
        meeting_link TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (expert_id) REFERENCES expert_profiles(id) ON DELETE SET NULL,
        FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 6. Direct Payment Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        payer_type TEXT CHECK(payer_type IN ('STUDENT', 'COLLEGE')) NOT NULL,
        payment_mode TEXT CHECK(payment_mode IN ('UPI', 'NEFT_IMPS', 'Bank_Transfer', 'Institutional_PO')) NOT NULL,
        transaction_reference TEXT NOT NULL,
        amount_paid REAL NOT NULL,
        verification_status TEXT DEFAULT 'VERIFIED' CHECK(verification_status IN ('SUBMITTED', 'VERIFIED', 'REJECTED')),
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES compiled_programs(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 7. Expressions of Interest (EOI)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cohort_expressions_of_interest (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        willing_budget_inr REAL NOT NULL,
        preferred_slot TEXT DEFAULT 'Weekend',
        expressed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES compiled_programs(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(program_id, student_id)
    );
    """)

    # 8. Program Enrollments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS program_enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        payment_ref_id INTEGER,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES compiled_programs(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (payment_ref_id) REFERENCES payment_records(id) ON DELETE SET NULL
    );
    """)

    # 9. Bids
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER,
        b2b_request_id INTEGER,
        expert_id INTEGER NOT NULL,
        bid_amount_inr REAL NOT NULL,
        counter_notes TEXT,
        status TEXT DEFAULT 'SUBMITTED' CHECK(status IN ('SUBMITTED', 'ACCEPTED', 'REJECTED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES compiled_programs(id) ON DELETE CASCADE,
        FOREIGN KEY (b2b_request_id) REFERENCES institutional_requests(id) ON DELETE CASCADE,
        FOREIGN KEY (expert_id) REFERENCES expert_profiles(id) ON DELETE CASCADE
    );
    """)

    # 10. Feedback & Certificates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback_and_certs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        rating_score INTEGER CHECK(rating_score BETWEEN 1 AND 5),
        review_text TEXT,
        cert_hash TEXT UNIQUE,
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES compiled_programs(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
