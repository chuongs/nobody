from __future__ import annotations

from typing import Tuple

import cv2
import face_recognition
import numpy as np


def extract_single_face_encoding(image_bgr: np.ndarray) -> Tuple[np.ndarray, tuple[int, int, int, int]]:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if len(locations) != 1:
        raise ValueError("Image must contain exactly one face")

    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    if len(encodings) != 1:
        raise ValueError("Could not encode face")

    top, right, bottom, left = locations[0]
    face_crop = image_bgr[top:bottom, left:right]
    if face_crop.size == 0:
        raise ValueError("Invalid face crop")
    return encodings[0], (top, right, bottom, left)


def is_face_match(stored_encoding: list[float], candidate_encoding: np.ndarray, threshold: float = 0.5) -> bool:
    stored = np.array(stored_encoding, dtype=np.float64)
    return bool(face_recognition.compare_faces([stored], candidate_encoding, tolerance=threshold)[0])
