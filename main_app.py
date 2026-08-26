"""
PragyanAI DemandX - Master Application Entry Point & Navigation Controller
Handles user authentication, session state initialization, quick-demo persona switching,
and role-based multi-page routing.
"""

import streamlit as st
from config.database import init_db
from modules.auth import authenticate_user, register_user

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="PragyanAI DemandX - Learning Exchange",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- INITIALIZE PERSISTENCE -----------------
init_db()

# ----------------- SESSION STATE BOOTSTRAP -----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ----------------- SIDEBAR AUTHENTICATION & PERSONA SWITCHER -----------------
with st.sidebar:
    st.title("🎓 PragyanAI DemandX")
    st.caption("AI-Aggregated Demand | RAG Compiler | Expert Exchange")

    if st.session_state.user:
        u = st.session_state.user
        st.success(f"Signed in as **{u['full_name']}**")
        st.info(
            f"**Role:** `{u['role'].upper()}`\n\n"
            f"**Username:** `{u['username']}`\n\n"
            f"**Institution:** {u['institution'] or 'Independent'}\n\n"
            f"**Department:** {u['department'] or 'General'}"
        )

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.markdown("### Access Gateway")
        tab_login, tab_demo, tab_register = st.tabs(["🔑 Sign In", "⚡ Quick Demo", "📝 Register"])

        # TAB 1: STANDARD SIGN IN
        with tab_login:
            login_username = st.text_input("Username", key="auth_login_user")
            login_password = st.text_input("Password", type="password", key="auth_login_pwd")

            if st.button("Sign In", use_container_width=True, type="primary"):
                if login_username and login_password:
                    user_data = authenticate_user(login_username, login_password)
                    if user_data:
                        st.session_state.user = user_data
                        st.success(f"Welcome back, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please enter both username and password.")

        # TAB 2: ONE-CLICK QUICK DEMO LOGIN
        with tab_demo:
            st.caption("Switch between seeded stakeholder accounts (Password: `Pragyan@2026`)")
            demo_persona = st.selectbox(
                "Select Test Persona",
                [
                    ("coord_sateesh", "Admin / Coordinator (Sateesh Ambesange)"),
                    ("stu_aarav", "Student - Valid & Enrolled (Aarav Sharma)"),
                    ("stu_bad_utr", "Student - Invalid/At-Risk (Abhishek Gowda)"),
                    ("exp_arjun", "Skill Expert - Semiconductor/EDA (Dr. Arjun)"),
                    ("exp_rohit", "Skill Expert - Agentic AI/MCP (Rohit Kulkarni)"),
                    ("hod_rvce", "College HOD - RVCE CSE (Dr. K. S. Ramaiah)"),
                ],
                format_func=lambda x: x[1],
                key="demo_persona_select",
            )

            if st.button("⚡ Fast Sign-In as Selected Persona", use_container_width=True):
                user_data = authenticate_user(demo_persona[0], "Pragyan@2026")
                if user_data:
                    st.session_state.user = user_data
                    st.success(f"Signed in as {user_data['full_name']}!")
                    st.rerun()
                else:
                    st.error("Persona not found. Please run the database seeder from the Coordinator Hub.")

        # TAB 3: SELF-REGISTRATION
        with tab_register:
            reg_name = st.text_input("Full Name", key="auth_reg_name")
            reg_username = st.text_input("Username", key="auth_reg_user")
            reg_password = st.text_input("Password", type="password", key="auth_reg_pwd")
            reg_role = st.selectbox(
                "Select Account Role",
                ["student", "college", "expert", "coordinator"],
                format_func=lambda x: {
                    "student": "Student (Learner / Demand Sourcing)",
                    "college": "College / Institutional HOD (B2B Buyer)",
                    "expert": "Skill Expert / Trainer (Supply)",
                    "coordinator": "PragyanAI Operations Coordinator",
                }.get(x, x),
                key="auth_reg_role",
            )
            reg_phone = st.text_input("Phone Number (+91)", key="auth_reg_phone", placeholder="+919876543210")
            reg_email = st.text_input("Email Address", key="auth_reg_email", placeholder="user@domain.com")
            reg_inst = st.text_input("College / Organization", key="auth_reg_inst", placeholder="e.g. RV College of Engineering")
            reg_dept = st.text_input("Department / Specialization", key="auth_reg_dept", placeholder="e.g. CSE 6th Sem")

            if st.button("Create Account", use_container_width=True):
                if reg_name and reg_username and reg_password:
                    ok, msg = register_user(
                        username=reg_username,
                        password=reg_password,
                        full_name=reg_name,
                        role=reg_role,
                        phone=reg_phone,
                        email=reg_email,
                        institution=reg_inst,
                        department=reg_dept,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please complete all required fields (Name, Username, Password).")

    st.divider()
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: gray; text-align: center;">
            PragyanAI DemandX Platform v1.0.0<br/>
            Direct Learning Exchange & Institutional Scoping
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------- ROLE-BASED NAVIGATION ROUTING -----------------
pages_config = {
    "Learner Experience": [
        st.Page("pages/01_student_portal.py", title="Student Dashboard & Cohorts", icon="👨‍🎓"),
    ],
    "Institutional Workspaces": [
        st.Page("pages/02_college_portal.py", title="College FDP Workspace", icon="🏛️"),
    ],
    "Expert Marketplace": [
        st.Page("pages/03_expert_portal.py", title="Expert Reverse Bidding", icon="💼"),
    ],
    "Operations & LMS": [
        st.Page("pages/04_coordinator_hub.py", title="Coordinator Operations Hub", icon="⚙️"),
        st.Page("pages/05_media_vault.py", title="Session Media & LMS Vault", icon="📂"),
    ],
}

nav = st.navigation(pages_config)
nav.run()
