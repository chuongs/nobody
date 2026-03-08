import hashlib

import numpy as np
import streamlit as st
from PIL import Image

from auth.register import USERS_DB, hash_password
from auth.session_manager import create_session


def authenticate(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Please fill in all required fields."
    
    users = USERS_DB.load()
    user = users.get(username)
    if not user:
        return False, "Invalid username or password."

    if user.get("password_hash") != hash_password(password):
        return False, "Invalid username or password."

    create_session(username)
    return True, "True"


def authenticate_face_login(captured_image, threshold: float = 0.5) -> tuple[bool, str, str | None]:
    from utils.face_encoding import extract_single_face_encoding, is_face_match

    pil_image = Image.open(captured_image).convert("RGB")

    width, height = pil_image.size
    square_size = min(width, height)
    left = (width - square_size) // 2
    top = (height - square_size) // 2
    right = left + square_size
    bottom = top + square_size

    avatar_image = pil_image.crop((left, top, right, bottom)).resize((256, 256), Image.Resampling.LANCZOS)
    image_bgr = np.array(avatar_image)[:, :, ::-1]

    try:
        candidate_encoding, _ = extract_single_face_encoding(image_bgr)
    except ValueError:
        import face_recognition

        rgb = np.array(avatar_image)
        face_count = len(face_recognition.face_locations(rgb))
        if face_count == 0:
            return False, "No face detected. Please try again.", None
        if face_count > 1:
            return False, "Please ensure only one face is visible.", None
        return False, "No face detected. Please try again.", None

    users = USERS_DB.load()
    for username, user in users.items():
        stored_encoding = user.get("face_encoding")
        if not stored_encoding:
            continue
        if is_face_match(stored_encoding, candidate_encoding, threshold=threshold):
            create_session(username)
            return True, "True", username

    return False, "Face data not found. Please register your face to use this feature.", None


def render_login_page() -> None:
    st.title("Login")

    login_mode = st.segmented_control(
        "",
        ["PASSWORD LOGIN", "FACE LOGIN"],
        selection_mode="single",
        default="PASSWORD LOGIN",
        key="login_mode",
        label_visibility="collapsed",
    )
    
    with st.container(border=True):
        if login_mode == "PASSWORD LOGIN":
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
    
            if st.button("Login", use_container_width=True):
                ok, msg = authenticate(username, password)
                if ok:
                    msg
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.warning("- " + msg)
    
        if login_mode == "FACE LOGIN":
            captured_image = st.camera_input("Camera", key="face_login_camera")
            if captured_image is not None:
                image_hash = hashlib.sha256(captured_image.getvalue()).hexdigest()
                if st.session_state.get("face_login_last_hash") != image_hash:
                    st.session_state.face_login_last_hash = image_hash
                    ok, msg, username = authenticate_face_login(captured_image)
                    if ok and username:
                        msg
                        st.session_state.username = username
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.warning("- " + msg)

    st.markdown("""
    <style>
    div[data-baseweb="button-group"] button{
        flex: 1 !important;
        width: 150px !important;
        border-radius:0 !important;
    }
    @media (max-width: 450px) {
        div[data-baseweb="button-group"] button{
            width: 225px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
