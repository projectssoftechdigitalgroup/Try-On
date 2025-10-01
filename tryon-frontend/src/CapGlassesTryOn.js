import React, { useState } from "react";
import "./CapGlassesTryOn.css";

const API_BASE = "http://127.0.0.1:8000";

const categories = {
  Caps: [
    { label: "Grey Cap", img: "/caps_hats/caps/cap_1.png", type: "cap", filename: "cap_1.png" },
    { label: "Red Cap", img: "/caps_hats/caps/cap_2.png", type: "cap", filename: "cap_2.png" },
    { label: "Visor Cap", img: "/caps_hats/caps/cap_3.png", type: "cap", filename: "cap_3.png" },
  ],
  Hats: [
    { label: "Blue Ribbon Hat", img: "/caps_hats/hats/hat_1.png", type: "hat", filename: "hat_1.png" },
    { label: "Wide-Brim Sun Hat", img: "/caps_hats/hats/hat_2.png", type: "hat", filename: "hat_2.png" },
    { label: "Cricket Hat", img: "/caps_hats/hats/hat_3.png", type: "hat", filename: "hat_3.png" },
  ],
  Glasses: [
    { label: "Heart Sun Glasses", img: "/caps_hats/glasses/glasses_1.png", type: "glasses", filename: "glasses_1.png" },
    { label: "Black Round Dashing Glasses", img: "/caps_hats/glasses/glasses_2.png", type: "glasses", filename: "glasses_2.png" },
    { label: "Colorful Beach Dashing Glasses", img: "/caps_hats/glasses/glasses_3.png", type: "glasses", filename: "glasses_3.png" },
    { label: "Eye Sight Aviator Glasses", img: "/caps_hats/glasses/glasses_4.png", type: "glasses", filename: "glasses_4.png" },
    { label: "Eye Sight Round Glasses", img: "/caps_hats/glasses/glasses_5.png", type: "glasses", filename: "glasses_5.png" },
  ],
};

export default function CapGlassesTryOn({ uploadedImage, goBackHome }) {
  const [recommendation, setRecommendation] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [tryOnImage, setTryOnImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const _ensureFile = async (img) => {
    if (!img) return null;
    if (img instanceof File) return img;

    const url = img.startsWith("/") ? API_BASE + img : img;
    try {
      const resp = await fetch(url);
      const blob = await resp.blob();
      return new File([blob], "photo.jpg", { type: blob.type || "image/jpeg" });
    } catch {
      return null;
    }
  };

  const analyzeFace = async () => {
    if (!uploadedImage) return;
    setLoading(true);
    setRecommendation(null);
    setTryOnImage(null);

    try {
      const fileToSend = await _ensureFile(uploadedImage);
      if (!fileToSend) return;

      const formData = new FormData();
      formData.append("file", fileToSend);

      const res = await fetch(`${API_BASE}/capglasses-tryon/`, { method: "POST", body: formData });
      const data = await res.json();

      setRecommendation({
        shape: data.face_shape || "Unknown",
        items: data.recommendations ? Object.values(data.recommendations).filter(Boolean) : ["No recommendation available."],
      });

      if (data.outputs?.tryon) {
        const path = data.outputs.tryon.startsWith("/") ? data.outputs.tryon : "/" + data.outputs.tryon;
        const url = `${API_BASE}${path}`;
        console.log("✅ Fixed Try-On URL:", url);
        setTryOnImage(url);
      }
    } catch {
      setRecommendation({ shape: "Unknown", items: ["⚠️ Could not detect face."] });
    } finally {
      setLoading(false);
    }
  };

  const tryOnItem = async (item) => {
    setSelectedItem(item.label);
    setLoading(true);
    try {
      const fileToSend = await _ensureFile(uploadedImage);
      if (!fileToSend) return;

      const formData = new FormData();
      formData.append("file", fileToSend);
      formData.append("accessory", item.type);
      formData.append("filename", item.filename);

      const res = await fetch(`${API_BASE}/capglasses-tryon/`, { method: "POST", body: formData });
      const data = await res.json();

      if (data.outputs?.tryon) {
        const path = data.outputs.tryon.startsWith("/") ? data.outputs.tryon : "/" + data.outputs.tryon;
        const url = `${API_BASE}${path}`;
        console.log("✅ Fixed Try-On URL:", url);
        setTryOnImage(url);
      } else {
        setTryOnImage(item.img);
      }
    } catch {
      setTryOnImage(item.img);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = async () => {
    if (!tryOnImage) return;
    try {
      const res = await fetch(tryOnImage);
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "tryon_result.png";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch {}
  };

  return (
    <div className="cap-glasses-container">
      <h2>Cap, Hats & Glasses Try-On 👓🧢🎩</h2>

      {uploadedImage && (
        <div className="image-wrapper">
          <img
            src={
              uploadedImage instanceof File
                ? URL.createObjectURL(uploadedImage)
                : uploadedImage.startsWith("/")
                ? `${API_BASE}${uploadedImage}`
                : uploadedImage
            }
            alt="preview"
            className="preview-image"
          />
        </div>
      )}

      <div className="action-buttons">
        <button className="btn btn-analyze" onClick={analyzeFace} disabled={loading}>
          {loading ? "⏳ Analyzing..." : "🔍 Analyze & Recommend"}
        </button>
        <button className="btn btn-reset" onClick={goBackHome}>
          ⬅ Back
        </button>
      </div>

      {recommendation && (
        <div className="recommendation-box">
          <h3>✨ Recommendation</h3>
          <p><strong>Face Shape:</strong> {recommendation.shape}</p>
          <ul className="recommendation-list">
            {recommendation.items.map((it, i) => (
              <li key={i} className="recommendation-item">{it}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="tryon-section">
        <h3>🎩 Select a Category</h3>
        <div className="tryon-card-grid categories-grid">
          {Object.keys(categories).map((cat) => (
            <div
              key={cat}
              className={`tryon-card category-card ${selectedCategory === cat ? "active" : ""}`}
              onClick={() => {
                setSelectedCategory(cat);
                setSelectedItem(null);
                setTryOnImage(null);
              }}
            >
              <img
                src={
                  cat.includes("Cap")
                    ? "/caps_hats/caps/cap_1.png"
                    : cat.includes("Hat")
                    ? "/caps_hats/hats/hat_1.png"
                    : "/caps_hats/glasses/glasses_1.png"
                }
                alt={cat}
              />
              <div>{cat}</div>
            </div>
          ))}
        </div>

        {selectedCategory && (
          <>
            <h3 className="items-heading">🛒 Choose an Item</h3>
            <div className="tryon-card-grid items-grid">
              {categories[selectedCategory].map((item) => (
                <div
                  key={item.label}
                  className={`tryon-card ${selectedItem === item.label ? "active" : ""}`}
                  onClick={() => tryOnItem(item)}
                >
                  <img src={item.img} alt={item.label} />
                  <div>{item.label}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {tryOnImage && (
        <div className="result-section">
          <h3>🎉 Try-On Result</h3>
          <div className="result-image-wrapper">
            <img src={tryOnImage} alt="Try-on result" className="result-image" />
          </div>
          <button className="btn btn-download" onClick={downloadImage}>
            ⬇ Download Try-On Image
          </button>
        </div>
      )}
    </div>
  );
}
