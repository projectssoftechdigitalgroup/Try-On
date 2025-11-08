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
    <div className="min-h-screen bg-black text-white flex flex-col overflow-y-auto custom-scrollbar">
      
      {/* HEADER */}
      <Header />

      {/* HERO */}
      <section className="text-center py-32 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-600/10 to-transparent blur-[160px]" />
        
        <h1 className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tight gradient-text drop-shadow-xl">
          Virtual Try-On Studio
        </h1>

        <p className="text-gray-300 text-lg mt-6 max-w-3xl mx-auto">
          Experience next-generation fashion preview — powered by 
          <span className="text-purple-400 font-semibold"> real-time AI styling.</span>
        </p>
      </section>

      {/* MAIN */}
      <main className="flex flex-col gap-16 items-center px-6 pb-32">

        {/* VIDEO FEED */}
        <div className="glass-strong w-full max-w-6xl rounded-3xl p-10 border border-white/10 shadow-[0_0_25px_rgba(139,92,246,0.3)] card-3d">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold gradient-text">Live Try-On Preview</h2>
            <StatusIndicator isConnected={isConnected} />
          </div>

          <div className="rounded-2xl overflow-hidden border border-white/20 video-container bg-black/60 p-[3px]">
            <div className="video-inner rounded-xl overflow-hidden">
              <VideoFeed
                isConnected={isConnected}
                selectedTop={selectedTop}
                selectedBottom={selectedBottom}
                selectedDress={selectedDress}
                selectedCategory={selectedCategory}
              />
            </div>
          </div>
        </div>

        {/* SELECTOR */}
        <div className="glass w-full max-w-4xl rounded-3xl p-10 border border-white/10 card-3d">
          <h3 className="text-2xl mb-8 font-semibold gradient-text">Choose Your Outfit</h3>

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

        {/* HOW IT WORKS */}
        <div className="glass w-full max-w-3xl rounded-3xl border border-white/10 p-10 card-3d">
          <h3 className="text-2xl font-semibold mb-10 gradient-text">How It Works</h3>

          {[
            "Stand clearly in front of the camera",
            "Select the outfit you want to preview",
            "The AI will overlay your selected style in real-time"
          ].map((step, index) => (
            <div key={index} className="flex items-start gap-5 mb-6 group">
              <div className="w-10 h-10 flex items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-cyan-400 text-white font-bold shadow-lg group-hover:scale-110 transition">
                {index + 1}
              </div>
              <p className="text-gray-300 pt-1 leading-relaxed">{step}</p>
            </div>
          ))}
        </div>

      </main>

      {/* FOOTER */}
      <footer className="text-center text-gray-500 py-6 text-sm border-t border-white/10">
        © {new Date().getFullYear()} Virtual Try-On by Hussain Kazmi — Futuristic Fashion UI ✨
      </footer>

    </div>
  );
}

export default App;
