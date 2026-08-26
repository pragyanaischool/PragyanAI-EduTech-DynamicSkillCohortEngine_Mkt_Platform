"""
Extended Multi-Stakeholder Database Seeding Module for PragyanAI DemandX.
Populates standard, anomalous, and edge-case records for testing and operations.
"""

import json
import sqlite3
from config.database import get_connection, init_db
from modules.auth import hash_password


def populate_extended_seed() -> dict:
    """Wipes and populates the database with extended multi-role and invalid data."""
    init_db()
    conn = get_connection()
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = OFF;")
    tables = [
        "feedback_and_certs",
        "bids",
        "cohort_expressions_of_interest",
        "program_enrollments",
        "payment_records",
        "compiled_programs",
        "institutional_requests",
        "student_demands",
        "expert_profiles",
        "users",
    ]
    for table in tables:
        c.execute(f"DELETE FROM {table};")
        c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
    c.execute("PRAGMA foreign_keys = ON;")

    pwd_hash = hash_password("Pragyan@2026")

    # -------------------------------------------------------------------------
    # 1. USERS (Coordinators, Experts, Colleges, Valid & Invalid Students)
    # -------------------------------------------------------------------------
    users = [
        # Coordinators (IDs: 1, 2, 3)
        ("coord_sateesh", pwd_hash, "Sateesh Ambesange", "coordinator", "+919845012345", "sateesh@pragyanai.com", "PragyanAI HQ", "Executive Operations"),
        ("coord_priya", pwd_hash, "Priya Nair", "coordinator", "+919876543210", "priya.nair@pragyanai.com", "PragyanAI Bengaluru", "Academic Quality"),
        ("coord_rahul", pwd_hash, "Rahul Verma", "coordinator", "+919811223344", "rahul.v@pragyanai.com", "PragyanAI Hub", "Student Logistics"),

        # Experts (IDs: 4, 5, 6, 7, 8, 9, 10)
        ("exp_arjun", pwd_hash, "Dr. Arjun Sengupta", "expert", "+919741001122", "arjun.sengupta@techlab.io", "Ex-TI / AI Systems", "Hardware AI"),
        ("exp_meera", pwd_hash, "Meera Krishnan", "expert", "+919632003344", "meera.k@cloudsystems.com", "Enterprise Cloud Corp", "Systems Architecture"),
        ("exp_vikram", pwd_hash, "Vikramaditya Roy", "expert", "+919523005566", "vikram.roy@quantai.org", "Quant AI Studio", "Generative AI"),
        ("exp_ananya", pwd_hash, "Dr. Ananya Deshmukh", "expert", "+919414007788", "ananya.d@semicon.in", "Silicon Labs", "VLSI / EDA"),
        ("exp_rohit", pwd_hash, "Rohit Kulkarni", "expert", "+919305009900", "rohit.k@agentic.ai", "OpenAgents Labs", "Agentic Systems"),
        ("exp_harish", pwd_hash, "Dr. Harish Madhavan", "expert", "+919845209911", "harish.m@edgeai.org", "Ex-Qualcomm / Edge Labs", "Edge AI & DSP"),
        ("exp_deepa", pwd_hash, "Deepa Sundaram", "expert", "+919845308822", "deepa.s@securityai.in", "CyberTech AI", "AI Security & Guardrails"),

        # Colleges (IDs: 11, 12, 13, 14)
        ("hod_rvce", pwd_hash, "Dr. K. S. Ramaiah", "college", "+919880011223", "hod.cse@rvce.edu.in", "RV College of Engineering", "CSE"),
        ("hod_bmsce", pwd_hash, "Dr. Sudha Murthy", "college", "+919880022334", "hod.ece@bmsce.ac.in", "BMS College of Engineering", "ECE"),
        ("hod_pes", pwd_hash, "Prof. Venkat Raman", "college", "+919880033445", "dean.academics@pes.edu", "PES University", "AI & ML Dept"),
        ("hod_nitk", pwd_hash, "Dr. B. K. Subbarao", "college", "+919880044556", "hod.it@nitk.edu.in", "NITK Surathkal", "Information Tech"),

        # Valid Students (IDs: 15, 16, 17, 18, 19, 20)
        ("stu_aarav", pwd_hash, "Aarav Sharma", "student", "+919100110011", "aarav.s@gmail.com", "RV College of Engineering", "CSE 6th Sem"),
        ("stu_sneha", pwd_hash, "Sneha Hegde", "student", "+919100110012", "sneha.h@gmail.com", "BMS College of Engineering", "ECE 8th Sem"),
        ("stu_karan", pwd_hash, "Karan Patel", "student", "+919100110013", "karan.p@gmail.com", "PES University", "AI 4th Sem"),
        ("stu_divya", pwd_hash, "Divya Iyer", "student", "+919100110014", "divya.i@gmail.com", "NITK Surathkal", "IT 6th Sem"),
        ("stu_kavya", pwd_hash, "Kavya Nambiar", "student", "+919871122334", "kavya.n@gmail.com", "PES University", "CSE 6th Sem"),
        ("stu_rahul_m", pwd_hash, "Rahul Menasinkai", "student", "+919844001122", "rahul.m@bmsce.ac.in", "BMS College of Engineering", "ECE 4th Sem"),

        # Flagged / Invalid Students (IDs: 21, 22, 23, 24)
        ("stu_bad_utr", pwd_hash, "Abhishek 'FakeUTR' Gowda", "student", "+919900112233", "abhi.fake@gmail.com", "VTU Affiliated Inst", "Mech 8th Sem"),
        ("stu_underpaid", pwd_hash, "Naveen 'PartialPay' Kumar", "student", "+919944556677", "naveen.k@gmail.com", "RIT Bengaluru", "ISE 6th Sem"),
        ("stu_bad_phone", pwd_hash, "Sanjay 'NoWhatsApp' Rao", "student", "98450", "sanjay.badphone@gmail.com", "DSCE Bengaluru", "CSE 4th Sem"),
        ("stu_unmet_pre", pwd_hash, "Tarun 'NonCS' Varma", "student", "+919733445566", "tarun.v@gmail.com", "Global Academy", "Civil 2nd Sem"),
    ]

    c.executemany("""
        INSERT INTO users (username, password_hash, full_name, role, phone, email, institution, department)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # -------------------------------------------------------------------------
    # 2. EXPERT PROFILES (Masked Tokens & Verified Specs)
    # -------------------------------------------------------------------------
    experts = [
        (4, "EXP-M0412", "Semiconductor & Embedded AI Systems", 15, "RISC-V, RTL Verification, TinyML, Verilog, Edge AI", 48, 4.92, 3500.0, "Principal Hardware AI Architect with 15+ years experience in EDA verification."),
        (5, "EXP-M0523", "Cloud Infrastructure & LLMOps", 11, "Docker, Kubernetes, Triton Server, vLLM, AWS, Terraform", 34, 4.85, 3000.0, "Senior Cloud Architect specializing in distributed LLM serving and GPU clusters."),
        (6, "EXP-M0634", "Generative AI & Enterprise RAG", 9, "LangChain, LlamaIndex, FAISS, Graph RAG, Multi-Vector Retrieval", 62, 4.96, 2800.0, "Staff AI Engineer focused on enterprise knowledge assistants."),
        (7, "EXP-M0745", "VLSI Front-End & FPGA Design", 13, "SystemVerilog, UVM, FPGA Prototyping, Xilinx Vivado, ASIC", 29, 4.78, 3200.0, "Lead Verification Engineer; IEEE technical speaker and FDP mentor."),
        (8, "EXP-M0856", "Autonomous Agents & Tool Orchestration", 7, "LangGraph, Model Context Protocol (MCP), CrewAI, AutoGen, Python", 41, 4.89, 2500.0, "Agentic AI specialist building cyclic stateful multi-agent workflows."),
        (9, "EXP-M0967", "Edge AI, TinyML & DSP Quantization", 14, "Edge Impulse, C++, CMSIS-NN, ESP32, TensorRT", 52, 4.94, 3400.0, "Principal Edge AI Specialist with 14+ years in embedded firmware."),
        (10, "EXP-M1078", "LLM Security, Red-Teaming & Guardrails", 8, "NeMo Guardrails, Llama-Guard, OWASP Top 10 for LLMs, PyRIT", 38, 4.88, 2700.0, "Security Researcher specializing in prompt injection defenses."),
    ]

    c.executemany("""
        INSERT INTO expert_profiles (user_id, token, industry_vertical, experience_years, skills, sessions_completed, rating, hourly_rate_inr, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, experts)

    # -------------------------------------------------------------------------
    # 3. COMPILED COHORTS & PROGRAMS
    # -------------------------------------------------------------------------
    syllabus_agentic = {
        "title": "Production Agentic AI & Model Context Protocol (MCP)",
        "duration_hours": 15,
        "target_audience": "UG/PG Students & AI Engineers",
        "modules": [
            {"unit": 1, "topic": "Agentic Architecture vs APIs", "concepts": ["ReAct Pattern", "Tool Calling"], "lab_deliverable": "Tool Dispatcher"},
            {"unit": 2, "topic": "LangGraph Stateful Workflows", "concepts": ["Cyclic Graphs", "State Reducers"], "lab_deliverable": "Code Review Agent"},
            {"unit": 3, "topic": "Model Context Protocol (MCP)", "concepts": ["Server-Client Architecture", "STDIO"], "lab_deliverable": "SQLite MCP Query Assistant"}
        ],
        "capstone_project": "Full-Stack Autonomous Market Intelligence Agent",
        "recommended_quorum": 5
    }

    syllabus_rag = {
        "title": "Enterprise RAG Architectures & Vector Search",
        "duration_hours": 10,
        "target_audience": "Final Year CS/IT Students",
        "modules": [
            {"unit": 1, "topic": "Dense Retrieval & Chunking", "concepts": ["Recursive Splitting", "FAISS"], "lab_deliverable": "Vector Search Benchmark"},
            {"unit": 2, "topic": "Hybrid Reranking", "concepts": ["BM25", "Cross-Encoders"], "lab_deliverable": "Enterprise PDF QA System"}
        ],
        "capstone_project": "Multi-Tenant Enterprise Knowledge Base",
        "recommended_quorum": 5
    }

    programs = [
        ("PRG-2026-AGNT-0042", "B2C_CROWD", "Production Agentic AI & Model Context Protocol (MCP)", 15, 250.0, 5, 4, json.dumps(syllabus_agentic), 5, 1, "LIVE", "https://chat.whatsapp.com/sampleInviteLinkAgnt2026", "https://meet.google.com/abc-prag-xyz"),
        ("PRG-2026-RAG-0018", "B2C_CROWD", "Enterprise RAG Architectures & Vector Search", 10, 200.0, 5, 2, json.dumps(syllabus_rag), 3, 2, "PAYMENT_PENDING", "", ""),
        ("PRG-2026-VLSI-0091", "B2C_CROWD", "Advanced SystemVerilog & UVM Verification Bootcamp", 20, 300.0, 10, 1, json.dumps(syllabus_agentic), 1, None, "PLEDGE_OPEN", "", "")
    ]

    c.executemany("""
        INSERT INTO compiled_programs (program_id, source_type, title, duration_hours, ticket_price_inr, target_quorum, enrolled_count, syllabus_json, expert_id, coordinator_id, status, whatsapp_group_link, meeting_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, programs)

    # -------------------------------------------------------------------------
    # 4. DIRECT PAYMENT TRANSACTIONS (Audit Ledger with Valid & Rejections)
    # -------------------------------------------------------------------------
    payments = [
        # Valid Verified Payments
        (1, 15, "STUDENT", "UPI", "UPI/2026/884920194820", 250.0, "VERIFIED"),
        (1, 16, "STUDENT", "UPI", "UPI/2026/773829104821", 250.0, "VERIFIED"),
        (1, 17, "STUDENT", "NEFT_IMPS", "IMPS-6029381048", 250.0, "VERIFIED"),
        (2, 18, "STUDENT", "UPI", "UPI/2026/993810294811", 200.0, "VERIFIED"),
        (1, 19, "STUDENT", "UPI", "UPI/2026/112233994455", 250.0, "VERIFIED"),

        # Anomalous & Rejected Payments
        (1, 21, "STUDENT", "UPI", "000000000000", 250.0, "REJECTED"),          # Fake UTR
        (1, 22, "STUDENT", "UPI", "UPI/2026/PARTIALPAY01", 50.0, "REJECTED"),   # Underpaid (₹50 of ₹250)
        (1, 23, "STUDENT", "UPI", "UPI/2026/778899001122", 250.0, "VERIFIED"),  # Valid UTR but malformed phone number
    ]

    c.executemany("""
        INSERT INTO payment_records (program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, payments)

    # Enrollments linking payments
    enrollments = [
        (1, 15, 1),
        (1, 16, 2),
        (1, 17, 3),
        (2, 18, 4),
        (1, 19, 5),
        (1, 21, 6),
        (1, 22, 7),
        (1, 23, 8),
    ]
    c.executemany("""
        INSERT INTO program_enrollments (program_id, student_id, payment_ref_id)
        VALUES (?, ?, ?)
    """, enrollments)

    # -------------------------------------------------------------------------
    # 5. INSTITUTIONAL REQUESTS & REVERSE BIDS
    # -------------------------------------------------------------------------
    syllabus_fdp = {
        "title": "5-Day National FDP on AI in Semiconductor EDA & RTL Design",
        "duration_hours": 30,
        "program_type": "FDP",
        "modules": [
            {"unit": 1, "topic": "AI in EDA", "concepts": ["Placement Optimization", "Timing Closure"], "lab_deliverable": "OpenROAD Python"},
            {"unit": 2, "topic": "LLMs for Verilog RTL", "concepts": ["Prompt Engineering for RTL"], "lab_deliverable": "HDL Code Generator"}
        ],
        "capstone_project": "Synthesis and Testbench Framework for RISC-V Core"
    }

    requests = [
        (11, "Dr. K. S. Ramaiah", "+919880011223", "hod.cse@rvce.edu.in", "FDP", "5-Day FDP on AI in Semiconductor EDA & RTL Design", "Hybrid", 45000.0, json.dumps(syllabus_fdp), 1, "BIDDING"),
        (12, "Dr. Sudha Murthy", "+919880022334", "hod.ece@bmsce.ac.in", "STP", "Short Term Training on Edge AI & TinyML on RISC-V", "Online", 25000.0, json.dumps(syllabus_fdp), None, "BIDDING"),
        (13, "Prof. Venkat Raman", "+919880033445", "dean.academics@pes.edu", "Workshop", "2-Day Workshop on Enterprise LangGraph & Agentic Systems", "Offline", 35000.0, json.dumps(syllabus_agentic), 5, "COORDINATION")
    ]

    c.executemany("""
        INSERT INTO institutional_requests (college_id, spoc_name, spoc_phone, spoc_email, program_type, scope_description, delivery_mode, budget_inr, compiled_syllabus, selected_expert_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, requests)

    bids = [
        (None, 1, 1, 42000.0, "Includes lab handouts and Vivado test scripts.", "SUBMITTED"),
        (None, 1, 4, 45000.0, "Complete GitHub repo with RTL verification testbenches.", "SUBMITTED"),
        (None, 2, 6, 24000.0, "Live TinyML deployment on microcontrollers.", "SUBMITTED"),
        (None, 3, 5, 35000.0, "2-day offline intensive on campus.", "ACCEPTED")
    ]

    c.executemany("""
        INSERT INTO bids (program_id, b2b_request_id, expert_id, bid_amount_inr, counter_notes, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, bids)

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "users_seeded": len(users),
        "experts_seeded": len(experts),
        "programs_seeded": len(programs),
        "payments_seeded": len(payments),
        "requests_seeded": len(requests),
    }


if __name__ == "__main__":
    result = populate_extended_seed()
    print("✅ Extended database seed completed:", result)
