import uuid

import streamlit as st

from utils.json_db import JsonDB


SESSION_DB = JsonDB("database/sessions.json", default_data={})


def restore_session() -> None:
    if st.session_state.get("authenticated"):
        return
    token = st.query_params.get("token")
    if not token:
        return

    sessions = SESSION_DB.load()
    username = sessions.get(token)
    if username:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["session_token"] = token


def create_session(username: str) -> str:
    token = str(uuid.uuid4())
    sessions = SESSION_DB.load()
    sessions[token] = username
    SESSION_DB.save(sessions)

    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["session_token"] = token
    st.query_params["token"] = token
    return token


def logout() -> None:
    sessions = SESSION_DB.load()
    token = st.session_state.get("session_token") or st.query_params.get("token")
    if token and token in sessions:
        del sessions[token]
        SESSION_DB.save(sessions)

    for key in ["authenticated", "username", "session_token", "page"]:
        if key in st.session_state:
            del st.session_state[key]

    if "token" in st.query_params:
        del st.query_params["token"]
