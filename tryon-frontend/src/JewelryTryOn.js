import React, { useEffect, useRef, useState } from "react";
import "./JewelleryTryOn.css";

const API_BASE = "http://127.0.0.1:8000";

export default function JewelryTryOn({ uploadedImage, goBackHome }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTryOn, setShowTryOn] = useState(false);
  const [showPromptTryOn, setShowPromptTryOn] = useState(false);
  const [showPromptInterface, setShowPromptInterface] = useState(false);
  const [tryOnResults, setTryOnResults] = useState({});
  const [tryOnLoading, setTryOnLoading] = useState({});
  const [galleryImages, setGalleryImages] = useState({});
  const [selectedOverlays, setSelectedOverlays] = useState({});
  const [promptInput, setPromptInput] = useState("");
  const [error, setError] = useState("");

  const latestReqRef = useRef({});

  const tryOnItems = [
    { key: "nosepin", label: "Nose Pin", thumb: "/jewellery_data/Nose pin/nosepin_1.png" },
    { key: "earrings", label: "Earrings", thumb: "/jewellery_data/Earring/earring_1.png" },
    { key: "necklace", label: "Necklace", thumb: "/jewellery_data/Necklace/necklace_1.png" },
    { key: "bindi", label: "Bindi", thumb: "/jewellery_data/Bindi/bindi_1.png" },
    { key: "tikka", label: "Maang Tikka", thumb: "/jewellery_data/Maang Tikka/maangtikka_1.png" },
  ];

  // 🪞 Fetch recommendations
  useEffect(() => {
    if (!uploadedImage) return;
    (async () => {
      setLoading(true);
      try {
        const blob = await (await fetch(uploadedImage)).blob();
        const fd = new FormData();
        fd.append("file", blob, "photo.jpg");
        const res = await fetch(`${API_BASE}/recommend-jewelry/`, { method: "POST", body: fd });
        const json = await res.json();
        setData(json);
      } catch {
        setData({ error: "Unable to fetch recommendations." });
      } finally {
        setLoading(false);
      }
    })();
  }, [uploadedImage]);

  // 🖼️ Fetch gallery images
  useEffect(() => {
    (async () => {
      for (const item of tryOnItems) {
        try {
          const res = await fetch(`${API_BASE}/list-jewelry-images/${item.key}`);
          if (res.ok) {
            const json = await res.json();
            const unique = Array.from(new Set(json.images || [])).sort();
            setGalleryImages((prev) => ({ ...prev, [item.key]: unique }));
          }
        } catch (e) {
          console.error("Gallery fetch failed for", item.key, e);
        }
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 💍 Try-on for single item
  const handleTryOn = async (itemKey, overlayUrl) => {
    if (!uploadedImage || tryOnLoading[itemKey]) return;

    setSelectedOverlays((prev) => ({ ...prev, [itemKey]: overlayUrl }));
    const reqId = (latestReqRef.current[itemKey] || 0) + 1;
    latestReqRef.current[itemKey] = reqId;
    setTryOnLoading((prev) => ({ ...prev, [itemKey]: true }));

    try {
      const blob = await (await fetch(uploadedImage, { cache: "no-store" })).blob();
      const fd = new FormData();
      fd.append("file", blob, "photo.jpg");
      fd.append("item", itemKey);
      if (overlayUrl) fd.append("overlay_url", overlayUrl);

      const res = await fetch(`${API_BASE}/tryon-jewelry/`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`Try-on failed: ${res.status}`);
      const blobRes = await res.blob();
      const url = URL.createObjectURL(blobRes);

      if (latestReqRef.current[itemKey] !== reqId) {
        URL.revokeObjectURL(url);
        return;
      }

      setTryOnResults((prev) => {
        const oldUrl = prev[itemKey];
        if (oldUrl) URL.revokeObjectURL(oldUrl);
        return { ...prev, [itemKey]: url };
      });
    } catch (e) {
      console.error(`Error trying on ${itemKey}`, e);
      alert(`Error trying on ${itemKey}`);
    } finally {
      setTryOnLoading((prev) => ({ ...prev, [itemKey]: false }));
    }
  };

  // Apply all selected overlays
  const handleApplyAll = async () => {
    if (!uploadedImage || Object.keys(selectedOverlays).length === 0) {
      return alert("Please select jewellery items first.");
    }

    try {
      const blob = await (await fetch(uploadedImage, { cache: "no-store" })).blob();
      const fd = new FormData();
      fd.append("file", blob, "photo.jpg");
      fd.append("items", JSON.stringify(selectedOverlays));

      const res = await fetch(`${API_BASE}/apply-all-jewelry/`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`Apply-all failed: ${res.status}`);
      const blobRes = await res.blob();
      const url = URL.createObjectURL(blobRes);

      setTryOnResults((prev) => {
        if (prev.all) URL.revokeObjectURL(prev.all);
        return { ...prev, all: url };
      });
    } catch (e) {
      console.error("Error applying jewellery", e);
      alert("Error applying jewellery");
    }
  };

  // ✨ Prompt-based Try-On
const handlePromptTryOn = async () => {
  if (!uploadedImage || !promptInput.trim()) {
    return alert("Please enter a jewellery description first.");
  }

  try {
    setLoading(true);
    setError("");

    // Get uploaded image as blob
    const blob = await (await fetch(uploadedImage)).blob();
    const fd = new FormData();
    fd.append("file", blob, "photo.jpg");
    fd.append("prompt", promptInput);

    // Fetch prompt-based try-on
    const res = await fetch(`${API_BASE}/prompt-jewelry-tryon/`, {
      method: "POST",
      body: fd,
    });

    if (!res.ok) throw new Error("Prompt-based try-on failed.");

    // Get JSON (Base64 string inside)
    const json = await res.json();
    if (!json.result_image_base64) throw new Error("No image returned from server.");

    // Convert Base64 to Blob URL
    const byteCharacters = atob(json.result_image_base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blobImage = new Blob([byteArray], { type: "image/png" });
    const url = URL.createObjectURL(blobImage);

    // Revoke old URL if exists
    if (tryOnResults.prompt) URL.revokeObjectURL(tryOnResults.prompt);

    setTryOnResults((prev) => ({ ...prev, prompt: url }));
  } catch (e) {
    console.error("Prompt-based try-on error:", e);
    setError("⚠️ Failed to process your jewellery prompt. Try again!");
  } finally {
    setLoading(false);
  }
};


  // Reset
  const handleReset = () => {
    Object.values(tryOnResults).forEach((src) => src && URL.revokeObjectURL(src));
    setTryOnResults({});
    setSelectedOverlays({});
    setPromptInput("");
  };

  // Downloads
  const handleDownloadReport = () => {
    if (!data) return alert("No recommendations available to download.");
    const report = `
Jewellery Recommendation Report
==============================
Face Shape: ${data.face_shape || "—"}
Recommended Metals: ${data.metals?.join(" / ") || "—"}
Recommended Gemstones: ${data.gemstones?.join(", ") || "—"}
Nosepin: ${data.nosepin || "—"}
Earrings: ${data.earrings || "—"}
Necklace: ${data.necklace || "—"}
Bindi: ${data.bindi || "—"}
Maang Tikka: ${data.tikka || "Suggested"}
Face Detected: ${data.face_detected ? "Yes" : "No"}
`;
    const blob = new Blob([report], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "Jewellery_Recommendation_Report.txt";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleDownloadImage = () => {
    const src = tryOnResults.all || tryOnResults.prompt;
    if (!src) return alert("No applied image to download.");
    const link = document.createElement("a");
    link.href = src;
    link.download = "Jewellery_Applied.png";
    link.click();
  };

  const previewSrc = tryOnResults.all || tryOnResults.prompt;

  const renderLine = (label, value) => (
    <div className="jewelry-line">
      <span className="label">{label}:</span>
      <span className="value">{value || "—"}</span>
    </div>
  );

  return (
    <div className="tryon-shell">
      <h2 className="title">Personalized Jewellery Recommendations</h2>

      <div className="home-btn-container">
        <button className="back-home-btn" onClick={goBackHome}>
          🏠 Back to Home
        </button>
      </div>

      {loading && <p className="progress">Processing your request…</p>}
      {!loading && !data && <p className="info-text">Upload an image to see your suggestions.</p>}
      {data?.error && <div className="error-box">❌ {data.error}</div>}

      {!loading && data && !data.error && (
        <>
          {/* ================================
               Recommendation Summary
          ================================== */}
          <div className="jewelry-card">
            {renderLine("Face Shape", data.face_shape)}
            {renderLine("Recommended Metals", data.metals?.join(" / "))}
            {renderLine("Recommended Gemstones", data.gemstones?.join(", "))}
            {renderLine("Nosepin", data.nosepin)}
            {renderLine("Earrings", data.earrings)}
            {renderLine("Necklace", data.necklace)}
            {renderLine("Bindi", data.bindi)}
            {renderLine("Maang Tikka", data.tikka || "Suggested")}
          </div>

          {/* ================================
               Action Buttons
          ================================== */}
          <div className="actions">
            <button className="tryon-btn" onClick={() => setShowTryOn(!showTryOn)}>
              {showTryOn ? "Hide Try-On" : "💍 Try On Jewellery"}
            </button>

            <button
              className="tryon-btn outline"
              onClick={() => setShowPromptTryOn(!showPromptTryOn)}
            >
              {showPromptTryOn ? "Hide Prompt Try-On" : "💎 Prompt-Based Jewellery Try-On"}
            </button>

            <button className="tryon-btn outline" onClick={handleApplyAll}>
              Apply Selected Jewellery
            </button>
            <button className="tryon-btn outline" onClick={handleReset}>
              🔄 Reset
            </button>
            <button className="tryon-btn outline" onClick={handleDownloadReport}>
              📄 Download Report
            </button>
            {previewSrc && (
              <button className="tryon-btn outline" onClick={handleDownloadImage}>
                📸 Download Applied Image
              </button>
            )}
          </div>

          {/* ================================
               Prompt-Based Try-On (Separate Interface)
          ================================== */}
          {showPromptTryOn && (
            <div className="prompt-interface fadeIn">
              {!showPromptInterface ? (
                <div className="prompt-landing">
                  <h3>💎 Prompt-Based Jewellery Try-On</h3>
                  <p>
                    Experience AI-powered jewellery design — describe your dream jewellery and
                    let AI create it instantly!
                  </p>
                  <button
                    className="tryon-btn primary"
                    onClick={() => setShowPromptInterface(true)}
                  >
                    ✨ Start Prompt Try-On
                  </button>
                </div>
              ) : (
                <div className="prompt-tryon-box enhanced-card">
                  <button
                    className="back-btn"
                    onClick={() => setShowPromptInterface(false)}
                  >
                    ⬅️ Back
                  </button>

                  <h3 className="prompt-title">💫 AI Jewellery Try-On (Prompt Mode)</h3>
                  <p className="prompt-desc">
                    Describe the jewellery you want (e.g., “gold necklace with ruby pendant”):
                  </p>

                  <textarea
                    className="prompt-input"
                    placeholder="Type your jewellery style prompt here..."
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                  />

                  <div className="prompt-actions">
                    <button
                      className="tryon-btn primary"
                      onClick={handlePromptTryOn}
                      disabled={loading}
                    >
                      {loading ? "⏳ Generating..." : "🚀 Generate Try-On"}
                    </button>

                    <button
                      className="tryon-btn secondary"
                      onClick={() => {
                        setPromptInput("");
                        setTryOnResults({});
                      }}
                    >
                      🔄 Clear
                    </button>
                  </div>

                  {error && <p className="error-msg">⚠️ {error}</p>}

                  {tryOnResults.prompt && (
                    <div className="prompt-preview">
                      <h4>✨ Your AI Jewellery Try-On Result:</h4>
                      <div className="tryon-image-box">
                        <img
                          src={tryOnResults.prompt}
                          alt="AI Jewellery Result"
                          className="tryon-result"
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ================================
               Normal Try-On Section
          ================================== */}
          {showTryOn && (
            <>
              <div className="preview-pane">
                <div className="pane-left">
                  <h4>Your Uploaded Photo</h4>
                  {uploadedImage ? (
                    <img src={uploadedImage} alt="Uploaded" className="uploaded-preview" />
                  ) : (
                    <p>No image uploaded</p>
                  )}
                </div>
                <div className="pane-right">
                  <h4>{previewSrc ? "Applied Jewellery" : "Try-On Result"}</h4>
                  {previewSrc && (
                    <img src={previewSrc} alt="preview" className="tryon-result" />
                  )}
                </div>
              </div>

              <div className="tryon-grid">
                {tryOnItems.map((item) => (
                  <div
                    key={item.key}
                    className={`tryon-card ${selectedOverlays[item.key] ? "active" : ""}`}
                  >
                    <h4>{item.label}</h4>
                    <div className="gallery-expanded">
                      {(galleryImages[item.key] || []).map((imgUrl, idx) => (
                        <img
                          key={`${item.key}-${idx}`}
                          src={imgUrl}
                          alt={`${item.label} ${idx + 1}`}
                          className={
                            selectedOverlays[item.key] === imgUrl ? "selected-thumb" : ""
                          }
                          onClick={() => handleTryOn(item.key, imgUrl)}
                        />
                      ))}
                    </div>
                    {tryOnLoading[item.key] && <p>Applying...</p>}
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
