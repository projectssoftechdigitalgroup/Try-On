"""
Complete FastAPI backend for Virtual Try-On System
This is your main.py file that should be run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import cv2
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import mediapipe as mp

app = FastAPI(title="Virtual Try-On API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Global variables for clothing
top_type = "shirt"
bottom_type = "pant"
top_img = None
bottom_img = None

cap = cv2.VideoCapture(0)

def load_clothing_image(clothing_type, category):
    """Load clothing image from database folder"""
    try:
        path = f"./database/{clothing_type}.png"
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Warning: Could not load {path}")
            # Create a placeholder image if file not found
            img = np.zeros((200, 200, 4), dtype=np.uint8)
            img[:, :, 3] = 128  # Semi-transparent
        return img
    except Exception as e:
        print(f"Error loading {clothing_type}: {e}")
        return np.zeros((200, 200, 4), dtype=np.uint8)

def overlay_clothing(frame, pose_landmarks):
    """Overlay clothing on the detected pose"""
    global top_img, bottom_img
    
    if pose_landmarks is None:
        return frame
    
    h, w, _ = frame.shape
    
    # Get key landmarks
    landmarks = pose_landmarks.landmark
    
    # Overlay top clothing (shirt)
    if top_img is not None:
        # Get shoulder landmarks
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate position and size for top
        shoulder_width = int(abs(right_shoulder.x - left_shoulder.x) * w * 1.5)
        shoulder_height = int(shoulder_width * 1.2)
        
        center_x = int((left_shoulder.x + right_shoulder.x) * w / 2)
        center_y = int((left_shoulder.y + right_shoulder.y) * h / 2)
        
        # Resize and overlay top
        if shoulder_width > 0 and shoulder_height > 0:
            top_resized = cv2.resize(top_img, (shoulder_width, shoulder_height))
            
            # Calculate overlay position
            x1 = max(0, center_x - shoulder_width // 2)
            y1 = max(0, center_y - shoulder_height // 4)
            x2 = min(w, x1 + shoulder_width)
            y2 = min(h, y1 + shoulder_height)
            
            # Adjust resized image if needed
            if x2 - x1 != shoulder_width or y2 - y1 != shoulder_height:
                top_resized = cv2.resize(top_resized, (x2 - x1, y2 - y1))
            
            # Overlay with alpha blending
            if top_resized.shape[2] == 4:  # Has alpha channel
                alpha = top_resized[:, :, 3] / 255.0
                for c in range(3):
                    frame[y1:y2, x1:x2, c] = (1 - alpha) * frame[y1:y2, x1:x2, c] + alpha * top_resized[:, :, c]
    
    # Overlay bottom clothing (pants)
    if bottom_img is not None:
        # Get hip landmarks
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Calculate position and size for bottom
        hip_width = int(abs(right_hip.x - left_hip.x) * w * 1.8)
        hip_height = int(hip_width * 1.5)
        
        center_x = int((left_hip.x + right_hip.x) * w / 2)
        center_y = int((left_hip.y + right_hip.y) * h / 2)
        
        # Resize and overlay bottom
        if hip_width > 0 and hip_height > 0:
            bottom_resized = cv2.resize(bottom_img, (hip_width, hip_height))
            
            # Calculate overlay position
            x1 = max(0, center_x - hip_width // 2)
            y1 = max(0, center_y)
            x2 = min(w, x1 + hip_width)
            y2 = min(h, y1 + hip_height)
            
            # Adjust resized image if needed
            if x2 - x1 != hip_width or y2 - y1 != hip_height:
                bottom_resized = cv2.resize(bottom_resized, (x2 - x1, y2 - y1))
            
            # Overlay with alpha blending
            if bottom_resized.shape[2] == 4:  # Has alpha channel
                alpha = bottom_resized[:, :, 3] / 255.0
                for c in range(3):
                    frame[y1:y2, x1:x2, c] = (1 - alpha) * frame[y1:y2, x1:x2, c] + alpha * bottom_resized[:, :, c]
    
    return frame

def gen_frames():
    """Generate video frames with clothing overlay"""
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process pose detection
        results = pose.process(rgb_frame)
        
        # Overlay clothing if pose is detected
        if results.pose_landmarks:
            frame = overlay_clothing(frame, results.pose_landmarks)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

top_img = load_clothing_image(top_type, "top")
bottom_img = load_clothing_image(bottom_type, "bottom")

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Virtual Try-On API is running!"}

@app.get("/video_feed")
def video_feed(
    top: Optional[str] = Query("shirt", description="Top clothing type"),
    bottom: Optional[str] = Query("pant", description="Bottom clothing type")
):
    """Video feed endpoint with dynamic clothing selection"""
    global top_type, bottom_type, top_img, bottom_img
    
    # Update clothing if changed
    if top != top_type:
        top_type = top
        top_img = load_clothing_image(top, "top")
        print(f"Changed top to: {top}")
    
    if bottom != bottom_type:
        bottom_type = bottom
        bottom_img = load_clothing_image(bottom, "bottom")
        print(f"Changed bottom to: {bottom}")
    
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/clothing-options")
def get_clothing_options():
    """Get available clothing options"""
    return {
        "tops": ["shirt", "fullsleeve", "tshirt", "hoodie"],
        "bottoms": ["pant", "skirt", "shorts", "jeans"]
    }

@app.get("/status")
def get_status():
    """Get current status"""
    return {
        "status": "running",
        "current_top": top_type,
        "current_bottom": bottom_type,
        "camera_connected": cap.isOpened()
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Virtual Try-On API...")
    print("Make sure to:")
    print("1. Install dependencies: pip install fastapi uvicorn opencv-python mediapipe numpy")
    print("2. Create ./database/ folder with clothing images (shirt.png, pant.png, etc.)")
    print("3. Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
