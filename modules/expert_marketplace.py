"""
Expert Marketplace & Reverse-Bidding Module.
Provides masked trainer rosters (protecting PII prior to engagement lock-in),
multi-variable competency fit scoring, and proposal bid submissions.
"""

from typing import Any, Dict, List
from config.database import get_connection


def get_anonymized_expert_roster() -> List[Dict[str, Any]]:
    """
    Retrieves expert profiles stripped of PII.
    Displays tokens, ratings, industry verticals, verified skill sets, and hourly rates.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, token, industry_vertical, experience_years, skills, 
               sessions_completed, rating, hourly_rate_inr, bio 
        FROM expert_profiles
        ORDER BY rating DESC, sessions_completed DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calculate_expert_fit_score(expert: Dict[str, Any], required_skills: str) -> float:
    """
    Computes a composite fit score (0 - 100%) based on:
    - Skill keyword overlap (50% weight)
    - Experience depth (25% weight, scaled to 15 years)
    - Historical teaching rating (25% weight, scaled to 5.0)
    """
    if not required_skills:
        return 50.0

    exp_skills = set(s.strip().lower() for s in expert.get("skills", "").split(",") if s.strip())
    req_skills = set(s.strip().lower() for s in required_skills.split(",") if s.strip())

    if not req_skills:
        overlap_score = 0.5
    else:
        matched = len(exp_skills.intersection(req_skills))
        overlap_score = matched / len(req_skills)

    exp_years = expert.get("experience_years", 0)
    exp_weight = min(exp_years / 15.0, 1.0)

    rating = expert.get("rating", 5.0)
    rating_weight = min(rating / 5.0, 1.0)

    total_score = (overlap_score * 0.50 + exp_weight * 0.25 + rating_weight * 0.25) * 100
    return round(total_score, 1)


def submit_expert_bid(
    expert_id: int,
    bid_amount: float,
    notes: str,
    program_id: int = None,
    b2b_request_id: int = None,
) -> bool:
    """Submits a competitive bid / counter-proposal for a B2C program or B2B institutional request."""
    if not program_id and not b2b_request_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bids (program_id, b2b_request_id, expert_id, bid_amount_inr, counter_notes, status)
        VALUES (?, ?, ?, ?, ?, 'SUBMITTED')
        """,
        (program_id, b2b_request_id, expert_id, float(bid_amount), notes.strip()),
    )
    conn.commit()
    conn.close()
    return True
