import { useState } from "react"
import { Menu, Zap, X } from "lucide-react"

const Header = () => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <header className="navbar sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto w-full">

        {/* Left: Logo */}
        <div className="flex-none flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-primary to-accent rounded-xl flex items-center justify-center shadow-lg shadow-primary/40">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold gradient-text">VirtualFit</h1>
            <p className="text-xs text-muted-foreground">AR Fashion Studio</p>
          </div>
        </div>

        {/* Center: Nav Links */}
        <nav className="hidden md:flex flex-1 justify-center space-x-10">
          <a href="#studio" className="relative group text-foreground hover:text-accent transition-all duration-300">
            Studio
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-primary to-accent transition-all duration-300 group-hover:w-full"></span>
          </a>
          <a href="#collection" className="relative group text-foreground hover:text-accent transition-all duration-300">
            Collection
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-primary to-accent transition-all duration-300 group-hover:w-full"></span>
          </a>
          <a href="#about" className="relative group text-foreground hover:text-accent transition-all duration-300">
            About
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-primary to-accent transition-all duration-300 group-hover:w-full"></span>
          </a>
        </nav>

        {/* Right: CTA */}
        <div className="hidden md:flex flex-none">
          <a href="#get-started" className="cta-btn">Get Started</a>
        </div>

        {/* Mobile Hamburger */}
        <button
          className="md:hidden glass rounded-lg p-2 ml-2"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden flex flex-col items-center space-y-4 py-4 glass">
          <a href="#studio" className="text-foreground hover:text-accent transition">Studio</a>
          <a href="#collection" className="text-foreground hover:text-accent transition">Collection</a>
          <a href="#about" className="text-foreground hover:text-accent transition">About</a>
          <a href="#get-started" className="cta-btn">Get Started</a>
        </div>
      )}
    </header>
  )
}

export default Header
