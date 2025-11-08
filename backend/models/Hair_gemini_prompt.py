import os
import base64
import traceback
import logging
from io import BytesIO
from PIL import Image
from typing import Dict, Any
from google import genai
from google.genai import types

# ---------------------- Logging ---------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)

# ---------------------- Globals ---------------------- #
LANGUAGES = {
    "en": {
        "success_msg": "🎯 YOUR FACE PRESERVED, HAIR EDITED! ✨",
        "api_setup_success": "✅ AI System successfully set up! Gemini 2.0 Flash connection verified.",
        "api_setup_error": "❌ API Connection Error: {}\n\nPlease check your API key.",
        "enter_api_first": "Please enter your API key and start the system first.",
    },
    "tr": {
        "success_msg": "🎯 YÜZÜNÜZ KORUNARAK SAÇ EDİTLENDİ! ✨",
        "api_setup_success": "✅ AI Sistemi başarıyla kuruldu! Gemini bağlantısı doğrulandı.",
        "api_setup_error": "❌ API Bağlantı Hatası: {}\n\nLütfen API key'inizi kontrol edin.",
        "enter_api_first": "Lütfen önce API key'inizi girin ve sistemi başlatın.",
    },
}

# ---------------------- Utility Functions ---------------------- #
def pil_to_b64(img: Image.Image) -> str:
    """Convert a PIL image to base64 string."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def b64_to_pil(b64_str: str) -> Image.Image:
    """Convert base64 string to PIL image."""
    return Image.open(BytesIO(base64.b64decode(b64_str)))


# ---------------------- Core Gemini Agents ---------------------- #
class HairChangeAgent:
    def __init__(self, client: genai.Client):
        self.client = client

    def change_hair_style(
        self, original_image: Image.Image, hair_request: str, language: str = "en"
    ):
        """Generate a new hairstyle using Gemini Vision API."""
        prompt = f"""
        MODIFY ONLY THE HAIR: {hair_request}

        RULES:
        - Keep face, eyes, nose, mouth, skin exactly the same
        - Keep body, clothing, and background unchanged
        - Only change hair color/style naturally
        - Maintain natural texture and lighting

        {"Türkçe yanıtla." if language == "tr" else "Respond in English."}
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=[prompt, original_image],
                generation_config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    temperature=0.01,
                    top_p=0.3,
                    top_k=5,
                ),
            )

            result_image = None
            result_text = ""

            # Extract image + text parts from Gemini response
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text
                elif hasattr(part, "inline_data") and part.inline_data:
                    try:
                        result_image = Image.open(BytesIO(part.inline_data.data))
                    except Exception:
                        pass

            return result_image, result_text

        except Exception as e:
            logging.exception("Hair generation failed.")
            return None, f"❌ Hair transformation error: {str(e)}"


class HairEvaluationAgent:
    def __init__(self, client: genai.Client):
        self.client = client

    def evaluate_hair_match(
        self, original_image: Image.Image, new_image: Image.Image, hair_request: str, language: str = "en"
    ):
        """Ask Gemini to evaluate how well the hair style fits the face."""
        if language == "tr":
            prompt = f"""
            Bu iki fotoğrafı karşılaştır: orijinal vs "{hair_request}" sonrası.

            🎯 PUAN (1-10):
            • Yüz uyumu:
            • Renk uyumu:
            • Doğallık:
            • Genel görünüm:

            📝 Yorum:
            """
        else:
            prompt = f"""
            Compare original vs new hair: "{hair_request}"

            🎯 RATE (1-10):
            • Face compatibility:
            • Color harmony:
            • Naturalness:
            • Overall look:

            📝 COMMENT:
            """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt, original_image, new_image],
                generation_config=types.GenerateContentConfig(response_modalities=["TEXT"]),
            )
            candidate = response.candidates[0]
            text_parts = [
                part.text for part in candidate.content.parts if hasattr(part, "text") and part.text
            ]
            return "\n".join(text_parts)
        except Exception as e:
            logging.exception("Evaluation error.")
            return f"❌ Evaluation error: {str(e)}"


# ---------------------- Gemini System Controller ---------------------- #
class HairGeminiSystem:
    """High-level wrapper for Gemini-based hair editing."""

    def __init__(self):
        self.client: genai.Client | None = None
        self.hair_changer: HairChangeAgent | None = None
        self.hair_evaluator: HairEvaluationAgent | None = None
        self.language: str = "en"

    def setup(self, api_key: str) -> Dict[str, Any]:
        """Initialize and validate Gemini API client."""
        api_key = api_key.strip()
        if not api_key:
            return {"ok": False, "message": "API key missing."}

        try:
            client = genai.Client(api_key=api_key)
            # quick ping to validate
            client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents="Connection test OK.",
                generation_config=types.GenerateContentConfig(response_modalities=["TEXT"]),
            )

            self.client = client
            self.hair_changer = HairChangeAgent(client)
            self.hair_evaluator = HairEvaluationAgent(client)

            return {"ok": True, "message": LANGUAGES[self.language]["api_setup_success"]}
        except Exception as e:
            logging.exception("Gemini setup failed.")
            return {"ok": False, "message": LANGUAGES[self.language]["api_setup_error"].format(e)}

    def process_hair_change(self, image_bytes: bytes, message: str) -> Dict[str, Any]:
        """Main processing function: apply hair change + evaluate result."""
        if not self.hair_changer or not self.hair_evaluator:
            return {"ok": False, "error": LANGUAGES[self.language]["enter_api_first"]}

        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")

            result_img, result_text = self.hair_changer.change_hair_style(img, message, self.language)
            if result_img is None:
                return {"ok": False, "error": result_text}

            evaluation_text = self.hair_evaluator.evaluate_hair_match(img, result_img, message, self.language)
            combined_text = (
                f"{LANGUAGES[self.language]['success_msg']}\n\n"
                f"{result_text}\n\n---\n\n{evaluation_text}"
            )

            return {"ok": True, "image_base64": pil_to_b64(result_img), "text": combined_text}
        except Exception as e:
            logging.exception("process_hair_change failed.")
            return {"ok": False, "error": str(e)}

    def evaluate_hair_match(self, orig_bytes: bytes, new_bytes: bytes, message: str) -> Dict[str, Any]:
        """Compare original and new hair image quality."""
        if not self.hair_evaluator:
            return {"ok": False, "error": LANGUAGES[self.language]["enter_api_first"]}

        try:
            orig = Image.open(BytesIO(orig_bytes)).convert("RGB")
            new = Image.open(BytesIO(new_bytes)).convert("RGB")
            evaluation = self.hair_evaluator.evaluate_hair_match(orig, new, message, self.language)
            return {"ok": True, "evaluation": evaluation}
        except Exception as e:
            logging.exception("evaluate_hair_match failed.")
            return {"ok": False, "error": str(e)}
