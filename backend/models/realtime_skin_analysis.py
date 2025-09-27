import cv2
import mediapipe as mp
import numpy as np
import math
import os
import base64
import json
import random
import requests
from groq import Groq
from dotenv import load_dotenv
import threading
import tkinter as tk
from PIL import Image, ImageTk

# ------------------- Load API Key -------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

grok_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ------------------- MediaPipe Setup -------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# Key regions for stable skin sampling
SKIN_POINTS = [33, 133, 362, 263, 1, 13, 10, 152, 234, 454]

# ------------------- Global Variables -------------------
run_mediapipe = False
run_groq = False
run_gemini = False
groq_result = None
gemini_result = None
stop_app = False
frame = None
frozen_display = None   # stores frozen analyzed frame
last_mediapipe_score = 5.0  # baseline for Groq

# ------------------- Helper Functions -------------------
def calculate_distance(p1, p2):
    return math.dist((p1[0], p1[1]), (p2[0], p2[1]))

def map_skin_tone(L, A, B):
    if L > 75:
        shade = "Fair"
    elif L > 60:
        shade = "Medium"
    elif L > 45:
        shade = "Tan"
    else:
        shade = "Deep"

    if A > 140 and B > 140:
        undertone = "Warm"
    elif A < 125 and B < 125:
        undertone = "Cool"
    else:
        undertone = "Neutral"

    return f"{shade}", undertone

def analyze_skin(frame, landmarks):
    h, w, _ = frame.shape
    skin_colors = []
    for idx in SKIN_POINTS:
        x, y = int(landmarks[idx][0]), int(landmarks[idx][1])
        if 0 <= x < w and 0 <= y < h:
            skin_colors.append(frame[y, x])

    if not skin_colors:
        return "Unknown", "Unknown"

    skin_colors = np.array(skin_colors, dtype=np.uint8)
    lab_colors = cv2.cvtColor(skin_colors.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB)
    L, A, B = np.mean(lab_colors.reshape(-1, 3), axis=0)
    return map_skin_tone(L, A, B)

def calculate_beauty(landmarks):
    global last_mediapipe_score
    face_height = calculate_distance(landmarks[10], landmarks[152])
    face_width = calculate_distance(landmarks[234], landmarks[454])
    eye_width = calculate_distance(landmarks[33], landmarks[263])
    nose_width = calculate_distance(landmarks[1], landmarks[5])
    lip_width = calculate_distance(landmarks[61], landmarks[291])

    ratios = {
        "Face Ratio": face_height / face_width if face_width else 0,
        "Eye Ratio": eye_width / face_width if face_width else 0,
        "Nose Ratio": nose_width / face_width if face_width else 0,
        "Lip Ratio": lip_width / face_width if face_width else 0,
    }

    ideal = {"Face Ratio": 1.6, "Eye Ratio": 0.46, "Nose Ratio": 0.3, "Lip Ratio": 0.4}
    score = 0
    for key in ratios:
        if ratios[key] > 0:
            score += min(ratios[key] / ideal[key], ideal[key] / ratios[key])
    score = score / len(ratios) * 10

    last_mediapipe_score = round(score, 1)  # Save baseline for Groq

    category = (
        "Perfect" if score > 8 else
        "Good" if score > 6 else
        "Average" if score > 4 else
        "Needs Improvement"
    )
    return round(score, 1), category

# ------------------- Groq Analysis -------------------
def analyze_groq_frame(snapshot):
    global groq_result, last_mediapipe_score
    if not grok_client:
        return

    try:
        _, buf = cv2.imencode('.jpg', cv2.cvtColor(snapshot, cv2.COLOR_BGR2RGB))
        img_b64 = base64.b64encode(buf).decode('utf-8')

        random_offset = round(random.uniform(-1.0, 1.0), 1)
        adjusted_score = max(0, min(10, last_mediapipe_score + random_offset))

        text_prompt = f"""
You are a professional dermatologist assistant.
Analyze the provided face image.

Guidelines:
- Skin tone/undertone must be realistic.
- Beauty score must be based on baseline {last_mediapipe_score} with adjusted {adjusted_score}.
- Add a one-line dermatologist remark.

Return ONLY JSON:
{{
  "skin_tone": "...",
  "undertone": "...",
  "beauty_score": {{"score": {adjusted_score}, "category": "..."}},
  "expert_comment": "..."
}}
"""

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": text_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}} 
            ]
        }]

        chat_completion = grok_client.chat.completions.create(
            messages=messages,
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=300
        )

        raw_text = chat_completion.choices[0].message.content.strip()
        json_start, json_end = raw_text.find("{"), raw_text.rfind("}")
        if json_start != -1 and json_end != -1:
            raw_text = raw_text[json_start:json_end+1]

        groq_result = json.loads(raw_text.replace("'", '"'))

    except Exception as e:
        groq_result = {"error": f"Groq API Error: {str(e)}"}

# ------------------- Gemini Analysis -------------------
# ------------------- Gemini Analysis -------------------
def analyze_gemini_frame(snapshot):
    global gemini_result, last_mediapipe_score
    if not GEMINI_API_KEY:
        return

    try:
        _, buf = cv2.imencode('.jpg', cv2.cvtColor(snapshot, cv2.COLOR_BGR2RGB))
        img_b64 = base64.b64encode(buf).decode("utf-8")

        random_offset = round(random.uniform(-1.0, 1.0), 1)
        adjusted_score = max(0, min(10, last_mediapipe_score + random_offset))

        prompt = f"""
You are a professional dermatologist assistant.
Analyze the face image.

Guidelines:
- Skin tone/undertone must be realistic.
- Beauty score must be based on baseline {last_mediapipe_score} with adjusted {adjusted_score}.
- Add a one-line dermatologist remark.

Return ONLY JSON:
{{
  "skin_tone": "Fair/Medium/Tan/Deep",
  "undertone": "Warm/Cool/Neutral",
  "beauty_score": {{"score": {adjusted_score}, "category": "..."}},
  "expert_comment": "..."
}}
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                ]
            }]
        }

        resp = requests.post(url, json=payload)
        resp.raise_for_status()

        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Extract JSON safely
        json_start, json_end = raw_text.find("{"), raw_text.rfind("}")
        if json_start != -1 and json_end != -1:
            raw_text = raw_text[json_start:json_end+1]

        gemini_result = json.loads(raw_text.replace("'", '"'))

    except Exception as e:
        gemini_result = {"error": f"Gemini API Error: {str(e)}"}

# ------------------- Tkinter GUI -------------------
root = tk.Tk()
root.title("Real-Time Skin Analysis")

video_label = tk.Label(root)
video_label.pack(padx=10, pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

button_style = {
    "fg": "white", "font": ("Helvetica", 12, "bold"),
    "padx": 12, "pady": 6, "relief": "raised", "borderwidth": 3
}

def start_mediapipe_callback():
    global run_mediapipe, run_groq, run_gemini, frozen_display, groq_result, gemini_result
    run_mediapipe, run_groq, run_gemini = True, False, False
    frozen_display, groq_result, gemini_result = None, None, None

def start_groq_callback():
    global run_mediapipe, run_groq, run_gemini, frozen_display, groq_result, gemini_result
    run_mediapipe, run_groq, run_gemini = False, True, False
    frozen_display, groq_result, gemini_result = None, None, None

def start_gemini_callback():
    global run_mediapipe, run_groq, run_gemini, frozen_display, groq_result, gemini_result
    run_mediapipe, run_groq, run_gemini = False, False, True
    frozen_display, groq_result, gemini_result = None, None, None

def quit_callback():
    global stop_app
    stop_app = True
    root.destroy()

# ✅ Buttons
tk.Button(btn_frame, text="Skin Analyze (MediaPipe)", command=start_mediapipe_callback, bg="#4CAF50", **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Skin Analyze (Groq AI)", command=start_groq_callback, bg="#2196F3", **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Skin Analyze (Gemini AI)", command=start_gemini_callback, bg="#9C27B0", **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Quit", command=quit_callback, bg="#f44336", **button_style).pack(side=tk.LEFT, padx=5)

# ------------------- OpenCV Capture -------------------
cap = cv2.VideoCapture(0)

frame_counter = 0

def update_frame():
    global frame, frozen_display, frame_counter
    ret, frame = cap.read()
    if not ret:
        return

    display_frame = frame.copy()

    # ✅ MediaPipe Live
    if run_mediapipe:
        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = [(lm.x * frame.shape[1], lm.y * frame.shape[0], lm.z * frame.shape[1])
                             for lm in face_landmarks.landmark]
                skin_tone, undertone = analyze_skin(frame, landmarks)
                score, category = calculate_beauty(landmarks)
                cv2.putText(display_frame, "[MediaPipe Live]", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
                cv2.putText(display_frame, f"Skin: {skin_tone}", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
                cv2.putText(display_frame, f"Undertone: {undertone}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
                cv2.putText(display_frame, f"Beauty: {score}/10 ({category})", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

    # ✅ Groq Live (every 20 frames)
    if run_groq:
        frame_counter += 1
        if frame_counter % 20 == 0:
            threading.Thread(target=analyze_groq_frame, args=(frame.copy(),), daemon=True).start()

        if groq_result:
            y = 20
            cv2.putText(display_frame, "[Groq Live]", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2); y += 25
            if "skin_tone" in groq_result:
                cv2.putText(display_frame, f"Skin Tone: {groq_result['skin_tone']}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2); y += 25
            if "undertone" in groq_result:
                cv2.putText(display_frame, f"Undertone: {groq_result['undertone']}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2); y += 25
            if "beauty_score" in groq_result:
                bs = groq_result["beauty_score"]
                cv2.putText(display_frame, f"Beauty: {bs['score']}/10 ({bs['category']})", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2); y += 25

    # ✅ Gemini Live (every 20 frames)
        # ✅ Gemini Live (every 20 frames)
    if run_gemini:
        frame_counter += 1
        if frame_counter % 20 == 0:
            threading.Thread(target=analyze_gemini_frame, args=(frame.copy(),), daemon=True).start()

        if gemini_result:
            y = 20
            cv2.putText(display_frame, "[Gemini Live]", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (156, 39, 176), 2); y += 25
            if "skin_tone" in gemini_result:
                cv2.putText(display_frame, f"Skin Tone: {gemini_result['skin_tone']}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (156, 39, 176), 2); y += 25
            if "undertone" in gemini_result:
                cv2.putText(display_frame, f"Undertone: {gemini_result['undertone']}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (156, 39, 176), 2); y += 25
            if "beauty_score" in gemini_result:
                bs = gemini_result["beauty_score"]
                cv2.putText(display_frame, f"Beauty: {bs['score']}/10 ({bs['category']})", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (156, 39, 176), 2); y += 25

    img = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    if not stop_app:
        video_label.after(10, update_frame)
    else:
        cap.release()

update_frame()
root.mainloop()
