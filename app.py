from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import cv2
import numpy as np
import mediapipe as mp
from werkzeug.utils import secure_filename
import time

# Initialize Flask app
app = Flask(__name__)

# Set up a path for static content (uploaded files)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Setup MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class VirtualWatchTryOn:
    def __init__(self, wrist_image, watch_image):
        self.wrist_image = wrist_image
        self.watch_image = watch_image  # Load selected watch image
        self.width = self.wrist_image.shape[1]
        self.height = self.wrist_image.shape[0]

        # Resize the watch image dynamically
        self.watch_image = cv2.resize(self.watch_image, (self.width // 3, self.height // 3))
        self.watch_width = self.watch_image.shape[1]
        self.watch_height = self.watch_image.shape[0]

        # Initialize MediaPipe Hands
        self.hands = mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def estimate_wrist_pose(self, hand_landmarks, image_shape):
        wrist = hand_landmarks.landmark[0]
        h, w = image_shape[:2]
        x_pixel = int(wrist.x * w)
        y_pixel = int(wrist.y * h)
        return x_pixel, y_pixel

    def get_hand_direction(self, hand_landmarks, image_shape):
        """Calculate hand direction to determine backward offset"""
        h, w = image_shape[:2]
        
        # Get key landmarks
        wrist = hand_landmarks.landmark[0]  # Wrist
        middle_mcp = hand_landmarks.landmark[9]  # Middle finger MCP joint
        
        # Convert to pixel coordinates
        wrist_x = wrist.x * w
        wrist_y = wrist.y * h
        middle_x = middle_mcp.x * w
        middle_y = middle_mcp.y * h
        
        # Calculate direction vector from wrist to middle finger
        direction_x = middle_x - wrist_x
        direction_y = middle_y - wrist_y
        
        # Normalize the direction vector
        magnitude = np.sqrt(direction_x**2 + direction_y**2)
        if magnitude > 0:
            direction_x /= magnitude
            direction_y /= magnitude
        
        return direction_x, direction_y

    def process_image(self):
        rgb_frame = cv2.cvtColor(self.wrist_image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                wrist_x, wrist_y = self.estimate_wrist_pose(hand_landmarks, self.wrist_image.shape)
                direction_x, direction_y = self.get_hand_direction(hand_landmarks, self.wrist_image.shape)
                self.overlay_watch_on_wrist(self.wrist_image, wrist_x, wrist_y, direction_x, direction_y)
        
        return self.wrist_image

    def overlay_watch_on_wrist(self, image, wrist_x, wrist_y, direction_x=0, direction_y=0):
        # Calculate backward offset based on hand direction
        # The watch should be positioned backward (opposite to finger direction)
        backward_offset = 30  # Adjust this value to control how far back the watch sits
        
        # Apply backward offset opposite to the hand direction
        offset_x = -direction_x * backward_offset
        offset_y = -direction_y * backward_offset
        
        # Calculate watch position with backward offset
        top_left_x = int(wrist_x - self.watch_width // 2 + offset_x)
        top_left_y = int(wrist_y - self.watch_height // 2 + offset_y)
        
        # Ensure the watch stays within image boundaries
        if top_left_x < 0: top_left_x = 0
        if top_left_y < 0: top_left_y = 0
        if top_left_x + self.watch_width > self.width: top_left_x = self.width - self.watch_width
        if top_left_y + self.watch_height > self.height: top_left_y = self.height - self.watch_height

        # Handle alpha channel if present (for PNG images with transparency)
        if len(self.watch_image.shape) == 3 and self.watch_image.shape[2] == 4:
            alpha_channel = self.watch_image[:, :, 3] / 255.0
            watch_rgb = self.watch_image[:, :, :3]
        else:
            alpha_channel = np.ones(self.watch_image.shape[:2], dtype=np.float32)
            watch_rgb = self.watch_image

        # Apply alpha blending for smooth overlay
        for c in range(0, 3):
            image[top_left_y:top_left_y+self.watch_height, top_left_x:top_left_x+self.watch_width, c] = \
                (alpha_channel * watch_rgb[:, :, c] + (1 - alpha_channel) * image[top_left_y:top_left_y+self.watch_height, top_left_x:top_left_x+self.watch_width, c])

@app.route('/', methods=['GET'])
def index():
    # Watch images to display
    watch_files = ['watch1.png', 'watch2.png', 'watch3.png']
    return render_template('index.html', watch_files=watch_files)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'wrist_image' not in request.files or 'watch_choice' not in request.form:
        return jsonify({'error': 'Missing wrist image or watch choice'}), 400

    wrist_file = request.files['wrist_image']
    watch_choice = request.form['watch_choice']
    
    # Map watch choice to watch file
    watch_image_path = os.path.join(app.config['UPLOAD_FOLDER'], watch_choice)
    if not os.path.exists(watch_image_path):
        return jsonify({'error': 'Invalid watch choice'}), 400

    watch_image = cv2.imread(watch_image_path, cv2.IMREAD_UNCHANGED)

    # Save and load the wrist image
    wrist_image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(wrist_file.filename))
    wrist_file.save(wrist_image_path)
    wrist_image = cv2.imread(wrist_image_path)

    # Process the image
    try:
        virtual_tryon = VirtualWatchTryOn(wrist_image, watch_image)
        result_image = virtual_tryon.process_image()
        
        # Save result image with unique filename using timestamp
        timestamp = int(time.time())  # Use timestamp to create unique file name
        result_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{timestamp}.png')
        cv2.imwrite(result_image_path, result_image)
        
        # Return the path to the result image
        result_image_url = f"/static/{os.path.basename(result_image_path)}"
        return jsonify({'result_image': result_image_url}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/take_picture/<watch_choice>', methods=['GET'])
def take_picture(watch_choice):
    return render_template('take_picture.html', watch_choice=watch_choice)

if __name__ == '__main__':
    # Ensure the 'uploads' folder exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    # Log the URL of the app
    print(f"App is running at http://127.0.0.1:5000/")
    
    app.run(debug=True)