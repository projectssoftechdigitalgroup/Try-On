import React, { useRef, useState, useEffect } from "react";

function CaptureImage({ setUploadedImage, goHome }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [captured, setCaptured] = useState(null);

  // Start camera when component mounts
  useEffect(() => {
    startCamera();
    return () => stopCamera(); // cleanup when unmount
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = mediaStream;
      setStream(mediaStream);
    } catch (err) {
      console.error("Error accessing webcam:", err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const capturePhoto = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/png");

    // Save for preview
    setCaptured(dataUrl);

    // Pass to parent (App.js) as "uploadedImage"
    setUploadedImage(dataUrl);

    // Stop camera after capture
    stopCamera();
  };

  return (
    <div className="capture-container">
      {!captured ? (
        <div className="camera-box">
          <video ref={videoRef} autoPlay playsInline />
          <div className="btn-row">
            <button onClick={capturePhoto} className="btn-primary">
              📸 Capture
            </button>
            <button onClick={goHome} className="btn-secondary">
              ⬅ Back to Home
            </button>
          </div>
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>
      ) : (
        <div className="preview-box">
          <h4>✅ Captured Image</h4>
          <img src={captured} alt="Captured" />
          <div className="btn-row">
            <button onClick={startCamera} className="btn-primary">
              🔄 Retake
            </button>
            <button onClick={goHome} className="btn-secondary">
              ⬅ Back to Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CaptureImage;
