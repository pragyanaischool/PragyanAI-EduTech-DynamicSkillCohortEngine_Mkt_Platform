"""
Coordinator Operations & Direct Cohort Management Module.
Handles batch claiming, WhatsApp group link provisioning, live class links,
and contact directory unlocking (trainers, students, and institutional SPOCs).
"""

from typing import Any, Dict, List, Optional, Tuple
from config.database import get_connection


def assign_coordinator_and_advance(program_id: int, coordinator_id: int) -> bool:
    """Assigns an operational coordinator to a compiled program and advances status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE compiled_programs 
        SET coordinator_id = ?, status = 'COORDINATION'
        WHERE id = ?
        """,
        (coordinator_id, program_id),
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def update_cohort_logistics(program_id: int, whatsapp_link: str, meeting_link: str) -> bool:
    """Updates the WhatsApp community link and live classroom URL for a cohort."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE compiled_programs 
        SET whatsapp_group_link = ?, meeting_link = ?, status = 'LIVE'
        WHERE id = ?
        """,
        (whatsapp_link.strip(), meeting_link.strip(), program_id),
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def get_program_contact_directory(program_id: int) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Unlocks complete contact directory for assigned coordinators:
    - Trainer: Full Name, Phone, Email, Anonymized Token
    - Enrolled Students: Names, Verified Phones, Emails, Colleges, Payment Reference
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch Program & Linked Expert Contact Details
    cursor.execute(
        """
        SELECT p.*, u.full_name as expert_name, u.phone as expert_phone, 
               u.email as expert_email, e.token as expert_token, e.industry_vertical
        FROM compiled_programs p
        LEFT JOIN expert_profiles e ON p.expert_id = e.id
        LEFT JOIN users u ON e.user_id = u.id
        WHERE p.id = ?
        """,
        (program_id,),
    )
    prog_row = cursor.fetchone()

    # 2. Fetch Enrolled Students with Direct Payment Proofs
    cursor.execute(
        """
        SELECT u.id, u.full_name, u.phone, u.email, u.institution, u.department,
               pr.payment_mode, pr.transaction_reference, pr.amount_paid, pr.verification_status
        FROM program_enrollments pe
        JOIN users u ON pe.student_id = u.id
        LEFT JOIN payment_records pr ON pe.payment_ref_id = pr.id
        WHERE pe.program_id = ?
        ORDER BY pe.id ASC
        """,
        (program_id,),
    )
    student_rows = cursor.fetchall()

    conn.close()
    program_dict = dict(prog_row) if prog_row else None
    student_list = [dict(s) for s in student_rows]

    return program_dict, student_list
