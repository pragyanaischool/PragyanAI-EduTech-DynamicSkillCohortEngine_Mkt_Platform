"""
Domain Services & Intelligence Layer for PragyanAI DemandX.

Exposes core business logic modules:
- Authentication & RBAC (auth)
- Semantic Clustering & Quorum Gates (cluster_engine)
- Coordinator Logistics & WhatsApp Provisioning (coordinator_ops)
- Anonymized Marketplace & Counter-Bidding (expert_marketplace)
- Courseware & LMS Document Parsers (media_viewer)
- RAG Program Compiler (rag_compiler)
"""

from modules.auth import authenticate_user, hash_password, register_user, verify_password
from modules.cluster_engine import cluster_and_evaluate_quorum
from modules.coordinator_ops import (
    assign_coordinator_and_advance,
    get_program_contact_directory,
    update_cohort_logistics,
)
from modules.expert_marketplace import (
    calculate_expert_fit_score,
    get_anonymized_expert_roster,
    submit_expert_bid,
)
from modules.media_viewer import render_pdf, render_ppt, render_video
from modules.rag_compiler import compile_academic_syllabus, get_vector_store

__all__ = [
    "authenticate_user",
    "hash_password",
    "register_user",
    "verify_password",
    "cluster_and_evaluate_quorum",
    "assign_coordinator_and_advance",
    "get_program_contact_directory",
    "update_cohort_logistics",
    "calculate_expert_fit_score",
    "get_anonymized_expert_roster",
    "submit_expert_bid",
    "render_pdf",
    "render_ppt",
    "render_video",
    "compile_academic_syllabus",
    "get_vector_store",
]
