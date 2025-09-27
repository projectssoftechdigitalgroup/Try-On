import cv2
import mediapipe as mp
import numpy as np
import random
import tempfile
import os
import base64
import json

from groq import Groq
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
 
grok_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

mp_face_mesh = mp.solutions.face_mesh
SKIN_POINTS = [33, 133, 362, 263, 1, 13]  # forehead, cheeks, chin


# --- Helper: consistent skin tone mapping ---
def map_skin_tone(L, A, B):
    if L > 75:
        shade = "Fair"
    elif L > 60:
        shade = "Medium"
    elif L > 45:
        shade = "Tan"
    else:
        shade = "Deep"

    if A > 135 and B > 135:
        undertone = "Warm"
    elif A < 130 and B < 130:
        undertone = "Cool"
    else:
        undertone = "Neutral"

    return f"{shade} skin tone with {undertone} undertone"


# ---------- (1) MediaPipe ----------
def analyze_with_mediapipe(image_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_file.read())
        tmp_path = tmp.name

    image = cv2.imread(tmp_path)
    if image is None:
        return {"error": "Invalid image"}

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
    results = face_mesh.process(rgb_image)

    if not results.multi_face_landmarks:
        return {"error": "No face detected"}

    h, w, _ = image.shape
    skin_colors = []
    for face_landmarks in results.multi_face_landmarks:
        for idx in SKIN_POINTS:
            x, y = int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)
            if 0 <= x < w and 0 <= y < h:
                skin_colors.append(rgb_image[y, x])

    if not skin_colors:
        return {"error": "Could not sample skin"}

    skin_colors = np.array(skin_colors, dtype=np.uint8)
    lab_colors = cv2.cvtColor(skin_colors.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB)
    avg_lab = np.mean(lab_colors.reshape(-1, 3), axis=0)
    L, A, B = avg_lab

    skin_tone = map_skin_tone(L, A, B)

    ratings = {
        "Skin Smoothness": random.randint(6, 10),
        "Facial Symmetry": random.randint(5, 9),
        "Eyes": random.randint(6, 10),
        "Lips": random.randint(6, 10),
        "Nose": random.randint(5, 9),
    }
    beauty_score = round(sum(ratings.values()) / len(ratings), 1)

    remarks = "Well-balanced natural features with a healthy glow."

    return {
        "skin_tone": skin_tone,
        "ratings": ratings,
        "beauty_score": beauty_score,
        "remarks": remarks,
    }


# ---------- (2) Groq Vision ----------
def analyze_with_groq(image_file):
    try:
        img_bytes = image_file.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        client = Groq(api_key=GROQ_API_KEY)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are a skincare AI. Analyze this face photo and return ONLY valid JSON with these fields:\n"
                            "{\n"
                            "  'skin_tone': 'Fair/Medium/Tan/Deep',\n"
                            "  'undertone': 'Warm/Cool/Neutral',\n"
                            "  'remarks': 'short comment about skin',\n"
                            "  'suggestions': ['tip1', 'tip2']\n"
                            "}"
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    }
                ],
            }
        ]

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        )

        raw_text = chat_completion.choices[0].message.content

        try:
            data = json.loads(raw_text.replace("'", "\""))
        except:
            data = {"remarks": raw_text}

        return data

    except Exception as e:
        return {"error": f"Groq error: {str(e)}"}


# ---------- (3) Gemini Vision ----------
import requests

def analyze_with_gemini(image_file):
    try:
        img_bytes = image_file.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        prompt = (
            "You are a skincare AI. Analyze this face photo and return ONLY valid JSON with fields:\n"
            "{\n"
            "  'skin_tone': 'Fair/Medium/Tan/Deep',\n"
            "  'undertone': 'Warm/Cool/Neutral',\n"
            "  'remarks': 'short skincare comment',\n"
            "  'suggestions': ['tip1','tip2']\n"
            "}"
        )

        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                ]
            }]
        }

        resp = requests.post(API_URL, json=payload)
        resp.raise_for_status()

        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

        try:
            return json.loads(raw_text)
        except:
            return {"remarks": raw_text}

    except Exception as e:
        return {"error": f"Gemini REST error: {str(e)}"}



# ---------- Main Switch ----------
def detect_tone(image_file, method="mediapipe"):
    try:
        if method == "mediapipe":
            return analyze_with_mediapipe(image_file)
        elif method == "groq":
            return analyze_with_groq(image_file)
        elif method == "gemini":
            return analyze_with_gemini(image_file)
        else:
            return {"error": "Invalid method. Use 'mediapipe', 'groq', or 'gemini'."}
    except Exception as e:
        return {"error": str(e)} 
 