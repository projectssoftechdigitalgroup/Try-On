# models/clothesTryOn.py
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logs

import cv2
import mediapipe as mp
import numpy as np
import random
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/clothes", tags=["Clothes Try-On"])

# -------------------------------
# Clothing Selection Model
# -------------------------------
class ClothingSelection(BaseModel):
    gender: str = "male"
    top: str = "m_shirt1"
    bottom: str = "m_pant"
    dress: str = "none"


# -------------------------------
# Global clothing selection state
# -------------------------------
current_selection = ClothingSelection()

# -------------------------------
# Correct Base Paths
# -------------------------------
# Go one directory up from "models" → backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database")

print(f"✅ Using clothing database path: {DATABASE_PATH}")

# -------------------------------
# Clothing Data Mapping
# -------------------------------
CLOTHING_DATA = {
    # === MALE - EASTERN WEAR ===
    "m_shirt1": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "shirt1.png"),
    "m_shirt2": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "shirt2.png"),
    "m_shirt3": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "shirt3.png"),
    "m_polo": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "polo.png"),
    "m_pant": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "pant.png"),
    "m_suit": os.path.join(DATABASE_PATH, "male", "Eastern-Wear", "full_suit.png"),

    # === MALE - TRADITIONAL WEAR ===
    "m_kurta": os.path.join(DATABASE_PATH, "male", "Traditional-Wear", "kurta.png"),
    "m_pajama": os.path.join(DATABASE_PATH, "male", "Traditional-Wear", "pajama.png"),

    # === FEMALE - EASTERN WEAR ===
    "f_blouse": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "blouse.png"),
    "f_denim-jacket": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "denim-jacket.png"),
    "f_tunic": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "tunic.png"),
    "f_jeans": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "jeans.png"),
    "f_skirt": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "skirt.png"),
    "f_sundress": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "sundress.png"),
    "f_gown": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "gown.png"),
    "f_redskirt": os.path.join(DATABASE_PATH, "female", "Eastern-Wear", "redskirt.png"),

    # === FEMALE - TRADITIONAL WEAR ===
    "f_saree": [
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "saree.png"),
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "saree2.png"),
    ],
    "f_lehenga": [
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "lehenga1.png"),
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "lehenga2.png"),
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "lehenga3.png"),
        os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "lehenga4.png"),
    ],
    "f_suit2": os.path.join(DATABASE_PATH, "female", "Traditional-Wear", "suit2.png"),

    # === KIDS - BOY EASTERN WEAR ===
    "kb_shirt": os.path.join(DATABASE_PATH, "kids", "boy", "Eastern-Wear", "shirt.png"),
    "kb_shorts": os.path.join(DATABASE_PATH, "kids", "boy", "Eastern-Wear", "shorts.png"),
    "kb_suit": os.path.join(DATABASE_PATH, "kids", "boy", "Eastern-Wear", "suit.png"),

    # === KIDS - GIRL EASTERN WEAR ===
    "kg_tshirt": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "shirt.png"),
    "kg_tshirt2": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "shirt2.png"),
    "kg_skirt": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "skirt.png"),
    "kg_skirt2": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "skirt2.png"),
}

# -------------------------------
# Load Clothing Images
# -------------------------------
def load_clothing_images():
    """
    Loads top_img, bottom_img, dress_img and sets top_type/bottom_type/dress_type/gender_type
    Uses placeholders when files missing to avoid crashes.
    """
    global top_img, bottom_img, dress_img, top_type, bottom_type, dress_type, gender_type
    gender_type = current_selection.gender
    top_type = current_selection.top
    bottom_type = current_selection.bottom
    dress_type = current_selection.dress

    def get_image(path_entry: Optional[str]):
        # if path_entry is list choose at random (for multiple variants)
        if isinstance(path_entry, list):
            path_entry_local = random.choice(path_entry)
        else:
            path_entry_local = path_entry

        if not path_entry_local:
            return None
        if not os.path.exists(path_entry_local):
            return None
        img = cv2.imread(path_entry_local, cv2.IMREAD_UNCHANGED)
        return img

    top_path = CLOTHING_DATA.get(top_type)
    bottom_path = CLOTHING_DATA.get(bottom_type)
    dress_path = CLOTHING_DATA.get(dress_type, None)

    top_img = get_image(top_path)
    bottom_img = get_image(bottom_path)
    dress_img = get_image(dress_path)

    # Use placeholders if something is missing (avoid crashing)
    if top_img is not None:
        print(f"✅ Loaded top: {top_path}")
    elif top_type != "none":
        print(f"⚠️ Top cloth not found at {top_path}, using placeholder")
        top_img = np.zeros((200, 200, 4), dtype=np.uint8)

    if bottom_img is not None:
        print(f"✅ Loaded bottom: {bottom_path}")
    elif bottom_type != "none":
        print(f"⚠️ Bottom cloth not found at {bottom_path}, using placeholder")
        bottom_img = np.zeros((200, 200, 4), dtype=np.uint8)

    if dress_img is not None:
        print(f"✅ Loaded dress: {dress_path}")
    elif dress_type != "none":
        print(f"⚠️ Dress cloth not found at {dress_path}, using placeholder")
        dress_img = np.zeros((300, 300, 4), dtype=np.uint8)


# Initialize clothing images
load_clothing_images()

# -------------------------------
# Mediapipe Pose Setup
# -------------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5
)

landmark_names = {
    "l_shoulder": 11, "r_shoulder": 12,
    "l_hip": 23, "r_hip": 24,
    "l_knee": 25, "r_knee": 26,
    "l_toe": 31, "r_toe": 32
}

# -------------------------------
# Overlay Helper
# -------------------------------
def overlay_transparent(background: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
    """
    Overlays `overlay` (RGBA) onto `background` (BGR) at position (x,y).
    Returns modified background. If overlay has no alpha channel or
    sizes mismatch it'll try to handle gracefully.
    """
    if overlay is None:
        return background

    h, w = overlay.shape[:2]

    # bounds checks + cropping the overlay if it goes out of frame
    if x >= background.shape[1] or y >= background.shape[0]:
        return background

    if x < 0:
        overlay = overlay[:, -x:]
        w = overlay.shape[1]
        x = 0
    if y < 0:
        overlay = overlay[-y:, :]
        h = overlay.shape[0]
        y = 0

    if x + w > background.shape[1]:
        w = background.shape[1] - x
        overlay = overlay[:, :w]
    if y + h > background.shape[0]:
        h = background.shape[0] - y
        overlay = overlay[:h, :]

    # require alpha channel
    if overlay.shape[2] < 4:
        return background

    overlay_img = overlay[:, :, :3]
    mask = overlay[:, :, 3:] / 255.0

    roi = background[y:y+h, x:x+w]
    # if sizes differ unexpectedly, skip to avoid crashing
    if roi.shape[:2] != overlay_img.shape[:2]:
        return background

    blended = (1.0 - mask) * roi + mask * overlay_img
    background[y:y+h, x:x+w] = blended.astype(np.uint8)
    return background


# -------------------------------
# Cloth Placement Logic
# -------------------------------
def place_cloth(frame: np.ndarray, cloth_img: np.ndarray, cloth_type: str, get_point) -> np.ndarray:
    if cloth_img is None or cloth_type == "none":
        return frame

    # Bottom / Pants / Skirts / Jeans
    if any(tag in cloth_type for tag in ["pant", "jeans", "pajama", "skirt", "tunic"]):
        l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
        l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

        hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
        leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))

        new_w = max(1, int(hip_w * 2.2))
        new_h = max(1, int(leg_h * 1.1))

        resized = cv2.resize(cloth_img, (new_w, new_h))
        cx = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2)
        cy = int(min(l_hip[1], r_hip[1]))

        return overlay_transparent(frame, resized, cx, cy)

    # Tops / Shirts / Kurtas / Blouses / Polo
    if any(tag in cloth_type for tag in ["shirt", "polo", "blouse", "kurta"]):
        l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
        l_hip, r_hip = get_point("l_hip"), get_point("r_hip")

        shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
        torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))

        new_w = max(1, int(shoulder_w * 2.0))
        new_h = max(1, int(torso_h * 1.4))

        resized = cv2.resize(cloth_img, (new_w, new_h))
        cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)
        cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.15)

        return overlay_transparent(frame, resized, cx, cy)

    # Full-body dresses / gowns / suits
    if any(tag in cloth_type for tag in ["full_suit", "sundress", "gown"]):
        l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
        l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

        shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
        dress_h = np.linalg.norm(np.array(l_toe) - np.array(l_sh)) * 1.1
        dress_w = max(1, int(shoulder_w * 4.0))

        resized = cv2.resize(cloth_img, (int(dress_w), int(dress_h)))
        cx = int((l_sh[0] + r_sh[0]) / 2 - dress_w / 2)
        cy = int(min(l_sh[1], r_sh[1])) - int(dress_h * 0.14)

        return overlay_transparent(frame, resized, cx, cy)

    # default fallback: return frame unchanged
    return frame


# -------------------------------
# Overlay Pipeline
# -------------------------------
def cloth_overlay(frame):
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark

        def get_point(name):
            idx = landmark_names[name]
            return int(lm[idx].x * w), int(lm[idx].y * h)

        orig_frame = frame.copy()

        # ✅ Make bottom ALWAYS visible (if exists)
        if bottom_type != "none" and bottom_img is not None:
            frame = place_cloth(frame, bottom_img, bottom_type, get_point)

        # ✅ Make top ALWAYS visible (if exists)
        if top_type != "none" and top_img is not None:
            frame = place_cloth(frame, top_img, top_type, get_point)

        # ✅ If dress selected, overlay it ON TOP (does NOT remove top/bottom)
        if dress_type != "none" and dress_img is not None:
            frame = place_cloth(frame, dress_img, dress_type, get_point)

        # ✅ Restore neck
        try:
            l_sh = get_point("l_shoulder")
            r_sh = get_point("r_shoulder")
            neck_center = ((l_sh[0] + r_sh[0]) // 2, min(l_sh[1], r_sh[1]) - 55)

            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            neck_width = max(2, abs(r_sh[0] - l_sh[0]) // 5)
            cv2.ellipse(mask, neck_center, (neck_width, neck_width), 0, 0, 180, 255, -1)
            frame[mask == 255] = orig_frame[mask == 255]
        except:
            pass

    return frame


# -------------------------------
# Video Stream Generator
# -------------------------------
def gen_frames():
    cap = cv2.VideoCapture(0)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame = cloth_overlay(frame)
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
    finally:
        try:
            cap.release()
        except Exception:
            pass


# -------------------------------
# API Routes
# -------------------------------
@router.post("/update")
async def update_clothing(selection: ClothingSelection):
    global current_selection
    current_selection = selection
    load_clothing_images()
    # return selection directly (Pydantic dict)
    return {"status": "success", **selection.dict()}


@router.get("/health")
async def health_check():
    return {"status": "connected", "clothing": current_selection.dict()}


@router.get("/video")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
  