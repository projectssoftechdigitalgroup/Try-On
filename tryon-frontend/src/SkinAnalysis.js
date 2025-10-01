import React, { useState, useEffect } from "react";
import "./SkinAnalysis.css";

const getProductSuggestions = (tone) => {
  if (!tone) return [];
  if (tone.includes("Fair") || tone.includes("Light")) {
    return [
      { name: "Moisturizing Sunscreen SPF 50", img: "/products/sunscreen_fair.jpg", link: "https://www.laroche-posay.us/our-products/sun/face-sunscreen/anthelios-mineral-zinc-oxide-sunscreen-spf-50-883140000907.html" },
      { name: "Hydrating Face Serum", img: "/products/serum_fair.jpg", link: "https://theordinary.com/en-pk/hyaluronic-acid-2-b5-serum-with-ceramides-100637.html" },
      { name: "Brightening Cleanser", img: "/products/cleanser_fair.jpg", link: "https://www.cerave.com/skincare/cleansers/foaming-facial-cleanser" },
    ];
  } else if (tone.includes("Medium") || tone.includes("Tan")) {
    return [
      { name: "Vitamin C Serum", img: "/products/vitaminC_medium.jpg", link: "https://truskin.com/products/best-vitamin-c-serum-for-face" },
      { name: "Oil-Free Moisturizer", img: "/products/moisturizer_medium.jpg", link: "https://www.neutrogena.com/products/skincare/neutrogena-hydro-boost-water-gel-with-hyaluronic-acid/6811047" },
      { name: "SPF 30 Sunblock", img: "/products/sunblock_medium.jpg", link: "https://www.cetaphil.com/us/products/product-categories/sunscreens" },
    ];
  } else if (tone.includes("Deep") || tone.includes("Dark")) {
    return [
      { name: "Shea Butter Moisturizer", img: "/products/shea_dark.jpg", link: "https://globalmamas.org/shop/shea-butter-lotion-unscented/" },
      { name: "SPF 30 Sunscreen", img: "/products/sunscreen_dark.jpg", link: "https://blackgirlsunscreen.com/product/black-girl-sunscreen-spf-30/" },
      { name: "Hydrating Night Cream", img: "/products/nightcream_dark.jpg", link: "https://www.cerave.com/skincare/moisturizers/skin-renewing-night-cream" },
    ];
  } else {
    return [{ name: "Balanced Skincare Routine Kit", img: "/products/routine_general.jpg", link: "#" }];
  }
};

const SkinAnalysis = ({ uploadedImage, goBackHome }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState(null);

  useEffect(() => {
    if (uploadedImage) {
      setResult(null);
      setSelectedMethod(null);
    }
  }, [uploadedImage]);

  const handleAnalyze = async (method) => {
    if (!uploadedImage) return alert("⚠️ Upload an image first.");

    let fileToSend = uploadedImage;
    if (!(uploadedImage instanceof File)) {
      try {
        const resp = await fetch(uploadedImage);
        if (!resp.ok) throw new Error("Failed to fetch uploaded image");
        const blob = await resp.blob();
        fileToSend = new File([blob], "photo.jpg", { type: blob.type || "image/jpeg" });
      } catch (err) {
        console.error("Failed to convert image URL to File:", err);
        return alert("⚠️ Could not load image for analysis.");
      }
    }

    const formData = new FormData();
    formData.append("file", fileToSend);

    try {
      setLoading(true);
      setSelectedMethod(method);
      const res = await fetch(`http://127.0.0.1:8000/analyze-skin/${method}/`, { method: "POST", body: formData });
      let data = await res.json();

      if (data.remarks && typeof data.remarks === "string") {
        const jsonMatch = data.remarks.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try { data = JSON.parse(jsonMatch[0]); } catch { console.warn("Failed to parse JSON."); }
        }
      }

      console.log("DEBUG response:", data);
      setResult(data);
    } catch (err) {
      console.error(`${method} analysis error:`, err);
      alert(`❌ Failed to analyze skin tone with ${method}.`);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!result) return alert("No analysis to download!");
    const products = getProductSuggestions(result.skin_tone).map(p => `${p.name}: ${p.link}`).join("\n");
    const text = `Skin Analysis Report\n\nSkin Tone: ${result.skin_tone || "N/A"}\nUndertone: ${result.undertone || "N/A"}\nRemarks: ${result.remarks || "N/A"}\n\nSuggested Products:\n${products}`;
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "skin_analysis_report.txt";
    link.click();
  };

  const analysisMethods = [
    { id: "mediapipe", title: "Skin Analyze with MediaPipe FaceMesh" },
    { id: "groq", title: "Skin Analyze with Groq AI" },
    { id: "gemini", title: "Skin Analyze with Gemini AI" }, // ✅ Added Gemini
  ];

  return (
    <div className="analysis-container">
      <h2 className="title">🧴 Skin Analysis</h2>

      {uploadedImage && (
        <div className="preview-container">
          <img src={uploadedImage instanceof File ? URL.createObjectURL(uploadedImage) : uploadedImage} alt="Skin preview" className="preview-img" />
        </div>
      )}

      <div className="method-grid">
        {analysisMethods.map((method) => (
          <div key={method.id} className={`method-card ${selectedMethod === method.id ? "active" : ""}`}>
            <h3>{method.title}</h3>
            <button className="analyze-btn" onClick={() => handleAnalyze(method.id)}>Analyze</button>
          </div>
        ))}
      </div>

      {loading && <p className="loading">⏳ Analyzing with {selectedMethod}...</p>}

      {result && (
        <div className="analysis-result">
          {result.skin_tone && <p>✨ <strong>Detected Skin Tone:</strong> {result.skin_tone}</p>}
          {result.undertone && <p>🎨 <strong>Undertone:</strong> {result.undertone}</p>}
          {result.remarks && <p>📝 <strong>Remarks:</strong> {result.remarks}</p>}

          {result.skin_tone && (
            <div className="product-section">
              <h4>🛍️ Suggested Products:</h4>
              <div className="product-list">
                {getProductSuggestions(result.skin_tone).map((product, i) => (
                  <div key={i} className="product-card">
                    <a href={product.link} target="_blank" rel="noopener noreferrer">
                      <img src={product.img} alt={product.name} className="product-img" />
                      <p className="product-name">{product.name}</p>
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="action-buttons">
            <button className="download-btn" onClick={downloadReport}>💾 Download Report</button>
            <button className="home-btn" onClick={() => goBackHome && goBackHome()}>🏠 Back Home</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkinAnalysis;
