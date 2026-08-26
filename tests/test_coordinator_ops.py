"""
Tests for modules/coordinator_ops.py.
Validates coordinator cohort assignment, WhatsApp group invite provisioning,
live classroom link updates, and unmasked contact directory resolution.
"""

import sqlite3
import pytest
from config.database import init_db
from modules.auth import register_user
from modules.coordinator_ops import (
    assign_coordinator_and_advance,
    get_program_contact_directory,
    update_cohort_logistics,
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up an in-memory database with populated program dependencies."""
    test_db = ":memory:"
    conn = sqlite3.connect(test_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    monkeypatch.setattr("modules.coordinator_ops.get_connection", lambda: conn)
    monkeypatch.setattr("modules.auth.get_connection", lambda: conn)
    monkeypatch.setattr("config.database.get_connection", lambda: conn)

    init_db(test_db)

    # 1. Register Coordinator, Expert, and Student
    register_user(
        "coord_user",
        "pass123",
        "Coordinator Jane",
        "coordinator",
        phone="+919888877777",
        email="jane@pragyan.ai",
    )
    register_user(
        "expert_user",
        "pass123",
        "Dr. Expert John",
        "expert",
        phone="+919876543210",
        email="john@expert.com",
    )
    register_user(
        "student_user",
        "pass123",
        "Student Alice",
        "student",
        phone="+919123456789",
        email="alice@student.edu",
        institution="PES Univ",
    )

    cursor = conn.cursor()

    # Resolve generated IDs dynamically
    cursor.execute("SELECT id FROM users WHERE username = 'coord_user'")
    coord_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM expert_profiles WHERE user_id = (SELECT id FROM users WHERE username = 'expert_user')")
    expert_profile_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'student_user'")
    student_id = cursor.fetchone()["id"]

    # 2. Create a test compiled program linked to the expert profile
    cursor.execute(
        """
        INSERT INTO compiled_programs (
            program_id, source_type, title, duration_hours, ticket_price_inr, 
            target_quorum, enrolled_count, syllabus_json, expert_id, status
        )
        VALUES ('PRG-TEST-001', 'B2C_CROWD', 'Agentic AI Systems', 15, 250.0, 5, 1, '{}', ?, 'PLEDGE_OPEN')
        """,
        (expert_profile_id,),
    )
    prog_id = cursor.lastrowid

    # 3. Create a payment record and enrollment for the student
    cursor.execute(
        """
        INSERT INTO payment_records (
            program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status
        )
        VALUES (?, ?, 'STUDENT', 'UPI', 'UPI-REF-TEST-9988', 250.0, 'VERIFIED')
        """,
        (prog_id, student_id),
    )
    pay_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO program_enrollments (program_id, student_id, payment_ref_id)
        VALUES (?, ?, ?)
        """,
        (prog_id, student_id, pay_id),
    )
    conn.commit()

    yield {
        "conn": conn,
        "program_id": prog_id,
        "coordinator_id": coord_id,
        "expert_profile_id": expert_profile_id,
        "student_id": student_id,
    }
    conn.close()


def test_assign_coordinator_and_advance(setup_test_db):
    conn = setup_test_db["conn"]
    prog_id = setup_test_db["program_id"]
    coord_id = setup_test_db["coordinator_id"]

    success = assign_coordinator_and_advance(program_id=prog_id, coordinator_id=coord_id)
    assert success is True

    cursor = conn.cursor()
    cursor.execute("SELECT coordinator_id, status FROM compiled_programs WHERE id = ?", (prog_id,))
    prog = cursor.fetchone()

    assert prog["coordinator_id"] == coord_id
    assert prog["status"] == "COORDINATION"


def test_update_cohort_logistics(setup_test_db):
    conn = setup_test_db["conn"]
    prog_id = setup_test_db["program_id"]
    wa_url = "https://chat.whatsapp.com/testBatchInvite123"
    meet_url = "https://meet.google.com/xyz-test-abc"

    success = update_cohort_logistics(program_id=prog_id, whatsapp_link=wa_url, meeting_link=meet_url)
    assert success is True

    cursor = conn.cursor()
    cursor.execute(
        "SELECT whatsapp_group_link, meeting_link, status FROM compiled_programs WHERE id = ?",
        (prog_id,),
    )
    prog = cursor.fetchone()

    assert prog["whatsapp_group_link"] == wa_url
    assert prog["meeting_link"] == meet_url
    assert prog["status"] == "LIVE"


def test_get_program_contact_directory_unmasks_correct_details(setup_test_db):
    prog_id = setup_test_db["program_id"]
    prog, students = get_program_contact_directory(program_id=prog_id)

    # Validate Program & Expert Details
    assert prog is not None
    assert prog["title"] == "Agentic AI Systems"
    assert prog["expert_name"] == "Dr. Expert John"
    assert prog["expert_phone"] == "+919876543210"
    assert prog["expert_email"] == "john@expert.com"
    assert prog["expert_token"].startswith("EXP-M")

    # Validate Enrolled Students Roster
    assert len(students) == 1
    student = students[0]
    assert student["full_name"] == "Student Alice"
    assert student["phone"] == "+919123456789"
    assert student["institution"] == "PES Univ"
    assert student["payment_mode"] == "UPI"
    assert student["transaction_reference"] == "UPI-REF-TEST-9988"
