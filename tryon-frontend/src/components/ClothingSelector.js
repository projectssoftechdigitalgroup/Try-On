"use client"

import { useState } from "react"
import { Sparkles, Shirt, Package } from "lucide-react"

const colorClasses = {
  Red: "bg-red-500",
  "Olive Green": "bg-green-700",
  Black: "bg-black",
  Green: "bg-green-500",
  Blue: "bg-blue-500",
  White: "bg-white border border-gray-300",
}

const topOptions = [
  { id: "shirt1", name: "Plain T-Shirt", image: "/shirt1.png", description: "Basic casual t-shirt", color: "Red" },
  { id: "shirt3", name: "Plain T-Shirt", image: "/shirt3.png", description: "Basic casual t-shirt", color: "Olive Green" },
  { id: "shirt2", name: "Plain T-Shirt", image: "/shirt2.png", description: "Basic casual t-shirt", color: "Black" },
  { id: "polo", name: "Plain Polo Shirt", image: "/polo.png", description: "Basic casual polo shirt", color: "Green" },
]

// ✅ Only keep bottoms supported by backend (pant)
const bottomOptions = [
  { id: "pant", name: "Formal Pants", image: "/pant.png", description: "Classic dress pants", color: "Black" },
]

const ClothingSelector = ({ selectedTop, selectedBottom, onTopChange, onBottomChange }) => {
  const [activeCategory, setActiveCategory] = useState("tops")

  // 🔗 Update backend state
  const updateBackend = async (top, bottom) => {
    try {
      await fetch("http://localhost:8000/update_clothing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ top, bottom }),
      })
    } catch (err) {
      console.error("❌ Failed to update backend:", err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-3 glass-strong rounded-full px-6 py-3 mb-4">
          <Sparkles className="w-5 h-5 text-accent" />
          <h3 className="text-xl font-bold gradient-text">Fashion Collection</h3>
        </div>
        <p className="text-muted-foreground text-sm">Select your perfect outfit combination</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-3 mb-8">
        <button
          className={`flex-1 relative overflow-hidden rounded-2xl p-4 font-semibold transition-all duration-300 ${
            activeCategory === "tops"
              ? "bg-gradient-to-r from-primary to-accent text-white shadow-lg shadow-primary/25 card-3d"
              : "glass hover:glass-strong text-foreground"
          }`}
          onClick={() => setActiveCategory("tops")}
        >
          <div className="flex items-center justify-center gap-2">
            <Shirt className="w-5 h-5" />
            <span>Tops</span>
          </div>
        </button>
        <button
          className={`flex-1 relative overflow-hidden rounded-2xl p-4 font-semibold transition-all duration-300 ${
            activeCategory === "bottoms"
              ? "bg-gradient-to-r from-primary to-accent text-white shadow-lg shadow-primary/25 card-3d"
              : "glass hover:glass-strong text-foreground"
          }`}
          onClick={() => setActiveCategory("bottoms")}
        >
          <div className="flex items-center justify-center gap-2">
            <Package className="w-5 h-5" />
            <span>Bottoms</span>
          </div>
        </button>
      </div>

      {/* Clothing Options */}
      <div className="space-y-4">
        {activeCategory === "tops" &&
          topOptions.map((option) => {
            const isSelected = selectedTop === option.id
            return (
              <div
                key={option.id}
                className={`group relative overflow-hidden cursor-pointer transition-all duration-500 rounded-2xl ${
                  isSelected
                    ? "glass-strong pulse-glow card-3d scale-105"
                    : "glass hover:glass-strong hover:scale-102 card-3d"
                }`}
                onClick={() => {
                  onTopChange(option.id)
                  updateBackend(option.id, selectedBottom) // 🔗 update backend
                }}
              >
                <div className="p-6 flex items-center gap-4">
                  <div
                    className={`relative w-20 h-20 rounded-xl overflow-hidden border-2 flex items-center justify-center ${
                      isSelected ? "border-primary shadow-lg shadow-primary/25" : "border-border"
                    }`}
                  >
                    <img src={option.image} alt={option.name} className="w-full h-full object-contain transition-transform group-hover:scale-110" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="font-bold text-lg">{option.name}</h5>
                      <div className={`w-3 h-3 rounded-full ${colorClasses[option.color]}`} />
                    </div>
                    <p className="text-muted-foreground text-sm mb-2">{option.description}</p>
                    <div className={`text-xs font-medium ${isSelected ? "text-primary" : "text-muted-foreground"}`}>
                      {isSelected ? "✨ Currently Selected" : "Click to try on"}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}

        {activeCategory === "bottoms" &&
          bottomOptions.map((option) => {
            const isSelected = selectedBottom === option.id
            return (
              <div
                key={option.id}
                className={`group relative overflow-hidden cursor-pointer transition-all duration-500 rounded-2xl ${
                  isSelected
                    ? "glass-strong pulse-glow card-3d scale-105"
                    : "glass hover:glass-strong hover:scale-102 card-3d"
                }`}
                onClick={() => {
                  onBottomChange(option.id)
                  updateBackend(selectedTop, option.id) // 🔗 update backend
                }}
              >
                <div className="p-6 flex items-center gap-4">
                  <div
                    className={`relative w-20 h-20 rounded-xl overflow-hidden border-2 flex items-center justify-center ${
                      isSelected ? "border-primary shadow-lg shadow-primary/25" : "border-border"
                    }`}
                  >
                    <img src={option.image} alt={option.name} className="w-full h-full object-contain transition-transform group-hover:scale-110" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="font-bold text-lg">{option.name}</h5>
                      <div className={`w-3 h-3 rounded-full ${colorClasses[option.color]}`} />
                    </div>
                    <p className="text-muted-foreground text-sm mb-2">{option.description}</p>
                    <div className={`text-xs font-medium ${isSelected ? "text-primary" : "text-muted-foreground"}`}>
                      {isSelected ? "✨ Currently Selected" : "Click to try on"}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}

export default ClothingSelector
