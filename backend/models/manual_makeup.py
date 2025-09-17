# app/main.py (excerpt)
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, cv2, numpy as np, traceback

from models import skin_tone_analysis, makeup_models, template_makeup
from models.chat_stylist import router as chat_router
# NEW ↓
from models.mediapipe_makeup import apply_makeup_bgr

# ... existing setup ...
app = FastAPI()
@app.post("/manual-makeup/")
async def manual_makeup(file: UploadFile = File(...), category: str = Form(...), color: str = Form("#ff1744")):
    """
    Lightweight manual try-on using MediaPipe overlays.
    category ∈ lips|blush|eyeshadow|eyeliner
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode uploaded image.")

        out_bgr = apply_makeup_bgr(img_bgr, feature=category, color_hex=color, is_stream=False)

        out_name = f"{category}_mp.png"
        out_dir = "data/output"
        os.makedirs(out_dir, exist_ok=True)
        out_path_abs = os.path.join(out_dir, out_name)
        cv2.imwrite(out_path_abs, out_bgr)

        # make it fetchable by frontend
        return {"output_path": f"output/{out_name}"}

    except Exception as e:
        tb = traceback.format_exc()
        print("Manual-makeup error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})
