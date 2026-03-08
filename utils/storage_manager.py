import json
import os
from typing import Any, Dict
from uuid import uuid4

import cv2
import numpy as np


BASE_STORAGE = os.path.join("private")


def _safe_user_root(username: str) -> str:
    safe_name = os.path.basename(username)
    user_root = os.path.abspath(os.path.join(BASE_STORAGE, safe_name))
    storage_root = os.path.abspath(BASE_STORAGE)
    if not user_root.startswith(storage_root):
        raise ValueError("Invalid username path")
    return user_root


def ensure_user_dirs(username: str) -> Dict[str, str]:
    user_root = _safe_user_root(username)
    face_dir = os.path.join(user_root, "face")
    pred_dir = os.path.join(user_root, "predictions")
    os.makedirs(face_dir, exist_ok=True)
    os.makedirs(pred_dir, exist_ok=True)
    return {
        "root": user_root,
        "face": face_dir,
        "predictions": pred_dir,
    }


def save_profile_face(username: str, face_bgr: np.ndarray) -> str:
    dirs = ensure_user_dirs(username)
    profile_path = os.path.join(dirs["face"], "profile.jpg")
    cv2.imwrite(profile_path, face_bgr)
    return profile_path


def create_prediction_folder(username: str) -> tuple[str, str]:
    dirs = ensure_user_dirs(username)
    prediction_id = str(uuid4())
    prediction_path = os.path.join(dirs["predictions"], prediction_id)
    os.makedirs(prediction_path, exist_ok=False)
    return prediction_id, prediction_path


def save_prediction_artifacts(
    username: str,
    input_bgr: np.ndarray,
    output_bgr: np.ndarray,
    metadata: Dict[str, Any],
) -> Dict[str, str]:
    prediction_id, pred_path = create_prediction_folder(username)
    input_path = os.path.join(pred_path, "input.jpg")
    output_path = os.path.join(pred_path, "output.jpg")
    metadata_path = os.path.join(pred_path, "metadata.json")

    cv2.imwrite(input_path, input_bgr)
    cv2.imwrite(output_path, output_bgr)

    payload = dict(metadata)
    payload["prediction_id"] = prediction_id
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {
        "prediction_id": prediction_id,
        "folder": pred_path,
        "input_path": input_path,
        "output_path": output_path,
        "metadata_path": metadata_path,
    }


def save_chat_history(username: str, message: str, reply: str) -> None:
    user_root = _safe_user_root(username)
    chat_dir = os.path.join(user_root, "chat")
    os.makedirs(chat_dir, exist_ok=True)

    history_path = os.path.join(chat_dir, "history.json")
    history: list[dict[str, str]] = []

    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            if isinstance(payload, list):
                history = [
                    item
                    for item in payload
                    if isinstance(item, dict)
                    and isinstance(item.get("message"), str)
                    and isinstance(item.get("reply"), str)
                ]
        except (json.JSONDecodeError, OSError):
            history = []

    history.append({"message": message, "reply": reply})

    with open(history_path, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
