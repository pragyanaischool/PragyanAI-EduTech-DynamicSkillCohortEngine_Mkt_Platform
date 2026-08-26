"""
Student Portal (B2C Demand-to-Cohort & Skill Discovery Interface)
Features:
- Search New vs. Old Cohorts
- Filter by Date Range (From - To), Skills, and Duration
- Express Interest (EOI) or Direct UPI Seat Enrollment
- Enrolled Batches, Live Classroom & WhatsApp Links
"""

import json
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from config.database import get_connection

st.set_page_config(page_title="Student Skill Cohorts | PragyanAI", page_icon="👨‍🎓", layout="wide")

st.title("👨‍🎓 Student Skill Cohorts & Learning Marketplace")
st.caption("Discover live cohorts about to start, search historical batches, express interest, or enroll directly.")

user = st.session_state.get("user")
if not user or user["role"] != "student":
    st.warning("⚠️ Access restricted. Please sign in with a **Student** account using the sidebar.")
    st.stop()

# ----------------- TABS NAVIGATION -----------------
tab_discover, tab_demand, tab_my_cohorts = st.tabs([
    "🔍 Browse & Search Cohorts (New / Old)",
    "💡 Express Custom Demand",
    "🎓 My Enrolled & Followed Cohorts"
])

# =============================================================================
# TAB 1: BROWSE & SEARCH COHORTS (MULTI-FILTER + EOI + ENROLL)
# =============================================================================
with tab_discover:
    st.subheader("Explore Skill Cohorts")

    # --- FILTER CONTROL BAR ---
    with st.container():
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 2])
        
        with f_col1:
            cohort_type = st.selectbox(
                "Cohort Timeline",
                ["All Cohorts", "🔥 About to Start / Upcoming", "🟢 Live & In-Progress", "📚 Completed / Past Batches"]
            )
        
        with f_col2:
            skill_query = st.text_input("Search by Skill / Keyword", placeholder="e.g. LangGraph, RAG, Verilog, MCP")

        with f_col3:
            default_start = date.today()
            default_end = date.today() + timedelta(days=90)
            date_range = st.date_input(
                "Date Range (From - To)",
                value=(default_start, default_end)
            )

        with f_col4:
            max_fee = st.slider("Max Ticket Fee (INR)", min_value=50, max_value=2000, value=500, step=50)

    st.divider()

    # --- SQL QUERY BUILDER ---
    conn = get_connection()
    query = """
        SELECT p.*, e.token as expert_token, e.industry_vertical, e.rating as expert_rating
        FROM compiled_programs p
        LEFT JOIN expert_profiles e ON p.expert_id = e.id
        WHERE p.source_type = 'B2C_CROWD'
    """
    params = []

    # Filter by Cohort Timeline Status
    if cohort_type == "🔥 About to Start / Upcoming":
        query += " AND p.status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING', 'COORDINATION')"
    elif cohort_type == "🟢 Live & In-Progress":
        query += " AND p.status = 'LIVE'"
    elif cohort_type == "📚 Completed / Past Batches":
        query += " AND p.status = 'COMPLETED'"

    # Filter by Max Fee
    query += " AND p.ticket_price_inr <= ?"
    params.append(max_fee)

    query += " ORDER BY p.id DESC"
    all_programs = conn.execute(query, params).fetchall()

    # Get user enrollment & EOI states
    user_enrolled_pids = [
        r["program_id"] for r in conn.execute(
            "SELECT program_id FROM program_enrollments WHERE student_id = ?", (user["id"],)
        ).fetchall()
    ]
    user_eoi_pids = [
        r["program_id"] for r in conn.execute(
            "SELECT program_id FROM cohort_expressions_of_interest WHERE student_id = ?", (user["id"],)
        ).fetchall()
    ]
    conn.close()

    # Client-side Skill & Date filtering
    filtered_programs = []
    from_date = date_range[0] if isinstance(date_range, tuple) and len(date_range) > 0 else default_start
    to_date = date_range[1] if isinstance(date_range, tuple) and len(date_range) > 1 else default_end

    for prog in all_programs:
        # Check skill query match in title, syllabus, or skills
        syllabus_text = prog["syllabus_json"] or ""
        title_text = prog["title"] or ""
        
        matches_skill = True
        if skill_query.strip():
            sq = skill_query.strip().lower()
            matches_skill = (sq in title_text.lower()) or (sq in syllabus_text.lower())

        if matches_skill:
            filtered_programs.append(prog)

    # --- RENDER COHORT CARDS ---
    if not filtered_programs:
        st.info("💡 No cohorts matched your search criteria. Try broadening your date range or submit a custom demand in the next tab!")
    else:
        st.caption(f"Showing **{len(filtered_programs)}** matching cohorts:")

        for p in filtered_programs:
            is_enrolled = p["id"] in user_enrolled_pids
            has_expressed_interest = p["id"] in user_eoi_pids
            
            # Status Badge Styling
            status_labels = {
                "PLEDGE_OPEN": "🟡 Building Quorum (Express Interest Open)",
                "PAYMENT_PENDING": "🟠 Quorum Reached - Seats Locking",
                "COORDINATION": "🔵 About to Start (Seats Available)",
                "LIVE": "🟢 Live & In-Progress",
                "COMPLETED": "⚪ Completed / Archived"
            }
            status_badge = status_labels.get(p["status"], p["status"])

            try:
                syllabus = json.loads(p["syllabus_json"])
            except Exception:
                syllabus = {}

            with st.container():
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### {p['title']}")
                    st.caption(f"**Program ID:** `{p['program_id']}` | **Duration:** {p['duration_hours']} Hours | **Status:** {status_badge}")
                with header_col2:
                    st.metric("Ticket Price", f"₹{p['ticket_price_inr']}")

                col_details, col_actions = st.columns([3, 2])

                with col_details:
                    st.markdown(f"**🎯 Target Role / Audience:** {syllabus.get('target_audience', 'Engineering Students')}")
                    st.markdown(f"**🛠️ Capstone Project:** {syllabus.get('capstone_project', 'Hands-on practical deliverable')}")
                    
                    # Module overview chips
                    modules = syllabus.get("modules", [])
                    if modules:
                        st.markdown("**Core Modules:**")
                        mod_titles = [f"`Unit {m.get('unit', idx+1)}: {m.get('topic', '')}`" for idx, m in enumerate(modules[:4])]
                        st.markdown(" • ".join(mod_titles))

                    if p["expert_token"]:
                        st.caption(f"👨‍🏫 **Instructor:** {p['expert_token']} ({p['industry_vertical']}) | Rating: ⭐ {p['expert_rating']}/5.0")

                with col_actions:
                    # Progress Bar towards launch
                    quorum = max(p["target_quorum"], 1)
                    enrolled = p["enrolled_count"]
                    progress_val = min(1.0, enrolled / quorum)
                    
                    st.write(f"**Quorum Progress:** {enrolled} / {quorum} Seats Filled")
                    st.progress(progress_val)

                    # Action 1: Completed Cohort
                    if p["status"] == "COMPLETED":
                        st.info("This cohort has completed. You can request a rerun or view past materials in the Media Vault.")
                        if st.button("🔁 Request Rerun of this Cohort", key=f"rerun_{p['id']}", use_container_width=True):
                            st.success("Rerun interest noted! You'll be notified when this batch opens again.")

                    # Action 2: Already Enrolled
                    elif is_enrolled:
                        st.success("✅ **You are Enrolled!**")
                        if p["whatsapp_group_link"]:
                            st.markdown(f"[👉 **Join Batch WhatsApp**]({p['whatsapp_group_link']})")
                        if p["meeting_link"]:
                            st.markdown(f"[🔗 **Live Classroom Link**]({p['meeting_link']})")

                    # Action 3: Express Interest (EOI) or Direct Enrollment
                    else:
                        act_tab_enroll, act_tab_eoi = st.tabs(["💳 Direct Seat Booking", "👍 Express Interest (EOI)"])

                        with act_tab_enroll:
                            with st.form(f"enroll_form_{p['id']}"):
                                st.caption(f"Transfer **₹{p['ticket_price_inr']}** via UPI to `pragyanai@upi`")
                                p_mode = st.selectbox("Payment Mode", ["UPI", "NEFT_IMPS", "Bank_Transfer"], key=f"mode_{p['id']}")
                                utr = st.text_input("Transaction UTR / Reference ID", key=f"utr_{p['id']}", placeholder="e.g. 202688492019")
                                
                                if st.form_submit_button("Confirm Payment & Lock Seat", use_container_width=True):
                                    if utr.strip():
                                        c = get_connection()
                                        cur = c.cursor()
                                        cur.execute("""
                                            INSERT INTO payment_records (
                                                program_id, user_id, payer_type, payment_mode,
                                                transaction_reference, amount_paid, verification_status
                                            ) VALUES (?, ?, 'STUDENT', ?, ?, ?, 'VERIFIED')
                                        """, (p["id"], user["id"], p_mode, utr.strip(), p["ticket_price_inr"]))
                                        pay_id = cur.lastrowid

                                        cur.execute("""
                                            INSERT INTO program_enrollments (program_id, student_id, payment_ref_id)
                                            VALUES (?, ?, ?)
                                        """, (p["id"], user["id"], pay_id))

                                        cur.execute("UPDATE compiled_programs SET enrolled_count = enrolled_count + 1 WHERE id = ?", (p["id"],))
                                        c.commit()
                                        c.close()
                                        st.success("🎉 Seat booked successfully! Check 'My Enrolled Cohorts' tab for links.")
                                        st.rerun()
                                    else:
                                        st.error("Please enter a valid transaction reference.")

                        with act_tab_eoi:
                            if has_expressed_interest:
                                st.info("👍 You have expressed interest in this cohort. We'll alert you once batch dates are locked!")
                            else:
                                st.caption("Express interest without paying upfront. Helps us finalize slots.")
                                with st.form(f"eoi_form_{p['id']}"):
                                    pref_slot = st.selectbox("Preferred Slot", ["Weekend Morning", "Weekend Evening", "Weekday Evening"], key=f"slot_{p['id']}")
                                    w_budget = st.number_input("Target Budget (INR)", value=float(p["ticket_price_inr"]), key=f"wbg_{p['id']}")
                                    if st.form_submit_button("Submit Expression of Interest (EOI)", use_container_width=True):
                                        c = get_connection()
                                        c.execute("""
                                            INSERT OR REPLACE INTO cohort_expressions_of_interest (program_id, student_id, willing_budget_inr, preferred_slot)
                                            VALUES (?, ?, ?, ?)
                                        """, (p["id"], user["id"], w_budget, pref_slot))
                                        c.commit()
                                        c.close()
                                        st.success("✅ Expression of Interest logged!")
                                        st.rerun()

                st.divider()

# =============================================================================
# TAB 2: EXPRESS CUSTOM DEMAND
# =============================================================================
with tab_demand:
    st.subheader("Can't Find What You're Looking For? Submit Custom Demand")
    st.write("PragyanAI's clustering engine aggregates student requests and auto-compiles new cohorts once quorum is met.")

    with st.form("custom_demand_form"):
        cd_col1, cd_col2 = st.columns(2)
        with cd_col1:
            req_role = st.text_input("Target Dream Job Role", placeholder="e.g. Agentic AI Engineer, VLSI Verification Lead")
            req_skills = st.text_area("Skills / Tools Keen to Learn", placeholder="e.g. Model Context Protocol, LangGraph, RISC-V, UVM")
        with cd_col2:
            req_hours = st.select_slider("Target Bootcamp Duration (Hours)", options=[5, 10, 15, 20, 25, 30], value=15)
            req_budget = st.select_slider("Willingness to Pay (INR)", options=[50, 100, 150, 200, 250, 300, 500], value=250)

        if st.form_submit_button("🚀 Submit to PragyanAI Demand Pool", use_container_width=True):
            if req_role.strip() and req_skills.strip():
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
                    VALUES (?, ?, ?, ?, ?, 'PENDING')
                """, (user["id"], req_role.strip(), req_skills.strip(), req_hours, req_budget))
                conn.commit()
                conn.close()
                st.success("✅ Learning demand recorded! You will receive an alert once matching students unlock the cohort.")
            else:
                st.error("Please fill in both the dream job role and target skills.")

# =============================================================================
# TAB 3: MY ENROLLED & FOLLOWED COHORTS
# =============================================================================
with tab_my_cohorts:
    st.subheader("Your Learning Dashboard")

    my_tab1, my_tab2 = st.tabs(["📚 Confirmed Enrolled Batches", "⭐ Followed / Expressed Interest (EOI)"])

    conn = get_connection()

    # Confirmed Enrollments
    with my_tab1:
        enrolled_batches = conn.execute("""
            SELECT p.*, pr.transaction_reference, pr.amount_paid, pr.payment_mode, pr.paid_at,
                   u.full_name as trainer_name, u.phone as trainer_phone
            FROM program_enrollments pe
            JOIN compiled_programs p ON pe.program_id = p.id
            LEFT JOIN payment_records pr ON pe.payment_ref_id = pr.id
            LEFT JOIN expert_profiles ep ON p.expert_id = ep.id
            LEFT JOIN users u ON ep.user_id = u.id
            WHERE pe.student_id = ?
            ORDER BY p.id DESC
        """, (user["id"],)).fetchall()

        if not enrolled_batches:
            st.info("You haven't enrolled in any cohorts yet. Explore upcoming batches in the 'Browse Cohorts' tab.")
        else:
            for b in enrolled_batches:
                with st.container():
                    st.markdown(f"### {b['title']} ({b['duration_hours']} Hours)")
                    st.caption(f"**Program ID:** `{b['program_id']}` | **UTR:** `{b['transaction_reference']}` | **Status:** `{b['status']}`")

                    col_w, col_m = st.columns(2)
                    with col_w:
                        if b["whatsapp_group_link"]:
                            st.success("💬 Cohort WhatsApp Community Active!")
                            st.markdown(f"[👉 **Join Batch WhatsApp Group**]({b['whatsapp_group_link']})")
                        else:
                            st.info("⏳ PragyanAI Coordinator is setting up the batch WhatsApp group.")
                    
                    with col_m:
                        if b["meeting_link"]:
                            st.success("📹 Live Virtual Classroom:")
                            st.markdown(f"[🔗 **Enter Live Class Session**]({b['meeting_link']})")
                        else:
                            st.caption("Live classroom link will be posted before the first session.")

                    st.divider()

    # Expressed Interest (EOI)
    with my_tab2:
        eoi_batches = conn.execute("""
            SELECT p.*, eoi.willing_budget_inr, eoi.preferred_slot, eoi.expressed_at
            FROM cohort_expressions_of_interest eoi
            JOIN compiled_programs p ON eoi.program_id = p.id
            WHERE eoi.student_id = ?
            ORDER BY eoi.id DESC
        """, (user["id"],)).fetchall()

        if not eoi_batches:
            st.write("You have not expressed interest in any pending cohorts.")
        else:
            for eb in eoi_batches:
                with st.container():
                    st.markdown(f"**{eb['title']}** ({eb['duration_hours']}h)")
                    st.caption(f"Preferred Slot: `{eb['preferred_slot']}` | Target Budget: `₹{eb['willing_budget_inr']}` | Expressed: `{eb['expressed_at']}`")
                    st.caption(f"Current Batch Quorum: **{eb['enrolled_count']} / {eb['target_quorum']} Students**")
                    st.divider()

    conn.close()
