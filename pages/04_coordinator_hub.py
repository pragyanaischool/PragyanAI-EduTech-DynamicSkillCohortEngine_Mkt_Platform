"""
PragyanAI Coordinator & Operations Command Center
Enables coordinators to claim unassigned cohorts, manage WhatsApp invite links,
view unmasked participant/trainer contact directories, and audit direct UPI payment UTRs.
"""

import json
import pandas as pd
import streamlit as st
from config.database import get_connection
from modules.coordinator_ops import (
    assign_coordinator_and_advance,
    update_cohort_logistics,
    get_program_contact_directory
)
from modules.cluster_engine import cluster_and_evaluate_quorum
from modules.rag_compiler import compile_academic_syllabus

st.title("⚙️ PragyanAI Operations & Coordinator Hub")
st.caption("Manage Batch Logistics, WhatsApp Groups, Participant Rosters, and Payment Verifications")

user = st.session_state.get("user")
if not user or user["role"] != "coordinator":
    st.warning("⚠️ Access restricted. Please sign in with a **Coordinator** account using the sidebar.")
    st.stop()

tab_active, tab_claim, tab_clustering, tab_payments = st.tabs([
    "📋 My Active Batches & Contact Vault",
    "🚀 Unassigned Programs (Claim Radar)",
    "🔄 Semantic Demand Cluster Engine",
    "💳 Direct Payment Audit Ledger"
])

# ----------------- TAB 1: ACTIVE BATCHES & DIRECTORY -----------------
with tab_active:
    st.subheader("Your Assigned Cohorts & Live Logistics")
    conn = get_connection()
    my_batches = conn.execute("""
        SELECT * FROM compiled_programs 
        WHERE coordinator_id = ? 
        ORDER BY id DESC
    """, (user["id"],)).fetchall()
    conn.close()

    if not my_batches:
        st.info("You currently have no active assigned cohorts. Claim open batches from the 'Unassigned Programs' tab.")
    else:
        for batch in my_batches:
            with st.expander(f"📍 {batch['title']} [{batch['program_id']}] — Status: {batch['status']}", expanded=True):
                prog_details, student_list = get_program_contact_directory(batch["id"])

                # --- Logistics Form ---
                col1, col2 = st.columns(2)
                with col1:
                    wa_url = st.text_input("WhatsApp Community Group Invite URL", value=batch["whatsapp_group_link"] or "", key=f"wa_{batch['id']}")
                with col2:
                    meet_url = st.text_input("Live Class Meeting Link (Google Meet / Zoom)", value=batch["meeting_link"] or "", key=f"meet_{batch['id']}")

                if st.button("💾 Save Logistics & Broadcast to Cohort", key=f"save_btn_{batch['id']}", use_container_width=True):
                    update_cohort_logistics(batch["id"], wa_url, meet_url)
                    st.success("✅ Logistics updated! Live links are now published on student dashboards.")
                    st.rerun()

                st.divider()

                # --- Trainer Unmasked Contacts ---
                st.markdown("#### 👨‍🏫 Lead Trainer Details (Unlocked)")
                t1, t2, t3 = st.columns(3)
                t1.write(f"**Name:** {prog_details.get('expert_name') or 'Pending Selection'}")
                t2.write(f"**Phone:** `{prog_details.get('expert_phone') or 'N/A'}`")
                t3.write(f"**Email:** `{prog_details.get('expert_email') or 'N/A'}`")

                if prog_details.get("expert_phone"):
                    clean_p = prog_details["expert_phone"].replace("+", "").replace(" ", "")
                    st.markdown(f"[💬 Chat with Trainer on WhatsApp](https://wa.me/{clean_p})")

                st.divider()

                # --- Participant Directory ---
                st.markdown(f"#### 👥 Enrolled Participants Directory ({len(student_list)} Learners)")
                if student_list:
                    df = pd.DataFrame(student_list)[[
                        "full_name", "phone", "email", "institution", "payment_mode", "transaction_reference", "amount_paid"
                    ]]
                    df.columns = ["Full Name", "Phone", "Email", "Institution", "Payment Mode", "Transaction UTR", "Amount (INR)"]
                    st.dataframe(df, use_container_width=True)

                    # Bulk phone list for WhatsApp group broadcast
                    phone_nums = [s["phone"].strip() for s in student_list if s.get("phone")]
                    st.text_area("📋 Copy Phone List (for Bulk WhatsApp Group Add)", ", ".join(phone_nums), height=70)
                else:
                    st.caption("No student enrollment records loaded for this cohort yet.")

# ----------------- TAB 2: UNASSIGNED PROGRAMS -----------------
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
        st.info("All current programs have assigned coordinators.")
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
                        st.success(f"Assigned to {u['program_id']}! Manage logistics in 'My Active Batches'.")
                        st.rerun()
                st.divider()

# ----------------- TAB 3: CLUSTERING ENGINE -----------------
with tab_clustering:
    st.subheader("Run Semantic Demand Aggregation Pipeline")
    st.write("Clusters raw student micro-requests into structured curricula and launches candidate batches.")

    if st.button("⚡ Scan & Evaluate Pending Student Requests", use_container_width=True):
        unlocked = cluster_and_evaluate_quorum(min_quorum=2)  # Demo threshold
        if unlocked:
            st.success(f"Detected {len(unlocked)} qualified demand clusters ready for compilation!")
            for u in unlocked:
                st.markdown(f"### Target Role: {u['role']} ({u['enrolled_count']} Learners)")
                st.caption(f"Aggregated Skills: `{u['skills']}` | Avg Budget: ₹{u['budget']}")
                
                if st.button(f"Compile & Launch Program: {u['role']}", key=f"comp_{u['cluster_key']}"):
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
                        st.success(f"🎉 Program `{prog_id}` compiled and launched under your coordination!")
                        st.rerun()
        else:
            st.info("No demand clusters currently meet the launch quorum threshold.")

# ----------------- TAB 4: PAYMENT AUDIT LEDGER -----------------
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
