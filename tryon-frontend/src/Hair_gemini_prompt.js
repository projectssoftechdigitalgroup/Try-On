import React, { useState } from "react";
import "./HairTryOn.css";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://127.0.0.1:8000";

const HairGeminiPrompt = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(null);

  const handleRunPrompt = async () => {
    try {
      setLoading(true);
      setError(null);
      setMessage("");

      // ✅ Use correct backend endpoint
      const res = await fetch(`${API_BASE}/run-hair-gemini-prompt/`, { method: "POST" });
      const data = await res.json();

      alert(data.message || "✅ Gemini Prompt script started!");
      setMessage(data.message || "Gemini Prompt script started!");
    } catch (err) {
      console.error("❌ Error running Gemini Prompt:", err);
      setError("Failed to trigger Gemini prompt. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hair-tryon-container">
      <h2 className="hair-title">💬 Gemini JS Prompt Runner</h2>
      <p className="hair-subtitle">
        This page directly triggers <strong>Hair_gemini_prompt.py</strong> on your backend.
      </p>

      <button className="btn-hair-back" onClick={() => navigate(-1)} disabled={loading}>
        ⬅ Back
      </button>

      <button className="fancy-card" onClick={handleRunPrompt} disabled={loading} style={{ marginTop: "20px" }}>
        🚀 Run Gemini Prompt Script
      </button>

      {loading && <p className="hair-loading">💫 Running Gemini prompt... please wait ⏳</p>}
      {error && <p className="hair-error">❌ {error}</p>}
      {message && <p className="hair-success">✅ {message}</p>}
    </div>
  );
};

export default HairGeminiPrompt;
