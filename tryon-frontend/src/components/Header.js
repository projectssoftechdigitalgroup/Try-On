"use client"

import { useState, useEffect } from "react"

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[rgba(10,10,20,0.95)] backdrop-blur-2xl border-b border-[rgba(255,255,255,0.08)] shadow-2xl"
          : "bg-[rgba(10,10,20,0.8)] backdrop-blur-xl border-b border-[rgba(255,255,255,0.05)] shadow-lg"
      }`}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        {/* 🌟 Logo Section - Enhanced with dark theme */}
        <div className="flex items-center gap-3 cursor-pointer group transition-all duration-300 hover:scale-110">
          <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-cyan-500 flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.5)] group-hover:shadow-[0_0_40px_rgba(99,102,241,0.8)] transition-all duration-300">
            <span className="text-2xl animate-bounce" style={{ animationDuration: "2s" }}>
              👗
            </span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent tracking-tight">
              Style Saathi
            </h1>
            <p className="text-xs font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text">
              Your Fashion Companion ✨
            </p>
          </div>
        </div>

        {/* 🌈 Desktop Nav - Updated for dark theme */}
        <nav className="hidden md:flex items-center gap-10">
          {["Home", "Collections", "Try-On", "Contact"].map((item) => (
            <div key={item} className="relative group">
              <a
                href="#"
                className="relative text-sm font-bold text-slate-200 tracking-wide hover:text-cyan-400 transition-all duration-200 flex items-center gap-1"
              >
                {item}
                <span className="absolute left-0 -bottom-2 h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-blue-500 rounded-full transition-all duration-300 w-0 group-hover:w-full"></span>
              </a>

              {/* 🎭 Enhanced Dropdown for Try-On */}
              {item === "Try-On" && (
                <div className="absolute left-0 top-full mt-4 hidden group-hover:block bg-[rgba(20,20,43,0.95)] backdrop-blur-2xl border border-[rgba(255,255,255,0.1)] rounded-2xl shadow-2xl py-3 w-56 transform transition-all duration-300 origin-top opacity-0 group-hover:opacity-100 scale-95 group-hover:scale-100">
                  {["Eastern Wear 🌸", "Traditional Wear 💃"].map((option, idx) => (
                    <a
                      key={idx}
                      href="#"
                      className="block px-5 py-3 text-sm font-semibold text-slate-300 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-cyan-500/20 hover:text-cyan-400 rounded-xl transition-all duration-200 hover:translate-x-1"
                    >
                      {option}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* 🔘 Actions - Updated buttons for dark theme */}
        <div className="flex items-center gap-4">
          <button className="hidden sm:block px-7 py-2.5 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 text-white text-sm font-bold rounded-full shadow-lg hover:shadow-2xl hover:shadow-indigo-500/50 hover:scale-110 transition-all duration-200 active:scale-95 relative overflow-hidden group">
            <span className="relative z-10">Sign In</span>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-indigo-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </button>

          {/* 📱 Mobile Menu Toggle - Updated for dark theme */}
          <button
            className="md:hidden p-2.5 text-slate-300 hover:bg-gradient-to-br hover:from-indigo-500/20 hover:to-cyan-500/20 rounded-xl transition-all duration-200 hover:scale-110"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
              />
            </svg>
          </button>
        </div>
      </div>

      {/* 📱 Mobile Dropdown - Updated for dark theme */}
      {menuOpen && (
        <div className="md:hidden bg-[rgba(20,20,43,0.95)] border-t border-[rgba(255,255,255,0.08)] backdrop-blur-xl shadow-2xl animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="px-6 py-5 space-y-2">
            {["Home", "Collections", "Try-On", "Contact"].map((item) => (
              <div key={item}>
                <a
                  href="#"
                  className="block px-4 py-3 text-slate-300 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-cyan-500/20 hover:text-cyan-400 rounded-xl transition-all duration-200 font-bold text-sm hover:translate-x-1"
                >
                  {item}
                </a>

                {/* Mobile submenu under Try-On */}
                {item === "Try-On" && (
                  <div className="ml-4 mt-2 space-y-1">
                    {["Eastern Wear 🌸", "Traditional Wear 💃"].map((option, idx) => (
                      <a
                        key={idx}
                        href="#"
                        className="block px-4 py-2.5 text-sm text-slate-400 hover:bg-indigo-500/20 hover:text-cyan-400 rounded-lg transition-all duration-200 font-semibold"
                      >
                        {option}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <button className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 text-white font-bold rounded-xl shadow-lg hover:shadow-indigo-500/40 transition-all duration-200 active:scale-95">
              Sign In
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
