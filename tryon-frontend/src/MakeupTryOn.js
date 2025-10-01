import React, { useState, useEffect } from "react";
import ManualTryOn from "./ManualTryOn";
import TemplateTryOn from "./TemplateTryOn";
import "./MakeupTryOn.css";

const MakeupTryOn = ({ uploadedImage, goBackHome }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);

  useEffect(() => {
    const fetchMakeup = async () => {
      if (!uploadedImage) return;

      try {
        setLoading(true);
        const response = await fetch(uploadedImage);
        const blob = await response.blob();
        const file = new File([blob], "uploaded.jpg", { type: blob.type });

        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://127.0.0.1:8000/makeup-tryon/", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        setResult(data);
      } catch (err) {
        console.error("Makeup try-on error:", err);
        alert("❌ Failed to get makeup suggestions.");
      } finally {
        setLoading(false);
      }
    };

    fetchMakeup();
  }, [uploadedImage]);

  if (!uploadedImage)
    return <p>Please upload an image first to try on makeup.</p>;

  const makeup = result?.makeup_recommendations || {};

  const downloadRecommendations = () => {
    if (!result) return alert("No makeup recommendations to download!");
    const entries = Object.entries(makeup).map(
      ([key, values]) => `${key}: ${Array.isArray(values) ? values.join(", ") : values}`
    );
    const text = `💄 AI Makeup Recommendations\n\n${entries.join("\n")}`;
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "makeup_recommendations.txt";
    link.click();
  };

  return (
    <div className="makeup-container">
      <h2>💄 AI Makeup Try-On</h2>

      <div className="preview-container">
        <img src={uploadedImage} alt="Uploaded" className="preview-img" />
      </div>

      {loading && <p className="loading">⏳ Analyzing image and generating recommendations...</p>}
      {result && result.error && <p className="error">{result.error}</p>}

      {result && !result.error && (
        <>
          <div className="result-section">
            <h3>💄 Makeup Recommendations</h3>
            {Object.keys(makeup).length > 0 ? (
              <div className="makeup-list">
                {Object.entries(makeup).map(([key, values]) => (
                  <div key={key} className="makeup-item">
                    <strong>{key}:</strong>{" "}
                    {Array.isArray(values) ? values.join(", ") : values}
                  </div>
                ))}
              </div>
            ) : (
              <p>No makeup recommendations available.</p>
            )}
          </div>

          {/* Option Cards */}
          {!selectedOption && (
            <div className="option-cards">
              <div
                className="option-card"
                onClick={() => setSelectedOption("manual")}
              >
                Manual / AI Try-On
              </div>
              <div
                className="option-card"
                onClick={() => setSelectedOption("template")}
              >
                Template / Occasion-Based Try-On
              </div>
            </div>
          )}

          {/* Load selected option */}
          {selectedOption === "manual" && <ManualTryOn uploadedImage={uploadedImage} />}
          {selectedOption === "template" && <TemplateTryOn uploadedImage={uploadedImage} />}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button className="download-btn" onClick={downloadRecommendations}>💾 Download Recommendations</button>
            <button className="home-btn" onClick={() => goBackHome && goBackHome()}>🏠 Back Home</button>
          </div>
        </>
      )}
    </div>
  );
};

export default MakeupTryOn;
