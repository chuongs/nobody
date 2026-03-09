import os

import streamlit as st

from auth.login import render_login_page
from auth.register import render_register_page
from auth.session_manager import logout, restore_session
from ui.account import render_account
from ui.chatbot import render_chatbot
from ui.dashboard import render_dashboard
from ui.history import render_history
from ui.prediction import render_predict
from utils.json_db import JsonDB
from utils.storage_manager import ensure_user_dirs

st.markdown("""
<link rel="stylesheet" href="https://site-assets.fontawesome.com/releases/v7.2.0/css/all.css">

<style>
div[data-testid="stMainBlockContainer"] {
    padding-top: 42.5px !important;
}
div[data-testid="stVerticalBlock"],
img {
    border-radius: 0 !important;
}
[data-testid="InputInstructions"] {
    display: none !important;
}
.divider3 {
    margin: -0.5rem -15px 0 !important;
}
@media (min-width: calc(736px + 8rem)) {
    div[data-testid="stMainBlockContainer"],
    div[data-testid="stBottomBlockContainer"] {
        padding-left: 10rem !important;
        padding-right: 10rem !important;
    }
}
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_icon="logo.png", page_title="Brain Tumor Detection", layout="wide")


JsonDB("database/users.json", default_data={})
JsonDB("database/sessions.json", default_data={})
os.makedirs(os.path.join("private"), exist_ok=True)

restore_session()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard" if st.session_state.get("authenticated") else "Login"

is_authenticated = st.session_state.get("authenticated", False)
username = st.session_state.get("username")

with st.sidebar:
    st.markdown("""
    <style>
    .brand-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: -44px;
        pointer-events: none;
    }
    .brand-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        background: rgb(255, 75, 75);
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    }
    .brand-logo i {
        font-size: 30px;
    }
    .brand-text {
        display: flex;
        flex-direction: column;
        justify-content: center;
        line-height: 1.25;
    }
    .brand-title {
        font-size: 20px;
        font-weight: 700;
    }
    .brand-sub {
        margin: 0;
        font-size: 12px;
        font-weight: 450;
        color: rgba(150,150,150,0.8);
    }
    #divider2 {
        margin-top: 1rem;
    }
    </style>
    
    <div class="brand-header">
        <div class="brand-logo">
            <i class="fa-duotone fa-solid fa-robot"></i>
        </div>
        <div class="brand-text">
            <div class="brand-title">Brain.</div>
            <div class="brand-sub">AI Medical System</div>
        </div>
    </div>
    <hr id="divider1">
    """, unsafe_allow_html=True)
    if not is_authenticated:
        if st.button("Login", use_container_width=True, type="primary"):
            st.session_state.page = "Login"
        if st.button("Register", use_container_width=True, type="primary"):
            st.session_state.page = "Register"
    else:
        ensure_user_dirs(username)
        for page in ["Dashboard", "Prediction", "History", "Chatbot", "Account"]:
            if st.button(page, use_container_width=True, type="primary"):
                st.session_state.page = page
        st.markdown("""<hr id="divider2">""", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

page = st.session_state.page

if not is_authenticated:
    if page == "Register":
        render_register_page()
    else:
        render_login_page()
else:
    if page == "Dashboard":
        render_dashboard(username)
    elif page == "Prediction":
        render_predict(username)
    elif page == "History":
        render_history(username)
    elif page == "Chatbot":
        render_chatbot(username)
    elif page == "Account":
        render_account(username)
    else:
        render_dashboard(username)
