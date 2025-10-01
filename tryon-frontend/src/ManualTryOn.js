import React, { useMemo, useState } from "react";
import "./ManualTryOn.css";

const API_BASE = "http://127.0.0.1:8000";

const CATEGORY_PALETTES = {
  foundation: [
    { name: "Light", hex: "#F3E5D8" },
    { name: "Medium", hex: "#D9B99B" },
    { name: "Dark", hex: "#7E553A" },
  ],
  blush: [
    { name: "Light", hex: "#F7A5B2" },
    { name: "Medium", hex: "#EB7C93" },
    { name: "Dark", hex: "#D9536A" },
  ],
  eyeshadow: [
    { name: "Light", hex: "#D8C4B6" },
    { name: "Medium", hex: "#8E6E5E" },
    { name: "Dark", hex: "#6A1B9A" },
  ],
  kohl: [
    { name: "Light", hex: "#3E2723" },
    { name: "Medium", hex: "#142850" },
    { name: "Dark", hex: "#000000" },
  ],
  mascara: [
    { name: "Light", hex: "#3E2723" },
    { name: "Medium", hex: "#1A1A1A" },
    { name: "Dark", hex: "#000000" },
  ],
  lipstick: [
    { name: "Light", hex: "#B56576" },
    { name: "Medium", hex: "#CF2F3A" },
    { name: "Dark", hex: "#9B111E" },
  ],
};

const CATEGORY_LABELS = {
  foundation: "Foundation",
  blush: "Blush",
  eyeshadow: "Eyeshadow",
  kohl: "Kohl",
  mascara: "Mascara",
  lipstick: "Lipstick",
};

const APPLY_ORDER = ["foundation","blush","eyeshadow","kohl","mascara","lipstick"];
const INTENSITY_DEFAULTS = { foundation:100, blush:60, eyeshadow:60, kohl:95, mascara:85, lipstick:85 };

const ManualTryOn = ({ uploadedImage }) => {
  const [selected, setSelected] = useState({
    foundation:null, blush:null, eyeshadow:null, kohl:null, mascara:null, lipstick:null
  });
  const [intensity, setIntensity] = useState({ ...INTENSITY_DEFAULTS });
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressText, setProgressText] = useState("");

  const baseImage = useMemo(() => resultImage || uploadedImage, [resultImage, uploadedImage]);
  const onPick = (cat, c) => setSelected(prev => ({ ...prev, [cat]: c }));

  const fetchUrlAsFile = async (url, filename="image.jpg") => {
    const resp = await fetch(url, { cache: "no-store" });
    const blob = await resp.blob();
    return new File([blob], filename, { type: blob.type || "image/jpeg" });
  };

  const mapCategoryForApi = c => (c === "lipstick" ? "lips" : c);

  const applySingle = async (cat, colorObj, inputUrl) => {
    const file = await fetchUrlAsFile(inputUrl || uploadedImage, "current.jpg");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("category", mapCategoryForApi(cat));
    fd.append("color", colorObj.hex);
    fd.append("intensity", String(intensity[cat] / 100));
    const res = await fetch(`${API_BASE}/manual-makeup/`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || `Failed applying ${cat}`);
    return `${API_BASE}/${data.output_path}`;
  };

  const handleApplyOne = async (cat) => {
    try {
      if (!uploadedImage) return alert("Upload an image first.");
      const c = selected[cat];
      if (!c) return alert(`Pick a ${CATEGORY_LABELS[cat]} color first.`);
      setLoading(true);
      setProgressText(`Applying ${CATEGORY_LABELS[cat]} (${c.name})…`);
      const out = await applySingle(cat, c, baseImage);
      setResultImage(out);
    } catch (e) {
      alert(`❌ ${e.message}`);
    } finally {
      setLoading(false);
      setProgressText("");
    }
  };

  const handleApplyAll = async () => {
    try {
      if (!uploadedImage) return alert("Upload an image first.");
      const queue = APPLY_ORDER.filter((cat) => selected[cat]);
      if (queue.length === 0) return alert("Pick at least one color.");
      setLoading(true);
      let current = uploadedImage;
      for (let i = 0; i < queue.length; i++) {
        const cat = queue[i];
        const col = selected[cat];
        setProgressText(`Applying ${CATEGORY_LABELS[cat]} (${col.name})… ${i + 1}/${queue.length}`);
        current = await applySingle(cat, col, current);
      }
      setResultImage(current);
      setProgressText("All selected makeup applied.");
    } catch (e) {
      alert(`❌ ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setProgressText(""), 800);
    }
  };

  const handleReset = () => { setResultImage(null); setProgressText(""); };
  const handleDownload = async () => {
    if (!baseImage) return alert("No image to download!");
    const res = await fetch(baseImage, { cache: "no-store" });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "makeup_tryon.jpg";
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="tryon-shell">
      <div className="tryon-header">
        <h2>💄 Virtual Try-On</h2>
        <div className="tryon-actions">
          <button className="btn ghost" onClick={handleReset} disabled={loading}>Reset</button>
          <button className="btn primary" onClick={handleApplyAll} disabled={loading || !uploadedImage}>
            {loading ? "Working…" : "Apply All"}
          </button>
          <button className="btn download" onClick={handleDownload} disabled={!baseImage}>💾 Download</button>
        </div>
      </div>

      <div className="tryon-body">
        <div className="preview-pane">
          <div className="preview-frame">
            {baseImage ? (
              <img src={baseImage} alt="Preview" className="preview-img" />
            ) : (
              <div className="preview-placeholder">Upload an image</div>
            )}
          </div>
          {loading && <p className="progress">{progressText || "Applying…"}</p>}
        </div>

        <div className="cards-grid">
          {Object.entries(CATEGORY_PALETTES).map(([cat, colors]) => {
            const selectedColor = selected[cat];
            return (
              <div className="card" key={cat}>
                <div className="card-head">
                  <h3>{CATEGORY_LABELS[cat]}</h3>
                  <button
                    className="btn small"
                    onClick={() => handleApplyOne(cat)}
                    disabled={!selectedColor || loading || !uploadedImage}
                  >
                    Apply
                  </button>
                </div>

                <div className="palette-row">
                  {colors.map((c, i) => {
                    const active = selectedColor?.hex === c.hex;
                    return (
                      <button
                        key={i}
                        className={`swatch ${active ? "active" : ""}`}
                        style={{ backgroundColor: c.hex }}
                        onClick={() => onPick(cat, c)}
                        title={c.name}
                        aria-label={`${CATEGORY_LABELS[cat]} ${c.name}`}
                      >
                        {active && <span className="tick">✓</span>}
                      </button>
                    );
                  })}
                </div>

                <div className="intensity-row">
                  <label>
                    Intensity
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={intensity[cat]}
                      onChange={(e) =>
                        setIntensity((prev) => ({ ...prev, [cat]: +e.target.value }))
                      }
                    />
                    <span className="pct">{intensity[cat]}%</span>
                  </label>
                </div>

                <div className="meta-row">
                  {selectedColor ? (
                    <span className="chip">Selected: <b>{selectedColor.name}</b></span>
                  ) : (
                    <span className="muted">Pick one color</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ManualTryOn;
