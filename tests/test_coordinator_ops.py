"""
Tests for modules/coordinator_ops.py.
Validates coordinator cohort assignment, WhatsApp group invite provisioning,
live classroom link updates, unmasked contact directory resolution, and 
handling of valid vs. invalid/at-risk learner payment states.
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
    """Sets up an in-memory database with populated program dependencies and multiple test students."""
    test_db = ":memory:"
    conn = sqlite3.connect(test_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    monkeypatch.setattr("modules.coordinator_ops.get_connection", lambda: conn)
    monkeypatch.setattr("modules.auth.get_connection", lambda: conn)
    monkeypatch.setattr("config.database.get_connection", lambda: conn)

    init_db(test_db)

    # 1. Register Coordinator, Expert, and Valid/Invalid Student Personas
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
        department="AI 4th Sem",
    )
    register_user(
        "student_invalid_utr",
        "pass123",
        "Student Bob",
        "student",
        phone="+919900112233",
        email="bob@student.edu",
        institution="RVCE",
        department="CSE 6th Sem",
    )
    register_user(
        "student_bad_phone",
        "pass123",
        "Student Charlie",
        "student",
        phone="98450",
        email="charlie@student.edu",
        institution="BMSCE",
        department="ECE 8th Sem",
    )

    cursor = conn.cursor()

    # Dynamic ID Lookups
    cursor.execute("SELECT id FROM users WHERE username = 'coord_user'")
    coord_id = cursor.fetchone()["id"]

    cursor.execute(
        "SELECT id FROM expert_profiles WHERE user_id = (SELECT id FROM users WHERE username = 'expert_user')"
    )
    expert_profile_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'student_user'")
    valid_student_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'student_invalid_utr'")
    invalid_utr_student_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'student_bad_phone'")
    bad_phone_student_id = cursor.fetchone()["id"]

    # 2. Create a test compiled program linked to the expert profile
    cursor.execute(
        """
        INSERT INTO compiled_programs (
            program_id, source_type, title, duration_hours, ticket_price_inr, 
            target_quorum, enrolled_count, syllabus_json, expert_id, status
        )
        VALUES ('PRG-TEST-001', 'B2C_CROWD', 'Agentic AI Systems', 15, 250.0, 5, 3, '{}', ?, 'PLEDGE_OPEN')
        """,
        (expert_profile_id,),
    )
    prog_id = cursor.lastrowid

    # 3. Create payment records (Valid, Fake UTR, and Underpaid/Malformed)
    # Payment 1: Valid Verified
    cursor.execute(
        """
        INSERT INTO payment_records (
            program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status
        )
        VALUES (?, ?, 'STUDENT', 'UPI', 'UPI-REF-TEST-9988', 250.0, 'VERIFIED')
        """,
        (prog_id, valid_student_id),
    )
    pay_id_valid = cursor.lastrowid

    # Payment 2: Rejected Fake UTR
    cursor.execute(
        """
        INSERT INTO payment_records (
            program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status
        )
        VALUES (?, ?, 'STUDENT', 'UPI', '000000000000', 250.0, 'REJECTED')
        """,
        (prog_id, invalid_utr_student_id),
    )
    pay_id_fake_utr = cursor.lastrowid

    # Payment 3: Underpaid & Bad Phone
    cursor.execute(
        """
        INSERT INTO payment_records (
            program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status
        )
        VALUES (?, ?, 'STUDENT', 'UPI', 'UPI-PARTIAL-50', 50.0, 'REJECTED')
        """,
        (prog_id, bad_phone_student_id),
    )
    pay_id_underpaid = cursor.lastrowid

    # Link enrollments
    cursor.execute(
        "INSERT INTO program_enrollments (program_id, student_id, payment_ref_id) VALUES (?, ?, ?)",
        (prog_id, valid_student_id, pay_id_valid),
    )
    cursor.execute(
        "INSERT INTO program_enrollments (program_id, student_id, payment_ref_id) VALUES (?, ?, ?)",
        (prog_id, invalid_utr_student_id, pay_id_fake_utr),
    )
    cursor.execute(
        "INSERT INTO program_enrollments (program_id, student_id, payment_ref_id) VALUES (?, ?, ?)",
        (prog_id, bad_phone_student_id, pay_id_underpaid),
    )
    conn.commit()

    yield {
        "conn": conn,
        "program_id": prog_id,
        "coordinator_id": coord_id,
        "expert_profile_id": expert_profile_id,
        "valid_student_id": valid_student_id,
        "invalid_utr_student_id": invalid_utr_student_id,
        "bad_phone_student_id": bad_phone_student_id,
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

    # 1. Validate Program & Trainer Profile Unmasking
    assert prog is not None
    assert prog["title"] == "Agentic AI Systems"
    assert prog["expert_name"] == "Dr. Expert John"
    assert prog["expert_phone"] == "+919876543210"
    assert prog["expert_email"] == "john@expert.com"
    assert prog["expert_token"].startswith("EXP-M")

    # 2. Validate Enrolled Students Roster
    assert len(students) == 3

    # Locate individual student records
    valid_student = next(s for s in students if s["full_name"] == "Student Alice")
    invalid_utr_student = next(s for s in students if s["full_name"] == "Student Bob")
    bad_phone_student = next(s for s in students if s["full_name"] == "Student Charlie")

    # Check Valid Student Assertions
    assert valid_student["phone"] == "+919123456789"
    assert valid_student["institution"] == "PES Univ"
    assert valid_student["payment_mode"] == "UPI"
    assert valid_student["transaction_reference"] == "UPI-REF-TEST-9988"
    assert valid_student["verification_status"] == "VERIFIED"
    assert valid_student["amount_paid"] == 250.0

    # Check Invalid / Anomaly Assertions
    assert invalid_utr_student["verification_status"] == "REJECTED"
    assert invalid_utr_student["transaction_reference"] == "000000000000"

    assert bad_phone_student["verification_status"] == "REJECTED"
    assert bad_phone_student["amount_paid"] == 50.0
    assert len(bad_phone_student["phone"]) < 10
