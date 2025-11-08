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
import os

# Define base database directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database")

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


    # === KIDS - BOY TRADITIONAL WEAR ===


    # === KIDS - GIRL EASTERN WEAR ===
    "kg_tshirt": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "shirt.png"),
    "kg_tshirt2": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "shirt2.png"),
    "kg_skirt": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "skirt.png"),
    "kg_skirt2": os.path.join(DATABASE_PATH, "kids", "girl", "Eastern-Wear", "skirt2.png"),

    # === KIDS - GIRL TRADITIONAL WEAR ===

}


def load_clothing_images():
    global top_img, bottom_img, dress_img, top_type, bottom_type, dress_type, gender_type
    gender_type = current_selection.gender
    top_type = current_selection.top
    bottom_type = current_selection.bottom
    dress_type = current_selection.dress

    def get_image(path_entry):
        if isinstance(path_entry, list):
            path_entry = random.choice(path_entry)
        return cv2.imread(path_entry, cv2.IMREAD_UNCHANGED) if path_entry else None

    top_path = CLOTHING_DATA.get(top_type)
    bottom_path = CLOTHING_DATA.get(bottom_type)
    dress_path = CLOTHING_DATA.get(dress_type, None)

    top_img = get_image(top_path)
    bottom_img = get_image(bottom_path)
    dress_img = get_image(dress_path)

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
        if cloth_type in ["jeans", "tunic", "skirt", "lehenga", "saree"]:
            y -= int(0.05 * background.shape[0])
        elif cloth_type in ["blouse", "sundress", "gown"]:
            y -= int(0.02 * background.shape[0])

    # --- Kids scaling adjustments ---
    if gender == "kid":
        overlay = cv2.resize(overlay, (int(w * 0.85), int(h * 0.85)))
        y -= int(0.03 * background.shape[0])

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


# -------------------------------
# Cloth Placement (Enhanced)
# -------------------------------
def place_cloth(frame, cloth_img, cloth_type, get_point):
    if cloth_img is None or cloth_type == "none":
        return frame

    # -------------------------
    # 👕 MALE LOGIC
    # -------------------------
    if gender_type == "male":
        # Bottoms (pant, pajama)
        if any(tag in cloth_type for tag in ["pant", "pajama"]):
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")
            hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
            leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))
            new_w, new_h = int(hip_w * 2.2), int(leg_h * 1.1)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx, cy = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2), int(min(l_hip[1], r_hip[1]))
            return overlay_transparent(frame, resized, cx, cy)

        # Tops (shirt, polo, kurta)
        elif any(tag in cloth_type for tag in ["shirt", "polo", "kurta"]):
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))
            new_w, new_h = int(shoulder_w * 2.0), int(torso_h * 1.4)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.15)
            return overlay_transparent(frame, resized, cx, cy)

        # Full suit (Eastern/Traditional)
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
    # 👚 FEMALE LOGIC
    # -------------------------
    elif gender_type == "female":
        # Bottoms (jeans, tunic)
        if any(tag in cloth_type for tag in ["jeans", "tunic"]):
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")
            hip_w = np.linalg.norm(np.array(r_hip) - np.array(l_hip))
            leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))
            new_w, new_h = int(hip_w * 3.6), int(leg_h * 1.1)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_hip[0] + r_hip[0]) / 2 - new_w / 2)
            cy = int(min(l_hip[1], r_hip[1])) - int(new_h * 0.12)
            return overlay_transparent(frame, resized, cx, cy)

        # Tops (blouse)
        elif "blouse" in cloth_type:
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))
            new_w, new_h = int(shoulder_w * 2.3), int(torso_h * 2.3)
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(new_h * 0.25)
            return overlay_transparent(frame, resized, cx, cy)

        # Full dresses (sundress, gown, saree, lehenga, skirt)
        elif any(tag in cloth_type for tag in ["sundress", "gown", "skirt", "saree", "lehenga", "traditional", "eastern"]):
            l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
            l_toe, r_toe = get_point("l_toe"), get_point("r_toe")
            shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
            dress_h = np.linalg.norm(np.array(l_toe) - np.array(l_sh)) * 1.1
            dress_w = shoulder_w * 3.4
            resized = cv2.resize(cloth_img, (int(dress_w), int(dress_h)))
            cx = int((l_sh[0] + r_sh[0]) / 2 - dress_w / 2)
            cy = int(min(l_sh[1], r_sh[1])) - int(dress_h * 0.07)
            return overlay_transparent(frame, resized, cx, cy)

    # -------------------------
    # 🧒 KIDS LOGIC
    # -------------------------
    elif gender_type == "kid":
        l_sh, r_sh = get_point("l_shoulder"), get_point("r_shoulder")
        l_hip, r_hip = get_point("l_hip"), get_point("r_hip")
        l_toe, r_toe = get_point("l_toe"), get_point("r_toe")
        shoulder_w = np.linalg.norm(np.array(r_sh) - np.array(l_sh))
        torso_h = np.linalg.norm(np.array(l_hip) - np.array(l_sh))
        leg_h = np.linalg.norm(np.array(l_toe) - np.array(l_hip))

        # --- Kid Girl Logic ---
        if cloth_type.startswith("kg_"):
            if any(tag in cloth_type for tag in ["shirt", "shirt2"]):
                new_w, new_h = int(shoulder_w * 2.4), int(torso_h * 2.0)
            elif any(tag in cloth_type for tag in ["skirt", "skirt2"]):
                new_w, new_h = int(shoulder_w * 2.5), int(leg_h * 1.1)
            elif any(tag in cloth_type for tag in ["suit"]):
                new_w, new_h = int(shoulder_w * 3.0), int(torso_h * 3.3)
            else:
                return frame
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx, cy = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2), int(min(l_sh[1], r_sh[1])) - int(new_h * 0.1)
            return overlay_transparent(frame, resized, cx, cy, gender="kid_girl", cloth_type=cloth_type)

        # --- Kid Boy Logic ---
        elif cloth_type.startswith("kb_"):
            if any(tag in cloth_type for tag in ["shirt"]):
                new_w, new_h = int(shoulder_w * 2.2), int(torso_h * 1.7)
            elif any(tag in cloth_type for tag in ["shorts", "pant", "pajama"]):
                new_w, new_h = int(shoulder_w * 2.0), int(leg_h * 1.0)
            elif any(tag in cloth_type for tag in ["suit"]):
                new_w, new_h = int(shoulder_w * 2.8), int(torso_h * 3.0)
            else:
                return frame
            resized = cv2.resize(cloth_img, (new_w, new_h))
            cx, cy = int((l_sh[0] + r_sh[0]) / 2 - new_w / 2), int(min(l_sh[1], r_sh[1])) - int(new_h * 0.1)
            return overlay_transparent(frame, resized, cx, cy, gender="kid_boy", cloth_type=cloth_type)

    return frame


# -------------------------------
# Cloth Overlay Pipeline
# -------------------------------
def cloth_overlay(frame):
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if not results.pose_landmarks:
        return frame

    lm = results.pose_landmarks.landmark

    def get_point(name):
        idx = landmark_names[name]
        return int(lm[idx].x * w), int(lm[idx].y * h)

    orig_frame = frame.copy()

    # === 1️⃣ DRESS CASE (single-piece) ===
    if dress_type != "none":
        frame = place_cloth(frame, dress_img, dress_type, get_point)

    # === 2️⃣ TWO-PIECE CASE ===
    else:
        # Always draw bottom first (pants/skirts)
        if bottom_type and bottom_type != "none" and bottom_img is not None:
            frame = place_cloth(frame, bottom_img, bottom_type, get_point)

        # Then draw top (shirt/blouse)
        if top_type and top_type != "none" and top_img is not None:
            frame = place_cloth(frame, top_img, top_type, get_point)

    # === 3️⃣ GENDER-SPECIFIC FIXES ===
    if gender_type == "female":
        # Reapply saree/lehenga if present
        if dress_type in ["f_saree", "f_lehenga"]:
            frame = place_cloth(frame, dress_img, dress_type, get_point)
        # Ensure blouses always above skirts/jeans
        elif top_type in ["f_blouse", "f_tunic"] and bottom_type in ["f_skirt", "f_jeans"]:
            frame = place_cloth(frame, top_img, top_type, get_point)

    elif gender_type == "male":
        # Ensure kurta overlays above pants
        if "kurta" in (top_type or "") and bottom_type in ["m_pajama", "m_pant"]:
            frame = place_cloth(frame, top_img, top_type, get_point)

    elif gender_type == "kid":
        # Kids: always layer bottom first, then top/dress
        if bottom_type and bottom_type != "none":
            frame = place_cloth(frame, bottom_img, bottom_type, get_point)
        if top_type and top_type != "none":
            frame = place_cloth(frame, top_img, top_type, get_point)
        if dress_type and dress_type != "none":
            frame = place_cloth(frame, dress_img, dress_type, get_point)

    # === 4️⃣ RESTORE NECK ===
    l_sh = get_point("l_shoulder")
    r_sh = get_point("r_shoulder")
    neck_center = ((l_sh[0] + r_sh[0]) // 2, min(l_sh[1], r_sh[1]) - 55)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    neck_width = abs(r_sh[0] - l_sh[0]) // 5
    neck_height = neck_width
    cv2.ellipse(mask, neck_center, (neck_width, neck_height), 0, 0, 180, 255, -1)
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
