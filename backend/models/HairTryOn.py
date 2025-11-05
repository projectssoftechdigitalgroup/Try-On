# ============================================
# 💇 HairTryOn.py — AI Hair Stylist Module (Final Integrated)
# ============================================

from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import Response, JSONResponse
import cv2
import numpy as np
import os, math, traceback, logging, base64, uuid
from io import BytesIO
from PIL import Image
from typing import Optional
from dotenv import load_dotenv

# Gemini imports
from google import genai
from google.genai import types

# ======================================================
# ⚙️ Router Setup
# ======================================================
router = APIRouter(prefix="/tryon", tags=["Hair Try-On"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAIR_STYLE_PATH = os.path.join(BASE_DIR, "data", "hair_style")
STATIC_PATH = os.path.join(BASE_DIR, "static")

FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_eye.xml"
face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("hair_tryon_backend.log"), logging.StreamHandler()],
)

# ---------------------- Gemini Setup ---------------------- #
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in .env file")

client = genai.Client(api_key=GEMINI_API_KEY)

# ======================================================
# 🔧 Helper Functions
# ======================================================
def trim_transparent_borders(img: np.ndarray) -> np.ndarray:
    if img.shape[2] < 4:
        return img
    alpha = img[:, :, 3]
    coords = cv2.findNonZero(alpha)
    if coords is None:
        return img
    x, y, w, h = cv2.boundingRect(coords)
    return img[y:y+h, x:x+w]


def estimate_head_tilt(gray: np.ndarray, face_box: tuple) -> float:
    (x, y, w, h) = face_box
    roi_gray = gray[y:y+h, x:x+w]
    eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 4, minSize=(15, 15))
    if len(eyes) >= 2:
        eyes = sorted(eyes, key=lambda e: e[0])
        (ex1, ey1, ew1, eh1) = eyes[0]
        (ex2, ey2, ew2, eh2) = eyes[1]
        dy = (ey2 + eh2/2) - (ey1 + eh1/2)
        dx = (ex2 + ew2/2) - (ex1 + ew1/2)
        return float(np.clip(math.degrees(math.atan2(dy, dx)), -20, 20))
    return 0.0


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)


def smooth_alpha_blend(base: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
    try:
        y1, y2 = max(y, 0), min(y + overlay.shape[0], base.shape[0])
        x1, x2 = max(x, 0), min(x + overlay.shape[1], base.shape[1])
        overlay_cropped = overlay[0:(y2 - y1), 0:(x2 - x1)]
        alpha = overlay_cropped[:, :, 3].astype(np.float32) / 255.0
        alpha = cv2.GaussianBlur(alpha, (7, 7), 0)
        for c in range(3):
            base[y1:y2, x1:x2, c] = alpha * overlay_cropped[:, :, c] + (1 - alpha) * base[y1:y2, x1:x2, c]
        return base
    except Exception as e:
        raise RuntimeError("Overlay blending failed.") from e


def image_to_base64(img: Image.Image) -> str:
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def save_base64_to_file(base64_str: str, prefix: str = "output") -> str:
    """Save base64 image to static folder and return file path."""
    try:
        if not os.path.exists(STATIC_PATH):
            os.makedirs(STATIC_PATH)
        file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(STATIC_PATH, file_name)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_str))
        return file_name
    except Exception as e:
        raise RuntimeError("Failed to save base64 image to file.") from e


# ======================================================
# 🧠 Gemini Image Generation + Analysis
# ======================================================
def generate_hair_with_gemini(image_bytes: bytes, prompt: str):
    try:
        original_image = Image.open(BytesIO(image_bytes))
        transform_prompt = f"""
        Modify only the hair according to this request: "{prompt}".
        Keep the person's face, background, and skin unchanged.
        Maintain realistic texture, lighting, and natural color.
        """

        transform_response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[transform_prompt, original_image],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                temperature=0.1,
                top_p=0.4,
                top_k=5
            )
        )

        result_text = ""
        transformed_image = None
        for part in transform_response.candidates[0].content.parts:
            if getattr(part, "text", None):
                result_text += part.text
            elif getattr(part, "inline_data", None):
                transformed_image = Image.open(BytesIO(part.inline_data.data))

        if not transformed_image:
            raise Exception("No transformed image returned by Gemini.")

        analysis_prompt = f"""
        Compare these two images (original and modified):
        - Face Match (1–10)
        - Color Harmony (1–10)
        - Realism (1–10)
        """

        analysis_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[analysis_prompt, original_image, transformed_image],
            config=types.GenerateContentConfig(response_modalities=["TEXT"], temperature=0.4)
        )

        analysis_text = ""
        for part in analysis_response.candidates[0].content.parts:
            if getattr(part, "text", None):
                analysis_text += part.text

        base64_img = image_to_base64(transformed_image)
        return {"image_base64": base64_img, "gemini_feedback": f"{result_text.strip()}\n\n{analysis_text.strip()}"}

    except Exception as e:
        logging.error(f"❌ Gemini generation error: {e}")
        return {"error": str(e)}

# ======================================================
# 🎨 1. Local Haar-based Try-On
# ======================================================
@router.post("/hair")
async def tryon_hair(image: UploadFile, style_name: str = Form(...)):
    """Local PNG hairstyle overlay using Haar Cascade."""
    try:
        contents = await image.read()
        np_img = np.frombuffer(contents, np.uint8)
        user_img = cv2.imdecode(np_img, cv2.IMREAD_UNCHANGED)
        if user_img is None:
            return JSONResponse({"error": "Invalid image file."}, status_code=400)

        gray = cv2.cvtColor(user_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.05, 4, minSize=(60, 60))
        if not len(faces):
            (h, w) = user_img.shape[:2]
            x, y = int(w * 0.25), int(h * 0.15)
            w, h = int(w * 0.5), int(h * 0.5)
        else:
            (x, y, w, h) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]

        style_path = os.path.join(HAIR_STYLE_PATH, style_name)
        overlay = cv2.imread(style_path, cv2.IMREAD_UNCHANGED)
        overlay = trim_transparent_borders(overlay)
        overlay = rotate_image(overlay, estimate_head_tilt(gray, (x, y, w, h)))
        hair_width = int(w * 1.9)
        hair_height = int(hair_width * overlay.shape[0] / overlay.shape[1])
        overlay = cv2.resize(overlay, (hair_width, hair_height))
        y_offset = y - int(h * 1.35)
        x_offset = x - int((hair_width - w) / 2)-8
        blended_img = smooth_alpha_blend(user_img.copy(), overlay, max(x_offset, 0), max(y_offset, 0))
        _, img_encoded = cv2.imencode(".png", blended_img)
        return Response(content=img_encoded.tobytes(), media_type="image/png")
    except Exception:
        logging.error("❌ Haar Try-On Error:\n" + traceback.format_exc())
        return JSONResponse({"error": "Unexpected Haar try-on failure."}, status_code=500)

# ======================================================
# ✨ 2. Gemini-enhanced Try-On (Color Preserved)
# ======================================================
@router.post("/hair_gemini")
async def tryon_hair_gemini(image: UploadFile, style_name: str = Form(...)):
    """Enhanced hair overlay using Gemini AI for realism."""
    try:
        contents = await image.read()
        np_img = np.frombuffer(contents, np.uint8)
        user_img = cv2.imdecode(np_img, cv2.IMREAD_UNCHANGED)
        if user_img is None:
            return JSONResponse({"error": "Invalid image file."}, status_code=400)

        gray = cv2.cvtColor(user_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.05, 4, minSize=(60, 60))
        if not len(faces):
            (h, w) = user_img.shape[:2]
            x, y = int(w * 0.25), int(h * 0.15)
            w, h = int(w * 0.5), int(h * 0.5)
        else:
            (x, y, w, h) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]

        style_path = os.path.join(HAIR_STYLE_PATH, style_name)
        overlay = cv2.imread(style_path, cv2.IMREAD_UNCHANGED)
        overlay = trim_transparent_borders(overlay)
        overlay = rotate_image(overlay, estimate_head_tilt(gray, (x, y, w, h)))
        hair_width = int(w * 1.9)
        hair_height = int(hair_width * overlay.shape[0] / overlay.shape[1])
        overlay = cv2.resize(overlay, (hair_width, hair_height))
        y_offset = y - int(h * 1.35)
        x_offset = x - int((hair_width - w) / 2)
        blended_img = smooth_alpha_blend(user_img.copy(), overlay, max(x_offset, 0), max(y_offset, 0))
        _, img_encoded = cv2.imencode(".png", blended_img)
        img_bytes = img_encoded.tobytes()

        prompt = f"Enhance hairstyle '{style_name}' realistically. Preserve color, improve edges and lighting."
        gemini_output = generate_hair_with_gemini(img_bytes, prompt)

        if not gemini_output or "image_base64" not in gemini_output:
            return Response(content=img_bytes, media_type="image/png")

        file_path = save_base64_to_file(gemini_output["image_base64"], prefix="hairgemini")
        return JSONResponse({
            "image_url": f"/static/{file_path}",
            "image_base64": gemini_output["image_base64"],
            "feedback": gemini_output.get("gemini_feedback", "Enhanced with Gemini realism")
        })
    except Exception:
        logging.error("❌ Gemini Try-On Error:\n" + traceback.format_exc())
        return JSONResponse({"error": "Unexpected Gemini try-on failure."}, status_code=500)

# ======================================================
# 💬 3. Prompt-based Gemini Hair Try-On
# ======================================================
@router.post("/hair_gemini_prompt")
async def tryon_hair_gemini_prompt(image: UploadFile, prompt: str = Form(...)):
    """
    Fully prompt-based Gemini hair transformation + analysis.

    Parameters:
    - image: Uploaded user image
    - prompt: Text prompt describing desired hairstyle

    Returns:
    - JSON containing:
        - image_base64: transformed hair image in base64
        - gemini_feedback: analysis/feedback from Gemini
    """
    try:
        contents = await image.read()
        gemini_output = generate_hair_with_gemini(contents, prompt)

        # Ensure image is returned in Base64
        if "image_base64" not in gemini_output and "image_bytes" in gemini_output:
            import base64
            gemini_output["image_base64"] = base64.b64encode(
                gemini_output["image_bytes"]
            ).decode("utf-8")
            del gemini_output["image_bytes"]

        # Provide default feedback if missing
        if "gemini_feedback" not in gemini_output:
            gemini_output["gemini_feedback"] = "✅ Hair transformation completed."

        return JSONResponse(content=gemini_output)

    except Exception:
        import traceback, logging
        logging.error("❌ Prompt Try-On Error:\n" + traceback.format_exc())
        return JSONResponse(
            {"error": "Gemini prompt-based transformation failed."},
            status_code=500
        )
