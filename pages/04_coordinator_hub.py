"""
PragyanAI Coordinator & Operations Command Center (pages/04_coordinator_hub.py)
Enables coordinators and platform admins to:
- Execute Extended Database Seed migrations on demand
- Audit and purge invalid, underpaid, or anomalous student records
- Inject new students, masked experts, and institutional requests directly into SQLite
- Provision WhatsApp community invite links and live class meeting URLs
- Access unlocked contact directories (students, trainers, institutional SPOCs)
- Scan pending student demands and compile new cohorts via LangChain RAG
- Audit direct UPI and bank transfer transactions
"""

import json
import pandas as pd
import streamlit as st
from config.database import get_connection
from config.seed_data_extended import populate_extended_seed
from modules.auth import register_user
from modules.coordinator_ops import (
    assign_coordinator_and_advance,
    get_program_contact_directory,
    update_cohort_logistics,
)
from modules.cluster_engine import cluster_and_evaluate_quorum
from modules.rag_compiler import compile_academic_syllabus

st.set_page_config(page_title="Operations Hub | PragyanAI", page_icon="⚙️", layout="wide")

st.title("⚙️ PragyanAI Operations & Coordinator Hub")
st.caption("Batch Logistics, WhatsApp Provisioning, Data Ingestion, and Exception Auditing")

user = st.session_state.get("user")
if not user or user["role"] != "coordinator":
    st.warning("⚠️ Access restricted. Please sign in with a **Coordinator / Operations** account.")
    st.stop()

# =============================================================================
# TOP ADMIN SEEDER CONTROL BAR
# =============================================================================
with st.expander("🛠️ Admin Database & Seeder Control", expanded=False):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.markdown("**Execute Extended Database Seeder**")
        st.caption("Resets tables and loads multi-stakeholder records (valid + anomalous test cases).")
    with c2:
        if st.button("⚡ Run seed_data_extended.py", type="primary", use_container_width=True):
            with st.spinner("Seeding database..."):
                stats = populate_extended_seed()
                st.success(
                    f"✅ Loaded: {stats['users_seeded']} users, "
                    f"{stats['experts_seeded']} experts, "
                    f"{stats['programs_seeded']} cohorts."
                )
                st.rerun()
    with c3:
        st.metric("Active Admin", user["username"])

st.divider()

# =============================================================================
# NAVIGATION TABS
# =============================================================================
tab_active, tab_exceptions, tab_add_entity, tab_claim, tab_clustering, tab_payments = st.tabs([
    "📋 Active Cohorts & WhatsApp Vault",
    "🚨 Invalid / At-Risk Queue",
    "➕ Add Entity (User / Expert / Request)",
    "🚀 Claim Open Programs",
    "🔄 Semantic Demand Cluster Engine",
    "💳 Direct Payment Audit Ledger"
])

# =============================================================================
# TAB 1: ACTIVE COHORTS & UNMASKED CONTACT DIRECTORY
# =============================================================================
with tab_active:
    st.subheader("Your Assigned Cohorts & Logistics")
    conn = get_connection()
    my_batches = conn.execute("""
        SELECT * FROM compiled_programs 
        WHERE coordinator_id = ? 
        ORDER BY id DESC
    """, (user["id"],)).fetchall()
    conn.close()

    if not my_batches:
        st.info("You currently have no active assigned cohorts. Claim open batches from the 'Claim Open Programs' tab.")
    else:
        for batch in my_batches:
            with st.expander(f"📍 {batch['title']} [{batch['program_id']}] — Status: {batch['status']}", expanded=True):
                prog_details, student_list = get_program_contact_directory(batch["id"])

                col1, col2 = st.columns(2)
                with col1:
                    wa_url = st.text_input(
                        "WhatsApp Group Invite URL",
                        value=batch["whatsapp_group_link"] or "",
                        key=f"wa_{batch['id']}"
                    )
                with col2:
                    meet_url = st.text_input(
                        "Live Class Meeting Link (Meet / Zoom)",
                        value=batch["meeting_link"] or "",
                        key=f"meet_{batch['id']}"
                    )

                if st.button("💾 Save Logistics & Broadcast", key=f"save_btn_{batch['id']}", use_container_width=True):
                    update_cohort_logistics(batch["id"], wa_url, meet_url)
                    st.success("✅ Logistics updated! Live links published to enrolled student dashboards.")
                    st.rerun()

                st.divider()

                # Trainer Unmasked Contacts
                st.markdown("#### 👨‍🏫 Lead Trainer Details (Unlocked)")
                t1, t2, t3 = st.columns(3)
                t1.write(f"**Name:** {prog_details.get('expert_name') or 'Pending Selection'}")
                t2.write(f"**Phone:** `{prog_details.get('expert_phone') or 'N/A'}`")
                t3.write(f"**Email:** `{prog_details.get('expert_email') or 'N/A'}`")

                if prog_details.get("expert_phone"):
                    clean_p = str(prog_details["expert_phone"]).replace("+", "").replace(" ", "").replace("-", "")
                    st.markdown(f"[💬 Chat with Trainer on WhatsApp](https://wa.me/{clean_p})")

                st.divider()

                # Participant Directory
                st.markdown(f"#### 👥 Enrolled Participants Directory ({len(student_list)} Learners)")
                if student_list:
                    df = pd.DataFrame(student_list)[[
                        "full_name", "phone", "email", "institution", "payment_mode", "transaction_reference", "amount_paid", "verification_status"
                    ]]
                    df.columns = ["Full Name", "Phone", "Email", "Institution", "Payment Mode", "Transaction UTR", "Amount (INR)", "Status"]
                    st.dataframe(df, use_container_width=True)

                    phone_nums = [str(s["phone"]).strip() for s in student_list if s.get("phone") and len(str(s["phone"]).strip()) >= 10]
                    st.text_area("📋 Copy Phone List (for Bulk WhatsApp Add)", ", ".join(phone_nums), height=70)
                else:
                    st.caption("No student enrollment records loaded for this cohort yet.")

# =============================================================================
# TAB 2: INVALID / AT-RISK QUEUE (ANOMALY DETECTION)
# =============================================================================
with tab_exceptions:
    st.subheader("🚨 Invalid & Flagged Student Exceptions")
    st.caption("Surfaces bogus transaction references, payment shortfalls, and undeliverable phone numbers.")

    conn = get_connection()
    flagged_records = conn.execute("""
        SELECT pr.id as payment_id, u.id as user_id, u.full_name, u.phone, u.email, u.institution,
               pr.transaction_reference, pr.amount_paid, pr.verification_status, 
               p.id as program_id, p.ticket_price_inr, p.title as program_title
        FROM payment_records pr
        JOIN users u ON pr.user_id = u.id
        JOIN compiled_programs p ON pr.program_id = p.id
        WHERE pr.verification_status = 'REJECTED' OR LENGTH(u.phone) < 10
        ORDER BY pr.id DESC
    """).fetchall()
    conn.close()

    if not flagged_records:
        st.success("✅ No invalid student records detected. All rosters verified.")
    else:
        st.warning(f"Found **{len(flagged_records)}** flagged records requiring coordinator action:")
        for fr in flagged_records:
            with st.container():
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{fr['full_name']}**")
                    st.caption(f"Phone: `{fr['phone']}` | Institution: {fr['institution']}\nCohort: *{fr['program_title']}*")
                with c2:
                    if fr["amount_paid"] < fr["ticket_price_inr"]:
                        st.error(f"❌ Underpaid: Paid ₹{fr['amount_paid']} / Required ₹{fr['ticket_price_inr']}")
                    if str(fr["transaction_reference"]).strip() in ("000000000000", "TEST", "1234"):
                        st.error(f"❌ Bogus UTR Reference: `{fr['transaction_reference']}`")
                    if len(str(fr["phone"]).strip()) < 10:
                        st.error(f"❌ Malformed Phone Number: `{fr['phone']}`")
                with c3:
                    if st.button("Reject & Purge", key=f"purge_{fr['payment_id']}", use_container_width=True):
                        c = get_connection()
                        cur = c.cursor()
                        cur.execute("DELETE FROM program_enrollments WHERE program_id = ? AND student_id = ?", (fr["program_id"], fr["user_id"]))
                        cur.execute("UPDATE payment_records SET verification_status = 'REJECTED' WHERE id = ?", (fr["payment_id"],))
                        c.commit()
                        c.close()
                        st.warning(f"Student {fr['full_name']} removed from active roster.")
                        st.rerun()
                st.divider()

# =============================================================================
# TAB 3: DYNAMIC DATA ADDITION (ADD ENTITY)
# =============================================================================
with tab_add_entity:
    st.subheader("➕ Manual Data Addition Console")
    st.caption("Inject new students, masked experts, or college requests directly into persistence.")

    entity_type = st.radio("Select Entity Type to Add", ["New Student", "New Skill Expert", "New College Request"], horizontal=True)

    if entity_type == "New Student":
        with st.form("admin_add_student"):
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st_name = st.text_input("Full Name")
                st_user = st.text_input("Username")
                st_pwd = st.text_input("Password", value="Pragyan@2026")
            with s_col2:
                st_phone = st.text_input("Phone Number (+91)", placeholder="+919876543210")
                st_email = st.text_input("Email Address", placeholder="student@college.edu")
                st_inst = st.text_input("College Name", value="RV College of Engineering")
                st_dept = st.text_input("Department / Semester", value="CSE 6th Sem")

            if st.form_submit_button("Register & Inject Student", use_container_width=True):
                if st_name and st_user and st_pwd:
                    ok, msg = register_user(st_user, st_pwd, st_name, "student", st_phone, st_email, st_inst, st_dept)
                    if ok:
                        st.success(f"✅ Student {st_name} successfully registered!")
                    else:
                        st.error(msg)
                else:
                    st.error("Name, username, and password are required.")

    elif entity_type == "New Skill Expert":
        with st.form("admin_add_expert"):
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                exp_name = st.text_input("Expert Full Name")
                exp_user = st.text_input("Expert Username")
                exp_pwd = st.text_input("Password", value="Pragyan@2026")
                exp_phone = st.text_input("Phone Number (+91)", placeholder="+919845001122")
            with e_col2:
                exp_vert = st.text_input("Industry Vertical", value="AI in Semiconductor EDA")
                exp_skills = st.text_area("Skills List", value="SystemVerilog, UVM, RISC-V, RTL Synthesis")
                exp_rate = st.number_input("Hourly Rate (INR)", value=3000.0, step=500.0)
                exp_bio = st.text_area("Bio / Background", value="Senior EDA Verification Lead with 12+ years experience.")

            if st.form_submit_button("Provision Masked Expert Profile", use_container_width=True):
                if exp_name and exp_user and exp_pwd:
                    ok, msg = register_user(exp_user, exp_pwd, exp_name, "expert", exp_phone, f"{exp_user}@pragyanai.com", "Industry Specialist", exp_vert)
                    if ok:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT id FROM users WHERE username = ?", (exp_user,))
                        u_row = c.fetchone()
                        if u_row:
                            c.execute("""
                                UPDATE expert_profiles 
                                SET industry_vertical = ?, skills = ?, hourly_rate_inr = ?, bio = ?
                                WHERE user_id = ?
                            """, (exp_vert, exp_skills, exp_rate, exp_bio, u_row["id"]))
                            conn.commit()
                        conn.close()
                        st.success(f"✅ Expert {exp_name} provisioned with masked token!")
                    else:
                        st.error(msg)
                else:
                    st.error("All basic fields are required.")

    elif entity_type == "New College Request":
        with st.form("admin_add_college_req"):
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                c_name = st.selectbox("Select Institution SPOC", ["Dr. K. S. Ramaiah (RVCE)", "Dr. Sudha Murthy (BMSCE)", "Prof. Venkat Raman (PES)"])
                c_type = st.selectbox("Program Type", ["FDP", "STP", "Workshop", "Guest Lecture"])
                c_scope = st.text_input("Domain Scope", value="Generative AI & Agentic Workflows for Faculty")
            with c_col2:
                c_mode = st.selectbox("Delivery Mode", ["Online", "Offline", "Hybrid"])
                c_budget = st.number_input("Budget (INR)", value=40000.0, step=5000.0)
                c_skills = st.text_input("Key Skills Required", value="LangChain, LangGraph, Python, Local LLMs")

            if st.form_submit_button("Ground via RAG & Inject Request", use_container_width=True):
                with st.spinner("Synthesizing syllabus via RAG..."):
                    syllabus = compile_academic_syllabus(c_scope, c_skills, 30, c_type)
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO institutional_requests (
                            college_id, spoc_name, spoc_phone, spoc_email, program_type,
                            scope_description, delivery_mode, budget_inr, compiled_syllabus, status
                        ) VALUES (11, 'Admin Injected SPOC', '+919880011223', 'admin.spoc@college.edu', ?, ?, ?, ?, ?, 'BIDDING')
                    """, (c_type, c_scope, c_mode, c_budget, json.dumps(syllabus)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Institutional request registered and submitted to expert bidding radar!")

# =============================================================================
# TAB 4: CLAIM UNASSIGNED PROGRAMS
# =============================================================================
with tab_claim:
    st.subheader("Open Batches Seeking Assigned Coordinators")
    conn = get_connection()
    unassigned = conn.execute("""
        SELECT * FROM compiled_programs 
        WHERE coordinator_id IS NULL OR status = 'PLEDGE_OPEN'
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    if not unassigned:
        st.info("All active programs have assigned coordinators.")
    else:
        for u in unassigned:
            with st.container():
                c_a, c_b, c_c = st.columns([3, 1, 1])
                with c_a:
                    st.markdown(f"**{u['title']}** ({u['duration_hours']} Hours)")
                    st.caption(f"ID: `{u['program_id']}` | Pledges: {u['enrolled_count']}/{u['target_quorum']} | Fee: ₹{u['ticket_price_inr']}")
                with c_b:
                    st.markdown(f"Status: `{u['status']}`")
                with c_c:
                    if st.button("Claim Batch", key=f"claim_{u['id']}", use_container_width=True):
                        assign_coordinator_and_advance(u["id"], user["id"])
                        st.success(f"Assigned to {u['program_id']}! Check 'Active Cohorts' tab.")
                        st.rerun()
                st.divider()

# =============================================================================
# TAB 5: DEMAND CLUSTERING ENGINE
# =============================================================================
with tab_clustering:
    st.subheader("Semantic Demand Aggregation Engine")
    st.write("Aggregates student micro-demands across institutions and auto-compiles launchable cohorts.")

    if st.button("⚡ Scan & Evaluate Pending Demands", use_container_width=True):
        unlocked = cluster_and_evaluate_quorum(min_quorum=2)
        if unlocked:
            st.success(f"Detected {len(unlocked)} qualified demand clusters ready for compilation!")
            for u in unlocked:
                st.markdown(f"### Target Role: {u['role']} ({u['enrolled_count']} Learners)")
                st.caption(f"Aggregated Skills: `{u['skills']}` | Avg Willingness to Pay: ₹{u['budget']}")
                
                if st.button(f"Compile & Launch Cohort: {u['role']}", key=f"comp_{u['cluster_key']}"):
                    with st.spinner("Synthesizing syllabus via RAG..."):
                        syllabus = compile_academic_syllabus(u["role"], u["skills"], u["duration"])
                        prog_id = f"PRG-2026-{abs(hash(u['cluster_key'])) % 10000:04d}"

                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO compiled_programs (
                                program_id, source_type, title, duration_hours, ticket_price_inr,
                                target_quorum, enrolled_count, syllabus_json, status, coordinator_id
                            ) VALUES (?, 'B2C_CROWD', ?, ?, ?, ?, ?, ?, 'COORDINATION', ?)
                        """, (
                            prog_id, syllabus["title"], u["duration"], u["budget"],
                            u["enrolled_count"], u["enrolled_count"], json.dumps(syllabus), user["id"]
                        ))
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 Cohort `{prog_id}` compiled and launched under your coordination!")
                        st.rerun()
        else:
            st.info("No demand clusters currently meet the launch quorum threshold.")

# =============================================================================
# TAB 6: PAYMENT AUDIT LEDGER
# =============================================================================
with tab_payments:
    st.subheader("Direct Payment Ledger (UPI & Bank Transfers)")
    conn = get_connection()
    payments = conn.execute("""
        SELECT pr.*, u.full_name, u.phone, p.title as program_title
        FROM payment_records pr
        JOIN users u ON pr.user_id = u.id
        JOIN compiled_programs p ON pr.program_id = p.id
        ORDER BY pr.id DESC
    """).fetchall()
    conn.close()

    if payments:
        p_df = pd.DataFrame([dict(r) for r in payments])[[
            "program_title", "full_name", "phone", "payer_type", "payment_mode",
            "transaction_reference", "amount_paid", "verification_status", "paid_at"
        ]]
        p_df.columns = ["Program", "Payer Name", "Phone", "Type", "Mode", "Transaction UTR", "Amount (INR)", "Status", "Timestamp"]
        st.dataframe(p_df, use_container_width=True)
    else:
        st.info("No payment transactions recorded yet.")
