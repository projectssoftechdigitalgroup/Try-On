import React, { useState } from "react";
import "./UploadImage.css";

const UploadImage = ({ setUploadedImage }) => {
  const [selectedImage, setSelectedImage] = useState(null);

  // Handle File Upload Preview
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const imageURL = URL.createObjectURL(file);
      setSelectedImage(imageURL);
      setUploadedImage(imageURL); // update parent App.js state
    }
  };

  // Upload to Backend
  const handleUpload = async () => {
    const fileInput = document.getElementById("fileUpload");

    if (!fileInput.files.length) {
      alert("⚠️ Please select an image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("user_id", "demoUser");

    try {
      const response = await fetch("http://127.0.0.1:8000/upload/", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      alert(`✅ Upload Successful! Saved at: ${data.path}`);
    } catch (error) {
      console.error("Upload error:", error);
      alert("❌ Upload failed. Try again.");
    }
  };

  return (
    <div className="upload-container">
      <h2> Upload Image</h2>

      <div className="upload-options">
        <label className="file-upload">
          <input
            type="file"
            id="fileUpload"
            accept="image/*"
            onChange={handleFileChange}
          />
          Select from Device
        </label>
      </div>

      <div className="preview">
        {selectedImage && <img src={selectedImage} alt="Uploaded Preview" />}
      </div>
    </div>
  );
};

export default UploadImage;
