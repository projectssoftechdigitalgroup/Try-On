# main.py
from fastapi import FastAPI, UploadFile, File, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, cv2, numpy as np, traceback, base64, subprocess

# --- Import project modules ---
from models import skin_tone_analysis, makeup_models, template_makeup
from models.skin_tone_analysis import analyze_with_gemini  # ✅ Import Gemini analyzer
from models.chat_stylist import router as chat_router
from models import jewellary_recommendation
from models.mediapipe_makeup import apply_makeup_bgr
from models import CapGlassesTryOn as cap_glasses_tryon

# ---------------- App ----------------
app = FastAPI(title="Beauty, Jewellery & Accessories Try-On API")

# ---------------- Middleware ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Include Routers ----------------
app.include_router(chat_router)
app.include_router(jewellary_recommendation.router)

# ---------------- Directories ----------------
UPLOAD_FOLDER  = "uploads"
TEMPLATES_DIR  = "data/templates"
OUTPUT_DIR     = "data/output"
JEWELLERY_DIR  = "data/jewellery_data"
CAPS_HATS_DIR  = "data/caps_hats"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Serve static folders
app.mount("/uploads",   StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/templates", StaticFiles(directory=TEMPLATES_DIR), name="templates")
app.mount("/output",    StaticFiles(directory=OUTPUT_DIR),    name="output")

if os.path.isdir(JEWELLERY_DIR):
    app.mount("/jewellery_data", StaticFiles(directory=JEWELLERY_DIR), name="jewellery_data")

if os.path.isdir(CAPS_HATS_DIR):
    app.mount("/caps_hats", StaticFiles(directory=CAPS_HATS_DIR), name="caps_hats")

# ---------------- Health ----------------
@app.get("/")
def root():
    return {"status": "ok", "service": "beauty-jewellery-capglasses-tryon 🚀"}

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
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Skin Analysis ----------------
@app.post("/analyze-skin/{method}/")
async def analyze_skin(method: str, file: UploadFile = File(...)):
    """
    Skin tone analysis using Mediapipe, Groq, or Gemini
    """
    try:
        method = method.lower()
        if method == "mediapipe":
            return skin_tone_analysis.analyze_with_mediapipe(file.file)
        elif method == "groq":
            return skin_tone_analysis.analyze_with_groq(file.file)
        elif method == "gemini":
            return analyze_with_gemini(file.file)  # ✅ Fixed
        else:
            return {"error": "Invalid method. Use 'mediapipe', 'groq', or 'gemini'."}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Makeup ----------------
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
        return makeup_models.get_makeup_suggestions_from_image(file.file)
    except Exception as e:
        return {"error": str(e)}

# ---------------- Templates ----------------
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
async def apply_template(file: UploadFile = File(...), occasion: str = Form(...), sample: str = Form("sample1.png")):
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
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Manual Makeup ----------------
@app.post("/manual-makeup/")
async def manual_makeup(file: UploadFile = File(...), category: str = Form(...), color: str = Form("#ff1744"),
                        intensity: float = Form(1.0), shade: str = Form(None)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode uploaded image.")

        out_bgr = apply_makeup_bgr(img_bgr, feature=category, color_hex=color, intensity=float(intensity))
        out_name = f"{category}_mp.png"
        out_path_abs = os.path.join(OUTPUT_DIR, out_name)
        cv2.imwrite(out_path_abs, out_bgr)
        return {"output_path": f"output/{out_name}"}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Jewellery ----------------
@app.post("/recommend-jewelry/")
async def recommend_jewelry(file: UploadFile = File(...)):
    try:
        return jewellary_recommendation.recommend_jewelry_from_image(file.file)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Cap/Glasses Try-On ----------------
@app.post("/capglasses-tryon/")
async def capglasses_tryon_api(file: UploadFile = File(...), accessory: str = Form(None), filename: str = Form(None)):
    try:
        contents = await file.read()
        result = cap_glasses_tryon.tryon_and_recommend(contents, accessory, filename)

        if isinstance(result, dict):
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=500, content={"error": "Unexpected return type", "received": str(type(result))})
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Real-Time Skin Analysis ----------------
@app.websocket("/ws/realtime-skin")
async def realtime_skin(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame_bytes = base64.b64decode(data.split(",")[1])
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                await websocket.send_json({"error": "Invalid frame"})
                continue
            result = skin_tone_analysis.analyze_frame(frame)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        print("Client disconnected from realtime-skin")
    except Exception:
        await websocket.close()

# ---------------- Launch Realtime ----------------
@app.post("/launch-realtime/")
async def launch_realtime():
    try:
        subprocess.Popen(["python", "models/realtime_skin_analysis.py"])
        return {"status": "started", "message": "Realtime Skin Analysis launched ✅, please wait it will take time"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------- Cap/Glasses Try-On ----------------
from models import realtime_cap_glasses

@app.post("/process-capglasses/")
async def process_capglasses(file: UploadFile = File(...), accessory: str = Form(None), filename: str = Form(None)):
    try:
        contents = await file.read()
        result = realtime_cap_glasses.process_frame(contents, accessory, filename)

        if result:
            return result   # { "frame": base64 string, "overlayBox": [...] }
        else:
            return JSONResponse(status_code=500, content={"error": "Processing failed"})
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

