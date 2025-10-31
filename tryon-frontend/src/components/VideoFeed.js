"use client"

import { useState, useEffect } from "react"

export default function VideoFeed({
  selectedTop,
  selectedBottom,
  selectedDress,
  selectedCategory,
  isConnected
}) {
  const [isVisible, setIsVisible] = useState(true)

  const selectedClothing = {
    top: selectedTop,
    bottom: selectedBottom,
    dress: selectedDress,
    category: selectedCategory,
  }

  const hasSelection =
    (selectedClothing.top && selectedClothing.top !== "none") ||
    (selectedClothing.bottom && selectedClothing.bottom !== "none") ||
    (selectedClothing.dress && selectedClothing.dress !== "none")

  useEffect(() => {
    console.log("🎥 VideoFeed mounted. Props:", {
      selectedClothing,
      isConnected,
    })
    setIsVisible(true)
  }, [selectedClothing, isConnected])

  if (!isVisible) {
    return (
      <div className="text-center text-red-400 py-8">
        ⚠️ Video Feed failed to load
      </div>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8 relative z-10">
      {/* ===== VIDEO FEED BOX ===== */}
      <div className="relative rounded-2xl overflow-hidden backdrop-blur-md bg-gradient-to-br from-indigo-500/10 via-cyan-500/5 to-indigo-500/10 border border-indigo-500/20 shadow-2xl">
        {/* ===== LIVE CAMERA FEED ===== */}
        <div className="relative flex flex-col items-center justify-center bg-black">
          <h3 className="text-2xl font-bold mt-4 text-blue-400">
            Live Camera Feed
          </h3>
          <div className="rounded-2xl overflow-hidden shadow-lg border border-gray-700 bg-black mt-4">
            <img
              src="http://127.0.0.1:8000/clothes/video"
              alt="Live Camera Stream"
              className="w-[800px] h-[500px] object-cover"
              onError={() => console.error("⚠️ Video feed not found")}
            />
          </div>
          <p className="mt-4 text-gray-300">
            {isConnected
              ? "✨ Ready to see your look!"
              : "Connecting to backend..."}
          </p>
        </div>
      </div>

      {/* ===== Selected Items Section ===== */}
      {hasSelection && (
        <div className="mt-8 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-cyan-500 rounded-full" />
            <h3 className="text-xl font-bold text-slate-100">Your Selection</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {selectedClothing.top !== "none" && (
              <ItemCard label="Top" icon="👕" value={selectedClothing.top} />
            )}
            {selectedClothing.bottom !== "none" && (
              <ItemCard label="Bottom" icon="👖" value={selectedClothing.bottom} />
            )}
            {selectedClothing.dress !== "none" && (
              <ItemCard label="Dress" icon="👗" value={selectedClothing.dress} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ====== Subcomponent for Selection Cards ======
function ItemCard({ label, icon, value }) {
  return (
    <div className="group relative">
      <div className="relative backdrop-blur-md bg-gradient-to-br from-indigo-500/10 to-cyan-500/10 border border-indigo-500/30 rounded-xl p-4 transition-all duration-300 hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/20">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider">
              {label}
            </p>
            <p className="text-slate-100 font-semibold">{value}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
