"""
Session Media & LMS Vault
Provides courseware viewing, PDF handouts inspection, PPTX presentation extraction,
and video lecture streaming for enrolled participants and coordinators.
"""

import os
import streamlit as st
from modules.media_viewer import render_pdf, render_ppt, render_video

st.title("📂 Session LMS & Media Vault")
st.caption("Pre-Class Preparation Kits, Lecture Slide Decks, Lab Handouts & Recorded Archives")

user = st.session_state.get("user")
if not user:
    st.warning("⚠️ Please sign in via the sidebar to access session materials.")
    st.stop()

tab_view, tab_upload = st.tabs(["👀 View & Inspect Materials", "⬆️ Upload Courseware (Coordinators)"])

# ----------------- TAB 1: VIEW MATERIALS -----------------
with tab_view:
    media_category = st.radio(
        "Select Asset Category",
        ["PDF Lecture Notes / Handouts", "PowerPoint Slides (.pptx)", "Video Stream Recording"],
        horizontal=True
    )

    if media_category == "PDF Lecture Notes / Handouts":
        st.subheader("PDF Courseware Viewer")
        pdf_file = st.file_uploader("Upload or Select PDF Document", type=["pdf"], key="viewer_pdf")
        if pdf_file:
            render_pdf(pdf_file)
        else:
            st.info("Upload a PDF syllabus, notes, or lab guide above to inspect its pages.")

    elif media_category == "PowerPoint Slides (.pptx)":
        st.subheader("PowerPoint Presentation Viewer")
        ppt_file = st.file_uploader("Upload PowerPoint Presentation (.pptx)", type=["pptx"], key="viewer_ppt")
        if ppt_file:
            render_ppt(ppt_file)
        else:
            st.info("Upload a .pptx slide deck above to inspect slide topics and bullet points.")

    elif media_category == "Video Stream Recording":
        st.subheader("Session Video Stream Playback")
        video_url = st.text_input(
            "Video Stream Link (MP4, YouTube, or HLS URL)",
            value="https://www.w3schools.com/html/mov_bbb.mp4"
        )
        if video_url.strip():
            render_video(video_url.strip())

# ----------------- TAB 2: UPLOAD (COORDINATOR ONLY) -----------------
with tab_upload:
    if user["role"] not in ("coordinator", "expert"):
        st.info("🔒 Courseware uploads are restricted to instructors and PragyanAI coordinators.")
    else:
        st.subheader("Upload Session Assets to Local Storage")
        u_file = st.file_uploader("Select Course Document (.pdf / .pptx)", key="coord_uploader")
        
        if u_file and st.button("Save to Session Vault", use_container_width=True):
            storage_dir = "storage/documents"
            os.makedirs(storage_dir, exist_ok=True)
            save_path = os.path.join(storage_dir, u_file.name)
            
            with open(save_path, "wb") as f:
                f.write(u_file.getbuffer())
            st.success(f"✅ Successfully saved asset to `{save_path}`!")
