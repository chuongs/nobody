from __future__ import annotations

import json
import os
from collections import Counter

import pandas as pd
import streamlit as st

from auth.register import USERS_DB

PREDICTIONS = ["glioma", "meningioma", "pituitary"]
ALL_CLASSES = [*PREDICTIONS, "no_tumor"]


def _load_prediction_events(username: str) -> pd.DataFrame:
    users = USERS_DB.load()
    history = users.get(username, {}).get("history", [])

    events: list[dict] = []

    for item in history:
        ts = pd.to_datetime(item.get("time"), errors="coerce")
        if pd.isna(ts):
            continue

        ts = ts.floor("s").isoformat()

        prediction_id = item.get("prediction_id", "")
        metadata_path = os.path.join(
            "private", username, "predictions", prediction_id, "metadata.json"
        )

        labels: list[str] = []
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            labels = [
                str(label).strip().lower()
                for label in metadata.get("labels", [])
                if str(label).strip()
            ]

        counts = Counter(label for label in labels if label in PREDICTIONS)
        total = sum(counts.values())

        if total == 0:
            events.append(
                dict(
                    timestamp=ts,
                    prediction="no_tumor",
                    quantity=1,
                    probability=1.0,
                )
            )
            continue

        for pred in PREDICTIONS:
            qty = int(counts.get(pred, 0))
            events.append(
                dict(
                    timestamp=ts,
                    prediction=pred,
                    quantity=qty,
                    probability=float(qty / total),
                )
            )

    if not events:
        return pd.DataFrame(
            columns=["timestamp", "prediction", "quantity", "probability"]
        )

    return pd.DataFrame(events).sort_values("timestamp").reset_index(drop=True)


def _build_scatter_frame(username: str) -> pd.DataFrame:
    users = USERS_DB.load()
    history = users.get(username, {}).get("history", [])

    rows = []

    for item in history:
        ts = pd.to_datetime(item.get("time"), errors="coerce")
        if pd.isna(ts):
            continue

        ts = ts.floor("s").isoformat()

        prediction_id = item.get("prediction_id", "")
        metadata_path = os.path.join(
            "private", username, "predictions", prediction_id, "metadata.json"
        )

        if not os.path.exists(metadata_path):
            continue

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        labels = metadata.get("labels", [])
        confidences = metadata.get("confidences", [])

        if not labels:
            rows.append(
                dict(timestamp=ts, tumor="no_tumor", confidence=1.0)
            )

        for label, conf in zip(labels, confidences):
            label = str(label).strip().lower()

            if label not in PREDICTIONS:
                continue

            rows.append(
                dict(
                    timestamp=ts,
                    tumor=label,
                    confidence=float(conf),
                )
            )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["idx"] = df.groupby(["timestamp", "tumor"]).cumcount()

    pivot = df.pivot_table(
        index="timestamp",
        columns=["tumor", "idx"],
        values="confidence",
    )

    pivot.columns = [c[0] for c in pivot.columns]

    for cls in ALL_CLASSES:
        if cls not in pivot.columns:
            pivot[cls] = None

    pivot = pivot[ALL_CLASSES]

    return pivot.sort_index().reset_index()


def _build_chart_frames(df: pd.DataFrame):
    quantity_df = (
        df.pivot_table(
            index="timestamp",
            columns="prediction",
            values="quantity",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=ALL_CLASSES, fill_value=0)
        .reset_index()
    )

    return quantity_df


def render_dashboard(username: str) -> None:
    st.title("Dashboard")

    prediction_df = _load_prediction_events(username)

    if prediction_df.empty:
        st.info("- No prediction data available yet. Results will appear here after your first analysis.")
        return

    scatter_df = _build_scatter_frame(username)

    if not scatter_df.empty:
        st.scatter_chart(
            scatter_df,
            x="timestamp",
            y=ALL_CLASSES,
            width="stretch",
            height=382,
        )

    quantity_df = _build_chart_frames(prediction_df)
    
    st.area_chart(
        quantity_df,
        x="timestamp",
        y=ALL_CLASSES,
        width="stretch",
    )
