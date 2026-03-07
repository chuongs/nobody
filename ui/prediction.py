from __future__ import annotations

import uuid
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from PIL import Image
from rembg import remove, new_session
from ultralytics import YOLO

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from streamlit_bokeh import streamlit_bokeh

from auth.register import USERS_DB
from utils.storage_manager import save_prediction_artifacts


DETECTOR_PATH = "yolo11n.pt"
MRI_MODEL_PATH = "best.pt"

# 🔴 Đặt model trong project
U2NET_PATH = "u2net.onnx"


# ===============================
# Load models
# ===============================
@st.cache_resource
def load_models() -> tuple[YOLO, YOLO]:
    return YOLO(DETECTOR_PATH), YOLO(MRI_MODEL_PATH)


# ===============================
# Load U2Net (background removal)
# ===============================
@st.cache_resource
def load_rembg_session():
    return new_session(model_name="u2net", model_path=U2NET_PATH)


# ===============================
# Image utils
# ===============================
def normalize_image(image: np.ndarray) -> np.ndarray:
    return image / 255.0


def resize_image(image: np.ndarray, size=(640, 640)) -> np.ndarray:
    return cv2.resize(image, size)


# ===============================
# Build results
# ===============================
def _build_results(boxes, model_names: dict):

    table_data = {
        "Label": [],
        "Confidence": [],
        "Box": [],
        "Width (px)": [],
        "Height (px)": [],
    }

    labels, confidences, boxes_meta = [], [], []

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        label = model_names[cls_id]

        w, h = x2 - x1, y2 - y1

        labels.append(label)
        confidences.append(conf)
        boxes_meta.append([int(x1), int(y1), int(x2), int(y2)])

        table_data["Label"].append(label)
        table_data["Confidence"].append(f"{conf:.2f}")
        table_data["Box"].append(f"({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
        table_data["Width (px)"].append(int(w))
        table_data["Height (px)"].append(int(h))

    return table_data, labels, confidences, boxes_meta


# ===============================
# Viewer
# ===============================
def show_viewer(image, boxes_meta, labels, confidences):

    h, w, _ = image.shape

    rgba = np.dstack((image, np.full((h, w), 255, dtype=np.uint8)))
    rgba = rgba.view(dtype=np.uint32).reshape(h, w)

    fig = figure(
        width=w,
        height=h,
        x_range=(0, w),
        y_range=(h, 0),
        tools="pan,box_zoom,reset,save",
        toolbar_location="below",
        sizing_mode="scale_both",
    )

    fig.min_border = 0
    fig.image_rgba(image=[rgba], x=0, y=0, dw=w, dh=h)

    data = {
        "x": [],
        "y": [],
        "label": [],
        "confidence": [],
        "box": [],
        "size": [],
    }

    for i, (x1, y1, x2, y2) in enumerate(boxes_meta):

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        bw = x2 - x1
        bh = y2 - y1

        data["x"].append(cx)
        data["y"].append(cy)
        data["label"].append(labels[i])
        data["confidence"].append(f"{confidences[i]:.2f}")
        data["box"].append(f"({x1}, {y1}, {x2}, {y2})")
        data["size"].append(f"{bw} × {bh} px")

    source = ColumnDataSource(data)

    renderer = fig.circle(
        x="x",
        y="y",
        radius=4,
        fill_color="red",
        line_color=None,
        source=source,
    )

    hover = HoverTool(
        renderers=[renderer],
        tooltips=[
            ("Label", "@label"),
            ("Confidence", "@confidence"),
            ("Box", "@box"),
            ("Size", "@size"),
        ],
    )

    fig.add_tools(hover)

    fig.axis.visible = False
    fig.grid.visible = False

    streamlit_bokeh(fig)


# ===============================
# Main predict UI
# ===============================
def render_predict(username: str) -> None:

    detector_model, mri_model = load_models()
    rembg_session = load_rembg_session()

    st.title("Prediction")

    with st.container(border=True):

        uploaded_file = st.file_uploader(
            "Upload an image (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
        )

        remove_bg_mode = st.toggle(
            "Remove background",
            value=False,
        )

        if uploaded_file is None:
            st.info("Please upload an image to get started.")
            return

    with st.container(border=True):

        image = Image.open(uploaded_file).convert("RGB")

        # ===============================
        # Background removal
        # ===============================
        if remove_bg_mode:

            image_no_background = remove(
                image,
                session=rembg_session,
            )

            image_white = Image.new(
                "RGB",
                image_no_background.size,
                (255, 255, 255),
            )

            image_white.paste(
                image_no_background,
                mask=image_no_background.split()[3],
            )

            input_image = image_white

        else:
            input_image = image

        st.image(input_image, caption="Input", use_container_width=True)

        image_cv = cv2.cvtColor(np.array(input_image), cv2.COLOR_RGB2BGR)

        resized_image = resize_image(image_cv)
        normalized_image = normalize_image(resized_image)
        normalized_image_uint8 = (normalized_image * 255).astype(np.uint8)

        # ===============================
        # Detect MRI
        # ===============================
        det_results = detector_model.predict(
            source=normalized_image_uint8,
            imgsz=640,
            conf=0.8,
            verbose=False,
        )

        if len(det_results[0].boxes) > 0:
            st.toast("Please upload an MRI image.", icon="🙃")
            return

        st.toast("MRI analysis completed successfully!", icon="🙂")

        # ===============================
        # Tumor detection
        # ===============================
        results = mri_model.predict(
            source=normalized_image_uint8,
            imgsz=640,
            conf=0.1,
            verbose=False,
        )

        boxes = results[0].boxes
        annotated_image = results[0].plot(line_width=2)
        annotated_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)

        table_data, labels, confidences, boxes_meta = _build_results(
            boxes,
            mri_model.names,
        )

        show_viewer(annotated_rgb, boxes_meta, labels, confidences)

        st.table(table_data)

        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "labels": labels,
            "confidences": confidences,
            "boxes": boxes_meta,
        }

        artifacts = save_prediction_artifacts(
            username,
            normalized_image_uint8,
            annotated_image,
            metadata,
        )

        users = USERS_DB.load()

        users[username].setdefault("history", []).append(
            {
                "prediction_id": artifacts["prediction_id"],
                "time": metadata["timestamp"],
                "result_path": artifacts["output_path"],
                "summary": ", ".join(sorted(set(labels)))
                if labels
                else "No tumor detected",
            }
        )

        USERS_DB.save(users)
