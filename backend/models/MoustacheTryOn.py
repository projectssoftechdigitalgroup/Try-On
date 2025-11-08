# ---------------------------------------------------
# 🧔 Moustache & Beard Try-On API (FastAPI + OpenCV)
# ---------------------------------------------------

from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import numpy as np
import io
import os

router = APIRouter()

# ✅ Correct path for moustache overlays
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up from /models
MOUSTACHE_DIR = os.path.join(BASE_DIR, "data", "moustache")

os.makedirs(MOUSTACHE_DIR, exist_ok=True)

# ✅ Available moustache style mappings
STYLE_MAP = {
    "Classic Walrus Moustache": "moustache1.png",
    "Imperial Handlebar": "moustache2.png",
    "Chevron Moustache": "moustache3.png",
    "English Mustache": "moustache4.png",
    "Door Knocker": "moustache5.png",
    "Van Dyke": "moustache6.png",
}


@router.post("/tryon/moustache")
async def try_on_moustache(image: UploadFile, style_name: str = Form(...)):
    """
    Apply the selected moustache or beard style to the user's uploaded face image.
    """
    try:
        # ✅ Read uploaded image into OpenCV
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        base_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if base_img is None:
            raise ValueError("Invalid input image format or unreadable file.")

        # ✅ Select overlay
        overlay_filename = STYLE_MAP.get(style_name, "moustache1.png")
        overlay_path = os.path.join(MOUSTACHE_DIR, overlay_filename)

        if not os.path.exists(overlay_path):
            raise FileNotFoundError(f"Overlay not found at: {overlay_path}")

        # ✅ Load overlay with alpha channel
        overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
        if overlay is None:
            raise ValueError(f"Failed to load overlay image: {overlay_path}")

        # ✅ Detect face
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            raise ValueError("No face detected. Please upload a clear frontal face image.")

        for (x, y, w, h) in faces:
            # Adjust moustache/beard width & height
            moustache_width = int(w * 0.65)
            moustache_height = int(moustache_width * overlay.shape[0] / overlay.shape[1])

            # ✅ Base position (under nose)
            x1 = x + int(w * 0.15)     # moved a bit more left
            y1 = y + int(h * 0.62)     # moved slightly upward
            x2 = x1 + moustache_width
            y2 = y1 + moustache_height

            # ✅ For beard styles → lower placement
            if "beard" in overlay_filename.lower():
                y1 = y + int(h * 0.70)   # lower under chin
                y2 = y1 + moustache_height + int(h * 0.10)

            if x1 < 0 or y1 < 0 or x2 > base_img.shape[1] or y2 > base_img.shape[0]:
                continue

            # ✅ Resize overlay
            resized_overlay = cv2.resize(overlay, (moustache_width, moustache_height), interpolation=cv2.INTER_AREA)

            # ✅ Separate channels
            if resized_overlay.shape[2] == 4:
                overlay_rgb = resized_overlay[:, :, :3]
                overlay_alpha = resized_overlay[:, :, 3] / 255.0
            else:
                overlay_rgb = resized_overlay
                overlay_alpha = np.ones((resized_overlay.shape[0], resized_overlay.shape[1]))

            # ✅ Blend overlay
            for c in range(3):
                base_img[y1:y2, x1:x2, c] = (
                    overlay_alpha * overlay_rgb[:, :, c]
                    + (1 - overlay_alpha) * base_img[y1:y2, x1:x2, c]
                )

        # ✅ Return processed image
        _, img_encoded = cv2.imencode(".jpg", base_img)
        return StreamingResponse(io.BytesIO(img_encoded.tobytes()), media_type="image/jpeg")

    except Exception as e:
        print("❌ Error in Moustache Try-On:", str(e))
        return JSONResponse({"error": str(e)}, status_code=400)
