import React, { useEffect, useState, useRef } from "react";
import "./realtime_wristTryOn.css";

const BACKEND_URL = "http://127.0.0.1:8000";

export default function RealTimeWristTryOn() {
  const [watchFiles, setWatchFiles] = useState([]);
  const [selectedWatch, setSelectedWatch] = useState(null);
  const [processedFrame, setProcessedFrame] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // 🔹 Fetch available watches from backend
  useEffect(() => {
    const fetchWatches = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/available-watches`);
        const data = await res.json();
        setWatchFiles(data.watches || []);
      } catch (error) {
        console.error("Error fetching watches:", error);
        setErrorMessage("Unable to fetch watches.");
      }
    };
    fetchWatches();
  }, []);

  // 🔹 Start webcam stream
  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err) {
        setErrorMessage("");
      }
    };

    startCamera();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // 🔹 Send webcam frames to backend when a watch is selected
  useEffect(() => {
    if (!selectedWatch) return;

    const interval = setInterval(async () => {
      try {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas) return;

        const ctx = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");
        formData.append("filename", selectedWatch); // ✅ Send selected watch name

        const res = await fetch(`${BACKEND_URL}/process-realtime-wrist/`, {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        if (data.frame) {
          setProcessedFrame(data.frame);
        }
      } catch (error) {
        console.error("Error sending frame:", error);
      }
    }, 700); // smoother refresh

    return () => clearInterval(interval);
  }, [selectedWatch]);

  const handleWatchSelect = (watch) => {
    setSelectedWatch(watch);
    setProcessedFrame(null); // reset frame when changing watch
  };

  // 🔹 UI Layout
  return (
    <div className="realtime-container">
      <h1>🎥 Real-Time Wrist Try-On</h1>

      {/* 🕐 Step 1: Choose Watch */}
      <div className="step">
        <div className="step-title">
          <div className="step-number">1</div> Choose Your Watch
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

      {/* 🎥 Step 2: Live Camera + Processed Frame */}
      <div className="step">
        <div className="step-title">
          <div className="step-number">2</div> Live Camera Preview
        </div>

        <div className="camera-container">
          <video ref={videoRef} autoPlay playsInline className="camera-feed" />
          <canvas ref={canvasRef} style={{ display: "none" }} />
          {processedFrame ? (
            <img
              src={processedFrame}
              alt="Processed Frame"
              className="processed-frame"
            />
          ) : (
            <p className="no-frame-text">Waiting for watch selection...</p>
          )}
        </div>
      </div>

      {/* ⚠️ Error Messages */}
      {errorMessage && <div className="error-message">{errorMessage}</div>}
    </div>
  );
}
