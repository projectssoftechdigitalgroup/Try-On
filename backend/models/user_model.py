def get_response(user_message):
    if "lipstick" in user_message.lower():
        return "Red lipstick will suit your skin tone! 💄"
    elif "foundation" in user_message.lower():
        return "Try a warm beige foundation for natural coverage."
    else:
        return "I recommend keeping your look natural with light makeup."
