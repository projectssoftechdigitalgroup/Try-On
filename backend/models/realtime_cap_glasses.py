# realtime_cap_glasses.py
import os, cv2, numpy as np, traceback, base64
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import mediapipe as mp
from collections import deque
import threading

# ---------------- Paths ----------------
CAPS_DIR = "data/caps_hats/caps"
GLASSES_DIR = "data/caps_hats/glasses"
HATS_DIR = "data/caps_hats/hats"
os.makedirs("data/output", exist_ok=True)

# ---------------- Mediapipe Init ----------------
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

router = APIRouter()

# ---------------- Frame Buffer ----------------
frame_buffer = deque(maxlen=5)   # keep last 5 processed frames
buffer_lock = threading.Lock()

def add_to_buffer(frame_b64):
    with buffer_lock:
        frame_buffer.append(frame_b64)

def get_latest_from_buffer():
    with buffer_lock:
        if frame_buffer:
            return frame_buffer[-1]
        return None

# ---------------- Utils ----------------
def overlay_image(bg, ov, x, y, scale=1.0):
    if ov is None:
        return bg
    if scale != 1.0:
        h, w = ov.shape[:2]
        ov = cv2.resize(ov, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    ov_h, ov_w = ov.shape[:2]
    bg_h, bg_w = bg.shape[:2]

    x1, y1 = max(x, 0), max(y, 0)
    x2, y2 = min(x + ov_w, bg_w), min(y + ov_h, bg_h)
    if x1 >= x2 or y1 >= y2:
        return bg

    ov_crop = ov[max(0, -y):ov_h - max(0, y + ov_h - bg_h),
                 max(0, -x):ov_w - max(0, x + ov_w - bg_w)]
    if ov_crop.size == 0:
        return bg

    if ov_crop.shape[2] == 4:  # RGBA
        b, g, r, a = cv2.split(ov_crop)
        alpha = a.astype(np.float32) / 255.0
        rgb = cv2.merge((b, g, r)).astype(np.float32)
    else:
        rgb = ov_crop.astype(np.float32)
        alpha = np.ones((ov_crop.shape[0], ov_crop.shape[1]), dtype=np.float32)

    roi = bg[y1:y1 + ov_crop.shape[0], x1:x1 + ov_crop.shape[1]].astype(np.float32)
    blended = (np.expand_dims(alpha, axis=2) * rgb + (1 - np.expand_dims(alpha, axis=2)) * roi)
    bg[y1:y1 + ov_crop.shape[0], x1:x1 + ov_crop.shape[1]] = blended.astype(np.uint8)
    return bg

# ---------------- Core Processing ----------------
def process_frame(image_bytes, accessory="cap", filename=None):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode uploaded image.")

        h, w = img.shape[:2]
        results = mp_face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return {"error": "No face detected."}

        lm = results.multi_face_landmarks[0].landmark
        acc = (accessory or "").lower()
        overlay_path = None

        if acc == "glasses":
            left_eye = (int(lm[33].x * w), int(lm[33].y * h))
            right_eye = (int(lm[263].x * w), int(lm[263].y * h))
            eye_width = abs(right_eye[0] - left_eye[0])
            mid_y = (left_eye[1] + right_eye[1]) // 2
            x_center = (left_eye[0] + right_eye[0]) // 2

            overlay_path = os.path.join(GLASSES_DIR, filename or "glasses_1.png")
            ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
            if ov is not None:
                scale = (eye_width * 1.4) / ov.shape[1]
                x = x_center - int(ov.shape[1] * scale) // 2
                y = mid_y - int(ov.shape[0] * scale * 0.5)
                img = overlay_image(img, ov, x, y, scale=scale)

        elif acc == "cap":
            forehead_y = int(lm[10].y * h)
            face_left = int(lm[234].x * w)
            face_right = int(lm[454].x * w)
            face_width = max(10, face_right - face_left)

            overlay_path = os.path.join(CAPS_DIR, filename or "cap_1.png")
            ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
            if ov is not None:
                desired_w = int(face_width * 1.3)
                scale = desired_w / ov.shape[1]
                new_h = int(ov.shape[0] * scale)
                face_center_x = (face_left + face_right) // 2
                x = face_center_x - desired_w // 2
                y = forehead_y - int(new_h * 0.6)
                img = overlay_image(img, ov, x, y, scale=scale)

        elif acc == "hat":
            forehead_y = int(lm[10].y * h)
            face_left = int(lm[234].x * w)
            face_right = int(lm[454].x * w)
            face_width = max(10, face_right - face_left)

            overlay_path = os.path.join(HATS_DIR, filename or "hat_2.png")
            ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
            if ov is not None:
                desired_w = int(face_width * 2.0)
                scale = desired_w / ov.shape[1]
                new_h = int(ov.shape[0] * scale)
                face_center_x = (face_left + face_right) // 2
                x = face_center_x - desired_w // 2
                y = forehead_y - int(new_h * 0.75)
                img = overlay_image(img, ov, x, y, scale=scale)

        # ✅ resize + compress to smooth like webcam
        img = cv2.resize(img, (640, 480))  # force consistent size
        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_b64 = base64.b64encode(buffer).decode("utf-8")
        frame_uri = "data:image/jpeg;base64," + frame_b64

        add_to_buffer(frame_uri)  # push into buffer

        return {"frame": frame_uri, "overlay_used": overlay_path}

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------------- REST API Route ----------------
@router.post("/process-capglasses/")
async def realtime_capglasses_api(
    file: UploadFile = File(...),
    accessory: str = Form("cap"),
    filename: str = Form(None)
):
    contents = await file.read()
    result = process_frame(contents, accessory, filename)

    # ✅ return latest available (smoothed) frame
    latest = get_latest_from_buffer()
    if latest:
        result["frame"] = latest

    return JSONResponse(content=result)
