# backend_hair_gemini_prompt.py
from fastapi import FastAPI, APIRouter, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import logging
import traceback
from models.Hair_gemini_prompt import HairGeminiSystem

# ---------------------- App Setup ---------------------- #
app = FastAPI(title="Hair Gemini Prompt API")
router = APIRouter(prefix="/", tags=["Hair Gemini Prompt"])

# ---------------------- Logging ---------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("hair_gemini_prompt.log"), logging.StreamHandler()],
)

# ---------------------- Paths ---------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "output")

if not os.path.exists(STATIC_OUTPUT_DIR):
    os.makedirs(STATIC_OUTPUT_DIR)

# ---------------------- Gemini Integration ---------------------- #
gemini_system = HairGeminiSystem()
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not API_KEY:
    logging.warning("⚠️ No GEMINI_API_KEY found in environment variables!")
else:
    setup_result = gemini_system.setup(API_KEY)
    logging.info(setup_result.get("message", "Gemini setup attempted."))

# ---------------------- Main Endpoint ---------------------- #
@router.post("/run-hair-gemini-prompt/")
async def run_hair_gemini_prompt(
    prompt: str = Form(default="Natural wavy brown hair"),
    image: UploadFile = None,
):
    """
    Run Gemini 2.0 Flash hair transformation with a custom prompt.
    Frontend FormData:
      - image: uploaded photo
      - prompt: hairstyle text (e.g., 'short golden bob cut')
    """
    try:
        if image is None:
            return JSONResponse({"error": "No image uploaded."}, status_code=400)

        if not gemini_system.client:
            return JSONResponse({"error": "Gemini system not initialized."}, status_code=500)

        image_bytes = await image.read()
        result = gemini_system.process_hair_change(image_bytes, prompt)

        if not result.get("ok"):
            return JSONResponse({"error": result.get("error", "Unknown error")}, status_code=500)

        # Save output image locally
        output_path = os.path.join(STATIC_OUTPUT_DIR, "output.png")
        with open(output_path, "wb") as f:
            f.write(
                bytes(result["image_base64"], encoding="utf-8")
                if isinstance(result["image_base64"], str)
                else result["image_base64"]
            )

        logging.info("✅ Gemini hair prompt processed successfully.")

        return {
            "status": "success",
            "message": "Gemini hair transformation completed!",
            "image_url": f"/static/output/output.png",
            "evaluation": result.get("text", ""),
        }

    except Exception:
        logging.error("❌ Unexpected error in run_hair_gemini_prompt:\n" + traceback.format_exc())
        return JSONResponse({"error": "Internal server error"}, status_code=500)

# ---------------------- Mount Static Files ---------------------- #
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---------------------- Include Router ---------------------- #
app.include_router(router)
