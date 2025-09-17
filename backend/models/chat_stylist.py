from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
from PIL import Image
import requests
from io import BytesIO

router = APIRouter()
client = Groq()

# -----------------------------
# Pydantic Models
# -----------------------------
class UserInput(BaseModel):
    message: str
    conversation_id: str
    role: str = "user"
    image_url: Optional[str] = None  # Optional image reference

# -----------------------------
# Conversation Management
# -----------------------------
class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are an expert AI stylist 👗. "
                    "You give personalized makeup, hair, and fashion advice. "
                    "Always consider skin tone, undertone, face shape, and uploaded images. "
                    "Be friendly, concise, and suggest suitable colors, styles, and tips."
                )
            }
        ]
        self.active = True

conversations: Dict[str, Conversation] = {}

def get_or_create_conversation(conversation_id: str) -> Conversation:
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation()
    return conversations[conversation_id]

# -----------------------------
# Image Analysis Function
# -----------------------------
def analyze_skin(image_url: str) -> str:
    """
    Analyze the user's skin from the image.
    Returns a text summary for the AI.
    """
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        # --- Placeholder analysis ---
        # Replace this with a real model for skin tone, undertone, spots, etc.
        # Example dummy output:
        skin_summary = "Skin Tone: Medium, Undertone: Warm"
        return skin_summary
    except Exception as e:
        return f"Could not analyze image: {e}"

# -----------------------------
# Groq API Query
# -----------------------------
def query_groq_api(conversation: Conversation) -> str:
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=conversation.messages,
            temperature=0.7,
            max_tokens=512,
            top_p=1,
            stream=True,
        )

        response = ""
        for chunk in completion:
            choice = chunk.choices[0]
            if hasattr(choice, "delta") and getattr(choice.delta, "content", None):
                response += choice.delta.content
            elif hasattr(choice, "message") and getattr(choice.message, "content", None):
                response += choice.message.content

        return response.strip() or "❌ No response received."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")

# -----------------------------
# Chat Endpoint
# -----------------------------
@router.post("/chat/groq/")
async def chat_with_groq(input: UserInput):
    conversation = get_or_create_conversation(input.conversation_id)

    if not conversation.active:
        raise HTTPException(status_code=400, detail="Chat ended. Start a new session.")

    # Build the user message
    message_content = input.message

    # If image is provided, analyze skin and include summary
    if input.image_url:
        skin_info = analyze_skin(input.image_url)
        message_content += f" [User image analyzed: {skin_info}]"

    # Append user's message
    conversation.messages.append({"role": input.role, "content": message_content})

    # Get AI response
    response = query_groq_api(conversation)

    # Append AI response
    conversation.messages.append({"role": "assistant", "content": response})

    return {"reply": response, "conversation_id": input.conversation_id}
