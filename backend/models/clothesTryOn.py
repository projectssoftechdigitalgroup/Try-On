# models/clothesTryOn.py
import os
import cv2
import mediapipe as mp
import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/clothes", tags=["Clothes Try-On"])

# -------------------------------
# Clothing Model
# -------------------------------
class ClothingSelection(BaseModel):
    top: str = "shirt1"
    bottom: str = "pant"

# Global state
current_selection = ClothingSelection()

# -------------------------------
# Clothing Paths
# -------------------------------
clothing_paths = {
    "shirt1": "./database/shirt1.png",
    "shirt2": "./database/shirt2.png",
    "shirt3": "./database/shirt3.png",
    "polo":   "./database/polo.png",
    "pant":   "./database/pant.png"
}

def load_clothing_images():
    global top_img, bottom_img, top_type, bottom_type
    top_type = current_selection.top
    bottom_type = current_selection.bottom

    top_path = clothing_paths.get(current_selection.top, "./database/shirt1.png")
    bottom_path = clothing_paths.get(current_selection.bottom, "./database/pant.png")

    top_img = cv2.imread(top_path, cv2.IMREAD_UNCHANGED)
    bottom_img = cv2.imread(bottom_path, cv2.IMREAD_UNCHANGED)

    if top_img is None:
        print(f"⚠️ Top cloth not found at {top_path}, using placeholder")
        top_img = np.zeros((200, 200, 4), dtype=np.uint8)
    if bottom_img is None:
        print(f"⚠️ Bottom cloth not found at {bottom_path}, using placeholder")
        bottom_img = np.zeros((200, 200, 4), dtype=np.uint8)

# Initialize
load_clothing_images()

# -------------------------------
# Mediapipe Pose
# -------------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)

landmark_names = {
    "l_shoulder": 11, "r_shoulder": 12,
    "l_hip": 23, "r_hip": 24,
    "l_ankle": 27, "r_ankle": 28,
    "l_wrist": 15, "r_wrist": 16,
    "l_toe": 31, "r_toe": 32
}

# -------------------------------
# Helpers
# -------------------------------
def overlay_transparent(background, overlay, x, y):
    h, w = overlay.shape[:2]
    if x >= background.shape[1] or y >= background.shape[0]:
        return background
    if x < 0:
        overlay = overlay[:, -x:]; w = overlay.shape[1]; x = 0
    if y < 0:
        overlay = overlay[-y:, :]; h = overlay.shape[0]; y = 0
    if x + w > background.shape[1]:
        w = background.shape[1] - x; overlay = overlay[:, :w]
    if y + h > background.shape[0]:
        h = background.shape[0] - y; overlay = overlay[:h, :]

    if overlay.shape[2] < 4:
        return background

    overlay_img = overlay[:, :, :3]
    mask = overlay[:, :, 3:] / 255.0
    roi = background[y:y+h, x:x+w]
    if roi.shape[:2] != overlay_img.shape[:2]:
        return background
    blended = (1.0 - mask) * roi + mask * overlay_img
    background[y:y+h, x:x+w] = blended.astype(np.uint8)
    return background

def place_cloth(frame, cloth_img, cloth_type, get_point):
    if cloth_img is None:
        return frame

    if cloth_type == "pant":
        l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
        l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

        hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
        leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))

        new_w = int(hip_w * 3.2)
        new_h = int(leg_h * 1.05)

        resized = cv2.resize(cloth_img, (new_w, new_h))
        cx = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2)
        cy = int(min(l_hip[1], r_hip[1]))
        return overlay_transparent(frame, resized, cx, cy)

    elif cloth_type in ["shirt1", "shirt2", "shirt3", "polo"]:
        l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
        l_hip, r_hip = get_point("l_hip"), get_point("r_hip")

        shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
        torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))

        new_w = int(shoulder_w * 1.89)
        new_h = int(torso_h * 1.38)

        resized = cv2.resize(cloth_img, (new_w, new_h))
        cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)
        cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.15)
        return overlay_transparent(frame, resized, cx, cy)

    return frame

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

        # Bottom
        frame = place_cloth(frame, bottom_img, bottom_type, get_point)
        # Top
        frame = place_cloth(frame, top_img, top_type, get_point)

        # Neck restore
        l_sh = get_point("l_shoulder")
        r_sh = get_point("r_shoulder")
        neck_center = ((l_sh[0] + r_sh[0]) // 2, min(l_sh[1], r_sh[1]) - 55)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        neck_width = abs(r_sh[0] - l_sh[0]) // 5
        neck_height = neck_width
        cv2.ellipse(mask, neck_center, (neck_width, neck_height), 0, 0, 180, 255, -1)
        frame[mask == 255] = orig_frame[mask == 255]

    return frame

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        frame = cloth_overlay(frame)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# -------------------------------
# Routes
# -------------------------------
@router.post("/update")
async def update_clothing(selection: ClothingSelection):
    global current_selection
    current_selection = selection
    load_clothing_images()
    return {"status": "success", "top": selection.top, "bottom": selection.bottom}

@router.get("/health")
async def health_check():
    return {"status": "connected", "clothing": {"top": current_selection.top, "bottom": current_selection.bottom}}

@router.get("/video")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
