import React from "react"
import ReactDOM from "react-dom/client"
import "./index.css"
import App from "./App"

// ✅ Import modern Google font
const globalFont = document.createElement("link")
globalFont.href = "https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap"
globalFont.rel = "stylesheet"
document.head.appendChild(globalFont)

// ✅ Add global styling dynamically for immersive visuals
const style = document.createElement("style")
style.textContent = `
  body {
    margin: 0;
    padding: 0;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #0a0a0f 0%, #111827 40%, #1e293b 100%);
    background-attachment: fixed;
    color: #f1f5f9;
    overflow-x: hidden;
  }

  #root {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding-top: 5vh;
    animation: fadeIn 1.2s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Optional subtle particle-style background effect */
  .background-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 25% 25%, rgba(255,255,255,0.08) 0%, transparent 60%),
                radial-gradient(circle at 75% 75%, rgba(255,255,255,0.05) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }

  /* Smooth scroll for transitions */
  html {
    scroll-behavior: smooth;
  }
`
document.head.appendChild(style)

const BackgroundOverlay = () => <div className="background-overlay"></div>

const root = ReactDOM.createRoot(document.getElementById("root"))
root.render(
  <React.StrictMode>
    <BackgroundOverlay />
    <div className="w-full max-w-[1600px] px-6 md:px-10 lg:px-20 relative z-10">
      <App />
    </div>
  </React.StrictMode>,
)
