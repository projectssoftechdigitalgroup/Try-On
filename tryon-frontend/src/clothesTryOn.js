"use client"

import { useState, useEffect } from "react"
import VideoFeed from "./components/VideoFeed"
import ClothingSelector from "./components/ClothingSelector"
import Header from "./components/Header"
import StatusIndicator from "./components/StatusIndicator"
import "./clothesTryOn.css"
import "./index.css"

function ClothesTryOn() {
  const [selectedTop, setSelectedTop] = useState("shirt1")   // default
  const [selectedBottom, setSelectedBottom] = useState("pant")
  const [isConnected, setIsConnected] = useState(false)

  // ✅ Backend base URL
  const BASE_URL = "http://127.0.0.1:8000/clothes"

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${BASE_URL}/health`, {
          method: "GET",
          headers: { Accept: "application/json" },
        })
        setIsConnected(response.ok)
      } catch (error) {
        console.error("[ClothesTryOn] Backend connection failed:", error)
        setIsConnected(false)
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 3000)
    return () => clearInterval(interval)
  }, [])

  // 🔄 Update backend clothing selection whenever it changes
  useEffect(() => {
    const updateSelection = async () => {
      try {
        const response = await fetch(`${BASE_URL}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ top: selectedTop, bottom: selectedBottom }),
        })
        const data = await response.json()
        console.log("[ClothesTryOn] Updated selection:", data)
      } catch (error) {
        console.error("[ClothesTryOn] Failed to update selection:", error)
      }
    }

    if (isConnected) {
      updateSelection()
    }
  }, [selectedTop, selectedBottom, isConnected])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />

      <main className="container mx-auto px-6 py-12">
        <div className="text-center mb-16">
          <h1 className="text-6xl md:text-8xl font-bold gradient-text mb-6 float-animation">
            IMMERSIVE
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Experience the future of fashion with our AI-powered virtual try-on
            technology
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-12">
          {/* Left side: Video Feed */}
          <div className="lg:col-span-2">
            <div className="glass-strong rounded-3xl p-8 card-3d">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold gradient-text">
                  Virtual Try-On Studio
                </h2>
                <StatusIndicator isConnected={isConnected} />
              </div>

              <div className="video-container">
                <div className="video-inner">
                  <VideoFeed
                    isConnected={isConnected}
                    baseUrl={BASE_URL}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right side: Clothing Selector + Instructions */}
          <div className="space-y-8">
            <div className="glass-strong rounded-2xl p-6">
              <ClothingSelector
                selectedTop={selectedTop}
                selectedBottom={selectedBottom}
                onTopChange={setSelectedTop}
                onBottomChange={setSelectedBottom}
              />
            </div>

            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-bold mb-6 gradient-text">
                How to Use
              </h3>
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center text-sm font-bold">
                    1
                  </div>
                  <span className="text-foreground">
                    Position yourself in front of the camera
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center text-sm font-bold">
                    2
                  </div>
                  <span className="text-foreground">
                    Select clothing from the collection
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center text-sm font-bold">
                    3
                  </div>
                  <span className="text-foreground">
                    Watch the magic happen in real-time
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default ClothesTryOn
