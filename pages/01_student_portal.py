"""
Student Portal (B2C Demand-to-Cohort Interface)
Handles skill demand submission, quorum-based program pledge gating,
direct UPI payment logging, and unlocked WhatsApp/Meet batch links.
"""

import json
import streamlit as st
from config.database import get_connection

st.title("👨‍🎓 Student Demand-to-Cohort Portal")
st.caption("Submit your dream career goals, pool micro-demand with peers, and join live technical cohorts.")

user = st.session_state.get("user")
if not user or user["role"] != "student":
    st.warning("⚠️ Access restricted. Please sign in with a **Student** account using the sidebar.")
    st.stop()

tab_demand, tab_pledge, tab_my_cohorts = st.tabs([
    "📥 Submit Learning Demand",
    "🔥 Trending Demand Pools (Pledge Gate)",
    "🎓 My Enrolled Cohorts & WhatsApp Group"
])

# ----------------- TAB 1: SUBMIT DEMAND -----------------
with tab_demand:
    st.subheader("Submit Target Career Roles & Desired Skills")
    st.write("PragyanAI semantic clustering aggregates individual demands to compile launch-ready programs.")

    with st.form("student_demand_form"):
        col1, col2 = st.columns(2)
        with col1:
            role_target = st.text_input("Target Dream Job Role", value="Agentic AI Systems Engineer")
            skills = st.text_area(
                "Skills & Frameworks Keen to Learn",
                value="LangGraph, Model Context Protocol (MCP), FAISS, Tool Calling",
                help="Enter comma-separated topics or tools."
            )
        with col2:
            duration = st.select_slider(
                "Preferred Program Duration (Hours)",
                options=[5, 10, 15, 20, 25, 30],
                value=15
            )
            budget = st.select_slider(
                "Willingness to Pay (INR)",
                options=[50, 100, 150, 200, 250, 300],
                value=250
            )

        btn_submit_demand = st.form_submit_button("🚀 Submit to PragyanAI Demand Aggregator", use_container_width=True)

    if btn_submit_demand:
        if role_target and skills:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (user["id"], role_target.strip(), skills.strip(), duration, budget))
            conn.commit()
            conn.close()
            st.success("✅ Your learning demand is logged! Once matching demand reaches quorum, a live cohort will launch.")
        else:
            st.warning("Please provide both a target job role and target skills.")

# ----------------- TAB 2: PLEDGE GATE -----------------
with tab_pledge:
    st.subheader("Active Program Quorums Ready for Enrollment")
    st.caption("Pledge your seat via UPI reference. Programs launch automatically when quorum is met.")

    conn = get_connection()
    programs = conn.execute("""
        SELECT * FROM compiled_programs 
        WHERE source_type = 'B2C_CROWD' AND status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING', 'COORDINATION', 'LIVE')
        ORDER BY id DESC
    """).fetchall()

    # Check programs already enrolled by user
    user_enrolled_pids = [
        row["program_id"] for row in conn.execute(
            "SELECT program_id FROM program_enrollments WHERE student_id = ?", (user["id"],)
        ).fetchall()
    ]
    conn.close()

    if not programs:
        st.info("No active B2C cohorts open for pledge right now. Submit your demand above to start one!")
    else:
        for p in programs:
            is_enrolled = p["id"] in user_enrolled_pids
            with st.expander(
                f"📌 {p['title']} ({p['duration_hours']}h) — ₹{p['ticket_price_inr']} | Status: {p['status']}",
                expanded=not is_enrolled
            ):
                try:
                    s = json.loads(p["syllabus_json"])
                except Exception:
                    s = {}

                c1, c2 = st.columns([3, 2])
                with c1:
                    st.markdown(f"**Target Audience:** {s.get('target_audience', 'Engineering Students')}")
                    st.markdown(f"**Capstone Project:** {s.get('capstone_project', 'Hands-on practical build')}")
                    modules = s.get("modules", [])
                    if modules:
                        st.markdown("**Curriculum Highlights:**")
                        for m in modules[:3]:
                            st.markdown(f"- *Unit {m.get('unit', '')}:* {m.get('topic', '')}")

                with c2:
                    st.metric("Batch Quorum Progress", f"{p['enrolled_count']} / {p['target_quorum']} Pledges")
                    st.progress(min(1.0, p["enrolled_count"] / max(p["target_quorum"], 1)))

                    if is_enrolled:
                        st.success("✅ You are enrolled in this batch! See 'My Enrolled Cohorts' tab for group link.")
                    else:
                        st.markdown("#### Confirm Seat via Direct UPI")
                        st.caption("Pay to `pragyanai@upi` or transfer to platform account.")
                        with st.form(f"pledge_pay_{p['id']}"):
                            pay_mode = st.selectbox("Payment Mode", ["UPI", "NEFT_IMPS", "Bank_Transfer"], key=f"pm_{p['id']}")
                            utr_ref = st.text_input("Transaction UTR / Reference ID", key=f"utr_{p['id']}")
                            
                            if st.form_submit_button("Submit Payment & Enroll", use_container_width=True):
                                if utr_ref.strip():
                                    c = get_connection()
                                    cur = c.cursor()
                                    cur.execute("""
                                        INSERT INTO payment_records (
                                            program_id, user_id, payer_type, payment_mode,
                                            transaction_reference, amount_paid, verification_status
                                        ) VALUES (?, ?, 'STUDENT', ?, ?, ?, 'VERIFIED')
                                    """, (p["id"], user["id"], pay_mode, utr_ref.strip(), p["ticket_price_inr"]))
                                    pay_id = cur.lastrowid

                                    cur.execute("""
                                        INSERT INTO program_enrollments (program_id, student_id, payment_ref_id)
                                        VALUES (?, ?, ?)
                                    """, (p["id"], user["id"], pay_id))

                                    cur.execute("""
                                        UPDATE compiled_programs 
                                        SET enrolled_count = enrolled_count + 1 
                                        WHERE id = ?
                                    """, (p["id"],))
                                    c.commit()
                                    c.close()
                                    st.success("🎉 Enrollment verified! Your cohort details are updated.")
                                    st.rerun()
                                else:
                                    st.error("Please enter a valid transaction reference number.")

# ----------------- TAB 3: MY ENROLLED COHORTS -----------------
with tab_my_cohorts:
    st.subheader("Your Active Cohorts & WhatsApp Classrooms")
    conn = get_connection()
    my_cohorts = conn.execute("""
        SELECT p.*, pr.transaction_reference, pr.amount_paid
        FROM program_enrollments pe
        JOIN compiled_programs p ON pe.program_id = p.id
        LEFT JOIN payment_records pr ON pe.payment_ref_id = pr.id
        WHERE pe.student_id = ?
        ORDER BY p.id DESC
    """, (user["id"],)).fetchall()
    conn.close()

    if not my_cohorts:
        st.info("You haven't enrolled in any cohorts yet. Browse the 'Trending Demand Pools' tab.")
    else:
        for cohort in my_cohorts:
            with st.container():
                st.markdown(f"### {cohort['title']} ({cohort['duration_hours']} Hours)")
                st.caption(f"Program ID: `{cohort['program_id']}` | Verified UTR: `{cohort['transaction_reference']}`")

                col_a, col_b = st.columns(2)
                with col_a:
                    if cohort["whatsapp_group_link"]:
                        st.success("💬 Official WhatsApp Cohort Group is active!")
                        st.markdown(f"[👉 **Join Batch WhatsApp Group**]({cohort['whatsapp_group_link']})")
                    else:
                        st.info("⏳ PragyanAI Coordinator is creating the WhatsApp group. Link will appear here shortly.")

                with col_b:
                    if cohort["meeting_link"]:
                        st.success("📹 Live Virtual Classroom:")
                        st.markdown(f"[🔗 **Join Live Session Class**]({cohort['meeting_link']})")
                    else:
                        st.caption("Live classroom link will be posted prior to the scheduled start time.")

                st.divider()
