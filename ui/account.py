import os

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from auth.register import USERS_DB, hash_password, is_valid_email
from utils.face_encoding import extract_single_face_encoding, is_face_match
from utils.storage_manager import ensure_user_dirs


def _update_password(username: str, current_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    users = USERS_DB.load()
    user = users.get(username)
    if not current_password or not new_password or not confirm_password:
        return False, "Please fill in all required fields."
        
    if user.get("password_hash") != hash_password(current_password):
        return False, "The current password you entered is incorrect."

    if new_password != confirm_password:
        return False, "New passwords do not match."

    user["password_hash"] = hash_password(new_password)
    USERS_DB.save(users)
    return True, "True"


def _update_email(username: str, email: str) -> tuple[bool, str]:
    users = USERS_DB.load()
    user = users.get(username)

    email = email.strip()
    if not email:
        return False, "Please enter your email address."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."

    user["email"] = email
    USERS_DB.save(users)
    return True, "True"


def face_registration(username: str, uploaded_file) -> tuple[bool, str]:
    pil_image = Image.open(uploaded_file).convert("RGB")
    width, height = pil_image.size
    square_size = min(width, height)
    left = (width - square_size) // 2
    top = (height - square_size) // 2
    right = left + square_size
    bottom = top + square_size

    avatar_image = pil_image.crop((left, top, right, bottom)).resize((256, 256), Image.Resampling.LANCZOS)
    image_bgr = cv2.cvtColor(np.array(avatar_image), cv2.COLOR_RGB2BGR)

    try:
        encoding, _ = extract_single_face_encoding(image_bgr)
    except ValueError as e:
        return False, str(e)

    users = USERS_DB.load()
    for existing_user in users.values():
        stored_encoding = existing_user.get("face_encoding")
        if not stored_encoding:
            continue
        if is_face_match(stored_encoding, encoding):
            return False, "This face is already registered"

    dirs = ensure_user_dirs(username)
    profile_path = os.path.join(dirs["face"], "profile.jpg")
    avatar_image.save(profile_path, format="JPEG")

    user = users.get(username)

    user["face_encoding"] = encoding.tolist()
    USERS_DB.save(users)
    return True, "True"


def render_account(username: str) -> None:
    st.title("Account")

    users = USERS_DB.load()
    user = users.get(username, {})
    has_face_registration = bool(user.get("face_encoding"))

    dirs = ensure_user_dirs(username)
    profile_path = os.path.join(dirs["face"], "profile.jpg")

    with st.container(border=True):
        avatar_col, info_col = st.columns([1, 3])
        with avatar_col:
            img_path = profile_path if os.path.exists(profile_path) else "profile.jpg"
            st.image(
                Image.open(img_path),
                caption="Avatar",
                use_container_width=True
            )
    
        with info_col:
            st.write(f"- Username: {username}")
            st.write(f"- Email: {user.get('email')}")
            st.write(f"- Number of predictions: {len(user.get('history'))}")

    with st.container(border=True):
        tab_password, tab_face, tab_email = st.tabs(["Change Password", "Face Registration", "Change Email"])
        with tab_password:
            if st.session_state.get("clear_password_form"):
                st.session_state["account_current_password"] = ""
                st.session_state["account_new_password"] = ""
                st.session_state["account_confirm_new_password"] = ""
                del st.session_state["clear_password_form"]
    
            current_password = st.text_input("Current password", type="password", key="account_current_password")
            new_password = st.text_input("New password", type="password", key="account_new_password")
            confirm_password = st.text_input("Confirm new password", type="password", key="account_confirm_new_password")
    
            if st.button("Change password", key="account_update_password", use_container_width=True):
                ok, msg = _update_password(username, current_password, new_password, confirm_password)
                if ok:
                    msg
                    st.session_state["password_success"] = True
                    st.session_state["clear_password_form"] = True
                    st.rerun()
                else:
                    st.warning("- " + msg)
    
            if st.session_state.get("password_success"):
                st.success("- Your password has been updated successfully!")
                del st.session_state["password_success"]
    
        with tab_face:
            if has_face_registration:
                if st.session_state.get("avatar_success"):
                    st.success("- Face registration completed successfully!")
                    del st.session_state["avatar_success"]
                st.session_state.pop("avatar_success", None)
                if st.button("Remove face registration", key="account_cancel_face_registration", use_container_width=True):
                    face_dir = dirs["face"]
                    if os.path.isdir(face_dir):
                        for filename in os.listdir(face_dir):
                            file_path = os.path.join(face_dir, filename)
                            if not os.path.isfile(file_path):
                                continue
                            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                                continue
                            os.remove(file_path)
    
                    users = USERS_DB.load()
                    user = users.get(username)
                    if user:
                        user["face_encoding"] = []
                        USERS_DB.save(users)
    
                    st.session_state["face_cancel_success"] = True
                    st.session_state.pop("account_avatar_output_name", None)
                    st.rerun()
            else:
                uploaded = st.file_uploader("Upload an image (JPG/PNG)", type=["jpg", "jpeg", "png"], key="account_avatar_upload")
                if st.session_state.get("face_cancel_success"):
                    st.success("- Face registration has been removed successfully!")
                    del st.session_state["face_cancel_success"]
    
                last_output_name = st.session_state.get("account_avatar_output_name")
                if uploaded is not None and uploaded.name != last_output_name:
                    ok, msg = face_registration(username, uploaded)
                    if ok:
                        st.session_state["account_avatar_output_name"] = uploaded.name
                        st.session_state["avatar_success"] = True
                        st.rerun()
                    else:
                        st.warning("- " + msg)
    
        with tab_email:
            new_email = st.text_input("New email", value=user.get("email"), key="account_new_email")
            if st.button("Change email", key="account_update_email", use_container_width=True):
                ok, msg = _update_email(username, new_email)
                if ok:
                    msg
                    st.session_state["email_success"] = True
                    st.rerun()
                else:
                    st.warning("- " + msg)
    
            if st.session_state.get("email_success"):
                st.success("- Your email has been updated successfully!")
                del st.session_state["email_success"]
