"use client"

import React from "react"

function VideoFeed({ isConnected, selectedTop, selectedBottom, baseUrl }) {
  if (!isConnected) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-xl">
        <p className="text-lg text-red-500 font-semibold">Backend not connected</p>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Live camera feed from FastAPI */}
      <img
        src={`${baseUrl}/video`}
        alt="Live Camera Feed"
        className="w-full h-[500px] object-cover rounded-xl border border-gray-700"
      />

      {/* Overlay showing current selection */}
      <div className="absolute top-4 left-4 bg-black/60 text-white px-3 py-1 rounded-lg text-sm">
        {selectedTop} + {selectedBottom}
      </div>
    </div>
  )
}

export default VideoFeed
