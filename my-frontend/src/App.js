"use client"

import { useState, useEffect } from "react"
import VideoFeed from "./components/VideoFeed"
import ClothingSelector from "./components/ClothingSelector"
import Header from "./components/Header"
import StatusIndicator from "./components/StatusIndicator"
import "./App.css"

function App() {
  const [selectedTop, setSelectedTop] = useState("shirt")
  const [selectedBottom, setSelectedBottom] = useState("pant")
  const [selectedDress, setSelectedDress] = useState("none")
  const [selectedCategory, setSelectedCategory] = useState("All")
  const [isConnected, setIsConnected] = useState(false)

  // Backend connection health check
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/health", {
          method: "GET",
          headers: { Accept: "application/json" },
        })
        setIsConnected(response.ok)
      } catch (error) {
        console.error("App - Backend connection failed:", error)
        setIsConnected(false)
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-black text-white overflow-hidden">
      {/* ===== HEADER ===== */}
      <Header />

      {/* ===== HERO SECTION ===== */}
      <section className="pt-48 pb-24 text-center relative">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/20 to-transparent blur-3xl opacity-30 pointer-events-none" />
        <h1 className="text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-blue-500 to-cyan-400 animate-gradient">
          IMMERSIVE VIRTUAL TRY-ON
        </h1>
        <p className="text-lg md:text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
          Step into the future of fashion with <span className="text-accent font-semibold">AI-powered virtual try-on</span> —
          personalize your style and preview your look in real-time.
        </p>
      </section>

      {/* ===== MAIN CONTENT ===== */}
      {/* ===== MAIN CONTENT ===== */}
      <main className="container mx-auto px-6 pb-24">
        {/* === VIDEO FEED & CLOTHING SELECTOR STACKED === */}
        <div className="flex flex-col items-center gap-12">
          {/* === VIDEO FEED === */}
          <div className="w-full max-w-6xl">
            <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl p-8 transition-transform hover:scale-[1.01] duration-300">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-blue-600">
                  Virtual Try-On Studio
                </h2>
                <StatusIndicator isConnected={isConnected} />
              </div>
              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/50 p-2">
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

          {/* === CLOTHING SELECTOR BELOW VIDEO FEED === */}
          <div className="w-full max-w-4xl bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 shadow-xl p-8 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300">
            <h3 className="text-2xl font-bold mb-6 text-blue-400">Choose Your Outfit</h3>
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

          {/* === HOW IT WORKS SECTION === */}
          <div className="w-full max-w-3xl bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 shadow-xl p-8 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300">
            <h3 className="text-2xl font-bold mb-8 text-cyan-400">How It Works</h3>
            <div className="space-y-6">
              {[{ step: 1, text: "Stand in front of your camera clearly" },
                { step: 2, text: "Select an outfit from the options" },
                { step: 3, text: "See your chosen style appear instantly!" }].map((item) => (
                <div key={item.step} className="flex items-start gap-4 group">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/40 group-hover:scale-110 transition-transform duration-300">
                    {item.step}
                  </div>
                  <span className="text-gray-200 font-medium leading-relaxed pt-1">{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
      
      {/* ===== FOOTER ===== */}
      <footer className="text-center text-gray-500 text-sm py-6 border-t border-white/10">
        © {new Date().getFullYear()} Virtual Try-On by Hussain Kazmi. All rights reserved.
      </footer>
    </div>
  )
}

export default App
