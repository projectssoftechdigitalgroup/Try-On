"use client";

import { useState, useEffect } from "react";
import VideoFeed from "./components/VideoFeed";
import ClothingSelector from "./components/ClothingSelector";
import Header from "./components/Header";
import StatusIndicator from "./components/StatusIndicator";
import "./clothesTryOn.css";

function App() {
  const [selectedTop, setSelectedTop] = useState("tshirt1");
  const [selectedBottom, setSelectedBottom] = useState("jeans1");
  const [selectedDress, setSelectedDress] = useState("none");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/clothes/health");
        setIsConnected(response.ok);
      } catch {
        setIsConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="tryon-page">

      {/* ===== HEADER ===== */}
      <Header />

      {/* ===== HERO SECTION ===== */}
      <section className="hero-section">
        <h1 className="hero-title">IMMERSIVE VIRTUAL TRY-ON</h1>
        <p className="hero-subtext">
          Step into the future of fashion with <span>AI-powered virtual try-on</span> —
          personalize your style and preview your look in real-time.
        </p>
      </section>

      {/* ===== MAIN CONTENT ===== */}
      <main className="main-container">

        {/* === VIDEO PREVIEW PANEL === */}
        <div className="panel video-panel">
          <div className="panel-header">
            <h2>Virtual Try-On Studio</h2>
            <StatusIndicator isConnected={isConnected} />
          </div>

          <div className="video-frame">
            <VideoFeed
              isConnected={isConnected}
              selectedTop={selectedTop}
              selectedBottom={selectedBottom}
              selectedDress={selectedDress}
              selectedCategory={selectedCategory}
            />
          </div>
        </div>

        {/* === OUTFIT SELECTOR PANEL === */}
        <div className="panel selector-panel">
          <h3>Choose Your Outfit</h3>

          <ClothingSelector
            selectedTop={selectedTop}
            selectedBottom={selectedBottom}
            selectedDress={selectedDress}
            selectedCategory={selectedCategory}
            onTopChange={setSelectedTop}
            onBottomChange={setSelectedBottom}
            onDressChange={setSelectedDress}
            onCategoryChange={setSelectedCategory}
          />
        </div>

        {/* === HOW IT WORKS PANEL === */}
        <div className="panel how-it-works">
          <h3>How It Works</h3>

          <div className="how-step">
            <div className="step-badge">1</div>
            <span>Stand in front of your camera clearly</span>
          </div>

          <div className="how-step">
            <div className="step-badge">2</div>
            <span>Select an outfit from the options</span>
          </div>

          <div className="how-step">
            <div className="step-badge">3</div>
            <span>See your chosen style appear instantly!</span>
          </div>
        </div>

      </main>

      {/* ===== FOOTER ===== */}
      <footer className="footer">
        © {new Date().getFullYear()} Virtual Try-On by Hussain Kazmi. All rights reserved.
      </footer>
    </div>
  );
}

export default App;
