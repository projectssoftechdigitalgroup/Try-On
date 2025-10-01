import os
import time
import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from werkzeug.utils import secure_filename
from fastapi.middleware.cors import CORSMiddleware

# ---------------- FastAPI app ----------------
app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to ["http://localhost:3000"] for React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Paths ----------------
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Mount static folder for frontend access
app.mount("/static", StaticFiles(directory=UPLOAD_FOLDER), name="static")

# ---------------- Mediapipe ----------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


# ---------------- Virtual Watch Try-On Class ----------------
class VirtualWatchTryOn:
    def __init__(self, wrist_image, watch_image):
        self.wrist_image = wrist_image
        self.watch_image = watch_image
        self.height, self.width = self.wrist_image.shape[:2]

        # Resize watch image dynamically (about 1/3 of wrist image size)
        self.watch_image = cv2.resize(
            self.watch_image,
            (self.width // 3, self.height // 3)
        )
        self.watch_height, self.watch_width = self.watch_image.shape[:2]

        # Initialize MediaPipe Hands
        self.hands = mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def estimate_wrist_pose(self, hand_landmarks, image_shape):
        """Estimate wrist landmark pixel position."""
        wrist = hand_landmarks.landmark[0]
        h, w = image_shape[:2]
        x_pixel = int(wrist.x * w)
        y_pixel = int(wrist.y * h)
        return x_pixel, y_pixel

    def get_hand_direction(self, hand_landmarks, image_shape):
        """Calculate normalized vector from wrist to middle finger."""
        h, w = image_shape[:2]
        wrist = hand_landmarks.landmark[0]       # Wrist
        middle_mcp = hand_landmarks.landmark[9]  # Middle finger MCP joint

        wrist_x = wrist.x * w
        wrist_y = wrist.y * h
        middle_x = middle_mcp.x * w
        middle_y = middle_mcp.y * h

        direction_x = middle_x - wrist_x
        direction_y = middle_y - wrist_y
        magnitude = np.sqrt(direction_x ** 2 + direction_y ** 2)

        if magnitude > 0:
            direction_x /= magnitude
            direction_y /= magnitude

        return direction_x, direction_y

    def process_image(self):
        """Run Mediapipe hand detection and overlay watch."""
        rgb_frame = cv2.cvtColor(self.wrist_image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                wrist_x, wrist_y = self.estimate_wrist_pose(
                    hand_landmarks, self.wrist_image.shape
                )
                direction_x, direction_y = self.get_hand_direction(
                    hand_landmarks, self.wrist_image.shape
                )
                self.overlay_watch_on_wrist(
                    self.wrist_image, wrist_x, wrist_y, direction_x, direction_y
                )

        return self.wrist_image

    def overlay_watch_on_wrist(self, image, wrist_x, wrist_y, direction_x=0, direction_y=0):
        """Overlay the watch image with alpha blending at estimated wrist position."""
        backward_offset = 30  # push backward from finger direction
        offset_x = -direction_x * backward_offset
        offset_y = -direction_y * backward_offset

        # Top-left corner
        top_left_x = int(wrist_x - self.watch_width // 2 + offset_x)
        top_left_y = int(wrist_y - self.watch_height // 2 + offset_y)

        # Clamp inside frame
        top_left_x = max(0, min(top_left_x, self.width - self.watch_width))
        top_left_y = max(0, min(top_left_y, self.height - self.watch_height))

        # Handle transparency (PNG with alpha)
        if self.watch_image.shape[2] == 4:
            alpha = self.watch_image[:, :, 3] / 255.0
            watch_rgb = self.watch_image[:, :, :3]
        else:
            alpha = np.ones((self.watch_height, self.watch_width), dtype=np.float32)
            watch_rgb = self.watch_image

        for c in range(3):
            image[top_left_y:top_left_y+self.watch_height, top_left_x:top_left_x+self.watch_width, c] = (
                alpha * watch_rgb[:, :, c]
                + (1 - alpha) * image[top_left_y:top_left_y+self.watch_height, top_left_x:top_left_x+self.watch_width, c]
            )


# ---------------- Routes ----------------

@app.get("/available-watches")
async def available_watches():
    try:
        # Define the allowed watch filenames
        allowed_watches = {"watch1.png", "watch2.png", "watch3.png"}

        # Get files from the folder
        files = os.listdir(UPLOAD_FOLDER)

        # Filter only allowed ones
        watches = [f for f in files if f in allowed_watches]

        return {"watches": watches}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/wrist-tryon")
async def wrist_tryon(
    wrist_image: UploadFile = File(...),
    watch_choice: str = Form(...)
):
    try:
        # --- Debug logging ---
        print(f"➡️ Selected watch: {watch_choice}")
        print(f"➡️ Uploaded file: {wrist_image.filename}")

        # Ensure safe filename (strip path if frontend sends URL)
        watch_filename = os.path.basename(watch_choice)
        watch_path = os.path.join(UPLOAD_FOLDER, watch_filename)
        print(f"➡️ Looking for watch at: {watch_path}")

        if not os.path.exists(watch_path):
            return JSONResponse(
                {"error": f"Invalid watch choice: {watch_filename}"}, 
                status_code=400
            )

        # Load watch image with alpha if available
        watch_img = cv2.imread(watch_path, cv2.IMREAD_UNCHANGED)
        if watch_img is None:
            return JSONResponse(
                {"error": f"Failed to load watch image {watch_filename}"}, 
                status_code=400
            )

        # Read wrist image directly from memory buffer instead of saving first
        wrist_bytes = await wrist_image.read()
        np_wrist = np.frombuffer(wrist_bytes, np.uint8)
        wrist_img = cv2.imdecode(np_wrist, cv2.IMREAD_COLOR)

        if wrist_img is None:
            return JSONResponse(
                {"error": "Failed to decode uploaded wrist image"}, 
                status_code=400
            )

        # Run try-on
        virtual_tryon = VirtualWatchTryOn(wrist_img, watch_img)
        result_img = virtual_tryon.process_image()

        # Save result
        result_filename = f"result_{int(time.time())}.png"
        result_path = os.path.join(UPLOAD_FOLDER, result_filename)
        cv2.imwrite(result_path, result_img)
        print(f"✅ Result saved: {result_path}")

        return {"result_image_url": f"/static/{result_filename}"}

    except Exception as e:
        import traceback
        print("❌ ERROR:", traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)
