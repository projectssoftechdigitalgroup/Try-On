from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, cv2, numpy as np, traceback

# --- Import your existing modules ---
from models import skin_tone_analysis, makeup_models, template_makeup
from models.chat_stylist import router as chat_router
from models import jewellary_recommendation            # ✅ Jewellery recommendation & try-on
from models.mediapipe_makeup import apply_makeup_bgr

# ---------------- App ----------------
app = FastAPI(title="Beauty & Jewellery Try-On API")

# ---------------- Middleware ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # ⚠️ Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Include Routers ----------------
app.include_router(chat_router)                        # Chat stylist
app.include_router(jewellary_recommendation.router)     # ✅ Mount all jewellery endpoints

# ---------------- Directories ----------------
UPLOAD_FOLDER   = "uploads"
TEMPLATES_DIR   = "data/templates"
OUTPUT_DIR      = "data/output"
JEWELLERY_DIR   = "data/jewellery_data"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Serve static folders
app.mount("/uploads",    StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/templates",  StaticFiles(directory=TEMPLATES_DIR), name="templates")
app.mount("/output",     StaticFiles(directory=OUTPUT_DIR),    name="output")
if os.path.isdir(JEWELLERY_DIR):
    app.mount("/jewellery_data", StaticFiles(directory=JEWELLERY_DIR), name="jewellery_data")

# ---------------- Health ----------------
@app.get("/")
def health_check():
    return {"status": "ok", "service": "beauty-jewellery-tryon"}

# ---------------- Upload ----------------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": "File uploaded successfully", "path": file_path, "url": f"/uploads/{file.filename}"}
    except Exception as e:
        tb = traceback.format_exc()
        print("Upload error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Skin Analysis ----------------
@app.post("/analyze-skin/{method}/")
async def analyze_skin(method: str, file: UploadFile = File(...)):
    try:
        method = method.lower()
        if method == "mediapipe":
            return skin_tone_analysis.analyze_with_mediapipe(file.file)
        elif method == "groq":
            return skin_tone_analysis.analyze_with_groq(file.file)
        else:
            return {"error": "Invalid method. Use 'mediapipe' or 'groq'."}
    except Exception as e:
        tb = traceback.format_exc()
        print("Analyze-skin error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Style-based Makeup ----------------
@app.post("/apply-makeup/")
async def apply_makeup(file: UploadFile = File(...), style: str = Form(...)):
    try:
        result_path = makeup_models.apply_style(file.file, style)
        return {"makeup_image": result_path}
    except Exception as e:
        return {"error": str(e)}

@app.post("/makeup-tryon/")
async def makeup_tryon(file: UploadFile = File(...)):
    try:
        result = makeup_models.get_makeup_suggestions_from_image(file.file)
        return result
    except Exception as e:
        return {"error": str(e)}

# ---------------- Templates (BeautyGAN-like) ----------------
@app.get("/available-templates/")
async def available_templates(request: Request):
    base_url = str(request.base_url).rstrip("/")
    out = {}
    for occasion in os.listdir(TEMPLATES_DIR):
        dirpath = os.path.join(TEMPLATES_DIR, occasion)
        if os.path.isdir(dirpath):
            files = [
                f"{base_url}/templates/{occasion}/{f}"
                for f in os.listdir(dirpath)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            if files:
                out[occasion] = files
    return out

@app.post("/apply-template/")
async def apply_template(
    file: UploadFile = File(...), occasion: str = Form(...), sample: str = Form("sample1.png")
):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        user_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if user_img is None:
            raise ValueError("Failed to decode uploaded image.")

        template_path = template_makeup.get_template_path(occasion, sample)
        if not template_path:
            return JSONResponse(status_code=404, content={"error": "Template not found"})

        template_img = cv2.imread(template_path)
        if template_img is None:
            raise ValueError(f"Failed to load template image: {template_path}")

        output = template_makeup.makeupTransfer(user_img, template_img)
        if output is None:
            raise RuntimeError("makeupTransfer returned None.")

        out_path = os.path.join(OUTPUT_DIR, f"result_{occasion}.png")
        cv2.imwrite(out_path, cv2.cvtColor(output, cv2.COLOR_RGB2BGR))
        return FileResponse(out_path, media_type="image/png")

    except Exception as e:
        tb = traceback.format_exc()
        print("Apply-template error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Manual Makeup (MediaPipe overlay) ----------------
@app.post("/manual-makeup/")
async def manual_makeup(
    file: UploadFile = File(...),
    category: str = Form(...),
    color: str = Form("#ff1744"),
    intensity: float = Form(1.0),
    shade: str = Form(None),
):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode uploaded image.")

        out_bgr = apply_makeup_bgr(
            img_bgr,
            feature=category,
            color_hex=color,
            intensity=float(intensity),
        )
        out_name = f"{category}_mp.png"
        out_path_abs = os.path.join(OUTPUT_DIR, out_name)
        cv2.imwrite(out_path_abs, out_bgr)
        return {"output_path": f"output/{out_name}"}
    except Exception as e:
        tb = traceback.format_exc()
        print("Manual-makeup error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ✅ Jewellery shortcut still available (same as router’s recommend endpoint)
@app.post("/recommend-jewelry/")
async def recommend_jewelry(file: UploadFile = File(...)):
    try:
        recs = jewellary_recommendation.recommend_jewelry_from_image(file.file)
        return recs
    except Exception as e:
        tb = traceback.format_exc()
        print("Jewellery recommendation error:", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})
