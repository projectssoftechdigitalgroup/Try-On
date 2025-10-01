"""
Update your FastAPI backend to support dynamic clothing selection.
Add this to your main.py file to handle clothing selection from the frontend.
"""

# Add these imports to your main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from typing import Optional

# Add CORS middleware after creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update your video_feed endpoint to accept clothing parameters
@app.get("/video_feed")
def video_feed(
    top: Optional[str] = Query("shirt", description="Top clothing type"),
    bottom: Optional[str] = Query("pant", description="Bottom clothing type")
):
    # Update global variables based on query parameters
    global top_type, bottom_type, top_img, bottom_img
    
    if top != top_type:
        top_type = top
        top_path = f"./database/{top}.png"
        top_img = cv2.imread(top_path, cv2.IMREAD_UNCHANGED)
        if top_img is None:
            print(f"Warning: Could not load {top_path}")
    
    if bottom != bottom_type:
        bottom_type = bottom
        bottom_path = f"./database/{bottom}.png"
        bottom_img = cv2.imread(bottom_path, cv2.IMREAD_UNCHANGED)
        if bottom_img is None:
            print(f"Warning: Could not load {bottom_path}")
    
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# Add an endpoint to get available clothing options
@app.get("/clothing-options")
def get_clothing_options():
    return {
        "tops": ["shirt", "fullsleeve"],
        "bottoms": ["pant", "skirt"]
    }

print("Backend updated! Make sure to:")
print("1. Install fastapi[all]: pip install fastapi[all]")
print("2. Add clothing images to ./database/ folder")
print("3. Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
