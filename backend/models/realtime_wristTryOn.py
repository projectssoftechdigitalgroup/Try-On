from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import cv2, numpy as np, os, base64, time, traceback
import mediapipe as mp

UPLOAD_FOLDER = "uploads"

router = APIRouter(prefix="/process-realtime-wrist", tags=["RealTime Wrist Try-On"])

mp_hands = mp.solutions.hands

# ---- Core Processor ----
def overlay_watch(frame, watch_img, wrist_x, wrist_y):
    h, w = frame.shape[:2]
    watch_h, watch_w = watch_img.shape[:2]

    top_left_x = wrist_x - watch_w // 2
    top_left_y = wrist_y - watch_h // 2

    top_left_x = max(0, min(top_left_x, w - watch_w))
    top_left_y = max(0, min(top_left_y, h - watch_h))

    if watch_img.shape[2] == 4:
        alpha = watch_img[:, :, 3] / 255.0
        rgb = watch_img[:, :, :3]
    else:
        alpha = np.ones((watch_h, watch_w), dtype=np.float32)
        rgb = watch_img

    region = frame[top_left_y:top_left_y+watch_h, top_left_x:top_left_x+watch_w]
    for c in range(3):
        region[:, :, c] = (alpha * rgb[:, :, c] + (1 - alpha) * region[:, :, c])

    frame[top_left_y:top_left_y+watch_h, top_left_x:top_left_x+watch_h] = region
    return frame

# ---- API Endpoint for Real-Time Frames ----
@router.post("/")
async def process_frame(
    file: UploadFile = File(...),
    filename: str = Form(...)
):
    try:
        # Load watch from uploads folder
        watch_path = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))
        watch_img = cv2.imread(watch_path, cv2.IMREAD_UNCHANGED)

        if watch_img is None:
            return {"error": f"Watch image not found: {filename}"}

        # Decode incoming frame
        frame_bytes = await file.read()
        np_frame = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Invalid video frame received"}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with mp_hands.Hands(static_image_mode=False,
                            max_num_hands=1,
                            min_detection_confidence=0.6) as hands:

            results = hands.process(rgb)
            if results.multi_hand_landmarks:
                for lm in results.multi_hand_landmarks:
                    h, w = frame.shape[:2]
                    x = int(lm.landmark[0].x * w)
                    y = int(lm.landmark[0].y * h)

                    # Resize watch relative to frame size
                    resized_watch = cv2.resize(watch_img, (w // 4, w // 4))
                    frame = overlay_watch(frame, resized_watch, x, y)

        # Encode result to Base64
        _, buffer = cv2.imencode(".jpg", frame)
        frame_base64 = base64.b64encode(buffer).decode("utf-8")

        return {"frame": f"data:image/jpeg;base64,{frame_base64}"}

    except Exception as e:
        print("❌ Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
