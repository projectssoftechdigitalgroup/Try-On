from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import cv2, numpy as np, os, traceback, base64, mediapipe as mp

router = APIRouter()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

@router.post("/process-realtime-wrist/")
async def realtime_wrist_tryon_api(
    file: UploadFile = File(...),
    filename: str = Form(None)
):
    try:
        # ✅ Read uploaded image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 🧩 Load selected watch overlay (PNG with alpha)
        watch_path = os.path.join("data/watches", filename or "watch1.png")
        overlay = cv2.imread(watch_path, cv2.IMREAD_UNCHANGED)
        if overlay is None:
            raise ValueError("Watch overlay not found!")

        # 🖐️ Detect wrist using MediaPipe
        with mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5) as hands:
            results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if results.multi_hand_landmarks:
                # Take the first detected hand
                hand_landmarks = results.multi_hand_landmarks[0]

                # Wrist landmark (landmark[0])
                wrist = hand_landmarks.landmark[0]
                h, w, _ = img.shape
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)

                # 🪄 Resize overlay relative to hand size (landmark[5] index knuckle)
                index_knuckle = hand_landmarks.landmark[5]
                hand_width = int(abs((index_knuckle.x - wrist.x) * w) * 3.0)
                aspect_ratio = overlay.shape[0] / overlay.shape[1]
                overlay_resized = cv2.resize(overlay, (hand_width, int(hand_width * aspect_ratio)))

                # 🧩 Calculate top-left corner
                x1 = wrist_x - overlay_resized.shape[1] // 2
                y1 = wrist_y - overlay_resized.shape[0] // 2

                # Ensure bounds are within image
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x1 + overlay_resized.shape[1]), min(h, y1 + overlay_resized.shape[0])

                # Adjust overlay size if it goes out of bounds
                overlay_resized = overlay_resized[:y2 - y1, :x2 - x1]

                # 🩵 Alpha blending
                if overlay_resized.shape[2] == 4:
                    alpha = overlay_resized[:, :, 3] / 255.0
                    for c in range(3):
                        img[y1:y2, x1:x2, c] = (
                            alpha * overlay_resized[:, :, c] +
                            (1 - alpha) * img[y1:y2, x1:x2, c]
                        )

        # Encode to base64 for frontend
        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_b64 = base64.b64encode(buffer).decode("utf-8")
        return JSONResponse(content={"frame": f"data:image/jpeg;base64,{frame_b64}"})

    except Exception as e:
        return JSONResponse(content={"error": str(e), "trace": traceback.format_exc()})
