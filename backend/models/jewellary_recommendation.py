import os, tempfile, cv2, numpy as np, random, math
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter(tags=["jewellery"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GALLERY_ROOT = os.path.join(BASE_DIR, "data", "jewellery_data")

FOLDER_MAP = {
    "nosepin": "Nose pin",
    "earrings": "Earring",
    "earring": "Earring",
    "necklace": "Necklace",
    "bindi": "Bindi",
    "tikka": "Maang Tikka",
}

# ------------------- Helpers -------------------

async def _file_to_bgr(upload: UploadFile) -> Optional[np.ndarray]:
    try:
        content = await upload.read()
        if not content:
            return None
        img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
        return img
    except:
        return None

def _read_image(path: str) -> Optional[np.ndarray]:
    return cv2.imread(path, cv2.IMREAD_UNCHANGED) if path and os.path.isfile(path) else None

def _safe_detect_landmarks(bgr) -> Optional[tuple]:
    try:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True) as fm:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            res = fm.process(rgb)
        return (res.multi_face_landmarks[0], bgr.shape[:2]) if res.multi_face_landmarks else None
    except:
        return None

def _pt(lm, shape_hw, idx):
    h, w = shape_hw
    p = lm.landmark[idx]
    return int(p.x * w), int(p.y * h)

def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def _angle_deg(p1, p2):
    dy = p2[1] - p1[1]
    dx = p2[0] - p1[0]
    return math.degrees(math.atan2(dy, dx))

def _alpha_overlay(base, overlay, center, scale=1.0, angle=0.0):
    try:
        if overlay is None:
            return base
        h, w = overlay.shape[:2]
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        overlay = cv2.resize(overlay, (new_w, new_h), cv2.INTER_AREA)

        if abs(angle) > 1e-2:
            M = cv2.getRotationMatrix2D((new_w / 2, new_h / 2), angle, 1.0)
            overlay = cv2.warpAffine(
                overlay, M, (new_w, new_h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0)
            )

        cx, cy = center
        x1, y1 = cx - new_w // 2, cy - new_h // 2
        x2, y2 = x1 + new_w, y1 + new_h
        H, W = base.shape[:2]
        if x1 >= W or y1 >= H or x2 <= 0 or y2 <= 0:
            return base

        x1c, y1c = max(0, x1), max(0, y1)
        x2c, y2c = min(W, x2), min(H, y2)
        overlay_crop = overlay[(y1c - y1):(y2c - y1), (x1c - x1):(x2c - x1)]

        if overlay_crop.shape[2] == 3:
            alpha = np.ones((*overlay_crop.shape[:2], 1), dtype=np.float32)
            rgb = overlay_crop.astype(np.float32)
        else:
            alpha = overlay_crop[:, :, 3:4].astype(np.float32) / 255.0
            rgb = overlay_crop[:, :, :3].astype(np.float32)

        roi = base[y1c:y2c, x1c:x2c].astype(np.float32)
        blended = alpha * rgb + (1 - alpha) * roi
        base[y1c:y2c, x1c:x2c] = blended.astype(np.uint8)
        return base
    except:
        return base

def _resolve_overlay_path(overlay_url: Optional[str], item: str) -> Optional[str]:
    """
    If overlay_url is provided like '/jewellery_data/Earring/earring_1.png',
    map it to the actual disk path under BASE_DIR/data/jewellery_data/... safely.
    Otherwise, pick a random candidate from the item's folder.
    """
    if overlay_url and overlay_url.startswith("/jewellery_data/"):
        # Safe, normalized path under GALLERY_ROOT
        safe_rel = overlay_url.lstrip("/")  # 'jewellery_data/...'
        candidate = os.path.normpath(os.path.join(BASE_DIR, "data", safe_rel))
        try:
            # Ensure candidate stays inside GALLERY_ROOT (avoid path traversal)
            if os.path.commonpath([candidate, GALLERY_ROOT]) == GALLERY_ROOT and os.path.isfile(candidate):
                return candidate
        except:
            return None  # any failure → ignore and fallback
        return None  # if not a file, fall back below

    folder = FOLDER_MAP.get(item.lower())
    if not folder:
        return None
    full = os.path.join(GALLERY_ROOT, folder)
    if not os.path.isdir(full):
        return None
    cands = [f for f in os.listdir(full) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    return os.path.join(full, random.choice(cands)) if cands else None

def _place_item(base, item, overlay_path=None):
    lm = _safe_detect_landmarks(base)
    if lm is None:
        return base, None
    landmarks, shape_hw = lm
    overlay = _read_image(overlay_path) if overlay_path else None
    if overlay is None:
        return base, None

    left_face = _pt(landmarks, shape_hw, 234)
    right_face = _pt(landmarks, shape_hw, 454)
    face_w = _dist(left_face, right_face) or min(base.shape[:2]) * 0.5
    warning = None
    item_l = item.lower()

    if item_l == "nosepin":
        nose_tip = _pt(landmarks, shape_hw, 1)
        nose_base = _pt(landmarks, shape_hw, 2)
        angle = _angle_deg(nose_tip, nose_base) * 0.6
        center = (nose_tip[0] + int(0.08 * face_w), nose_tip[1] - int(0.02 * face_w))
        scale = max(0.075 * face_w / overlay.shape[1], 0.045)
        return _alpha_overlay(base, overlay, center, scale, angle), warning

    if item_l in ("earrings", "earring"):
        if face_w < 60:
            warning = "Ears not visible, skipping earrings"
            return base, warning
        scale = max(0.28 * face_w / overlay.shape[1], 0.14)
        base = _alpha_overlay(base, overlay, left_face, scale)
        base = _alpha_overlay(base, overlay, right_face, scale)
        return base, warning

    if item_l == "bindi":
        inner_left = _pt(landmarks, shape_hw, 105)
        inner_right = _pt(landmarks, shape_hw, 334)
        center_x = (inner_left[0] + inner_right[0]) // 2
        center_y = (inner_left[1] + inner_right[1]) // 2 - int(0.02 * face_w)
        scale = max(0.09 * face_w / overlay.shape[1], 0.06)
        return _alpha_overlay(base, overlay, (center_x, center_y), scale), warning

    if item_l == "tikka":
        inner_left = _pt(landmarks, shape_hw, 105)
        inner_right = _pt(landmarks, shape_hw, 334)
        center_x = (inner_left[0] + inner_right[0]) // 2
        center_y = min(inner_left[1], inner_right[1]) - int(0.08 * face_w)
        scale = max(0.34 * face_w / overlay.shape[1], 0.20)
        return _alpha_overlay(base, overlay, (center_x, center_y), scale), warning

    if item_l == "necklace":
        chin = _pt(landmarks, shape_hw, 152)
        center = (chin[0], chin[1] + int(0.28 * face_w))
        scale = max(0.85 * face_w / overlay.shape[1], 0.55)
        return _alpha_overlay(base, overlay, center, scale), warning

    return base, warning

# ------------------- Endpoints -------------------

@router.post("/recommend-jewelry/")
async def recommend_jewelry(file: UploadFile = File(...)):
    try:
        bgr = await _file_to_bgr(file)
        face_detected = bool(bgr is not None and _safe_detect_landmarks(bgr) is not None)
        return {
            "metals": random.sample(["Yellow Gold", "Rose Gold", "Silver", "White Gold"], 2),
            "gemstones": random.sample(["Emerald", "Ruby", "Pearl", "Sapphire", "Amethyst"], 2),
            "face_shape": random.choice(["Oval", "Round", "Heart", "Square"]),
            "nosepin": "Tiny Stud",
            "earrings": "Gemstone Studs",
            "necklace": "Classic Pendant",
            "bindi": "Medium Bindi",
            "tikka": "Pearl Chain Tikka",
            "face_detected": face_detected,
        }
    except:
        return {
            "metals": ["Yellow Gold", "Silver"],
            "gemstones": ["Pearl", "Ruby"],
            "face_shape": "Oval",
            "nosepin": "Tiny Stud",
            "earrings": "Gemstone Studs",
            "necklace": "Classic Pendant",
            "bindi": "Medium Bindi",
            "tikka": "Pearl Chain Tikka",
            "face_detected": False,
            "note": "fallback",
        }

@router.get("/list-jewelry-images/{item}")
async def list_jewelry_images(item: str):
    folder = FOLDER_MAP.get(item.lower())
    if not folder:
        return JSONResponse({"error": f"Unknown item '{item}'"}, status_code=400)
    path = os.path.join(GALLERY_ROOT, folder)
    if not os.path.isdir(path):
        return JSONResponse({"error": f"Folder not found: {path}"}, status_code=404)
    files = sorted({
        f"/jewellery_data/{folder}/{f}"
        for f in os.listdir(path)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    })
    return {"images": list(files)}

@router.post("/tryon-jewelry/")
async def tryon_jewelry(file: UploadFile = File(...), item: str = Form(...), overlay_url: str = Form(None)):
    try:
        bgr = await _file_to_bgr(file)
        if bgr is None:
            return JSONResponse({"error": "Invalid image"}, status_code=400)
        overlay_path = _resolve_overlay_path(overlay_url, item)
        out, warn = _place_item(bgr, item, overlay_path)
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        cv2.imwrite(tmp, out)
        headers = {}
        if warn:
            headers["X-Warning"] = warn
        # reduce client-side caching issues during rapid switching
        headers["Cache-Control"] = "no-store"
        return FileResponse(tmp, media_type="image/png", filename=f"tryon_{item}.png", headers=headers)
    except:
        return JSONResponse(status_code=500, content={"error": "Try-on failed"})

@router.post("/apply-all-jewelry/")
async def apply_all_jewelry(file: UploadFile = File(...), items: str = Form(...)):
    try:
        bgr = await _file_to_bgr(file)
        if bgr is None:
            return JSONResponse({"error": "Invalid image"}, status_code=400)

        import json
        selected_overlays = json.loads(items) if items else {}

        out = bgr.copy()
        for key, overlay_url in selected_overlays.items():
            overlay_path = _resolve_overlay_path(overlay_url, key)
            out, _ = _place_item(out, key, overlay_path)

        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        cv2.imwrite(tmp, out)
        return FileResponse(tmp, media_type="image/png", filename="tryon_selected.png")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
