import React, { useState } from "react";
import UploadImage from "./UploadImage";
import CaptureImage from "./CaptureImage";
import SkinAnalysis from "./SkinAnalysis";
import MakeupTryOn from "./MakeupTryOn";
import ChatStylist from "./ChatStylist";
import JewelryTryOn from "./JewelryTryOn";
import RealtimeSkinAnalysis from "./realtime_skin_analysis";
import CapGlassesTryOn from "./CapGlassesTryOn";
import RealtimeCapGlasses from "./realtime_cap_glasses";
import WristTryOn from "./wristTryOn";
import ClothesTryOn from "./clothesTryOn";
import MoustacheTryOn from "./MoustacheTryOn"; // ✅ New
import HairTryOn from "./HairTryOn"; // ✅ New
import "./App.css";

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [activeFeature, setActiveFeature] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showCapture, setShowCapture] = useState(false);

  const resetImage = () => {
    setUploadedImage(null);
    setShowUpload(false);
    setShowCapture(false);
    setActiveFeature("faceTryOn");
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1>✨ Virtual Try-On</h1>
        <p className="subtitle">
          Upload a photo or capture one live to try different styles instantly
        </p>
      </header>

      <main className="app-main">
        {/* Main Feature Cards */}
        {!activeFeature && (
          <div className="cards-container">
            <div className="card" onClick={() => setActiveFeature("faceTryOn")}>
              <div className="card-title">🎭 Face Try-On</div>
              <div className="card-description">
                Access all face-based try-on features
              </div>
            </div>

            <div className="card" onClick={() => setActiveFeature("wristTryOn")}>
              <div className="card-title">✋ Wrist Try-On</div>
              <div className="card-description">
                Try watches, bracelets, and rings virtually
              </div>
            </div>

            <div className="card" onClick={() => setActiveFeature("clothesTryOn")}>
              <div className="card-title">👕 Clothes Try-On</div>
              <div className="card-description">
                Try shirts, pants, frocks, and outfits virtually
              </div>
            </div>
          </div>
        )}

        {/* Face Try-On Section */}
        {activeFeature === "faceTryOn" && (
          <div className="face-tryon-container">
            {/* Step 1: Upload / Capture / Realtime */}
            {!uploadedImage && !showUpload && !showCapture && (
              <div className="cards-container">
                <div className="card" onClick={() => setShowUpload(true)}>
                  <div className="card-title">📤 Upload Image</div>
                  <div className="card-description">
                    Upload a photo from your device
                  </div>
                </div>

                <div className="card" onClick={() => setShowCapture(true)}>
                  <div className="card-title">📸 Capture Live Image</div>
                  <div className="card-description">
                    Use your webcam to take a picture
                  </div>
                </div>

                <div className="card" onClick={() => setActiveFeature("realtime")}>
                  <div className="card-title">📹 Real-Time Skin Analysis</div>
                  <div className="card-description">
                    Analyze your skin live with webcam
                  </div>
                </div>

                <div
                  className="card"
                  onClick={() => setActiveFeature("realtimeCapGlasses")}
                >
                  <div className="card-title">🕶️ Real-Time Cap/Glasses Try-On</div>
                  <div className="card-description">
                    Try caps, hats, and glasses live
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Upload or Capture */}
            {showUpload && !uploadedImage && (
              <UploadImage setUploadedImage={setUploadedImage} />
            )}
            {showCapture && !uploadedImage && (
              <CaptureImage
                setUploadedImage={setUploadedImage}
                goHome={() => setShowCapture(false)}
              />
            )}

            {/* Step 3: Preview */}
            {uploadedImage && (
              <div className="image-preview-box">
                <h3 className="H3">🖼️ Your Selected Image</h3>
                <img src={uploadedImage} alt="Preview" className="image-preview" />
                <button onClick={resetImage} className="btn-secondary">
                  🔄 Change Image
                </button>
              </div>
            )}

            {/* Step 4: Face Feature Options */}
            {uploadedImage && (
              <div className="cards-container">
                <div className="card" onClick={() => setActiveFeature("skin")}>
                  <div className="card-title">🧴 Skin Analysis</div>
                  <div className="card-description">
                    Detect skin tone and get personalized recommendations
                  </div>
                </div>

                <div className="card" onClick={() => setActiveFeature("makeup")}>
                  <div className="card-title">💄 Makeup Try-On</div>
                  <div className="card-description">
                    Try lipstick, eyeshadow, foundation, etc.
                  </div>
                </div>

                <div className="card" onClick={() => setActiveFeature("jewelry")}>
                  <div className="card-title">💍 Jewellery Try-On</div>
                  <div className="card-description">
                    Try earrings, nose rings, necklaces, and bindis
                  </div>
                </div>

                <div className="card" onClick={() => setActiveFeature("capglasses")}>
                  <div className="card-title">🧢 Cap/Glasses Try-On</div>
                  <div className="card-description">
                    Try virtual caps, hats, and glasses
                  </div>
                </div>

                {/* ✅ New Moustache Try-On */}
                <div className="card" onClick={() => setActiveFeature("moustache")}>
                  <div className="card-title">🧔 Moustache Try-On</div>
                  <div className="card-description">
                    Experiment with different beard and moustache styles
                  </div>
                </div>

                {/* ✅ New Hair Try-On */}
                <div className="card" onClick={() => setActiveFeature("hair")}>
                  <div className="card-title">💇 Hair Try-On</div>
                  <div className="card-description">
                    Try new haircuts, colors, and styles virtually
                  </div>
                </div>

                <div className="card" onClick={() => setActiveFeature("chat")}>
                  <div className="card-title">🤖 Chat with Stylist</div>
                  <div className="card-description">
                    Get AI-based makeup advice and styling tips
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Wrist Try-On */}
        {activeFeature === "wristTryOn" && (
          <WristTryOn goBackHome={() => setActiveFeature(null)} />
        )}

        {/* Clothes Try-On */}
        {activeFeature === "clothesTryOn" && (
          <ClothesTryOn goBackHome={() => setActiveFeature(null)} />
        )}

        {/* Face Try-On Subfeatures */}
        {activeFeature === "skin" && (
          <SkinAnalysis
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "makeup" && (
          <MakeupTryOn
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "jewelry" && (
          <JewelryTryOn
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "capglasses" && (
          <CapGlassesTryOn
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "realtime" && (
          <RealtimeSkinAnalysis goBackHome={() => setActiveFeature("faceTryOn")} />
        )}
        {activeFeature === "realtimeCapGlasses" && (
          <RealtimeCapGlasses goBackHome={() => setActiveFeature("faceTryOn")} />
        )}
        {activeFeature === "moustache" && (
          <MoustacheTryOn
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "hair" && (
          <HairTryOn
            uploadedImage={uploadedImage}
            goBackHome={() => setActiveFeature("faceTryOn")}
          />
        )}
        {activeFeature === "chat" && (
          <ChatStylist goBackHome={() => setActiveFeature("faceTryOn")} />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Powered by AI | Virtual Try-On Project</p>
      </footer>
    </div>
  );
}

export default App;
