from __future__ import annotations

import json
import os

import streamlit as st

from auth.register import USERS_DB


def _safe_user_file(username: str, path: str) -> str:
    user_root = os.path.abspath(os.path.join("private", username))
    file_abs = os.path.abspath(path)
    if not file_abs.startswith(user_root):
        raise ValueError("Unauthorized file path")
    return file_abs


def render_history(username: str) -> None:
    st.title("History")
    users = USERS_DB.load()
    history = users.get(username, {}).get("history", [])

    if not history:
        st.info("- No predictions available yet.")
        return

    with st.container(border=True):
        history_list = list(reversed(history))
        for idx, item in enumerate(history_list):
            prediction_id = item["prediction_id"]
            pred_folder = os.path.join("private", username, "predictions", prediction_id)
            input_path = os.path.join(pred_folder, "input.jpg")
            output_path = os.path.join(pred_folder, "output.jpg")
            metadata_path = os.path.join(pred_folder, "metadata.json")
    
            input_safe = _safe_user_file(username, input_path)
            output_safe = _safe_user_file(username, output_path)
            metadata_safe = _safe_user_file(username, metadata_path)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if os.path.exists(input_safe):
                    st.image(input_safe, caption="Original", use_container_width=True)
            with col2:
                if os.path.exists(output_safe):
                    st.image(output_safe, caption="Output", use_container_width=True)
            with col3:
                st.write(f"- Time: {item.get('time', 'N/A')}")
                st.write(f"- Summary: {item.get('summary', 'N/A')}")
    
                labels = []
                if os.path.exists(metadata_safe):
                    with open(metadata_safe, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    labels = metadata.get("labels", [])
                st.write(f"- Labels: {', '.join(labels) if labels else 'None'}")
    
                toggle_key = f"show_detail_{prediction_id}"
                show_detail = st.toggle(
                    "Show details",
                    key=toggle_key,
                )
    
            if show_detail and os.path.exists(metadata_safe):
                with st.container(border=True):
                    with open(metadata_safe, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    st.image(output_safe, caption="Output", use_container_width=True)
                    st.write("Data Table")
                    table_data = {"Label": [], "Confidence": [], "Box": [], "Width (px)": [], "Height (px)": []}
                    for label, conf, box in zip(
                        metadata.get("labels", []), metadata.get("confidences", []), metadata.get("boxes", [])
                    ):
                        x1, y1, x2, y2 = box
                        width = int(x2) - int(x1)
                        height = int(y2) - int(y1)
        
                        table_data["Label"].append(label)
                        table_data["Confidence"].append(f"{float(conf):.2f}")
                        table_data["Box"].append(f"({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
                        table_data["Width (px)"].append(width)
                        table_data["Height (px)"].append(height)
                    st.table(table_data)

            if idx < len(history_list) - 1:
                st.markdown('<hr class="divider3">', unsafe_allow_html=True)

    st.markdown("""
    <style>
    @media (max-width: 640px){
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:nth-child(1),
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:nth-child(2) {
            flex: 1 1 calc(50% - 0.5rem) !important;
        }
        div[data-testid="stColumn"]{
            min-width:0 !important;
        }
    }
    div[data-testid="stVerticalBlock"]:has(
    > div[data-testid="stLayoutWrapper"]
    > div[data-testid="stHorizontalBlock"]) {
        padding: 1rem !important;
    }
    """, unsafe_allow_html=True)
