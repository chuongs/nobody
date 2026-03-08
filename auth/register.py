import hashlib
import re

import streamlit as st

from utils.json_db import JsonDB


USERS_DB = JsonDB("database/users.json", default_data={})


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def register_user(username: str, password: str, email: str, confirm: str) -> tuple[bool, str]:
    username = username.strip()
    email = email.strip()
    if not username or not password or not email:
        return False, "Please fill in all required fields."

    if not is_valid_email(email):
        return False, "Please enter a valid email address."

    if password != confirm:
        return False, "Passwords do not match."

    users = USERS_DB.load()
    if username in users:
        return False, "This username already exists."

    users[username] = {
        "password_hash": hash_password(password),
        "email": email,
        "face_encoding": [],
        "history": [],
    }
    USERS_DB.save(users)
    return True, "True"


def render_register_page() -> None:
    st.title("Register")
    
    with st.container(border=True):
        if st.session_state.get("clear_register_form"):
            st.session_state["register_username"] = ""
            st.session_state["register_email"] = ""
            st.session_state["register_password"] = ""
            st.session_state["register_confirm"] = ""
            del st.session_state["clear_register_form"]
        
        username = st.text_input("Username", key="register_username")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm = st.text_input("Confirm Password", type="password", key="register_confirm")
    
        if st.button("Register", use_container_width=True):
            ok, msg = register_user(username, password, email, confirm)
            if ok:
                msg
                st.session_state["register_success"] = True
                st.session_state["clear_register_form"] = True
                st.rerun()
            else:
                st.warning("- " + msg)
    
        if st.session_state.get("register_success"):
            st.success("- Your account has been created successfully!")
            st.info("- You can register your face in the Account section.")
            del st.session_state["register_success"]
