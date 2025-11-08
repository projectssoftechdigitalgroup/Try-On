import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow Lite logs

import cv2
import mediapipe as mp
import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow frontend (React) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for production set ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Clothing Selection Model
# -------------------------------
class ClothingSelection(BaseModel):
    gender: str = "male"
    top: str = "m_shirt1"
    bottom: str = "m_pant"
    dress: str = "none"


# Global clothing selection state
current_selection = ClothingSelection()

# -------------------------------
# Clothing Paths
# -------------------------------
clothing_paths = {
    # MALE
    "m_shirt1": "./database/male/shirt1.png",
    "m_shirt2": "./database/male/shirt2.png",
    "m_polo": "./database/male/polo.png",
    "m_kurta": "./database/male/kurta.png",
    "m_pant": "./database/male/pant.png",
    "m_pajama": "./database/male/pajama.png",
    "m_full_suit": "./database/male/full_suit.png",

    # FEMALE
    "f_blouse": "./database/female/blouse.png",
    "f_tunic": "./database/female/tunic.png",
    "f_skirt": "./database/female/skirt.png",
    "f_jeans": "./database/female/jeans.png",
    "f_sundress": "./database/female/sundress.png",
    "f_gown": "./database/female/gown.png",
}


def load_clothing_images():
    global top_img, bottom_img, dress_img, top_type, bottom_type, dress_type, gender_type
    gender_type = current_selection.gender
    top_type = current_selection.top
    bottom_type = current_selection.bottom
    dress_type = current_selection.dress

    top_path = clothing_paths.get(top_type)
    bottom_path = clothing_paths.get(bottom_type)
    dress_path = clothing_paths.get(dress_type, None)

    top_img = cv2.imread(top_path, cv2.IMREAD_UNCHANGED) if top_path else None
    bottom_img = cv2.imread(bottom_path, cv2.IMREAD_UNCHANGED) if bottom_path else None
    dress_img = cv2.imread(dress_path, cv2.IMREAD_UNCHANGED) if dress_path else None

    if top_img is None and top_type != "none":
        print(f"⚠️ Top cloth not found at {top_path}, using placeholder")
        top_img = np.zeros((200, 200, 4), dtype=np.uint8)
    if bottom_img is None and bottom_type != "none":
        print(f"⚠️ Bottom cloth not found at {bottom_path}, using placeholder")
        bottom_img = np.zeros((200, 200, 4), dtype=np.uint8)
    if dress_type != "none" and dress_img is None:
        print(f"⚠️ Dress not found at {dress_path}, using placeholder")
        dress_img = np.zeros((300, 300, 4), dtype=np.uint8)


# Initialize clothing images
load_clothing_images()

# -------------------------------
# Mediapipe Pose
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
def overlay_transparent(background, overlay, x, y, gender="male", cloth_type=None):
    h, w = overlay.shape[:2]

    # --- Female clothing adjustments ---
    if gender == "female":
        if cloth_type in ["jeans", "tunic"]:
            # Move jeans and tunic slightly higher
            y -= int(0.05 * background.shape[0])
        elif cloth_type == "blouse":
            # Slightly raise blouse for better alignment
            y -= int(0.02 * background.shape[0])

    # --- Boundary checks ---
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

    # --- Ensure valid alpha channel ---
    if overlay.shape[2] < 4:
        return background

    # --- Alpha blending ---
    overlay_img = overlay[:, :, :3]
    mask = overlay[:, :, 3:] / 255.0
    roi = background[y:y+h, x:x+w]
    if roi.shape[:2] != overlay_img.shape[:2]:
        return background

    blended = (1.0 - mask) * roi + mask * overlay_img
    background[y:y+h, x:x+w] = blended.astype(np.uint8)
    return background



# -------------------------------
# Cloth Placement
# -------------------------------
def place_cloth(frame, cloth_img, cloth_type, get_point):
    if cloth_img is None or cloth_type == "none":
        return frame

    # -------------------------
    # 👕 MALE CLOTHING LOGIC
    # -------------------------
    if gender_type == "male":
        # Bottoms (pant, pajama)
        if any(tag in cloth_type for tag in ["pant", "pajama"]):
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

            hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
            leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))

            new_w = int(hip_w * 2.2)
            new_h = int(leg_h * 1.1)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2)
            cy = int(min(l_hip[1], r_hip[1]))
            return overlay_transparent(frame, resized, cx, cy)

        # Tops (shirt, polo, kurta)
        elif any(tag in cloth_type for tag in ["shirt", "polo", "kurta"]):
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")

            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))

            new_w = int(shoulder_w * 2.0)
            new_h = int(torso_h * 1.4)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.15)
            return overlay_transparent(frame, resized, cx, cy)

        # Full suit
        elif "full_suit" in cloth_type:
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            suit_h = np.linalg.norm(np.array(l_toe) - np.array(l_sh)) * 1.1
            suit_w = shoulder_w * 4.0

            resized = cv2.resize(cloth_img, (int(suit_w), int(suit_h)))
            cx = int((l_sh[0] + r_sh[0]) / 2 - suit_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(suit_h * 0.14)
            return overlay_transparent(frame, resized, cx, cy)

    # -------------------------
    # 👚 FEMALE CLOTHING LOGIC
    # -------------------------
    elif gender_type == "female":
        # Bottoms (jeans, skirt, tunic)
        if any(tag in cloth_type for tag in ["jeans","tunic"]):
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

            hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
            leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))

            new_w = int(hip_w * 3.6)
            new_h = int(leg_h * 1.1)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2)

            # ✅ Slightly higher placement for tunic and jeans
            offset_y = int(new_h * 0.12) if any(tag in cloth_type for tag in ["jeans", "tunic"]) else 0
            cy = int(min(l_hip[1], r_hip[1])) - offset_y

            return overlay_transparent(frame, resized, cx, cy)

        # Tops (blouse)
        elif "blouse" in cloth_type:
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")

            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))

            new_w = int(shoulder_w * 2.3)
            new_h = int(torso_h * 2.3)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)

            # ✅ Lower the blouse slightly to overlap the jeans/tunic
            cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.25)
            return overlay_transparent(frame, resized, cx, cy)

        # Full dress (sundress, gown)
        elif any(tag in cloth_type for tag in ["sundress", "gown","skirt"]):
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")

            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            dress_h = np.linalg.norm(np.array(l_toe) - np.array(l_sh)) * 1.1
            dress_w = shoulder_w * 3.4

            resized = cv2.resize(cloth_img, (int(dress_w), int(dress_h)))
            cx = int((l_sh[0] + r_sh[0]) / 2 - dress_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(dress_h * 0.07)
            return overlay_transparent(frame, resized, cx, cy)

    return frame



# -------------------------------
# Cloth Overlay Pipeline
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

        if dress_type != "none":
            frame = place_cloth(frame, dress_img, dress_type, get_point)
        else:
            frame = place_cloth(frame, bottom_img, bottom_type, get_point)
            frame = place_cloth(frame, top_img, top_type, get_point)

        # Female blouse overlay fix
        if (
            gender_type == "female"
            and top_type == "f_blouse"
            and bottom_type in ["f_skirt", "f_jeans", "f_tunic"]
        ):
            frame = place_cloth(frame, top_img, top_type, get_point)

        # Neck restore
        l_sh = get_point("l_shoulder")
        r_sh = get_point("r_shoulder")
        neck_center = ((l_sh[0] + r_sh[0]) // 2, min(l_sh[1], r_sh[1]) - 55)

        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        neck_width = abs(r_sh[0] - l_sh[0]) // 5
        neck_height = neck_width

        cv2.ellipse(mask, neck_center, (neck_width, neck_height),
                    0, 0, 180, 255, -1)

        frame[mask == 255] = orig_frame[mask == 255]

    return frame


# -------------------------------
# Video Stream
# -------------------------------
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


@app.post("/update_clothing")
async def update_clothing(selection: ClothingSelection):
    global current_selection
    current_selection = selection
    load_clothing_images()
    return {
        "status": "success",
        "gender": selection.gender,
        "top": selection.top,
        "bottom": selection.bottom,
        "dress": selection.dress
    }


@app.get("/health")
async def health_check():
    return {
        "status": "connected",
        "clothing": {
            "gender": current_selection.gender,
            "top": current_selection.top,
            "bottom": current_selection.bottom,
            "dress": current_selection.dress
        }
    }


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/")
def root():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Virtual Try-On Backend...")
    print("📹 Camera feed available at: http://localhost:8000/video_feed")
    print("🔧 Health check at: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
