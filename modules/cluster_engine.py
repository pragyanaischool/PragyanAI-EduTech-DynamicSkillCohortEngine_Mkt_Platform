"""
Semantic Demand Aggregation & Quorum Engine.
Evaluates micro-requests from students, aggregates common skill targets,
and triggers program compilation when enrollment thresholds are satisfied.
"""

from typing import Any, Dict, List
from config.database import get_connection
from config.settings import settings


def cluster_and_evaluate_quorum(min_quorum: int = None) -> List[Dict[str, Any]]:
    """
    Scans all pending student demand records, clusters requests by target career role
    and duration preference, and identifies clusters ready for automated program compilation.
    """
    threshold = min_quorum if min_quorum is not None else settings.MIN_QUORUM
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM student_demands 
        WHERE status = 'PENDING' OR status = 'CLUSTERED'
    """)
    demands = cursor.fetchall()

    clusters: Dict[str, List[Any]] = {}
    for d in demands:
        # Canonical cluster key based on normalized target role and duration
        key = f"{d['dream_job_role'].strip().lower().replace(' ', '_')}_{d['duration_hours']}h"
        clusters.setdefault(key, []).append(d)

    unlocked_programs: List[Dict[str, Any]] = []

    for key, group in clusters.items():
        if len(group) >= threshold:
            sample = group[0]
            # Aggregate requested skills across learners
            all_skills = set()
            for g in group:
                for s in g["target_skills"].split(","):
                    clean_s = s.strip()
                    if clean_s:
                        all_skills.add(clean_s)

            # Average willingness to pay among learners
            avg_budget = sum(g["budget_inr"] for g in group) / len(group)

            unlocked_programs.append({
                "cluster_key": key,
                "role": sample["dream_job_role"],
                "skills": ", ".join(sorted(all_skills)),
                "duration": sample["duration_hours"],
                "budget": round(avg_budget, 2),
                "enrolled_count": len(group),
                "student_ids": [g["id"] for g in group],
            })

    conn.close()
    return unlocked_programs


def mark_demands_as_locked(student_demand_ids: List[int], cluster_id: str) -> None:
    """Updates the status of aggregated student demands once a program is compiled."""
    if not student_demand_ids:
        return

    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in student_demand_ids)
    cursor.execute(
        f"""
        UPDATE student_demands 
        SET status = 'LOCKED', cluster_id = ?
        WHERE id IN ({placeholders})
        """,
        [cluster_id] + student_demand_ids,
    )
    conn.commit()
    conn.close()
