import os, uuid, traceback, cv2, numpy as np, mediapipe as mp
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# ----------------- Configuration -----------------
OUTPUT_DIR = "data/output"
CAPS_DIR = "data/caps_hats/caps"
GLASSES_DIR = "data/caps_hats/glasses"
HATS_DIR = "data/caps_hats/hats"   # ✅ new hats directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------- Utilities -----------------
def _read_bytes(input_obj):
    if isinstance(input_obj, (bytes, bytearray)):
        return bytes(input_obj)
    if hasattr(input_obj, "read"):
        try:
            input_obj.seek(0)
        except:
            pass
        return input_obj.read()
    raise ValueError("Unsupported input type")

def _save_image_bgr(img_bgr, prefix="capglasses"):
    fname = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    out_path = os.path.join(OUTPUT_DIR, fname)
    cv2.imwrite(out_path, img_bgr)
    return f"output/{fname}"

def overlay_image(bg, ov, x, y, scale=1.0):
    if ov is None:
        return bg
    if scale != 1.0:
        h, w = ov.shape[:2]
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        ov = cv2.resize(ov, (new_w, new_h), interpolation=cv2.INTER_AREA)

    ov_h, ov_w = ov.shape[:2]
    bg_h, bg_w = bg.shape[:2]

    x1, y1 = max(x, 0), max(y, 0)
    x2, y2 = min(x + ov_w, bg_w), min(y + ov_h, bg_h)
    if x1 >= x2 or y1 >= y2:
        return bg

    ov_x1, ov_y1 = max(0, -x), max(0, -y)
    ov_x2, ov_y2 = ov_x1 + (x2 - x1), ov_y1 + (y2 - y1)
    ov_crop = ov[ov_y1:ov_y2, ov_x1:ov_x2]

    if ov_crop.shape[2] == 4:
        b, g, r, a = cv2.split(ov_crop)
        alpha = a.astype(np.float32) / 255.0
        rgb = cv2.merge((b, g, r)).astype(np.float32)
    else:
        rgb = ov_crop.astype(np.float32)
        alpha = np.ones((ov_crop.shape[0], ov_crop.shape[1]), dtype=np.float32)

    roi = bg[y1:y2, x1:x2].astype(np.float32)
    alpha_3 = np.expand_dims(alpha, axis=2)
    blended = (alpha_3 * rgb + (1.0 - alpha_3) * roi)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    bg[y1:y2, x1:x2] = blended
    return bg

# ----------------- Face Shape Detection -----------------
def detect_face_shape(img_bgr):
    mpf = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.5
    )
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    res = mpf.process(rgb)
    if not res.multi_face_landmarks:
        return "Unknown", {"face_detected": False}
    lm = res.multi_face_landmarks[0].landmark
    h, w = img_bgr.shape[:2]

    def pt(i): return (lm[i].x * w, lm[i].y * h)
    jaw_left, jaw_right = pt(234), pt(454)
    cheek_left, cheek_right = pt(50), pt(280)
    forehead, chin = pt(10), pt(152)

    jaw_w = abs(jaw_right[0] - jaw_left[0])
    cheek_w = abs(cheek_right[0] - cheek_left[0])
    face_len = abs(forehead[1] - chin[1])

    jaw_to_cheek = jaw_w / cheek_w if cheek_w else 1
    len_to_cheek = face_len / cheek_w if cheek_w else 1

    if len_to_cheek < 1.3 and jaw_to_cheek < 0.9:
        shape = "Round"
    elif 1.3 <= len_to_cheek < 1.5 and 0.9 <= jaw_to_cheek <= 1.05:
        shape = "Square"
    elif len_to_cheek >= 1.7 and jaw_to_cheek >= 0.95:
        shape = "Long"
    elif 1.45 <= len_to_cheek < 1.7 and jaw_to_cheek < 0.95:
        shape = "Heart"
    else:
        shape = "Oval"
    return shape, {"face_detected": True, "jaw_to_cheek": round(jaw_to_cheek, 2), "length_to_cheek": round(len_to_cheek, 2)}

# ----------------- Main Try-On -----------------
def tryon_and_recommend(input_file, accessory=None, filename=None):
    try:
        img = cv2.imdecode(np.frombuffer(_read_bytes(input_file), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return {"face_shape": "Unknown", "recommendations": ["Invalid image"], "outputs": {}, "debug": {"face_detected": False}}

        face_shape, dbg = detect_face_shape(img)
        out_path = None
        acc = (accessory or "").lower()
        overlay_path = None

        mp_face = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = mp_face.process(rgb)

        if acc == "glasses" and res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            h, w = img.shape[:2]
            left_eye = (int(lm[33].x * w), int(lm[33].y * h))
            right_eye = (int(lm[263].x * w), int(lm[263].y * h))
            mid_y = (left_eye[1] + right_eye[1]) // 2
            eye_width = abs(right_eye[0] - left_eye[0])
            x_center = (left_eye[0] + right_eye[0]) // 2
            overlay_path = os.path.join(GLASSES_DIR, filename or "glasses_1.png")
            if os.path.exists(overlay_path):
                ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
                scale_factor = 1.4
                new_w = int(eye_width * scale_factor)
                x = x_center - new_w // 2
                y_off = mid_y - int(eye_width * 0.26)
                scale = new_w / (ov.shape[1] if ov.shape[1] else 1)
                img = overlay_image(img, ov, x, y_off, scale=scale)
                out_path = _save_image_bgr(img)

        elif acc == "cap" and res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            h, w = img.shape[:2]
            forehead_y = int(lm[10].y * h)
            face_left = int(lm[234].x * w)
            face_right = int(lm[454].x * w)
            face_width = max(10, face_right - face_left)

            overlay_path = os.path.join(CAPS_DIR, filename or "cap_1.png")
            if os.path.exists(overlay_path):
                ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
                desired_w = int(face_width * 1.3)
                scale = desired_w / ov.shape[1] if ov.shape[1] else 1.0
                new_h = int(ov.shape[0] * scale)
                ov_resized = cv2.resize(ov, (desired_w, new_h), interpolation=cv2.INTER_AREA)

                face_center_x = (face_left + face_right) // 2
                x = face_center_x - desired_w // 2
                y = forehead_y - int(new_h * 0.60)
                img = overlay_image(img, ov_resized, x, y, scale=1.0)
                out_path = _save_image_bgr(img)

        elif acc == "hat" and res.multi_face_landmarks:   # ✅ new hats support
            lm = res.multi_face_landmarks[0].landmark
            h, w = img.shape[:2]
            forehead_y = int(lm[10].y * h)
            face_left = int(lm[234].x * w)
            face_right = int(lm[454].x * w)
            face_width = max(10, face_right - face_left)

            overlay_path = os.path.join(HATS_DIR, filename or "hat_2.png")
            if os.path.exists(overlay_path):
                ov = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
                desired_w = int(face_width * 2.3)   # hats usually wider
                scale = desired_w / ov.shape[1] if ov.shape[1] else 1.0
                new_h = int(ov.shape[0] * scale)
                ov_resized = cv2.resize(ov, (desired_w, new_h), interpolation=cv2.INTER_AREA)

                face_center_x = (face_left + face_right) // 2
                x = face_center_x - desired_w // 2
                y = forehead_y - int(new_h * 0.75)   # hats sit higher
                img = overlay_image(img, ov_resized, x, y, scale=1.0)
                out_path = _save_image_bgr(img)

        rec_map = {
            "Round": {"Cap": "Baseball caps", "Hat": "Wide-brim hats", "Sun Glasses": "Rectangular"},
            "Square": {"Cap": "Curved-brim", "Hat": "Fedora", "Sun Glasses": "Aviator"},
            "Oval": {"Cap": "Bucket hats", "Hat": "All hats", "Sun Glasses": "All styles"},
            "Heart": {"Cap": "Soft-brim", "Hat": "Floppy hats", "Sun Glasses": "Medium aviators"},
            "Long": {"Cap": "Flat-brim", "Hat": "Tall crowns", "Sun Glasses": "Oversized"},
            "Unknown": {"Cap": "Neutral", "Hat": "Simple hats", "Sun Glasses": "Wayfarers"},
        }

        return {
            "face_shape": face_shape,
            "recommendations": rec_map.get(face_shape, []),
            "outputs": {"tryon": out_path} if out_path else {},
            "debug": {**dbg, "overlay_used": overlay_path, "detections": bool(res.multi_face_landmarks)}
        }

    except Exception as e:
        return {
            "face_shape": "Unknown",
            "recommendations": [f"Error: {e}"],
            "outputs": {},
            "debug": {"error": str(e), "traceback": traceback.format_exc()},
        }

# ----------------- FastAPI -----------------
app = FastAPI()
app.mount("/output", StaticFiles(directory="data/output"), name="output")

@app.post("/capglasses-tryon/")
async def capglasses_tryon(file: UploadFile, accessory: str = Form(None), filename: str = Form(None)):
    try:
        result = tryon_and_recommend(await file.read(), accessory, filename)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "traceback": traceback.format_exc()}, status_code=500
        )
  