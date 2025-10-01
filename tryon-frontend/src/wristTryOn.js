import React, { useState, useRef, useEffect } from "react";
import "./wristTryOn.css";

const BACKEND_URL = "http://127.0.0.1:8000"; // ✅ backend URL

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
  const [previewMode, setPreviewMode] = useState(false); // ✅ new: preview step

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // ================== Fetch Watches ==================
  useEffect(() => {
    const fetchWatches = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/available-watches`);
        const data = await res.json();
        if (res.ok && data.watches) {
          setWatchFiles(data.watches);
        } else {
          setWatchFiles([]);
        }
      } catch (err) {
        console.error("Failed to fetch watches:", err);
        setWatchFiles([]);
      }
    };
    fetchWatches();
  }, []);

  const hideMessages = () => {
    setErrorMessage("");
    setSuccessMessage("");
  };

  // ================== Watch Selection ==================
  const handleWatchSelect = (watch) => {
    setSelectedWatch(watch);
    hideMessages();
  };

  // ================== File Upload ==================
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setWristImage(URL.createObjectURL(file));
      setCapturedBlob(file);
      hideMessages();
    }
  };

  // ================== Camera ==================
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
    } catch (err) {
      setErrorMessage("Unable to access camera. Check permissions.");
      console.error(err);
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

    canvas.toBlob(
      (blob) => {
        setCapturedBlob(blob);
        setWristImage(URL.createObjectURL(blob));
        setPreviewMode(true); // ✅ show preview instead of closing camera
      },
      "image/jpeg",
      1
    );
  };

  const retakePhoto = () => {
    setPreviewMode(false);
    setCapturedBlob(null);
    setWristImage(null);
  };

  // ================== Submit Try-On ==================
  const handleTryOn = async () => {
    if (!selectedWatch || !wristImage) {
      setErrorMessage("Please select a watch and upload/capture your wrist image.");
      return;
    }

    setErrorMessage("");
    setSuccessMessage("");
    setLoading(true);

    const formData = new FormData();
    try {
      if (capturedBlob) {
        formData.append("file", capturedBlob, "wrist_photo.jpg");
      }
      formData.append("watch_choice", selectedWatch);

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
            {watchFiles.length > 0 ? (
              watchFiles.map((watch, idx) => (
                <div
                  key={idx}
                  className={`watch-option ${selectedWatch === watch ? "selected" : ""}`}
                  onClick={() => handleWatchSelect(watch)}
                >
                  <img
                    src={`${BACKEND_URL}/uploads/${watch}`}
                    alt={`Watch ${idx + 1}`}
                    className="watch-image"
                  />
                  <div className="watch-name">{watch}</div>
                </div>
              ))
            ) : (
              <p>No watches available</p>
            )}
          </div>
        </div>

        {/* Step 2: Upload or Capture */}
        <div className="step">
          <div className="step-title">
            <div className="step-number">2</div>
            Upload or Capture Wrist Photo
          </div>

          {!cameraActive && !previewMode && (
            <div className="upload-section">
              <input
                type="file"
                accept="image/*"
                id="fileInput"
                className="file-input"
                onChange={handleFileChange}
                hidden
              />
              <button className="upload-btn" onClick={() => document.getElementById("fileInput").click()}>
                📁 Choose File
              </button>
              <button className="upload-btn" onClick={() => setCameraActive(true)}>
                📷 Take Picture
              </button>
            </div>
          )}

          {/* Camera mode */}
          {cameraActive && !previewMode && (
            <div className="camera-container">
              <video ref={videoRef} autoPlay playsInline></video>
              <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
              <div className="camera-overlay">
                <div className="wrist-guide">Position your wrist here</div>
              </div>
              <div className="instructions">
                <h3>📋 Instructions</h3>
                <ul>
                  <li>Allow camera access when prompted</li>
                  <li>Position your wrist inside the dashed guide</li>
                  <li>Ensure good lighting for best results</li>
                  <li>Keep your hand steady when capturing</li>
                  <li>Make sure your wrist is clearly visible</li>
                </ul>
              </div>
              <div className="controls">
                <button className="control-btn capture-btn" onClick={capturePhoto}>
                  📸 Capture
                </button>
                <button className="control-btn back-btn" onClick={() => setCameraActive(false)}>
                  ← Cancel
                </button>
              </div>
            </div>
          )}

          {/* Preview mode */}
          {previewMode && wristImage && (
            <div className="preview-section">
              <h3>📷 Photo Preview:</h3>
              <img src={wristImage} className="preview-image" alt="Preview" />
              <div className="controls">
                <button className="control-btn retake-btn" onClick={retakePhoto}>
                  🔄 Retake
                </button>
                <button className="control-btn use-photo-btn" onClick={() => setCameraActive(false)}>
                  ✅ Use This Photo
                </button>
              </div>
            </div>
          )}

          {/* If uploaded */}
          {wristImage && !previewMode && !cameraActive && (
            <div className="preview-section">
              <p>Preview:</p>
              <img src={wristImage} className="preview-image" alt="Preview" />
            </div>
          )}
        </div>

        {/* Step 3: Try-On */}
        <div className="step">
          <div className="step-title">
            <div className="step-number">3</div>
            Try It On
          </div>
          <button
            className="try-on-btn"
            onClick={handleTryOn}
            disabled={!selectedWatch || !wristImage || loading}
          >
            ✨ Try On Watch
          </button>
        </div>

        {/* Messages */}
        {errorMessage && <div className="error-message">{errorMessage}</div>}
        {successMessage && <div className="success-message">{successMessage}</div>}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Processing your image...</p>
          </div>
        )}

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

export default WristTryOn;
