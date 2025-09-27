# realtime_cap_glasses.py
import os, cv2, numpy as np, random, traceback, base64
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import mediapipe as mp

# ---------------- Paths ----------------
CAPS_DIR = "data/caps_hats"
OUTPUT_DIR = "data/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- Mediapipe Init ----------------
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# ---------------- Router ----------------
router = APIRouter()

# ---------------- Utils ----------------
def overlay_image(bg, fg, x, y, scale=1.0):
    """Overlay fg image with alpha channel onto bg image."""
    if fg is None:
        return bg

    fg = cv2.resize(fg, (0, 0), fx=scale, fy=scale)
    h, w = fg.shape[:2]

    # Clamp coordinates to prevent overflow
    x1, y1 = max(x,0), max(y,0)
    x2, y2 = min(x+w, bg.shape[1]), min(y+h, bg.shape[0])
    fg_crop = fg[y1-y:y2-y, x1-x:x2-x]

    if fg.shape[2] == 4:  # RGBA
        alpha = fg_crop[:, :, 3] / 255.0
        for c in range(3):
            bg[y1:y2, x1:x2, c] = (alpha * fg_crop[:, :, c] +
                                   (1 - alpha) * bg[y1:y2, x1:x2, c])
    else:
        bg[y1:y2, x1:x2] = fg_crop

    return bg

def detect_face_shape(image):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = mp_face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return "unknown"

    h, w = image.shape[:2]
    landmarks = results.multi_face_landmarks[0].landmark

    jaw = int(abs(landmarks[234].x * w - landmarks[454].x * w))
    cheekbones = int(abs(landmarks[50].x * w - landmarks[280].x * w))
    face_length = int(abs(landmarks[10].y * h - landmarks[152].y * h))

    if jaw < cheekbones and face_length > cheekbones:
        return "oval"
    elif jaw == cheekbones:
        return "round"
    else:
        return "square"

# ---------------- Core Processing ----------------
def process_frame(image_bytes, accessory="cap", filename=None):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode uploaded image.")

        h, w = img.shape[:2]

        # Run Mediapipe
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            raise ValueError("No face detected.")

        landmarks = results.multi_face_landmarks[0].landmark
        face_shape = detect_face_shape(img)

        # Pick overlay file
        if not filename:
            available = [f for f in os.listdir(CAPS_DIR) if f.lower().endswith((".png", ".jpg"))]
            if not available:
                raise FileNotFoundError("No accessory files found in caps_hats directory.")
            filename = random.choice(available)

        overlay_path = os.path.join(CAPS_DIR, filename)
        overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
        if overlay is None:
            raise ValueError("Failed to load overlay image.")

        # Position Accessory
        if accessory == "glasses":
            left_eye = (int(landmarks[33].x * w), int(landmarks[33].y * h))
            right_eye = (int(landmarks[263].x * w), int(landmarks[263].y * h))
            eye_width = abs(right_eye[0] - left_eye[0])

            scale = eye_width / overlay.shape[1] * 1.2
            x = left_eye[0] - int(0.1 * overlay.shape[1]*scale)
            y = left_eye[1] - int(overlay.shape[0]*scale/2)

        else:  # cap/hat
            forehead = (int(landmarks[10].x * w), int(landmarks[10].y * h))
            chin = (int(landmarks[152].x * w), int(landmarks[152].y * h))
            face_height = abs(chin[1] - forehead[1])

            scale = face_height / overlay.shape[0] * 1.5
            x = forehead[0] - int(overlay.shape[1]*scale/2)
            y = forehead[1] - int(overlay.shape[0]*scale*0.8)

        # Apply overlay
        result_img = overlay_image(img.copy(), overlay, x, y, scale=scale)

        # Encode base64
        _, buffer = cv2.imencode(".jpg", result_img)
        frame_b64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "frame": "data:image/jpeg;base64," + frame_b64,
            "face_shape": face_shape,
            "overlay_used": filename
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "trace": tb}

# ---------------- REST API Route ----------------
@router.post("/realtime-capglasses/")
async def realtime_capglasses_api(
    file: UploadFile = File(...),
    accessory: str = Form("cap"),
    filename: str = Form(None)
):
    try:
        contents = await file.read()
        result = process_frame(contents, accessory, filename)
        return JSONResponse(content=result)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})
