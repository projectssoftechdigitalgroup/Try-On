**Virtual Try-On Application**

**Introduction:** 

The Virtual Try-On application is an intelligent beauty, fashion, and accessories try-on platform that allows users to experiment with different looks instantly, using either a live webcam feed or uploaded images.
It is designed to help users make better style decisions by visualizing how various products such as makeup, jewellery, hairstyles, caps, glasses, clothes, and wrist accessories would appear on them.

This system integrates AI-based facial landmark detection, segmentation, real-time AR overlays, and Generative AI models (Gemini, Groq, Mediapipe) to ensure realistic placement, matching skin tones, blending textures, and providing personalized style recommendations.

The project is ideal for:

- Makeup Artists
- Skincare / Cosmetic Brands
- Jewellery & Fashion Stores
- Virtual Try-On E-commerce Platforms
- User Personal Styling / Self Grooming

✨ **Features**

**1) Face Try-On**

  The Face Try-On Module allows users to virtually try multiple facial appearance transformations.
 Image Input Options:
<img width="1300" height="274" alt="image" src="https://github.com/user-attachments/assets/c8f5f6e6-5c62-4ce7-983c-d66564748fe8" />

🧴 **Skin Analysis**

Analyze the user's skin tone using three different AI models:

- Mediapipe
- Gemini
- Groq

**Output Includes:**

- Skin tone classification
- Personalized beauty remarks
- Recommended cosmetic product range

💄 **Makeup Try-On**

Try virtual lipstick, foundation, eyeshadow, blush, and highlighter.

- Makeup Recommendations Generated Automatically:
- Try-On Modes:

- **Mode	Description:**

      - Manual / AI Try-On Select makeup shades manually or allow AI to apply the best tones.
      - Template / Occasion-Based Try-On	Wedding, Party, Casual, Festival Looks ready in one click.


💍 **Jewellery Try-On**

Overlay earrings, nose pins, necklaces, mang tikka, bindis and more.

- **Mode	Description**
  
      - Manual Placement	Select jewellery and apply visually.
      - Prompt-Based Try-On	Describe your jewellery style and AI will apply it.


🧢 **Cap / 🕶️ Glasses Try-On**

Try accessories including caps, hats, sunglasses, goggles.

**Includes:**

- Automatic face landmark detection
- Accessory scale + rotation adjustment
- Style suggestions based on face shape

🧔 **Moustache / Beard Try-On**

Test different moustache and beard styles with realistic blending.


💇 **Hair Try-On**

Experiment with hair color, length, and styles.

**Hair Try-On Modes:**

        - ✨ Simple Try-On	Quick preview using predefined hairstyle overlays.
        - 🧠 Gemini AI Model	AI-based blending for realistic integration.
        - 💬 Gemini Prompt-Based Hair Styling	Describe the hairstyle and AI adjusts it with feedback on realism & suitability.

🤖 **Chat with Stylist**

AI-powered personal fashion assistant using Groq:

- Styling suggestions
- Product recommendations
- Face-shape-based guidance

**2) Wrist Try-On**

Try watches, bracelets, and bangles instantly.

**Wrist Try-On Modes:**

- Manual Placement	Select watch and apply visually.
- Realtime-Based Try-On	select your watch style and AI will apply it using AR.
  
**Features:**

- Hand/wrist detection
- adjustment
- Material shine & reflection preservation

**3) Clothes Try-On**

The Clothes Try-On module allows users to try outfits in real-time using their live camera feed. Clothing auto-adjusts to body position, posture, and movement — giving a highly immersive try-on experience.

🎥 **Virtual Try-On Studio**

Once the camera is active, the user enters the Virtual Try-On Studio, which includes:

**UI Element	Description**
- Connected / Disconnected Status	Indicates backend availability for smooth real-time try-on.
- Live Camera Feed	Streams your camera feed in real-time.
- Clothing Overlay System	Selected clothes appear directly on your body.
- Instant Preview	No delays — see the outfit as you move naturally.

**A glowing message like:**

- ✨ Ready to see your look?
- lets the user know everything is functioning smoothly.

 **Your Selection Panel**

This panel shows your current outfit choice:

- Top	👕 Shirt / Hoodie / T-shirt
- Bottom	👖 Jeans / Pants / Skirt
- Dress	👗 One-piece outfits 

The user can change any piece instantly.
No refresh. No re-upload. No lag.

**Choose Your Outfit — Outfit Selector**

The clothing selector offers multiple categories to match personal preferences and cultural wear styles.

**Category	Description**

- Male	Shirts, Hoodies, Pants, Jackets, etc.
- Female	Blouses, Kurtis, Jeans, Tops, Dresses
- Kids	Cute outfits & child-friendly styles
  
- Eastern 🌸	Shalwar Kameez, Kurti, Dupatta styles
- Traditional 💃	Cultural wear, party wear & special-occasion attire
  
- Tops	Shirts, Tees, Hoodies
- Bottoms	Jeans, Trousers, Skirts
  
- Full Dress	Complete outfit sets

Note : **Users can scroll, preview, and instantly apply clothing — all in real time.**

**Real-Time Smart Fitting**

The system:

- Detects body & shoulder alignment
- Warps clothing automatically to match pose
- Supports movement without jittering
- Works across different body proportions

'




-------------------------------------x------------------------------------------------x--------------------------------------------------




 **Technology Used**
 

- **AI Processing** 
    - Mediapipe Library
    - Gemini Model
    - Groq API
    - SMPL Model
      
- **AR & Effects**
    - OpenCV
    - Image Masking
    - Face Landmarks
      
- **Backend**
    - Python (FastAPI)
      
- **Frontend**
    - React.js
    - Tailwind CSS
      
- **Real-Time Capture**
    - Browser Camera /Web Cam
      
- 🚀 **Getting Started**
  
🧰 **Prerequisites**

Before installing and running the project, ensure the following tools and libraries are installed on your system:

- **System Requirements**

  - Python	3.9 or above
  - React.js	Frontend framework
  - Git	To clone the repository
 
- **Python Libraries**

Ensure these core AI / CV libraries are installed (they will be auto-installed if using requirements.txt):

**Library	Purpose**

- Mediapipe	Facial landmarks, hand tracking, segmentation
- OpenCV	Image processing and overlay rendering
- NumPy	Computational operations and matrix handling
- Pillow (PIL)	Image handling and editing
- FastAPI Backend framework


**AI Integration Requirements**
  
- **Model / API	Used**

- Google Gemini AI	Hair Try-On, Skin Tone Remarks, Prompt Styling	Requires Gemini API Key
- Groq AI	Fast AI Chat / Stylist Chat	Requires Groq API Key
- Mediapipe Built-In Models	Facial + Hand Landmark Detection	No key required

  
**API Keys Required**

Create and configure keys in your .env file:

              - GEMINI_API_KEY=your_key_here
              - GROQ_API_KEY=your_key_here

- **Installation**
  
           - git clone https://github.com/projectssoftechdigitalgroup/Try-On.git
           - cd Try-On

**Backend Setup:**

          - cd backend
          - uvicorn app.main:app --reload

**Frontend Setup:**

          - cd tryon-frontend
          - npm start

**Access Frotend Application on :**

          - http://localhost:3000/
          
**Access Backend Application on :**

          - http://127.0.0.1:8000/docs
          
## 📌 About

This project is developed by **SofTech Digital Group**, with the mission to revolutionize
personal styling and AI-based beauty technology by enabling real-time and image-based virtual try-on.

### 👨‍💻 Project Contributors

<img width="719" height="175" alt="image" src="https://github.com/user-attachments/assets/afc1fe58-3ccc-4a5c-b5c0-38fd7450a482" />



