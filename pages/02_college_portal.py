"""
College & Institutional B2B Workspace
Allows HODs and academic SPOCs to scope FDPs/STPs, ground curricula via RAG,
evaluate anonymized expert panels, and monitor coordinator logistics.
"""

import json
import streamlit as st
from config.database import get_connection
from modules.rag_compiler import compile_academic_syllabus
from modules.expert_marketplace import get_anonymized_expert_roster, calculate_expert_fit_score

st.title("🏛️ Institutional B2B Workspace (Colleges & HODs)")
st.caption("Outcome-based FDP / STP Scoping, Blind Expert Panels & Coordinator Logistics")

user = st.session_state.get("user")
if not user or user["role"] != "college":
    st.warning("⚠️ Access restricted. Please sign in with a **College** account using the sidebar.")
    st.stop()

tab_request, tab_proposals, tab_my_requests = st.tabs([
    "📝 Scope FDP / STP Request",
    "🛡️ Review Anonymized Expert Panels",
    "📊 Active Institutional Programs"
])

# ----------------- TAB 1: SCOPE REQUEST -----------------
with tab_request:
    st.subheader("Configure Institutional Scope & Compile Syllabus")
    st.write("PragyanAI grounds your syllabus against NBA, NAAC, and IEEE outcome benchmarks using RAG.")

    with st.form("b2b_scope_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_type = st.selectbox("Program Type", ["FDP", "STP", "Workshop", "Guest Lecture"])
            scope = st.text_input("Domain Scope", value="AI in Semiconductor EDA & RTL Design")
            skills_req = st.text_area(
                "Target Technical Competencies",
                value="RISC-V, RTL Verification, TinyML, Verilog, Edge AI"
            )
        with col2:
            spoc_name = st.text_input("Department SPOC Name", value=user["full_name"])
            spoc_phone = st.text_input("SPOC Contact Phone", value=user["phone"])
            spoc_email = st.text_input("SPOC Official Email", value=user["email"])
            
            c_mode, c_dur = st.columns(2)
            with c_mode:
                delivery_mode = st.selectbox("Delivery Mode", ["Online", "Offline", "Hybrid"])
            with c_dur:
                duration_hours = st.number_input("Duration (Hours)", min_value=2, max_value=60, value=30, step=5)
                
            budget_alloc = st.number_input("Budget Allocation (INR)", min_value=5000.0, max_value=500000.0, value=45000.0, step=5000.0)

        btn_compile = st.form_submit_button("🚀 Ground Syllabus via RAG & Submit to Bidding Radar", use_container_width=True)

    if btn_compile:
        with st.spinner("Compiling NBA/NAAC-aligned syllabus via RAG..."):
            try:
                syllabus = compile_academic_syllabus(scope, skills_req, duration_hours, p_type)
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO institutional_requests (
                        college_id, spoc_name, spoc_phone, spoc_email, program_type,
                        scope_description, delivery_mode, budget_inr, compiled_syllabus, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'BIDDING')
                """, (
                    user["id"], spoc_name.strip(), spoc_phone.strip(), spoc_email.strip(),
                    p_type, scope.strip(), delivery_mode, budget_alloc, json.dumps(syllabus)
                ))
                conn.commit()
                conn.close()
                st.success("✅ Program submitted to Expert Bidding Radar! Review your compiled syllabus below:")
                st.json(syllabus)
            except Exception as e:
                st.error(f"Error compiling syllabus: {str(e)}")

# ----------------- TAB 2: REVIEW EXPERT PANELS -----------------
with tab_proposals:
    st.subheader("Anonymized Expert Panel Proposals")
    st.caption("Trainers are tokenized (e.g., EXP-M0412) to protect PII before contract lock-in.")

    conn = get_connection()
    bids = conn.execute("""
        SELECT b.*, e.token, e.industry_vertical, e.experience_years, e.skills, e.rating, e.sessions_completed, r.scope_description
        FROM bids b
        JOIN expert_profiles e ON b.expert_id = e.id
        JOIN institutional_requests r ON b.b2b_request_id = r.id
        WHERE r.college_id = ? AND b.status = 'SUBMITTED'
    """, (user["id"],)).fetchall()
    conn.close()

    if not bids:
        st.info("No incoming expert bids on your active requests yet. Check the verified expert directory below.")
        
        # Display sample qualified experts
        experts = get_anonymized_expert_roster()
        for exp in experts[:3]:
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1:
                    st.image(f"https://api.dicebear.com/7.x/bottts/svg?seed={exp['token']}", width=80)
                    st.caption(f"**{exp['token']}**")
                with c2:
                    st.markdown(f"**{exp['industry_vertical']}** ({exp['experience_years']} Yrs Exp)")
                    st.markdown(f"⭐ **{exp['rating']}/5.0** | Delivered **{exp['sessions_completed']} sessions**")
                    st.caption(f"Skills: `{exp['skills']}`")
                with c3:
                    st.metric("Base Rate", f"₹{exp['hourly_rate_inr']}/hr")
                st.divider()
    else:
        for bid in bids:
            with st.expander(f"💼 Bid for '{bid['scope_description']}': ₹{bid['bid_amount_inr']} from {bid['token']}", expanded=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1:
                    st.image(f"https://api.dicebear.com/7.x/bottts/svg?seed={bid['token']}", width=80)
                    st.caption(f"**{bid['token']}**")
                with c2:
                    st.markdown(f"**{bid['industry_vertical']}** ({bid['experience_years']} Years Experience)")
                    st.markdown(f"Rating: ⭐ {bid['rating']}/5.0 | Total Sessions: {bid['sessions_completed']}")
                    st.info(f"**Delivery Plan:** {bid['counter_notes']}")
                with c3:
                    st.metric("Proposed Bid", f"₹{bid['bid_amount_inr']}")
                    if st.button("Accept Proposal", key=f"acc_bid_{bid['id']}"):
                        c = get_connection()
                        c.execute("UPDATE bids SET status = 'ACCEPTED' WHERE id = ?", (bid['id'],))
                        c.execute("UPDATE institutional_requests SET selected_expert_id = ?, status = 'COORDINATION' WHERE id = ?", (bid['expert_id'], bid['b2b_request_id']))
                        c.commit()
                        c.close()
                        st.success("Proposal accepted! A PragyanAI Coordinator has been assigned.")
                        st.rerun()

# ----------------- TAB 3: ACTIVE REQUESTS -----------------
with tab_my_requests:
    st.subheader("Your Department's Submitted Requests")
    conn = get_connection()
    my_reqs = conn.execute("""
        SELECT * FROM institutional_requests 
        WHERE college_id = ? 
        ORDER BY id DESC
    """, (user["id"],)).fetchall()
    conn.close()

    if not my_reqs:
        st.write("No institutional requests submitted yet.")
    else:
        for req in my_reqs:
            with st.container():
                st.markdown(f"### {req['program_type']}: {req['scope_description']}")
                st.caption(f"Mode: `{req['delivery_mode']}` | Budget: `₹{req['budget_inr']}` | Status: **{req['status']}**")
                if req["compiled_syllabus"]:
                    with st.expander("View Approved Syllabus Blueprint"):
                        try:
                            st.json(json.loads(req["compiled_syllabus"]))
                        except Exception:
                            st.write(req["compiled_syllabus"])
                st.divider()
