# main.py
from fastapi import FastAPI, UploadFile, File, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, time, re, cv2, numpy as np, traceback, base64, subprocess, io, requests
from PIL import Image

# --- Import project modules ---
from models import skin_tone_analysis, makeup_models, template_makeup
from models.skin_tone_analysis import analyze_with_gemini
from models.chat_stylist import router as chat_router
from models import jewellary_recommendation
from models.mediapipe_makeup import apply_makeup_bgr
from models import CapGlassesTryOn as cap_glasses_tryon
from models import wrist_module
from models import realtime_cap_glasses
from models import clothesTryOn
from models.MoustacheTryOn import router as moustache_router
from models.HairTryOn import router as HairTryOnRouter
from models.realtime_wristTryOn import router as realtime_wristTryOn 


# ---------------- App ----------------
app = FastAPI(title="Beauty, Jewellery & Accessories Try-On API")

# ---------------- Middleware ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ⚠️ Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Include Routers ----------------
app.include_router(chat_router)
app.include_router(jewellary_recommendation.router)
app.include_router(clothesTryOn.router)
app.include_router(moustache_router)
app.include_router(HairTryOnRouter)
app.include_router(realtime_wristTryOn)
# ---------------- Directories ----------------
UPLOAD_FOLDER  = "uploads"
TEMPLATES_DIR  = "data/templates"
OUTPUT_DIR     = "data/output"
JEWELLERY_DIR  = "data/jewellery_data"
CAPS_HATS_DIR  = "data/caps_hats"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ✅ Serve static folders with consistent URLs
app.mount("/uploads",   StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/templates", StaticFiles(directory=TEMPLATES_DIR), name="templates")
app.mount("/output",    StaticFiles(directory=OUTPUT_DIR),    name="output")

if os.path.isdir(JEWELLERY_DIR):
    app.mount("/jewellery_data", StaticFiles(directory=JEWELLERY_DIR), name="jewellery_data")

if os.path.isdir(CAPS_HATS_DIR):
    app.mount("/caps_hats", StaticFiles(directory=CAPS_HATS_DIR), name="caps_hats")

# ---------------- Utility ----------------
def secure_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
    return filename

# ---------------- Health ----------------
@app.get("/")
def root():
    return {"status": "ok", "service": "beauty-jewellery-capglasses-tryon 🚀"}

# ---------------- Upload ----------------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "message": "File uploaded successfully",
            "path": file_path,
            "url": f"/uploads/{secure_filename(file.filename)}"
        }
    except Exception as e:
        tb = traceback.format_exc()
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
        elif method == "gemini":
            return analyze_with_gemini(file.file)
        else:
            return {"error": "Invalid method. Use 'mediapipe', 'groq', or 'gemini'."}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Wrist Try-On ----------------
@app.post("/wrist-tryon/")
async def wrist_tryon(
    request: Request,
    wrist_image: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    watch_choice: str = Form(...)
):
    try:
        uploaded = wrist_image or file
        if uploaded is None:
            return JSONResponse(status_code=400, content={"error": "Missing wrist image."})

        watch_filename = os.path.basename(watch_choice)
        watch_path = os.path.join(UPLOAD_FOLDER, watch_filename)
        if not os.path.exists(watch_path):
            return JSONResponse(status_code=400, content={"error": f"Invalid watch choice: {watch_filename}."})

        watch_image = cv2.imread(watch_path, cv2.IMREAD_UNCHANGED)
        if watch_image is None:
            return JSONResponse(status_code=500, content={"error": "Failed to load watch image."})

        safe_name = secure_filename(uploaded.filename or f"wrist_{int(time.time())}.jpg")
        wrist_filename = f"wrist_{int(time.time())}_{safe_name}"
        wrist_path = os.path.join(UPLOAD_FOLDER, wrist_filename)

        contents = await uploaded.read()
        with open(wrist_path, "wb") as f:
            f.write(contents)

        wrist_image_cv = cv2.imread(wrist_path)
        if wrist_image_cv is None:
            return JSONResponse(status_code=400, content={"error": "Failed to decode wrist image."})

        virtual_tryon = wrist_module.VirtualWatchTryOn(wrist_image_cv, watch_image)
        result_img = virtual_tryon.process_image()
        if result_img is None:
            return JSONResponse(status_code=500, content={"error": "Try-on processing failed."})

        result_filename = f"result_{int(time.time())}.png"
        result_path = os.path.join(UPLOAD_FOLDER, result_filename)
        cv2.imwrite(result_path, result_img)

        base = str(request.base_url).rstrip("/")
        result_url = f"{base}/uploads/{result_filename}"

        return {"message": "✅ Try-on completed successfully!", "result_image_url": result_url}

    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR in /wrist-tryon:\n", tb)
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
async def manual_makeup(
    file: UploadFile = File(...),
    category: str = Form(...),
    color: str = Form("#ff1744"),
    intensity: float = Form(1.0),
    shade: str = Form(None)
):
    try:
        contents = await file.read()
        if not contents:
            return JSONResponse(status_code=400, content={"error": "No file content received."})

        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return JSONResponse(status_code=400, content={"error": "Invalid or corrupted image file."})

        out_bgr = apply_makeup_bgr(img_bgr, feature=category, color_hex=color, intensity=float(intensity))
        out_name = f"{category}_mp.png"
        out_path_abs = os.path.join(OUTPUT_DIR, out_name)
        cv2.imwrite(out_path_abs, out_bgr)

        return {"output_path": f"/output/{out_name}"}

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

# ---------------- Prompt-Based Jewelry Try-On ----------------
from fastapi.responses import JSONResponse
import os, io, base64, time, traceback, requests
from fastapi import UploadFile, File, Form
from PIL import Image

@app.post("/prompt-jewelry-tryon/")
async def prompt_jewelry_tryon(file: UploadFile = File(...), prompt: str = Form(...)):
    """
    AI-powered Jewellery visualization using Gemini 2.0 Vision API.
    Returns an image overlay result.
    """
    try:
        # ✅ Load GEMINI API key from environment
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            return JSONResponse(
                status_code=400,
                content={"error": "Gemini API key not set. Please set GEMINI_API_KEY in environment."}
            )

        GEMINI_URL = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        )

        # ✅ Validate uploaded image
        image_bytes = await file.read()
        Image.open(io.BytesIO(image_bytes))  # Raise exception if invalid

        # ✅ Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # ✅ Prepare Gemini payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": file.content_type,
                                "data": image_base64
                            }
                        },
                    ]
                }
            ]
        }

        # ✅ Call Gemini API
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()

        print("🔹 Gemini API Response:", result)

        # ✅ Handle API key / request errors
        if "error" in result:
            err_msg = result["error"].get("message", "Unknown Gemini error")
            return JSONResponse(
                status_code=400,
                content={"error": f"Gemini API error: {err_msg}", "details": result}
            )

        # ✅ Check for candidates
        if "candidates" not in result or not result["candidates"]:
            return JSONResponse(
                status_code=500,
                content={"error": "Gemini did not return any candidates", "details": result}
            )

        # ✅ Extract base64 image from Gemini response
        image_data_b64 = result["candidates"][0].get("content", [{}])[0].get("image", None)
        if not image_data_b64:
            return JSONResponse(
                status_code=500,
                content={"error": "No image returned by Gemini", "details": result}
            )

        # ✅ Save image to output folder
        tmp_path = os.path.join(OUTPUT_DIR, f"tryon_{int(time.time())}.png")
        img_data = base64.b64decode(image_data_b64)
        with open(tmp_path, "wb") as f:
            f.write(img_data)

        base_url = "http://127.0.0.1:8000"  # adjust if deployed elsewhere
        result_url = f"{base_url}/output/{os.path.basename(tmp_path)}"

        return {
            "message": "✅ Jewelry prompt processed successfully!",
            "result_image_url": result_url
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ Error in /prompt-jewelry-tryon/:\n", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Cap/Glasses Try-On ----------------
@app.post("/capglasses-tryon/")
async def capglasses_tryon_api(file: UploadFile = File(...), accessory: str = Form(None), filename: str = Form(None)):
    try:
        contents = await file.read()
        result = cap_glasses_tryon.tryon_and_recommend(contents, accessory, filename)
        return JSONResponse(content=result if isinstance(result, dict) else {"error": "Unexpected return type"})
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
        return {"status": "started", "message": "Realtime Skin Analysis launched ✅"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------- Cap/Glasses Real-Time ----------------
@app.post("/process-capglasses/")
async def process_capglasses(file: UploadFile = File(...), accessory: str = Form(None), filename: str = Form(None)):
    try:
        contents = await file.read()
        result = realtime_cap_glasses.process_frame(contents, accessory, filename)
        return result if result else JSONResponse(status_code=500, content={"error": "Processing failed"})
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})

# ---------------- Watches ----------------
@app.get("/watches/")
async def get_watches():
    try:
        if os.path.exists(UPLOAD_FOLDER):
            watches = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if watches:
                return {"watches": watches}
        return {"watches": ["watch1.png", "watch2.png", "watch3.png"]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/available-watches")
async def available_watches():
    try:
        allowed_watches = {"watch1.png", "watch2.png", "watch3.png"}
        files = os.listdir(UPLOAD_FOLDER)
        watches = [f for f in files if f in allowed_watches]
        return {"watches": watches}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

