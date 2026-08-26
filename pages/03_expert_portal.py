"""
Skill Expert Portal & Reverse-Bidding Workspace
Allows domain trainers and industry specialists to review anonymous demand opportunities,
submit competitive bids, and manage delivery slots.
"""

import json
import streamlit as st
from config.database import get_connection
from modules.expert_marketplace import submit_expert_bid

st.title("💼 Skill Expert & Trainer Marketplace")
st.caption("Discover high-intent student cohorts and college FDPs. Counter-bid transparently without cold outreach.")

user = st.session_state.get("user")
if not user or user["role"] != "expert":
    st.warning("⚠️ Access restricted. Please sign in with an **Expert** account using the sidebar.")
    st.stop()

conn = get_connection()
exp_profile = conn.execute("SELECT * FROM expert_profiles WHERE user_id = ?", (user["id"],)).fetchone()
conn.close()

if not exp_profile:
    st.error("Expert profile not found. Please contact platform operations.")
    st.stop()

st.info(f"🛡️ Logged in as Masked Token: **{exp_profile['token']}** | Domain: **{exp_profile['industry_vertical']}**")

tab_radar, tab_b2c_slots, tab_my_bids = st.tabs([
    "🎯 Institutional B2B Opportunities",
    "🔥 Student Cohort Slots",
    "📤 My Submitted Bids"
])

# ----------------- TAB 1: B2B OPPORTUNITIES -----------------
with tab_radar:
    st.subheader("Live College Requests Seeking Subject Experts")
    conn = get_connection()
    b2b_reqs = conn.execute("""
        SELECT * FROM institutional_requests 
        WHERE status = 'BIDDING' 
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    if not b2b_reqs:
        st.info("No institutional FDP/STP requests currently open for bidding.")
    else:
        for req in b2b_reqs:
            with st.expander(f"🏛️ {req['program_type']}: {req['scope_description']} (Budget: ₹{req['budget_inr']})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Delivery Mode:** {req['delivery_mode']}")
                    if req["compiled_syllabus"]:
                        try:
                            s = json.loads(req["compiled_syllabus"])
                            st.markdown(f"**Target Audience:** {s.get('target_audience', 'Faculty / Students')}")
                            st.markdown(f"**Capstone:** {s.get('capstone_project', 'Hands-on lab')}")
                        except Exception:
                            pass
                with c2:
                    st.metric("College Budget Allocation", f"₹{req['budget_inr']}")

                st.markdown("#### Submit Your Delivery Bid")
                with st.form(f"bid_form_b2b_{req['id']}"):
                    bid_val = st.number_input("Your Proposed Rate (INR)", min_value=1000.0, value=float(req['budget_inr']), step=1000.0)
                    delivery_notes = st.text_area(
                        "Delivery Plan & Lab Prerequisites",
                        value="Will deliver hands-on labs with complete GitHub starter code and verification scripts."
                    )
                    if st.form_submit_button("Submit Counter-Bid", use_container_width=True):
                        ok = submit_expert_bid(
                            expert_id=exp_profile["id"],
                            bid_amount=bid_val,
                            notes=delivery_notes,
                            b2b_request_id=req["id"]
                        )
                        if ok:
                            st.success("✅ Bid successfully registered! College SPOC and coordinator have been notified.")
                            st.rerun()

# ----------------- TAB 2: B2C COHORT SLOTS -----------------
with tab_b2c_slots:
    st.subheader("Student Crowdsourced Cohorts Seeking Lead Instructors")
    conn = get_connection()
    b2c_progs = conn.execute("""
        SELECT * FROM compiled_programs 
        WHERE source_type = 'B2C_CROWD' AND status IN ('PLEDGE_OPEN', 'PAYMENT_PENDING')
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    if not b2c_progs:
        st.info("No B2C student cohorts currently open for expert claiming.")
    else:
        for prog in b2c_progs:
            with st.expander(f"📌 {prog['title']} ({prog['duration_hours']}h) — Enrolled: {prog['enrolled_count']}/{prog['target_quorum']}"):
                st.write(f"Estimated Ticket Price: ₹{prog['ticket_price_inr']} per learner.")
                with st.form(f"bid_b2c_{prog['id']}"):
                    proposed_fee = st.number_input("Proposed Instructor Honorarium (INR)", value=float(prog['duration_hours'] * 2000), step=1000.0)
                    plan_notes = st.text_area("Teaching Methodology & Lab Schedule", "50% Theory + 50% Live Hands-on Coding.")
                    if st.form_submit_button("Apply as Lead Instructor"):
                        ok = submit_expert_bid(
                            expert_id=exp_profile["id"],
                            bid_amount=proposed_fee,
                            notes=plan_notes,
                            program_id=prog["id"]
                        )
                        if ok:
                            st.success("Application logged! Platform coordinator will review and finalize.")
                            st.rerun()

# ----------------- TAB 3: MY SUBMITTED BIDS -----------------
with tab_my_bids:
    st.subheader("Your Active & Past Bids")
    conn = get_connection()
    my_bids = conn.execute("""
        SELECT b.*, COALESCE(p.title, r.scope_description) as program_name
        FROM bids b
        LEFT JOIN compiled_programs p ON b.program_id = p.id
        LEFT JOIN institutional_requests r ON b.b2b_request_id = r.id
        WHERE b.expert_id = ?
        ORDER BY b.id DESC
    """, (exp_profile["id"],)).fetchall()
    conn.close()

    if not my_bids:
        st.write("You have not submitted any bids yet.")
    else:
        for b in my_bids:
            with st.container():
                st.markdown(f"**Program:** {b['program_name']}")
                st.caption(f"Bid Amount: `₹{b['bid_amount_inr']}` | Status: **{b['status']}** | Notes: *{b['counter_notes']}*")
                st.divider()
