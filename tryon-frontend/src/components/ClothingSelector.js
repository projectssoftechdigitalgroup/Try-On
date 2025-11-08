"use client";

import { useState, useMemo } from "react";
import {
  Sparkles,
  Shirt,
  Package,
  Sparkle,
  User,
  Users,
  Baby,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  Loader2,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const ALL_CLOTHING_OPTIONS = [
  // === MALE - EASTERN WEAR ===
  { id: "m_shirt1", gender: "male", type: "tops", category: "Eastern-Wear", name: "Plain Shirt (Red)", image: "/database/male/Eastern-Wear/shirt1.png" },
  { id: "m_shirt2", gender: "male", type: "tops", category: "Eastern-Wear", name: "Plain Shirt (Black)", image: "/database/male/Eastern-Wear/shirt2.png" },
  { id: "m_shirt3", gender: "male", type: "tops", category: "Eastern-Wear", name: "Plain Shirt (White)", image: "/database/male/Eastern-Wear/shirt3.png" },
  { id: "m_polo", gender: "male", type: "tops", category: "Eastern-Wear", name: "Polo Shirt", image: "/database/male/Eastern-Wear/polo.png" },
  { id: "m_pant", gender: "male", type: "bottoms", category: "Eastern-Wear", name: "Formal Pants", image: "/database/male/Eastern-Wear/pant.png" },
  { id: "m_suit", gender: "male", type: "full_dress", category: "Eastern-Wear", name: "Full Suit", image: "/database/male/Eastern-Wear/full_suit.png" },

  // === MALE - TRADITIONAL WEAR ===
  { id: "m_kurta", gender: "male", type: "tops", category: "Traditional-Wear", name: "Kurta", image: "/database/male/Traditional-Wear/kurta.png" },
  { id: "m_pajama", gender: "male", type: "bottoms", category: "Traditional-Wear", name: "Pajama", image: "/database/male/Traditional-Wear/pajama.png" },

  // === FEMALE - EASTERN WEAR ===
  { id: "f_blouse", gender: "female", type: "tops", category: "Eastern-Wear", name: "Blouse", image: "/database/female/Eastern-Wear/blouse.png" },
  { id: "f_denim-jacket", gender: "female", type: "tops", category: "Eastern-Wear", name: "Denim Jacket", image: "/database/female/Eastern-Wear/denim-jacket.png" },
  { id: "f_tunic", gender: "female", type: "bottoms", category: "Eastern-Wear", name: "Tunic", image: "/database/female/Eastern-Wear/tunic.png" },
  { id: "f_jeans", gender: "female", type: "bottoms", category: "Eastern-Wear", name: "Jeans", image: "/database/female/Eastern-Wear/jeans.png" },
  { id: "f_skirt", gender: "female", type: "full_dress", category: "Eastern-Wear", name: "Skirt", image: "/database/female/Eastern-Wear/skirt.png" },
  { id: "f_sundress", gender: "female", type: "full_dress", category: "Eastern-Wear", name: "Sundress", image: "/database/female/Eastern-Wear/sundress.png" },
  { id: "f_gown", gender: "female", type: "full_dress", category: "Eastern-Wear", name: "Gown", image: "/database/female/Eastern-Wear/gown.png" },
  { id: "f_redskirt", gender: "female", type: "full_dress", category: "Eastern-Wear", name: "Red Skirt", image: "/database/female/Eastern-Wear/redskirt.png" },

  // === FEMALE - TRADITIONAL WEAR ===
  { id: "f_saree1", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Saree", image: "/database/female/Traditional-Wear/saree.png" },
  { id: "f_saree2", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Saree (Alt)", image: "/database/female/Traditional-Wear/saree2.png" },
  { id: "f_lehenga1", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Lehenga", image: "/database/female/Traditional-Wear/lehenga1.png" },
  { id: "f_lehenga2", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Lehenga (Alt 1)", image: "/database/female/Traditional-Wear/lehenga2.png" },
  { id: "f_lehenga3", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Lehenga (Alt 2)", image: "/database/female/Traditional-Wear/lehenga3.png" },
  { id: "f_lehenga4", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Lehenga (Alt 3)", image: "/database/female/Traditional-Wear/lehenga4.png" },
  { id: "f_suit2", gender: "female", type: "full_dress", category: "Traditional-Wear", name: "Suit", image: "/database/female/Traditional-Wear/suit2.png" },

  // === KIDS - BOY EASTERN WEAR ===
  { id: "kb_shirt", gender: "kid", type: "tops", category: "Eastern-Wear", name: "Boy Shirt", image: "/database/kids/boy/Eastern-Wear/shirt.png" },
  { id: "kb_shorts", gender: "kid", type: "bottoms", category: "Eastern-Wear", name: "Boy Shorts", image: "/database/kids/boy/Eastern-Wear/shorts.png" },
  { id: "kb_suit", gender: "kid", type: "full_dress", category: "Eastern-Wear", name: "Boy Suit", image: "/database/kids/boy/Eastern-Wear/suit.png" },

  // === KIDS - GIRL EASTERN WEAR ===
  { id: "kg_tshirt", gender: "kid", type: "tops", category: "Eastern-Wear", name: "Girl T-Shirt", image: "/database/kids/girl/Eastern-Wear/shirt.png" },
  { id: "kg_tshirt2", gender: "kid", type: "tops", category: "Eastern-Wear", name: "Girl T-Shirt 2", image: "/database/kids/girl/Eastern-Wear/shirt2.png" },
  { id: "kg_skirt", gender: "kid", type: "full_dress", category: "Eastern-Wear", name: "Girl Skirt", image: "/database/kids/girl/Eastern-Wear/skirt.png" },
  { id: "kg_skirt2", gender: "kid", type: "bottoms", category: "Eastern-Wear", name: "Girl Skirt 2", image: "/database/kids/girl/Eastern-Wear/skirt2.png" },
];

const ClothingSelector = ({
  selectedTop,
  selectedBottom,
  selectedDress,
  onTopChange,
  onBottomChange,
  onDressChange,
}) => {
  const [currentGender, setCurrentGender] = useState("male");
  const [kidsSubGender, setKidsSubGender] = useState("girl");
  const [activeCategory, setActiveCategory] = useState("tops");
  const [subCategory, setSubCategory] = useState("Eastern-Wear");
  const [status, setStatus] = useState({ message: "", type: "" });

  const filteredOptions = useMemo(() => {
    if (currentGender === "kid") {
      return ALL_CLOTHING_OPTIONS.filter(
        (c) =>
          c.gender === "kid" &&
          c.id.startsWith(kidsSubGender === "boy" ? "kb_" : "kg_") &&
          c.type === activeCategory &&
          c.category === subCategory
      );
    }
    return ALL_CLOTHING_OPTIONS.filter(
      (c) =>
        c.gender === currentGender &&
        c.type === activeCategory &&
        c.category === subCategory
    );
  }, [currentGender, kidsSubGender, activeCategory, subCategory]);

  const handleSelect = async (item) => {
    let newTop = selectedTop;
    let newBottom = selectedBottom;
    let newDress = selectedDress;
  
    // ✅ Top selected → update top, keep bottom, remove dress
    if (item.type === "tops") {
      newTop = item.id;
      newDress = "none";
    }
  
    // ✅ Bottom selected → update bottom, keep top, remove dress
    else if (item.type === "bottoms") {
      newBottom = item.id;
      newDress = "none";
    }
  
    // ✅ Full dress selected → hide both top & bottom
    else if (item.type === "full_dress") {
      newDress = item.id;
      newTop = "none";
      newBottom = "none";
    }
  
    // Update React state
    onTopChange(newTop);
    onBottomChange(newBottom);
    onDressChange(newDress);
  
    const clothingData = {
      gender: item.gender,
      top: newTop,
      bottom: newBottom,
      dress: newDress,
    };
  
    setStatus({ message: "Updating outfit...", type: "loading" });
  
    try {
      const res = await fetch(`${API_BASE}/clothes/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(clothingData),
      });
  
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
  
      setStatus({ message: "✅ Outfit updated successfully!", type: "success" });
      console.log("✅ Clothing updated:", data);
    } catch (err) {
      console.error("❌ Failed to update clothing:", err);
      setStatus({
        message: "❌ Failed to update outfit. Retrying...",
        type: "error",
      });
  
      setTimeout(() => handleSelect(item), 2000);
    }
  
    setTimeout(() => setStatus({ message: "", type: "" }), 4000);
  };
  
  const GENDER_TABS = [
    { id: "male", label: "Male", icon: <User className="w-4 h-4" /> },
    { id: "female", label: "Female", icon: <Users className="w-4 h-4" /> },
    { id: "kid", label: "Kids", icon: <Baby className="w-4 h-4" /> },
  ];

  return (
    <div className="container my-10">
      <div className="glass-strong p-6 text-white">
        <h2 className="text-3xl font-bold gradient-text mb-6 flex items-center gap-3">
          <Sparkles className="text-accent w-6 h-6" /> Outfit Selector
        </h2>

        {/* Status Message */}
        {status.message && (
          <div
            className={`mb-4 flex items-center gap-2 text-sm font-semibold ${
              status.type === "success"
                ? "text-green-400"
                : status.type === "error"
                ? "text-red-400"
                : "text-yellow-300"
            }`}
          >
            {status.type === "loading" && <Loader2 className="animate-spin w-4 h-4" />}
            {status.type === "success" && <CheckCircle className="w-4 h-4" />}
            {status.type === "error" && <AlertTriangle className="w-4 h-4" />}
            <span>{status.message}</span>
          </div>
        )}

        {/* Gender Selection */}
        <div className="category-selector">
          {GENDER_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentGender(tab.id)}
              className={`category-btn ${currentGender === tab.id ? "active" : ""}`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Kids Sub-Gender */}
        {currentGender === "kid" && (
          <div className="category-selector">
            {["boy", "girl"].map((g) => (
              <button
                key={g}
                onClick={() => setKidsSubGender(g)}
                className={`category-btn ${kidsSubGender === g ? "active" : ""}`}
              >
                {g === "boy" ? "Boy 👦" : "Girl 👧"}
              </button>
            ))}
          </div>
        )}

        {/* Subcategory */}
        <div className="category-selector">
          {["Eastern-Wear", "Traditional-Wear"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSubCategory(cat)}
              className={`category-btn ${subCategory === cat ? "active" : ""}`}
            >
              {cat === "Eastern-Wear" ? "Eastern 🌸" : "Traditional 💃"}
            </button>
          ))}
        </div>

        {/* Category Tabs */}
        <div className="category-selector">
          {[
            { id: "tops", label: "Tops", icon: <Shirt className="w-4 h-4" /> },
            { id: "bottoms", label: "Bottoms", icon: <Package className="w-4 h-4" /> },
            { id: "full_dress", label: "Full Dress", icon: <Sparkle className="w-4 h-4" /> },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`category-btn ${activeCategory === cat.id ? "active" : ""}`}
            >
              {cat.icon}
              {cat.label}
            </button>
          ))}
        </div>

        {/* Clothing Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6 mt-6">
          {filteredOptions.map((item) => (
            <div
              key={item.id}
              onClick={() => handleSelect(item)}
              className="glass card-3d p-4 cursor-pointer text-center pulse-glow relative"
            >
              <img
                src={item.image}
                alt={item.name}
                className="w-full h-44 object-contain mb-3 rounded-lg float-animation"
              />
              <p className="text-sm font-semibold tracking-wide">{item.name}</p>
              <ChevronRight className="absolute right-3 top-3 text-gray-400 w-4 h-4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClothingSelector;
