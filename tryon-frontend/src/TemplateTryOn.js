import React, { useState, useEffect } from "react";
import "./TemplateTryOn.css";

const TemplateTryOn = ({ uploadedImage }) => {
  const [templates, setTemplates] = useState({});
  const [selectedOccasion, setSelectedOccasion] = useState(null);
  const [appliedSample, setAppliedSample] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch template list from backend
  useEffect(() => {
    fetch("http://127.0.0.1:8000/available-templates/")
      .then((res) => res.json())
      .then((data) => setTemplates(data))
      .catch((err) => console.error("Error fetching templates", err));
  }, []);

  const applyTemplate = async (occasion, sample) => {
    if (!uploadedImage) return;
    setLoading(true);
    setResultImage(null);

    try {
      const formData = new FormData();
      const resp = await fetch(uploadedImage);
      const blob = await resp.blob();
      formData.append("file", blob, "face.png");
      formData.append("occasion", occasion);
      formData.append("sample", sample);

      const res = await fetch("http://127.0.0.1:8000/apply-template/", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to apply template");
      const blobResult = await res.blob();
      const url = URL.createObjectURL(blobResult);
      setResultImage(url);
      setAppliedSample(sample);
    } catch (err) {
      console.error(err);
      alert("❌ Something went wrong while applying template!");
    } finally {
      setLoading(false);
    }
  };

  const resetOccasion = () => {
    setSelectedOccasion(null);
    setResultImage(null);
    setAppliedSample(null);
  };

  // --- New Download Function ---
  const handleDownload = () => {
    if (!resultImage) return alert("No result image to download!");
    const link = document.createElement("a");
    link.href = resultImage;
    link.download = appliedSample ? `template_${appliedSample}.png` : "template_result.png";
    link.click();
  };

  return (
    <div className="template-container">
      <h2>🎨 Template / Occasion-Based Try-On</h2>

      {uploadedImage && (
        <img src={uploadedImage} alt="Uploaded" className="template-preview" />
      )}

      {!selectedOccasion && (
        <>
          <p>Select an occasion to try a curated look:</p>
          <div className="occasion-cards">
            {Object.keys(templates).map((occasion) => (
              <div
                key={occasion}
                className="occasion-card"
                onClick={() => setSelectedOccasion(occasion)}
              >
                <h3>{occasion.toUpperCase()}</h3>
                <img
                  src={templates[occasion][0]}
                  alt={occasion}
                  className="template-thumb"
                />
              </div>
            ))}
          </div>
        </>
      )}

      {selectedOccasion && (
        <div className="occasion-result">
          <h3>✅ Selected Occasion: {selectedOccasion}</h3>

          <div className="template-options">
            {templates[selectedOccasion].map((sampleUrl, idx) => (
              <div key={idx} className="template-thumb-box">
                <img
                  src={sampleUrl}
                  alt={`sample-${idx}`}
                  className="template-thumb"
                  onClick={() =>
                    applyTemplate(selectedOccasion, `sample${idx + 1}.png`)
                  }
                />
                <p className="template-label">Sample {idx + 1}</p>
              </div>
            ))}
          </div>

          {loading && <p className="loading-text">⏳ Applying template...</p>}

          {appliedSample && (
            <div className="applied-sample">
              <strong>Applied Sample:</strong> {appliedSample}
            </div>
          )}

          {resultImage && (
            <div className="result-box">
              <h4>Result:</h4>
              <img src={resultImage} alt="Result" className="result-img" />
              <button className="download-btn" onClick={handleDownload}>
                💾 Download Result
              </button>
            </div>
          )}

          <button className="back-btn" onClick={resetOccasion}>
            🔙 Back to Occasions
          </button>
        </div>
      )}
    </div>
  );
};

export default TemplateTryOn;
