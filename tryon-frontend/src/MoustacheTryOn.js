import React, { useState } from "react";
import "./MoustacheTryOn.css";

const API_BASE = "http://127.0.0.1:8000";

const MoustacheTryOn = ({ uploadedImage, goBackHome }) => {
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // ✅ Available moustache & beard styles
  const moustacheStyles = [
    { id: 1, name: "Classic Walrus Moustache", file: "moustache1.png" },
    { id: 2, name: "Imperial Handlebar", file: "moustache2.png" },
    { id: 3, name: "Chevron Moustache", file: "moustache3.png" },
    { id: 4, name: "English Mustache", file: "moustache4.png" },
    { id: 5, name: "Door Knocker", file: "moustache5.png" },
    { id: 6, name: "Van Dyke", file: "moustache6.png" },
  ];

  // ✅ Handle moustache try-on
  const handleTryOn = async (style) => {
    if (loading) return; // prevent spam-clicking
    if (!uploadedImage) {
      alert("Please upload your face image first!");
      return;
    }

    setSelectedStyle(style);
    setLoading(true);
    setResultImage(null);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      const blob = await fetch(uploadedImage).then((r) => r.blob());
      formData.append("image", blob, "user_image.png");
      formData.append("style_name", style.name);

      const response = await fetch(`${API_BASE}/tryon/moustache`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Server returned ${response.status}`);
      }

      const resultBlob = await response.blob();
      const imageUrl = URL.createObjectURL(resultBlob);
      setResultImage(imageUrl);
    } catch (err) {
      console.error("❌ Error applying moustache:", err);
      setErrorMsg(err.message || "Failed to apply moustache. Please check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="moustache-tryon-container">
      {/* 🔹 Title Section */}
      <h2 className="moustache-title">🧔 Virtual Moustache Try-On</h2>
      <p className="moustache-subtitle">
        Instantly preview different moustache and beard styles on your face!
      </p>

      {/* 🔹 Style Selection Grid */}
      <div className="moustache-grid">
        {moustacheStyles.map((style) => (
          <button
            key={style.id}
            className={`moustache-card ${
              selectedStyle?.id === style.id ? "selected" : ""
            }`}
            onClick={() => handleTryOn(style)}
            disabled={loading}
          >
            <img
              src={`/moustache/${style.file}`}
              alt={style.name}
              className="moustache-img"
              onError={(e) => (e.target.style.display = "none")}
            />
            <p>{style.name}</p>
          </button>
        ))}
      </div>

      {/* 🔹 Loading Indicator */}
      {loading && (
        <p className="moustache-loading">
          🪒 Applying <strong>{selectedStyle?.name}</strong>... Please wait ⏳
        </p>
      )}

      {/* 🔹 Error Message */}
      {errorMsg && <p className="moustache-error">❌ {errorMsg}</p>}

      {/* 🔹 Result Section */}
      <div className="moustache-result-box">
        <div className="moustache-column">
          <img
            src={uploadedImage}
            alt="Original Face"
            className="moustache-preview"
          />
          <span className="moustache-label">Original</span>
        </div>

        {resultImage && (
          <div className="moustache-column">
            <img
              src={resultImage}
              alt="Result with Moustache"
              className="moustache-preview"
            />
            <span className="moustache-label">
              With {selectedStyle?.name || "Moustache"}
            </span>
          </div>
        )}
      </div>

      {/* 🔹 Back Button */}
      <button onClick={goBackHome} className="btn-back" disabled={loading}>
        ⬅ Back to Face Try-On
      </button>
    </div>
  );
};

export default MoustacheTryOn;
