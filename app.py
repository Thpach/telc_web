import os
import random
import fitz
from PIL import Image
import streamlit as st

st.set_page_config(page_title="TELC Exam Practice", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown("<h2 style='text-align: center; color: #f8fafc;'>TELC Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password_input = st.text_input("Enter Password", type="password")
            if st.button("Login", use_container_width=True):
                if password_input == "telc2026":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong Password!")
        return False
    return True

if not check_password():
    st.stop()

st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #020617; }
    button[kind="primary"] { background-color: #10b981 !important; border: none; }
    </style>
""", unsafe_allow_html=True)

BASE_FOLDER = "TELC"

if "current_pdf" not in st.session_state: st.session_state.current_pdf = None
if "selected_folder" not in st.session_state: st.session_state.selected_folder = ""
if "lv3_page" not in st.session_state: st.session_state.lv3_page = 0

def get_subfolders():
    if not os.path.exists(BASE_FOLDER): return []
    return sorted([d for d in os.listdir(BASE_FOLDER) if os.path.isdir(os.path.join(BASE_FOLDER, d))])

def render_page(doc, page_num):
    if page_num >= len(doc): return None
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def pick_random_pdf(folder):
    folder_path = os.path.join(BASE_FOLDER, folder)
    if not os.path.exists(folder_path): return None
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    return random.choice(files) if files else None

st.sidebar.title("TELC APP")
subfolders = get_subfolders()
if subfolders:
    selected = st.sidebar.selectbox("Select Section:", subfolders)
    if selected != st.session_state.selected_folder:
        st.session_state.selected_folder = selected
        st.session_state.current_pdf = pick_random_pdf(selected)
        st.session_state.lv3_page = 0
    if st.sidebar.button("Random Test", type="primary", use_container_width=True):
        st.session_state.current_pdf = pick_random_pdf(selected)
        st.session_state.lv3_page = 0
        st.rerun()
else:
    st.sidebar.error("'TELC' folder not found!")

if st.session_state.current_pdf:
    pdf_path = os.path.join(BASE_FOLDER, st.session_state.selected_folder, st.session_state.current_pdf)
    st.subheader(f"Section: {st.session_state.selected_folder} | File: {st.session_state.current_pdf}")
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    folder_upper = st.session_state.selected_folder.upper()
    if "HV1" in folder_upper or "HV2" in folder_upper:
        for p in range(page_count):
            img = render_page(doc, p)
            if img: st.image(img, use_container_width=True)
    elif "LV3" in folder_upper and page_count >= 3:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### Left Page (Text / Questions)")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Page 1", use_container_width=True):
                    st.session_state.lv3_page = 0
                    st.rerun()
            with btn_col2:
                if st.button("Page 2", use_container_width=True):
                    st.session_state.lv3_page = 1
                    st.rerun()
            img_left = render_page(doc, st.session_state.lv3_page)
            if img_left: st.image(img_left, use_container_width=True)
        with col_right:
            st.markdown("### Right Page (Options)")
            img_right = render_page(doc, 2)
            if img_right: st.image(img_right, use_container_width=True)
    else:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### Left Page")
            img_left = render_page(doc, 0)
            if img_left: st.image(img_left, use_container_width=True)
        with col_right:
            st.markdown("### Right Page")
            for p in range(1, page_count):
                img_right = render_page(doc, p)
                if img_right: st.image(img_right, use_container_width=True)
else:
    st.info("Please select a section.")