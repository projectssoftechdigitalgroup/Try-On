# makeup_models.py
from models import skin_tone_analysis

def get_makeup_suggestions_from_image(image_file):
    """
    Analyze skin from the uploaded image and return recommended makeup 
    (lipstick, eyeshadow, blush, foundation, highlighter) based on skin tone.
    """
    # Step 1: Analyze skin using MediaPipe
    analysis = skin_tone_analysis.analyze_with_mediapipe(image_file)

    if not analysis or "error" in analysis:
        return {"error": analysis.get("error", "Failed to analyze skin.")}

    skin_tone = analysis.get("skin_tone", "")

    # Step 2: Return makeup recommendations based on skin tone
    if "Fair" in skin_tone:
        suggestions = {
            "Lipstick": ["Soft Pink", "Peach", "Coral"],
            "Eyeshadow": ["Champagne", "Soft Brown", "Rose Gold"],
            "Blush": ["Peach", "Light Pink"],
            "Foundation": ["Light Shade"],
            "Highlighter": ["Pearl", "Ivory"]
        }
    elif "Medium" in skin_tone or "Tan" in skin_tone:
        suggestions = {
            "Lipstick": ["Berry", "Rose", "Warm Red"],
            "Eyeshadow": ["Gold", "Bronze", "Warm Brown"],
            "Blush": ["Coral", "Rose"],
            "Foundation": ["Medium Shade"],
            "Highlighter": ["Champagne", "Golden"]
        }
    elif "Deep" in skin_tone or "Dark" in skin_tone:
        suggestions = {
            "Lipstick": ["Plum", "Burgundy", "Rich Red"],
            "Eyeshadow": ["Copper", "Deep Bronze", "Dark Brown"],
            "Blush": ["Deep Rose", "Berry"],
            "Foundation": ["Deep Shade"],
            "Highlighter": ["Golden", "Bronze"]
        }
    else:
        suggestions = {
            "Lipstick": ["Neutral Shades"],
            "Eyeshadow": ["Neutral Shades"],
            "Blush": ["Neutral Shades"],
            "Foundation": ["Neutral Shades"],
            "Highlighter": ["Neutral Shades"]
        }

    # Return combined result
    return {
        "skin_analysis": analysis,
        "makeup_recommendations": suggestions
    }
