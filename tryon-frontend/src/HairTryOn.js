// HairTryOn.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import "./HairTryOn.css";

const API_BASE = "http://127.0.0.1:8000";

const LANGUAGES = {
  en: {
    title: "🎨 AI Hair Stylist",
    subtitle: "Professional hair transformation system powered by Gemini 2.0 Flash",
    description:
      "Transform your hair while preserving your face and analyze if it suits you!",
    chatPlaceholder: "e.g., 'honey blonde hair color' or 'short bob cut'",
    sendButton: "📤 Send",
    clearChat: "🗑️ Clear Chat",
  },
  tr: {
    title: "🎨 AI Saç Stilisti",
    subtitle: "Gemini 2.0 Flash ile güçlendirilmiş profesyonel saç değiştirme sistemi",
    description: "Yüzünüzü koruyarak saçınızı değiştirir ve yakışıp yakışmadığını analiz eder!",
    chatPlaceholder: "Örn: 'bal sarısı saç rengi' veya 'kısa bob kesimi'",
    sendButton: "📤 Gönder",
    clearChat: "🗑️ Chat'i Temizle",
  },
};

const HairTryOn = ({ uploadedImage, goBackHome }) => {
  const [mode, setMode] = useState(null);
  const [selectedStyle, setSelectedStyle] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const hairStyles = [
    { id: 1, name: "Long Spiral Ringlets", file: "hair1.png" },
    { id: 2, name: "Straight Platinum Blonde", file: "hair2.png" },
    { id: 3, name: "Medium Soft Curls", file: "hair3.png" },
    { id: 4, name: "Highlighted Wavy Layers", file: "hair4.png" },
    { id: 5, name: "Auburn Wavy", file: "hair5.png" },
    { id: 6, name: "Tight Kinky Curl Ponytail", file: "hair6.png" },
  ];

  // ===== Hair Try-On Handler =====
  const handleTryOn = async (style) => {
    if (loading || !uploadedImage) return;
    setSelectedStyle(style);
    setLoading(true);
    setResultImage(null);
    setErrorMsg(null);

    try {
      const blob = await fetch(uploadedImage).then((r) => r.blob());
      const file = new File([blob], "user_image.png", { type: blob.type });

      const formData = new FormData();
      formData.append("image", file);
      formData.append("style_name", style.file);

      let endpoint = `${API_BASE}/tryon/hair`;
      if (mode === "gemini") endpoint = `${API_BASE}/tryon/hair_gemini`;

      const res = await fetch(endpoint, { method: "POST", body: formData });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server returned ${res.status}: ${errorText}`);
      }

      const contentType = res.headers.get("Content-Type");

      if (contentType && contentType.includes("application/json")) {
        const data = await res.json();
        if (data.image_base64) {
          setResultImage(`data:image/png;base64,${data.image_base64}`);
        } else if (data.image_url) {
          const cleanPath = data.image_url.replace(/^\/|^static[\\/]/, "");
          const imgUrl = data.image_url.startsWith("http")
            ? data.image_url
            : `${API_BASE}/static/${cleanPath}`;
          setResultImage(imgUrl);
        } else if (data.error) {
          throw new Error(data.error);
        } else {
          throw new Error("❌ No image returned from backend.");
        }
      } else {
        const resultBlob = await res.blob();
        setResultImage(URL.createObjectURL(resultBlob));
      }
    } catch (err) {
      console.error("❌ Hair try-on error:", err);
      setErrorMsg(err.message || "Failed to apply hairstyle.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mode === "gemini" && uploadedImage && hairStyles.length > 0) {
      handleTryOn(hairStyles[0]);
    }
  }, [mode, uploadedImage]);

  // === Step 1: Mode Selection ===
  if (!mode) {
    return (
      <div className="hair-tryon-container">
        <h2 className="hair-title">💇‍♀️ Choose Hair Try-On Mode</h2>
        <p className="hair-subtitle">Select the AI model you want to use:</p>

        <div className="model-card-wrapper">
          <div className="fancy-card" onClick={() => setMode("simple")}>
            <h3>✨ Simple Try-On</h3>
            <p>Fast preview using predefined hairstyle overlays.</p>
          </div>

          <div className="fancy-card" onClick={() => setMode("gemini")}>
            <h3>🧠 Gemini AI Model</h3>
            <p>Advanced AI overlay for accurate hairstyle blending.</p>
          </div>

          <div className="fancy-card" onClick={() => setMode("gemini_prompt")}>
            <h3>💬 Gemini Prompt-Based</h3>
            <p>Chat directly with Gemini to customize your hairstyle!</p>
          </div>
        </div>

        <div className="hair-buttons">
          <button onClick={goBackHome} className="btn-hair-back">
            ⬅ Back to Face Try-On
          </button>
        </div>
      </div>
    );
  }

  // === Step 2: Gemini Prompt Mode ===
  if (mode === "gemini_prompt") {
    return (
      <GeminiPromptUI
        goBackHome={goBackHome}
        uploadedImage={uploadedImage}
        setMode={setMode}
      />
    );
  }

  // === Step 3: Simple / Gemini Mode ===
  return (
    <div className="hair-tryon-container">
      <h2>{mode === "gemini" ? "🧠 Gemini Hair Try-On" : "✨ Simple Hair Try-On"}</h2>

      <div className="hair-grid">
        {hairStyles.map((style) => (
          <button
            key={style.id}
            className={`hair-card ${selectedStyle?.id === style.id ? "selected" : ""}`}
            onClick={() => handleTryOn(style)}
            disabled={loading}
          >
            <img src={`/hair_style/${style.file}`} alt={style.name} className="hair-img" />
            <p>{style.name}</p>
          </button>
        ))}
      </div>

      {loading && <p className="hair-loading">💫 Generating hairstyle... Please wait ⏳</p>}
      {errorMsg && <p className="hair-error">❌ {errorMsg}</p>}

      {resultImage && (
        <div className="result-box">
          <h3>🎉 Result Preview</h3>
          <img src={resultImage} alt="Result" className="result-image" />
        </div>
      )}

      {/* === Bottom Buttons: Switch, Download, Back === */}
      <div className="hair-action-row-bottom">
        <button className="btn-switch-model" onClick={() => setMode(null)} disabled={loading}>
          🔄 Switch Mode
        </button>
        {resultImage && (
          <a href={resultImage} download="hair_result.png" className="btn-download">
            💾 Download Result
          </a>
        )}
        <button onClick={goBackHome} className="btn-hair-back">
          ⬅ Back to Face Try-On
        </button>
      </div>
    </div>
  );
};

// === Gemini Prompt UI ===
function GeminiPromptUI({ goBackHome, uploadedImage, setMode }) {
  const [lang, setLang] = useState("en");
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendHairRequest = async () => {
    if (!uploadedImage || !chatInput) {
      alert("Please enter your hair request first!");
      return;
    }

    setLoading(true);
    setChatHistory((prev) => [...prev, { role: "user", content: chatInput }]);

    const blob = await fetch(uploadedImage).then((r) => r.blob());
    const file = new File([blob], "uploaded.png", { type: blob.type });

    const formData = new FormData();
    formData.append("image", file);
    formData.append("prompt", chatInput);

    try {
      const res = await axios.post(`${API_BASE}/tryon/hair_gemini_prompt`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (res.data.image_base64) {
        setResultImage(`data:image/png;base64,${res.data.image_base64}`);
        const formattedFeedback = res.data.gemini_feedback
          ?.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
          .replace(/\n/g, "<br/>")
          .replace(/(Face Match|Color Harmony|Realism):/g, "<br/><b>$1:</b>");

        setChatHistory((prev) => [
          ...prev,
          {
            role: "ai",
            content:
              formattedFeedback ||
              "✅ Gemini hair transformation successful, but no feedback returned.",
            isHtml: true,
          },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { role: "ai", content: "⚠️ No image returned from backend." },
        ]);
      }

      setChatInput("");
    } catch (err) {
      console.error("Gemini error:", err.response?.data || err.message);
      setChatHistory((prev) => [
        ...prev,
        { role: "ai", content: "❌ Failed to process request." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setChatHistory([]);
    setResultImage(null);
    setChatInput("");
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>{LANGUAGES[lang].title}</h1>
        <h3>{LANGUAGES[lang].subtitle}</h3>
        <p>{LANGUAGES[lang].description}</p>
        <div className="lang-buttons">
          <button onClick={() => setLang("en")}>🇺🇸 English</button>
          <button onClick={() => setLang("tr")}>🇹🇷 Türkçe</button>
        </div>
      </div>

      <div className="upload-result-container">
        <div className="upload-column">
          <h4>📸 Your Uploaded Photo</h4>
          {uploadedImage ? <img src={uploadedImage} alt="uploaded" /> : <p>No image uploaded yet.</p>}

          {resultImage && (
            <>
              <h4>🎉 Result</h4>
              <img src={resultImage} alt="result" />
            </>
          )}
        </div>

        <div className="chat-column">
          <h4>💬 Chat with Gemini</h4>
          <div className="chat-box">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                <b>{msg.role}:</b>{" "}
                {msg.isHtml ? <span dangerouslySetInnerHTML={{ __html: msg.content }} /> : msg.content}
              </div>
            ))}
          </div>

          <textarea
            placeholder={LANGUAGES[lang].chatPlaceholder}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
          />
          <button className="send-btn" onClick={sendHairRequest} disabled={loading}>
            {loading ? "⏳ Processing..." : LANGUAGES[lang].sendButton}
          </button>
          <button className="clear-btn" onClick={clearChat}>
            {LANGUAGES[lang].clearChat}
          </button>
        </div>
      </div>

      {/* === Bottom Buttons: Switch, Download, Back === */}
      <div className="hair-action-row-bottom">
        <button className="btn-switch-model" onClick={() => setMode(null)} disabled={loading}>
          🔄 Switch Mode
        </button>
        {resultImage && (
          <a href={resultImage} download="hair_result.png" className="btn-download">
            💾 Download Result
          </a>
        )}
        <button onClick={goBackHome} className="btn-hair-back">
          ⬅ Back to Face Try-On
        </button>
      </div>
    </div>
  );
}

export default HairTryOn;
