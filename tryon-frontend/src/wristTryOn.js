// WristTryOnCards.js
import React, { useState, useRef, useEffect } from "react";
import "./wristTryOn.css";
import RealTimeWristTryOn from "./realtime_wristTryOn";

const BACKEND_URL = "http://127.0.0.1:8000";

// ======================== WristTryOn Component (Manual) ========================
const WristTryOn = () => {
  const [watchFiles, setWatchFiles] = useState([]);
  const [selectedWatch, setSelectedWatch] = useState(null);
  const [wristImage, setWristImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const fetchWatches = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/available-watches`);
        const data = await res.json();
        setWatchFiles(data.watches || []);
      } catch {
        setWatchFiles([]);
      }
    };
    fetchWatches();
  }, []);

  const hideMessages = () => {
    setErrorMessage("");
    setSuccessMessage("");
  };

  const handleWatchSelect = (watch) => {
    setSelectedWatch(watch);
    hideMessages();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setWristImage(URL.createObjectURL(file));
      setCapturedBlob(file);
      hideMessages();
    }
  };

  useEffect(() => {
    if (cameraActive) startCamera();
    else stopCamera();
    return () => stopCamera();
  }, [cameraActive]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 640, height: 480 },
      });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    } catch {
      setErrorMessage("Unable to access camera. Check permissions.");
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  const capturePhoto = () => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      setCapturedBlob(blob);
      setWristImage(URL.createObjectURL(blob));
      setPreviewMode(true);
    }, "image/jpeg", 1);
  };

  const retakePhoto = () => {
    setPreviewMode(false);
    setCapturedBlob(null);
    setWristImage(null);
  };

  const handleTryOn = async () => {
    if (!selectedWatch || !wristImage) {
      setErrorMessage("Please select a watch and upload/capture your wrist image.");
      return;
    }

    setErrorMessage("");
    setSuccessMessage("");
    setLoading(true);

    const formData = new FormData();
    if (capturedBlob) formData.append("file", capturedBlob, "wrist_photo.jpg");
    formData.append("watch_choice", selectedWatch);

    try {
      const res = await fetch(`${BACKEND_URL}/wrist-tryon/`, {
        method: "POST",
        body: formData,
      });
      const result = await res.json();
      if (res.ok && result.result_image_url) {
        setResultImage(result.result_image_url);
        setSuccessMessage("✅ Try-on completed successfully!");
        setTimeout(() => {
          document.getElementById("resultSection")?.scrollIntoView({ behavior: "smooth" });
        }, 200);
      } else {
        setErrorMessage(result.error || "Processing error occurred.");
      }
    } catch (err) {
      setErrorMessage("Network error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      {/* Manual Try-On interface */}
      <div className="header">
        <h1>⌚ Virtual Watch Try-On</h1>
        <p>Select a watch and upload or capture your wrist photo!</p>
      </div>

      <div className="main-content">
        {/* Step 1: Choose Watch */}
        <div className="step">
          <div className="step-title">
            <div className="step-number">1</div>
            Choose Your Watch
          </div>
          <div className="watch-grid">
            {watchFiles.length > 0
              ? watchFiles.map((watch, idx) => (
                  <div
                    key={idx}
                    className={`watch-option ${selectedWatch === watch ? "selected" : ""}`}
                    onClick={() => handleWatchSelect(watch)}
                  >
                    <img src={`${BACKEND_URL}/uploads/${watch}`} alt={`Watch ${idx + 1}`} className="watch-image" />
                    <div className="watch-name">{watch}</div>
                  </div>
                ))
              : <p>No watches available</p>}
          </div>
        </div>

        {/* Step 2: Upload / Capture */}
        <div className="step">
          <div className="step-title">
            <div className="step-number">2</div>
            Upload or Capture Wrist Photo
          </div>

          {!cameraActive && !previewMode && (
            <div className="upload-section">
              <input type="file" accept="image/*" id="fileInput" hidden onChange={handleFileChange} />
              <button className="upload-btn" onClick={() => document.getElementById("fileInput").click()}>
                📁 Choose File
              </button>
              <button className="upload-btn" onClick={() => setCameraActive(true)}>
                📷 Take Picture
              </button>
            </div>
          )}

          {cameraActive && !previewMode && (
            <div className="camera-container">
              <video ref={videoRef} autoPlay playsInline></video>
              <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
              <div className="camera-overlay">
                <div className="wrist-guide">Position your wrist here</div>
              </div>
              <div className="controls">
                <button className="control-btn capture-btn" onClick={capturePhoto}>📸 Capture</button>
                <button className="control-btn back-btn" onClick={() => setCameraActive(false)}>← Cancel</button>
              </div>
            </div>
          )}

          {previewMode && wristImage && (
            <div className="preview-section">
              <h3>📷 Photo Preview:</h3>
              <img src={wristImage} alt="Preview" className="preview-image" />
              <div className="controls">
                <button className="control-btn retake-btn" onClick={retakePhoto}>🔄 Retake</button>
                <button className="control-btn use-photo-btn" onClick={() => setCameraActive(false)}>✅ Use This Photo</button>
              </div>
            </div>
          )}

          {wristImage && !previewMode && !cameraActive && (
            <div className="preview-section">
              <p>Preview:</p>
              <img src={wristImage} alt="Preview" className="preview-image" />
            </div>
          )}
        </div>

        {/* Step 3: Try-On */}
        <div className="step">
          <div className="step-title">
            <div className="step-number">3</div>
            Try It On
          </div>
          <button className="try-on-btn" onClick={handleTryOn} disabled={!selectedWatch || !wristImage || loading}>
            ✨ Try On Watch
          </button>
        </div>

        {/* Messages */}
        {errorMessage && <div className="error-message">{errorMessage}</div>}
        {successMessage && <div className="success-message">{successMessage}</div>}
        {loading && <div className="loading"><div className="spinner"></div><p>Processing your image...</p></div>}

        {/* Result */}
        {resultImage && (
          <div className="result-preview" id="resultSection">
            <h3>🖼️ Your Virtual Try-On Result:</h3>
            <img src={resultImage} alt="Try-on result" className="result-img" />
          </div>
        )}
      </div>
    </div>
  );
};

// ======================== Wrapper Component for Two Cards ========================
const WristTryOnCards = () => {
  const [activeCard, setActiveCard] = useState(null); // null | "manual" | "realtime"

  return (
    <div className="cards-container">
      {!activeCard && (
        <div className="cards-grid">
         <div
  style={{
    display: "flex",
    justifyContent: "center", // centers horizontally
    alignItems: "center", // centers vertically
    flexDirection: "row", // keep them in a row
    height: "40vh", // full height center
    gap: "50px", // space between cards
    margin: "0 auto", // ensure centered
  }}
>
  {/* Manual Wrist Try On Card */}
  <div
    style={{
      border: "2px solid #ff4081",
      borderRadius: "15px",
      width: "450px",
      padding: "30px 20px",
      textAlign: "center",
      cursor: "pointer",
      boxShadow: "0 5px 15px rgba(0,0,0,0.1)",
      transition: "all 0.3s ease",
      backgroundColor: "#fff",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = "translateY(-6px)";
      e.currentTarget.style.borderColor = "#1d6ed0";
      e.currentTarget.style.boxShadow = "0 8px 20px rgba(52, 152, 219, 0.4)";
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = "none";
      e.currentTarget.style.borderColor = "#ff4081";
      e.currentTarget.style.boxShadow = "0 5px 15px rgba(0,0,0,0.1)";
    }}
    onClick={() => setActiveCard("manual")}
  >
    <h2 style={{ color: "#ff4081", fontSize: "1.4rem", fontWeight: "700" }}>
      Manual Wrist Try On
    </h2>
    <p style={{ color: "#ff4081", fontSize: "0.95rem" }}>
      Click to open the manual wrist try-on interface
    </p>
  </div>

  {/* Real-Time Wrist Try On Card */}
  <div
    style={{
      border: "2px solid #ff4081",
      borderRadius: "15px",
      width: "450px",
      padding: "30px 20px",
      textAlign: "center",
      cursor: "pointer",
      boxShadow: "0 5px 15px rgba(0,0,0,0.1)",
      transition: "all 0.3s ease",
      backgroundColor: "#fff",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = "translateY(-6px)";
      e.currentTarget.style.borderColor = "#1d6ed0";
      e.currentTarget.style.boxShadow = "0 8px 20px rgba(52, 152, 219, 0.4)";
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = "none";
      e.currentTarget.style.borderColor = "#3498db";
      e.currentTarget.style.boxShadow = "0 5px 15px rgba(0,0,0,0.1)";
    }}
    onClick={() => setActiveCard("realtime")}
  >
    <h2 style={{ color: "#ff4081", fontSize: "1.4rem", fontWeight: "700" }}>
      Real Time Wrist Try On
    </h2>
    <p style={{ color: "#ff4081", fontSize: "0.95rem" }}>
      Click to open the real-time wrist try-on interface
    </p>
  </div>
</div>

        </div>
      )}

      {activeCard && (
        <div className="wrist-tryon-wrapper">
          <button className="close-btn" onClick={() => setActiveCard(null)}>Back Button</button>
          {activeCard === "manual" && <WristTryOn />}
          {activeCard === "realtime" && <RealTimeWristTryOn />}
        </div>
      )}
    </div>
  );
};

export default WristTryOnCards;
