// src/realtime_cap_glasses.js
import React, { useEffect, useRef, useState } from "react";
import "./realtime_cap_glasses.css";

const categories = {
  Caps: [
    { label: "Grey Cap", img: process.env.PUBLIC_URL + "/caps_hats/caps/cap_1.png", type: "cap", filename: "cap_1.png" },
    { label: "Red Cap", img: process.env.PUBLIC_URL + "/caps_hats/caps/cap_2.png", type: "cap", filename: "cap_2.png" },
    { label: "Visor Cap", img: process.env.PUBLIC_URL + "/caps_hats/caps/cap_3.png", type: "cap", filename: "cap_3.png" },
  ],
  Hats: [
    { label: "Blue Ribbon Hat", img: process.env.PUBLIC_URL + "/caps_hats/hats/hat_1.png", type: "hat", filename: "hat_1.png" },
    { label: "Wide-Brim Sun Hat", img: process.env.PUBLIC_URL + "/caps_hats/hats/hat_2.png", type: "hat", filename: "hat_2.png" },
    { label: "Cricket Hat", img: process.env.PUBLIC_URL + "/caps_hats/hats/hat_3.png", type: "hat", filename: "hat_3.png" },
  ],
  Glasses: [
    { label: "Heart Sun Glasses", img: process.env.PUBLIC_URL + "/caps_hats/glasses/glasses_1.png", type: "glasses", filename: "glasses_1.png" },
    { label: "Black Round Dashing Glasses", img: process.env.PUBLIC_URL + "/caps_hats/glasses/glasses_2.png", type: "glasses", filename: "glasses_2.png" },
    { label: "Colorful Beach Glasses", img: process.env.PUBLIC_URL + "/caps_hats/glasses/glasses_3.png", type: "glasses", filename: "glasses_3.png" },
    { label: "Eye Sight Aviator Glasses", img: process.env.PUBLIC_URL + "/caps_hats/glasses/glasses_4.png", type: "glasses", filename: "glasses_4.png" },
    { label: "Eye Sight Round Glasses", img: process.env.PUBLIC_URL + "/caps_hats/glasses/glasses_5.png", type: "glasses", filename: "glasses_5.png" },
  ],
};

export default function RealtimeCapGlasses({ goBackHome }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [frameSrc, setFrameSrc] = useState(null); // stores backend frame

  // Start webcam
  useEffect(() => {
    async function initCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Camera error:", err);
      }
    }
    initCamera();
  }, []);

  // Fetch processed frame periodically
  useEffect(() => {
    if (!selectedItem) return;

    const interval = setInterval(async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const frameDataUrl = canvas.toDataURL("image/jpeg");
      const blob = await (await fetch(frameDataUrl)).blob();

      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");
      formData.append("accessory", selectedItem.type);
      formData.append("filename", selectedItem.filename);

      try {
        const res = await fetch("http://localhost:8000/process-capglasses/", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        if (data.frame) {
          setFrameSrc(data.frame); // ✅ trigger smooth transition
        }
      } catch (err) {
        console.error("Overlay error:", err);
      }
    }, 400);

    return () => clearInterval(interval);
  }, [selectedItem]);

  const resetSelection = () => {
    setSelectedItem(null);
    setFrameSrc(null);
  };

  return (
    <div className="rcg-container">
      <h2 className="rcg-title">🎩 Realtime Cap, Hat & Glasses Try-On</h2>

      {goBackHome && (
        <button className="rcg-back-btn" onClick={goBackHome}>
          ⬅ Back
        </button>
      )}

      {/* Categories */}
      {!selectedCategory && (
        <div className="rcg-categories">
          {Object.keys(categories).map((cat) => (
            <div
              key={cat}
              className="rcg-category-card"
              onClick={() => setSelectedCategory(cat)}
            >
              <h3>{cat}</h3>
            </div>
          ))}
        </div>
      )}

      {/* Items in category */}
      {selectedCategory && !selectedItem && (
        <div>
          <button
            className="rcg-back-btn"
            onClick={() => {
              setSelectedCategory(null);
              resetSelection();
            }}
          >
            ← Back to Categories
          </button>

          <h3 className="rcg-title">{selectedCategory}</h3>
          <div className="rcg-options">
            {categories[selectedCategory].map((item, idx) => (
              <div
                key={idx}
                className={`rcg-card ${selectedItem?.filename === item.filename ? "active" : ""}`}
                onClick={() => setSelectedItem(item)}
              >
                <img src={item.img} alt={item.label} />
                <p>{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ✅ Single smooth result view */}
      <div className="rcg-video-container">
        <video ref={videoRef} className="hidden" width="640" height="480" autoPlay playsInline />
        <canvas ref={canvasRef} style={{ display: "none" }} width="640" height="480" />

        {frameSrc && (
          <img
            key={frameSrc}
            src={frameSrc}
            alt="Try-On Result"
            className="rcg-video fade-frame"
            width="640"
            height="480"
          />
        )}
      </div>

      {selectedItem && (
        <div className="mt-4 flex gap-4 justify-center">
          <button
            className="px-4 py-2 bg-green-500 text-white rounded shadow hover:scale-105 transition"
            onClick={resetSelection}
          >
            🔄 Try Another
          </button>
          <button
            className="px-4 py-2 bg-gray-300 rounded shadow hover:scale-105 transition"
            onClick={() => {
              setSelectedCategory(null);
              resetSelection();
            }}
          >
            ⬅ Back to Categories
          </button>
        </div>
      )}
    </div>
  );
}
