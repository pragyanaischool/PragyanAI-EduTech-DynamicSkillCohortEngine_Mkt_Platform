"""
Database Seeding Script for PragyanAI DemandX.
Populates end-to-end mock records across:
- Users (Coordinators, Experts, College HODs, Students)
- Masked Expert Profiles
- Student Demand Records (B2C)
- Institutional FDP / STP Requests (B2B)
- Compiled Programs / Cohorts
- Direct Payment Records (UPI / Bank Transfer)
- Program Enrollments & Reverse Bids
"""

import json
import sqlite3
import os
from config.database import get_connection, init_db
from modules.auth import hash_password


def populate_seed_data():
    """Wipes and populates the platform database with standard seed records."""
    # Ensure tables exist
    init_db()
    conn = get_connection()
    c = conn.cursor()

    # Disable foreign keys temporarily for clean table truncate
    c.execute("PRAGMA foreign_keys = OFF;")

    tables = [
        "feedback_and_certs",
        "bids",
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

    # Standard testing password hash: Pragyan@2026
    pwd_hash = hash_password("Pragyan@2026")

    # =========================================================================
    # 1. USERS SEED (Coordinators, Experts, Colleges, Students)
    # =========================================================================
    users_data = [
        # Coordinators (PragyanAI Operational Team)
        (
            "coord_sateesh",
            pwd_hash,
            "Sateesh Ambesange",
            "coordinator",
            "+919845012345",
            "sateesh@pragyanai.com",
            "PragyanAI HQ",
            "Operations",
        ),
        (
            "coord_priya",
            pwd_hash,
            "Priya Nair",
            "coordinator",
            "+919876543210",
            "priya.nair@pragyanai.com",
            "PragyanAI Bengaluru",
            "Academic Ops",
        ),
        (
            "coord_rahul",
            pwd_hash,
            "Rahul Verma",
            "coordinator",
            "+919811223344",
            "rahul.v@pragyanai.com",
            "PragyanAI Hub",
            "Student Logistics",
        ),
        # Experts (Domain Specialists & Researchers)
        (
            "exp_arjun",
            pwd_hash,
            "Dr. Arjun Sengupta",
            "expert",
            "+919741001122",
            "arjun.sengupta@techlab.io",
            "Ex-TI / AI Systems",
            "Hardware AI",
        ),
        (
            "exp_meera",
            pwd_hash,
            "Meera Krishnan",
            "expert",
            "+919632003344",
            "meera.k@cloudsystems.com",
            "Enterprise Cloud Corp",
            "Systems Architecture",
        ),
        (
            "exp_vikram",
            pwd_hash,
            "Vikramaditya Roy",
            "expert",
            "+919523005566",
            "vikram.roy@quantai.org",
            "Quant AI Studio",
            "Generative AI",
        ),
        (
            "exp_ananya",
            pwd_hash,
            "Dr. Ananya Deshmukh",
            "expert",
            "+919414007788",
            "ananya.d@semicon.in",
            "Silicon Labs",
            "VLSI / EDA",
        ),
        (
            "exp_rohit",
            pwd_hash,
            "Rohit Kulkarni",
            "expert",
            "+919305009900",
            "rohit.k@agentic.ai",
            "OpenAgents Labs",
            "Agentic Systems",
        ),
        # College HODs / SPOCs (B2B Institutional Buyers)
        (
            "hod_rvce",
            pwd_hash,
            "Dr. K. S. Ramaiah",
            "college",
            "+919880011223",
            "hod.cse@rvce.edu.in",
            "RV College of Engineering",
            "CSE",
        ),
        (
            "hod_bmsce",
            pwd_hash,
            "Dr. Sudha Murthy",
            "college",
            "+919880022334",
            "hod.ece@bmsce.ac.in",
            "BMS College of Engineering",
            "ECE",
        ),
        (
            "hod_pes",
            pwd_hash,
            "Prof. Venkat Raman",
            "college",
            "+919880033445",
            "dean.academics@pes.edu",
            "PES University",
            "AI & ML Dept",
        ),
        (
            "hod_nitk",
            pwd_hash,
            "Dr. B. K. Subbarao",
            "college",
            "+919880044556",
            "hod.it@nitk.edu.in",
            "NITK Surathkal",
            "Information Tech",
        ),
        # Students (B2C Demand Generators)
        (
            "stu_aarav",
            pwd_hash,
            "Aarav Sharma",
            "student",
            "+919100110011",
            "aarav.s@gmail.com",
            "RV College of Engineering",
            "CSE 6th Sem",
        ),
        (
            "stu_sneha",
            pwd_hash,
            "Sneha Hegde",
            "student",
            "+919100110012",
            "sneha.h@gmail.com",
            "BMS College of Engineering",
            "ECE 8th Sem",
        ),
        (
            "stu_karan",
            pwd_hash,
            "Karan Patel",
            "student",
            "+919100110013",
            "karan.p@gmail.com",
            "PES University",
            "AI 4th Sem",
        ),
        (
            "stu_divya",
            pwd_hash,
            "Divya Iyer",
            "student",
            "+919100110014",
            "divya.i@gmail.com",
            "NITK Surathkal",
            "IT 6th Sem",
        ),
        (
            "stu_manish",
            pwd_hash,
            "Manish Reddy",
            "student",
            "+919100110015",
            "manish.r@gmail.com",
            "MSRIT Bengaluru",
            "CSE 8th Sem",
        ),
        (
            "stu_tanvi",
            pwd_hash,
            "Tanvi Joshi",
            "student",
            "+919100110016",
            "tanvi.j@gmail.com",
            "Dayananda Sagar CE",
            "ECE 6th Sem",
        ),
        (
            "stu_aditya",
            pwd_hash,
            "Aditya Rao",
            "student",
            "+919100110017",
            "aditya.r@gmail.com",
            "BMSIT Bengaluru",
            "CSE 4th Sem",
        ),
        (
            "stu_pooja",
            pwd_hash,
            "Pooja Bhat",
            "student",
            "+919100110018",
            "pooja.b@gmail.com",
            "RVCE Bengaluru",
            "ISE 6th Sem",
        ),
    ]

    c.executemany(
        """
        INSERT INTO users (username, password_hash, full_name, role, phone, email, institution, department)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        users_data,
    )

    # =========================================================================
    # 2. EXPERT PROFILES SEED (Masked Tokens & Verified Metrics)
    # =========================================================================
    # User IDs 4, 5, 6, 7, 8
    experts_data = [
        (
            4,
            "EXP-M0412",
            "Semiconductor & Embedded AI Systems",
            15,
            "RISC-V, RTL Verification, TinyML, Verilog, Edge AI",
            48,
            4.92,
            3500.0,
            "Principal Hardware AI Architect with 15+ years experience in EDA verification and silicon validation.",
        ),
        (
            5,
            "EXP-M0523",
            "Cloud Infrastructure & LLMOps",
            11,
            "Docker, Kubernetes, Triton Server, vLLM, AWS, Terraform",
            34,
            4.85,
            3000.0,
            "Senior Cloud Architect specializing in distributed LLM serving, GPU cluster provisioning, and inference latency.",
        ),
        (
            6,
            "EXP-M0634",
            "Generative AI & Enterprise RAG",
            9,
            "LangChain, LlamaIndex, FAISS, Graph RAG, Multi-Vector Retrieval",
            62,
            4.96,
            2800.0,
            "Staff AI Engineer focused on enterprise knowledge assistants, hybrid semantic search, and evaluation pipelines.",
        ),
        (
            7,
            "EXP-M0745",
            "VLSI Front-End & FPGA Design",
            13,
            "SystemVerilog, UVM, FPGA Prototyping, Xilinx Vivado, ASIC",
            29,
            4.78,
            3200.0,
            "Former Lead Verification Engineer at Tier-1 semiconductor MNC; IEEE technical speaker and FDP mentor.",
        ),
        (
            8,
            "EXP-M0856",
            "Autonomous Agents & Tool Orchestration",
            7,
            "LangGraph, Model Context Protocol (MCP), CrewAI, AutoGen, Python",
            41,
            4.89,
            2500.0,
            "Agentic AI specialist building cyclic stateful multi-agent workflows and MCP enterprise tool servers.",
        ),
    ]

    c.executemany(
        """
        INSERT INTO expert_profiles (user_id, token, industry_vertical, experience_years, skills, sessions_completed, rating, hourly_rate_inr, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        experts_data,
    )

    # =========================================================================
    # 3. STUDENT DEMAND POOL SEED (Individual Micro-Requests)
    # =========================================================================
    # User IDs 13 to 20
    demands_data = [
        (13, "Agentic AI Engineer", "LangGraph, MCP, Multi-Agent Tool Calling", 15, 250.0, "agentic_ai_15h", "CLUSTERED"),
        (14, "Agentic AI Engineer", "LangGraph, Cyclic State Machines, FastEmbed", 15, 250.0, "agentic_ai_15h", "CLUSTERED"),
        (15, "Agentic AI Engineer", "AI Agents, MCP Servers, LangGraph, Python", 15, 300.0, "agentic_ai_15h", "CLUSTERED"),
        (16, "RAG Systems Engineer", "Hybrid Search, FAISS, Cross-Encoders, LangChain", 10, 200.0, "rag_systems_10h", "CLUSTERED"),
        (17, "RAG Systems Engineer", "RAG Pipeline, Vector DBs, BM25, LlamaIndex", 10, 200.0, "rag_systems_10h", "CLUSTERED"),
        (18, "VLSI Verification Engineer", "SystemVerilog, UVM, RTL Testbench", 20, 300.0, "vlsi_uvm_20h", "PENDING"),
        (19, "TinyML Embedded Engineer", "Edge Impulse, MicroPython, ESP32 TinyML", 15, 150.0, "tinyml_15h", "PENDING"),
        (20, "Generative AI Developer", "Fine-Tuning, LoRA, HuggingFace, PyTorch", 25, 300.0, "genai_finetune_25h", "PENDING"),
    ]

    c.executemany(
        """
        INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, cluster_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        demands_data,
    )

    # =========================================================================
    # 4. COMPILED PROGRAMS / COHORTS SEED
    # =========================================================================
    syllabus_agentic = {
        "title": "Production Agentic AI & Model Context Protocol (MCP)",
        "duration_hours": 15,
        "target_audience": "UG/PG Engineering Students & Aspiring AI Engineers",
        "modules": [
            {
                "unit": 1,
                "topic": "Foundations of Agentic Workflows vs Standard LLM APIs",
                "concepts": ["ReAct Pattern", "Function Calling Protocols"],
                "lab_deliverable": "Building Deterministic Tool Dispatcher",
            },
            {
                "unit": 2,
                "topic": "Stateful Orchestration with LangGraph",
                "concepts": ["Cyclic Graphs", "State Reducers", "Human-in-the-Loop"],
                "lab_deliverable": "Multi-Step Code Review Agent",
            },
            {
                "unit": 3,
                "topic": "Model Context Protocol (MCP) Integration",
                "concepts": ["MCP Server-Client Architecture", "STDIO Transport"],
                "lab_deliverable": "Local SQLite MCP Query Assistant",
            },
            {
                "unit": 4,
                "topic": "Agent Evaluation & Production Observability",
                "concepts": ["Trajectory Eval", "LangSmith Traces"],
                "lab_deliverable": "Benchmark Suite for Agent Resiliency",
            },
        ],
        "case_studies": ["Autonomous Financial Document Parser", "Enterprise Multi-Agent Customer Support Swarm"],
        "capstone_project": "Full-Stack Autonomous Market Intelligence Agent with Web Search & PDF Parsing",
        "recommended_quorum": 5,
    }

    syllabus_rag = {
        "title": "Enterprise RAG Architectures & Vector Search",
        "duration_hours": 10,
        "target_audience": "Pre-final / Final Year CS/IT Students",
        "modules": [
            {
                "unit": 1,
                "topic": "Chunking Strategies & Dense Embeddings",
                "concepts": ["Recursive Splitting", "Semantic Chunking"],
                "lab_deliverable": "Vector Index Benchmarking in FAISS",
            },
            {
                "unit": 2,
                "topic": "Hybrid Retrieval & Cross-Encoder Re-Ranking",
                "concepts": ["BM25 + Dense Fusion", "FlashRank"],
                "lab_deliverable": "End-to-End Enterprise PDF Q&A Pipeline",
            },
        ],
        "case_studies": ["Legal Case Precedent Search", "Clinical Trial Literature Mining"],
        "capstone_project": "Multi-Tenant Enterprise Knowledge Base with Source Citation Guardrails",
        "recommended_quorum": 5,
    }

    programs_data = [
        # Cohort 1 - Live with WhatsApp and Meet Links
        (
            "PRG-2026-AGNT-0042",
            "B2C_CROWD",
            "Production Agentic AI & Model Context Protocol (MCP)",
            15,
            250.0,
            5,
            3,
            json.dumps(syllabus_agentic),
            5,
            1,
            "LIVE",
            "https://chat.whatsapp.com/sampleInviteLinkAgnt2026",
            "https://meet.google.com/abc-prag-xyz",
        ),
        # Cohort 2 - Quorum Reached, Pending Coordinator Assignment
        (
            "PRG-2026-RAG-0018",
            "B2C_CROWD",
            "Enterprise RAG Architectures & Vector Search",
            10,
            200.0,
            5,
            2,
            json.dumps(syllabus_rag),
            3,
            None,
            "PAYMENT_PENDING",
            "",
            "",
        ),
        # Cohort 3 - Open for Pledges
        (
            "PRG-2026-VLSI-0091",
            "B2C_CROWD",
            "Advanced SystemVerilog & UVM Verification Bootcamp",
            20,
            300.0,
            10,
            1,
            json.dumps(syllabus_agentic),
            1,
            None,
            "PLEDGE_OPEN",
            "",
            "",
        ),
    ]

    c.executemany(
        """
        INSERT INTO compiled_programs (
            program_id, source_type, title, duration_hours, ticket_price_inr,
            target_quorum, enrolled_count, syllabus_json, expert_id, coordinator_id,
            status, whatsapp_group_link, meeting_link
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        programs_data,
    )

    # =========================================================================
    # 5. PAYMENT LEDGER & PROGRAM ENROLLMENTS
    # =========================================================================
    payments_data = [
        (1, 13, "STUDENT", "UPI", "UPI/2026/884920194820", 250.0, "VERIFIED"),
        (1, 14, "STUDENT", "UPI", "UPI/2026/773829104821", 250.0, "VERIFIED"),
        (1, 15, "STUDENT", "NEFT_IMPS", "IMPS-6029381048", 250.0, "VERIFIED"),
        (2, 16, "STUDENT", "UPI", "UPI/2026/993810294811", 200.0, "VERIFIED"),
        (2, 17, "STUDENT", "Bank_Transfer", "HDFC-TXN-994820", 200.0, "VERIFIED"),
    ]

    c.executemany(
        """
        INSERT INTO payment_records (
            program_id, user_id, payer_type, payment_mode,
            transaction_reference, amount_paid, verification_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        payments_data,
    )

    enrollments_data = [
        (1, 13, 1),
        (1, 14, 2),
        (1, 15, 3),
        (2, 16, 4),
        (2, 17, 5),
    ]

    c.executemany(
        """
        INSERT INTO program_enrollments (program_id, student_id, payment_ref_id)
        VALUES (?, ?, ?)
    """,
        enrollments_data,
    )

    # =========================================================================
    # 6. INSTITUTIONAL B2B REQUESTS & REVERSE BIDS
    # =========================================================================
    syllabus_fdp = {
        "title": "5-Day National Faculty Development Program on AI in EDA & RTL Design",
        "duration_hours": 30,
        "program_type": "FDP",
        "modules": [
            {
                "unit": 1,
                "topic": "Introduction to AI/ML in Electronic Design Automation",
                "concepts": ["Placement Optimization", "Timing Closure"],
                "lab_deliverable": "OpenROAD Python Tooling",
            },
            {
                "unit": 2,
                "topic": "LLMs for Verilog Generation & Testbench Automation",
                "concepts": ["Prompt Engineering for RTL", "Syntax Correction"],
                "lab_deliverable": "Automated HDL Code Generator",
            },
        ],
        "case_studies": ["Semiconductor RTL Bug Detection using Transformers"],
        "capstone_project": "Hands-on Synthesis & Automated Testbench Framework for RISC-V Core",
    }

    requests_data = [
        (
            9,
            "Dr. K. S. Ramaiah",
            "+919880011223",
            "hod.cse@rvce.edu.in",
            "FDP",
            "5-Day FDP on AI in Semiconductor EDA & RTL Design",
            "Hybrid",
            45000.0,
            json.dumps(syllabus_fdp),
            1,
            "BIDDING",
        ),
        (
            10,
            "Dr. Sudha Murthy",
            "+919880022334",
            "hod.ece@bmsce.ac.in",
            "STP",
            "Short Term Training Program on Edge AI & TinyML on RISC-V",
            "Online",
            25000.0,
            json.dumps(syllabus_fdp),
            None,
            "BIDDING",
        ),
        (
            11,
            "Prof. Venkat Raman",
            "+919880033445",
            "dean.academics@pes.edu",
            "Workshop",
            "2-Day Hands-on Workshop on Enterprise LangGraph & Agentic Systems",
            "Offline",
            35000.0,
            json.dumps(syllabus_agentic),
            5,
            "COORDINATION",
        ),
    ]

    c.executemany(
        """
        INSERT INTO institutional_requests (
            college_id, spoc_name, spoc_phone, spoc_email,
            program_type, scope_description, delivery_mode,
            budget_inr, compiled_syllabus, selected_expert_id, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        requests_data,
    )

    bids_data = [
        (
            None,
            1,
            1,
            42000.0,
            "Will deliver with comprehensive lab handouts, Vivado test scripts, and FPGA demo kits for offline portion.",
            "SUBMITTED",
        ),
        (
            None,
            1,
            4,
            45000.0,
            "Includes 5 hands-on lab sessions on RTL verification with complete GitHub starter repo.",
            "SUBMITTED",
        ),
        (
            None,
            2,
            1,
            24000.0,
            "Available for online weekend slots; includes live TinyML deployment on microcontrollers.",
            "SUBMITTED",
        ),
        (
            None,
            3,
            5,
            35000.0,
            "Full 2-day offline intensive on campus with multi-agent orchestration codebases.",
            "ACCEPTED",
        ),
    ]

    c.executemany(
        """
        INSERT INTO bids (program_id, b2b_request_id, expert_id, bid_amount_inr, counter_notes, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        bids_data,
    )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    populate_seed_data()
