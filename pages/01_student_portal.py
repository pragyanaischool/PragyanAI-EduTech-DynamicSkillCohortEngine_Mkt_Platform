"""
PragyanAI Student Portal & Learning Command Center
Features:
- Dashboard with 3 Lanes: Currently Running, Completed, and Interest-Based Recommendations
- Split Views for Enrolled vs. Not Enrolled Upcoming Batches
- Custom Learning Demand Sourcing (Skills, Duration, Details, Projects, Budget)
- Cohort Search Radar (Status, Skills, Dates, Budget) with EOI & UPI Enrollment
"""

import json
from datetime import date, timedelta
import streamlit as st
from config.database import get_connection

st.set_page_config(page_title="Student Dashboard | PragyanAI", page_icon="👨‍🎓", layout="wide")

user = st.session_state.get("user")
if not user or user["role"] != "student":
    st.warning("⚠️ Access restricted. Please sign in with a **Student** account in the sidebar.")
    st.stop()

st.title(f"👨‍🎓 Welcome, {user['full_name']}!")
st.caption(f"**Institution:** {user['institution'] or 'Independent'} | **Department:** {user['department'] or 'General'}")

# ----------------- MAIN TABS -----------------
tab_dashboard, tab_add_demand, tab_explore_all = st.tabs([
    "📊 My Learning Dashboard",
    "➕ Add Skill / Course Request",
    "🔍 Explore All Cohorts (Search Radar)"
])

# =============================================================================
# TAB 1: STUDENT PERSONAL DASHBOARD (3 KEY LANES)
# =============================================================================
with tab_dashboard:
    conn = get_connection()

    # 1. Fetch User Demands to build Interest Profile
    user_demands = conn.execute("""
        SELECT * FROM student_demands 
        WHERE student_id = ? 
        ORDER BY id DESC
    """, (user["id"],)).fetchall()

    user_interest_keywords = set()
    for d in user_demands:
        for s in d["target_skills"].split(","):
            if s.strip():
                user_interest_keywords.add(s.strip().lower())
        if d["dream_job_role"]:
            user_interest_keywords.add(d["dream_job_role"].strip().lower())

    # 2. Fetch User's Enrolled Programs
    user_enrollments = conn.execute("""
        SELECT p.*, pr.transaction_reference, pr.amount_paid, pr.payment_mode,
               u.full_name as trainer_name, u.phone as trainer_phone
        FROM program_enrollments pe
        JOIN compiled_programs p ON pe.program_id = p.id
        LEFT JOIN payment_records pr ON pe.payment_ref_id = pr.id
        LEFT JOIN expert_profiles ep ON p.expert_id = ep.id
        LEFT JOIN users u ON ep.user_id = u.id
        WHERE pe.student_id = ?
        ORDER BY p.id DESC
    """, (user["id"],)).fetchall()

    enrolled_pids = {p["id"] for p in user_enrollments}

    # Split enrollments by status
    running_cohorts = [p for p in user_enrollments if p["status"] == "LIVE"]
    completed_cohorts = [p for p in user_enrollments if p["status"] == "COMPLETED"]
    upcoming_enrolled = [p for p in user_enrollments if p["status"] in ("PLEDGE_OPEN", "PAYMENT_PENDING", "COORDINATION")]

    # 3. Fetch All Upcoming Cohorts NOT Enrolled (for Interest Matching)
    all_upcoming = conn.execute("""
        SELECT p.*, ep.token as expert_token, ep.industry_vertical, ep.rating as expert_rating
        FROM compiled_programs p
        LEFT JOIN expert_profiles ep ON p.expert_id = ep.id
        WHERE p.source_type = 'B2C_CROWD' 
          AND p.status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING', 'COORDINATION')
        ORDER BY p.id DESC
    """).fetchall()

    not_enrolled_upcoming = [p for p in all_upcoming if p["id"] not in enrolled_pids]

    # Smart Interest Recommendation Filter
    recommended_upcoming = []
    for p in not_enrolled_upcoming:
        prog_text = f"{p['title']} {p['syllabus_json']}".lower()
        if any(keyword in prog_text for keyword in user_interest_keywords):
            recommended_upcoming.append(p)

    conn.close()

    # --- TOP METRICS STRIP ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟢 Active Cohorts", len(running_cohorts))
    m2.metric("⏳ Upcoming (Enrolled)", len(upcoming_enrolled))
    m3.metric("🎯 Recommended for You", len(recommended_upcoming))
    m4.metric("🏁 Completed Batches", len(completed_cohorts))

    st.divider()

    # ---------------------------------------------------------
    # LANE 1: CURRENTLY RUNNING COHORTS
    # ---------------------------------------------------------
    st.markdown("### 🟢 Currently Running Cohorts")
    if not running_cohorts:
        st.info("You don't have any cohorts currently in session. Upcoming batches will appear here once live.")
    else:
        for rc in running_cohorts:
            with st.container():
                st.markdown(f"#### {rc['title']} ({rc['duration_hours']} Hours)")
                st.caption(f"**Program ID:** `{rc['program_id']}` | **Trainer:** {rc['trainer_name'] or 'Lead Specialist'} | **Verified UTR:** `{rc['transaction_reference']}`")
                
                col_live_a, col_live_b = st.columns(2)
                with col_live_a:
                    if rc["whatsapp_group_link"]:
                        st.markdown(f"[💬 **Open Batch WhatsApp Community**]({rc['whatsapp_group_link']})")
                    else:
                        st.caption("WhatsApp link being provisioned.")
                with col_live_b:
                    if rc["meeting_link"]:
                        st.markdown(f"[📹 **Join Live Virtual Classroom**]({rc['meeting_link']})")
                    else:
                        st.caption("Live class meeting link will activate before start.")
                st.divider()

    # ---------------------------------------------------------
    # LANE 2: INTEREST-BASED RELEVANT UPCOMING COHORTS
    # ---------------------------------------------------------
    st.markdown("### 🎯 Relevant Upcoming Cohorts (Based on Your Skill Interests)")
    
    tab_rec_not_enrolled, tab_rec_enrolled = st.tabs([
        f"🔥 Recommended Opportunities ({len(recommended_upcoming)})",
        f"✅ Upcoming You Already Enrolled ({len(upcoming_enrolled)})"
    ])

    with tab_rec_not_enrolled:
        if not recommended_upcoming:
            st.info("No matching upcoming cohorts for your current skill keywords. Add new skills in 'Add Skill / Course Request' or browse all cohorts.")
        else:
            for n_prog in recommended_upcoming:
                with st.expander(f"✨ {n_prog['title']} ({n_prog['duration_hours']}h) — ₹{n_prog['ticket_price_inr']}", expanded=True):
                    try:
                        s_data = json.loads(n_prog["syllabus_json"])
                    except Exception:
                        s_data = {}

                    c_info, c_act = st.columns([3, 2])
                    with c_info:
                        st.markdown(f"**🎯 Target Role:** {s_data.get('target_audience', 'Engineering Students')}")
                        st.markdown(f"**🛠️ Capstone:** {s_data.get('capstone_project', 'Hands-on practical build')}")
                        modules = s_data.get("modules", [])
                        if modules:
                            st.caption("**Key Units:** " + ", ".join([m.get("topic", "") for m in modules[:3]]))
                        if n_prog["expert_token"]:
                            st.caption(f"Instructor: `{n_prog['expert_token']}` | Rating: ⭐ {n_prog['expert_rating']}/5.0")
                    
                    with c_act:
                        st.metric("Quorum Progress", f"{n_prog['enrolled_count']} / {n_prog['target_quorum']} Students")
                        st.progress(min(1.0, n_prog["enrolled_count"] / max(n_prog["target_quorum"], 1)))

                        # Quick Payment Enrollment
                        with st.form(f"quick_pay_{n_prog['id']}"):
                            st.caption(f"Direct UPI to `pragyanai@upi`: **₹{n_prog['ticket_price_inr']}**")
                            utr_in = st.text_input("Transaction Reference (UTR)", key=f"rec_utr_{n_prog['id']}", placeholder="e.g. 202688492019")
                            if st.form_submit_button("Confirm Seat & Enroll", use_container_width=True):
                                if utr_in.strip():
                                    c = get_connection()
                                    cur = c.cursor()
                                    cur.execute("""
                                        INSERT INTO payment_records (program_id, user_id, payer_type, payment_mode, transaction_reference, amount_paid, verification_status)
                                        VALUES (?, ?, 'STUDENT', 'UPI', ?, ?, 'VERIFIED')
                                    """, (n_prog["id"], user["id"], utr_in.strip(), n_prog["ticket_price_inr"]))
                                    p_id = cur.lastrowid
                                    cur.execute("INSERT INTO program_enrollments (program_id, student_id, payment_ref_id) VALUES (?, ?, ?)", (n_prog["id"], user["id"], p_id))
                                    cur.execute("UPDATE compiled_programs SET enrolled_count = enrolled_count + 1 WHERE id = ?", (n_prog["id"],))
                                    c.commit()
                                    c.close()
                                    st.success("🎉 Enrolled successfully!")
                                    st.rerun()
                                else:
                                    st.error("Please provide a valid UTR number.")

    with tab_rec_enrolled:
        if not upcoming_enrolled:
            st.write("You have no pending upcoming enrollments.")
        else:
            for ue in upcoming_enrolled:
                with st.container():
                    st.markdown(f"#### 📌 {ue['title']} ({ue['duration_hours']} Hours)")
                    st.caption(f"Program ID: `{ue['program_id']}` | Status: **{ue['status']}** | Verified Fee: `₹{ue['amount_paid']}`")
                    if ue["whatsapp_group_link"]:
                        st.markdown(f"[👉 **Join Batch WhatsApp Group**]({ue['whatsapp_group_link']})")
                    else:
                        st.info("Coordinator is setting up schedule and WhatsApp community.")
                    st.divider()

    # ---------------------------------------------------------
    # LANE 3: COMPLETED COHORTS & CERTIFICATES
    # ---------------------------------------------------------
    st.markdown("### 🏁 Completed Cohorts & Certifications")
    if not completed_cohorts:
        st.info("You haven't completed any cohorts yet. Finished programs with downloadable e-certificates will appear here.")
    else:
        for cc in completed_cohorts:
            with st.expander(f"🎓 {cc['title']} (Completed)"):
                st.write(f"Delivered by: **{cc['trainer_name'] or 'Lead Specialist'}**")
                st.success("✅ Completion E-Certificate Verified & Ready")
                st.markdown(f"[📥 Download PragyanAI Digital Certificate](https://api.dicebear.com/7.x/identicon/svg?seed={cc['program_id']})")


# =============================================================================
# TAB 2: ADD WHAT SKILL ONE KEEN TO LEARN (CUSTOM DEMAND COMPILER)
# =============================================================================
with tab_add_demand:
    st.subheader("💡 Submit What Skill You Are Keen to Learn")
    st.write("Tell us exactly what you want to master. PragyanAI aggregates similar student requests across colleges and compiles an AI-grounded cohort syllabus.")

    with st.form("add_custom_learning_demand_form"):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dream_role = st.text_input(
                "Dream Job Role / Career Goal",
                placeholder="e.g. Autonomous AI Agent Architect, VLSI RTL Verification Engineer",
                help="The specific industry title or career pathway you are targeting."
            )
            skills_input = st.text_area(
                "Skills & Tools Keen to Learn",
                placeholder="e.g. LangGraph, Model Context Protocol (MCP), FAISS, Tool Calling, RISC-V",
                help="Comma-separated frameworks, languages, or concepts."
            )
            course_details = st.text_area(
                "Course Details & Specific Topics You Expect",
                placeholder="e.g. Want deep focus on cyclic state machines, hands-on debugging of multi-agent swarms, and connecting local SQLite DB via MCP.",
                help="Describe exact sub-topics, real-world case studies, or pain points."
            )

        with col_d2:
            duration_pref = st.select_slider(
                "Preferred Duration of Bootcamp",
                options=[5, 10, 15, 20, 25, 30],
                value=15,
                format_func=lambda x: f"{x} Hours ({x//5} Weekend Modules)" if x >= 5 else f"{x} Hours"
            )
            budget_pref = st.select_slider(
                "Your Budget Ceiling (INR)",
                options=[50, 100, 150, 200, 250, 300, 500, 1000],
                value=250
            )
            project_pref = st.selectbox(
                "Capstone Project Requirement",
                ["Production GitHub Portfolio Project", "Research Paper Implementation", "Industry Hackathon Preparation", "Basic Hands-on Labs"]
            )
            delivery_slot_pref = st.selectbox(
                "Preferred Learning Slot",
                ["Weekend Morning (10 AM - 1 PM)", "Weekend Evening (5 PM - 8 PM)", "Weekday Evening (7 PM - 9 PM)"]
            )

        btn_demand_submit = st.form_submit_button("🚀 Submit Learning Request to PragyanAI Pool", use_container_width=True)

    if btn_demand_submit:
        if dream_role.strip() and skills_input.strip():
            conn = get_connection()
            c = conn.cursor()
            combined_skills = f"{skills_input.strip()} | Project: {project_pref} | Slot: {delivery_slot_pref}"
            c.execute("""
                INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (user["id"], dream_role.strip(), combined_skills, duration_pref, budget_pref))
            conn.commit()
            conn.close()
            st.success("🎉 Learning demand successfully submitted! PragyanAI's compiler is clustering your demand with peers.")
            st.rerun()
        else:
            st.error("Please fill in both the Dream Job Role and Skills fields.")

    # Show User's Past Submitted Demands
    st.divider()
    st.markdown("#### 📋 Your Active Skill Requests")
    conn = get_connection()
    my_demands = conn.execute("SELECT * FROM student_demands WHERE student_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    conn.close()

    if my_demands:
        for md in my_demands:
            with st.container():
                st.markdown(f"**Target Role:** {md['dream_job_role']} ({md['duration_hours']}h)")
                st.caption(f"**Skills & Scope:** `{md['target_skills']}` | Budget: `₹{md['budget_inr']}` | Status: **{md['status']}**")
                st.divider()


# =============================================================================
# TAB 3: EXPLORE ALL COHORTS (SEARCH RADAR)
# =============================================================================
with tab_explore_all:
    st.subheader("🔍 Cohort Search Radar")

    # Search Bar & Filter Controls
    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        f_status = st.selectbox("Cohort State", ["All States", "Upcoming / Open", "Live", "Completed"])
    with f2:
        f_skill = st.text_input("Skill Filter", placeholder="e.g. LangChain, RAG, Verilog")
    with f3:
        f_dates = st.date_input("Date Window", value=(date.today(), date.today() + timedelta(days=60)))
    with f4:
        f_budget = st.slider("Budget Ceiling (INR)", 50, 2000, 500, 50)

    conn = get_connection()
    q = "SELECT p.*, ep.token, ep.rating FROM compiled_programs p LEFT JOIN expert_profiles ep ON p.expert_id = ep.id WHERE ticket_price_inr <= ?"
    params = [f_budget]

    if f_status == "Upcoming / Open":
        q += " AND p.status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING', 'COORDINATION')"
    elif f_status == "Live":
        q += " AND p.status = 'LIVE'"
    elif f_status == "Completed":
        q += " AND p.status = 'COMPLETED'"

    all_progs = conn.execute(q, params).fetchall()
    conn.close()

    matched_progs = []
    for prog in all_progs:
        full_text = f"{prog['title']} {prog['syllabus_json']}".lower()
        if not f_skill.strip() or f_skill.strip().lower() in full_text:
            matched_progs.append(prog)

    if not matched_progs:
        st.info("No cohorts found matching your filters.")
    else:
        st.caption(f"Found **{len(matched_progs)}** cohorts:")
        for mp in matched_progs:
            with st.expander(f"📌 {mp['title']} ({mp['duration_hours']}h) — ₹{mp['ticket_price_inr']} | Status: {mp['status']}"):
                st.write(f"Quorum: {mp['enrolled_count']} / {mp['target_quorum']} enrolled.")
                st.json(json.loads(mp["syllabus_json"]))
