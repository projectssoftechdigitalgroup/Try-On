"use client"

import { useState, useEffect } from "react"
import { VideoFeed } from "@/components/video-feed"
import { ClothingSelector } from "@/components/clothing-selector"
import { Header } from "@/components/header"
import { StatusIndicator } from "@/components/status-indicator"

export default function VirtualTryOnApp() {
  const [selectedTop, setSelectedTop] = useState("shirt")
  const [selectedBottom, setSelectedBottom] = useState("pant")
  const [isConnected, setIsConnected] = useState(false)

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch("http://localhost:8000/video_feed")
        setIsConnected(response.ok)
      } catch (error) {
        setIsConnected(false)
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Video Feed Section */}
          <div className="lg:col-span-2">
            <div className="glass rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold gradient-text">Virtual Try-On</h2>
                <StatusIndicator isConnected={isConnected} />
              </div>

              <VideoFeed isConnected={isConnected} selectedTop={selectedTop} selectedBottom={selectedBottom} />
            </div>
          </div>

          {/* Clothing Selection Panel */}
          <div className="space-y-6">
            <ClothingSelector
              selectedTop={selectedTop}
              selectedBottom={selectedBottom}
              onTopChange={setSelectedTop}
              onBottomChange={setSelectedBottom}
            />

            {/* Instructions */}
            <div className="glass rounded-xl p-4">
              <h3 className="font-semibold mb-3 text-accent">How to Use</h3>
              <ul className="text-sm text-muted-foreground space-y-2">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full" />
                  Stand in front of your camera
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full" />
                  Select clothing items from the panel
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full" />
                  See clothes overlay in real-time
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
