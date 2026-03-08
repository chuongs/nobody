from __future__ import annotations

import json
import os
from typing import TypedDict

import requests
import streamlit as st

from utils.storage_manager import save_chat_history


WEBHOOK_URL = "https://sj2ddx52f4.app.n8n.cloud/webhook/50e8fbbd-d475-43fe-b7ed-70db7c0e5948"


class ChatItem(TypedDict):
    message: str
    reply: str


def send_message(message: str, username: str) -> str:
    response = requests.post(
        WEBHOOK_URL,
        json={"message": message, "sessionId": username},
        timeout=30,
    )
    response.raise_for_status()
    reply = response.text
    save_chat_history(username=username, message=message, reply=reply)
    return reply


def load_chat_history(username: str) -> list[ChatItem]:
    history_path = os.path.join("private", os.path.basename(username), "chat", "history.json")

    if not os.path.exists(history_path):
        return []

    with open(history_path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [
        item
        for item in payload
        if isinstance(item, dict)
        and isinstance(item.get("message"), str)
        and isinstance(item.get("reply"), str)
    ]


def render_chatbot(username: str) -> None:
    st.title("Chatbot")

    history = load_chat_history(username)
    prompt = st.chat_input("Send a message...")

    if not history and not prompt:
        st.info("- Please enter your question below to start chatting with the assistant.")

    for item in history:
        with st.chat_message("user"):
            st.write(item["message"])
        with st.chat_message("assistant"):
            st.write(item["reply"])

    if not prompt:
        return

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("""
        <style>
        .typing {
            display: flex;
            align-items: center;
            height: 25.6px;
        }
        .typing span {
            width: 8px;
            height: 8px;
            margin-right: 8px;
            background-color: #999;
            border-radius: 50%;
            animation: bounce 1.2s infinite ease-in-out;
        }
        .typing span:nth-child(1) {
            margin-left: 1px;
        }
        .typing span:nth-child(2) {
            animation-delay: .2s;
        }
        .typing span:nth-child(3) {
            animation-delay: .4s;
        }
        @keyframes bounce {
            0%, 80%, 100% { 
                transform: scale(0.6);
                opacity: .3;
            }
            40% { 
                transform: scale(1);
                opacity: 1;
            }
        }
        </style>
        <p class="typing"><span></span><span></span><span></span></p>
        """, unsafe_allow_html=True)
        reply = send_message(prompt, username)
        placeholder.markdown(reply)
