import React, { useState } from "react";
import "./realtime_skin_analysis.css";

export default function RealtimeSkinAnalysis({ goBackHome }) {
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const startRealtime = async () => {
    try {
      setLoading(true);
      setStatus("🚀 Launching real-time analysis...");
      const res = await fetch("http://127.0.0.1:8000/launch-realtime/", {
        method: "POST",
      });
      const data = await res.json();
      setStatus(data.message || "✅ Real-time skin analysis started!, please wait...");
    } catch (err) {
      setStatus("❌ Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const captureSnapshot = async () => {
    try {
      setStatus("📸 Capturing snapshot...");
      await fetch("http://127.0.0.1:8000/capture-snapshot/", { method: "POST" });
      setStatus("✅ Snapshot captured!");
    } catch (err) {
      setStatus("❌ Capture error: " + err.message);
    }
  };

  const analyzeSnapshot = async () => {
    try {
      setStatus("🔍 Analyzing snapshot...");
      const res = await fetch("http://127.0.0.1:8000/analyze-snapshot/", { method: "POST" });
      const data = await res.json();
      setStatus(JSON.stringify(data, null, 2));
    } catch (err) {
      setStatus("❌ Analysis error: " + err.message);
    }
  };

  return (
    <div className="realtime-container">
      <h2 className="title">📹 Real-Time Skin Analysis</h2>
      <p className="subtitle">
        Run advanced AI-powered skin analysis live or on captured snapshots.
      </p>

      <div className="btn-group">
        <button className="btn start" onClick={startRealtime} disabled={loading}>
          {loading ? "⏳ Starting..." : "🚀 Start Analysis"}
        </button>
        <button className="btn back" onClick={goBackHome}>
          ⬅ Back
        </button>
      </div>

      {status && <pre className="status-box">{status}</pre>}
    </div>
  );
}
