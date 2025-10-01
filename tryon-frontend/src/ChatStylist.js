import React, { useState, useRef, useEffect } from "react";
import "./ChatStylist.css";

const ChatStylist = ({ goBackHome }) => { // added prop
  const [messages, setMessages] = useState([
    { from: "ai", text: "💖 Hi! I'm your AI stylist 👗. Ask me about makeup & style!" }
  ]);
  const [input, setInput] = useState("");
  const [conversationId] = useState(() => Date.now().toString());
  const chatBoxRef = useRef(null);

  const emojiMap = {
    happy: ["😃", "😁", "😆", "🥰", "😍", "🤩", "🥳", "😎"],
    sad: ["😢", "😭", "🙁", "😪"],
    surprised: ["😱", "🤯", "😮"],
    angry: ["😡", "😤", "🤬"],
    thinking: ["🤔", "🧐", "🤓"],
    playful: ["😂", "🤣", "😆", "😬", "😅", "🤪", "🤭"],
    love: ["💖", "🌸", "💄", "👗", "🎀", "✨"],
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const chooseEmoji = (text) => {
    const lowerText = text.toLowerCase();
    if (/love|heart|cute|glam|beautiful|makeup|fashion|style/.test(lowerText))
      return emojiMap.love[Math.floor(Math.random() * emojiMap.love.length)];
    if (/happy|yay|awesome|good|great|amazing/.test(lowerText))
      return emojiMap.happy[Math.floor(Math.random() * emojiMap.happy.length)];
    if (/sad|unhappy|cry|tired|😢|😭/.test(lowerText))
      return emojiMap.sad[Math.floor(Math.random() * emojiMap.sad.length)];
    if (/wow|surprise|oh|shock|😱/.test(lowerText))
      return emojiMap.surprised[Math.floor(Math.random() * emojiMap.surprised.length)];
    if (/angry|mad|😡/.test(lowerText))
      return emojiMap.angry[Math.floor(Math.random() * emojiMap.angry.length)];
    if (/think|consider|idea|🤔/.test(lowerText))
      return emojiMap.thinking[Math.floor(Math.random() * emojiMap.thinking.length)];
    return emojiMap.playful[Math.floor(Math.random() * emojiMap.playful.length)];
  };

  const formatAIReply = (text) => {
    const emoji = chooseEmoji(text);
    const trimmedText = text.length > 200 ? text.slice(0, 200) + "…" : text;
    return `${emoji} ${trimmedText}`;
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages(prev => [...prev, { from: "user", text: input }]);
    const userMessage = input;
    setInput("");

    try {
      const res = await fetch("http://127.0.0.1:8000/chat/groq/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId,
          role: "user",
        }),
      });

      const data = await res.json();
      if (data.reply) {
        setMessages(prev => [...prev, { from: "ai", text: formatAIReply(data.reply) }]);
      } else {
        setMessages(prev => [...prev, { from: "ai", text: "❌ No response from Groq." }]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => [...prev, { from: "ai", text: "❌ Failed to connect to backend." }]);
    }
  };

  return (
    <div className="chat-container">
      <h2>💖Fashion & Beauty Bot</h2>

      <div className="chat-box" ref={chatBoxRef}>
        {messages.map((msg, i) => (
          <p key={i} className={msg.from}>{msg.text}</p>
        ))}
      </div>

      <div className="chat-input">
        <input
          type="text"
          placeholder="Ask for advice..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>

      {/* Back Home Button */}
      {goBackHome && (
        <button className="back-home-btn" onClick={goBackHome}>
          🔙 Back to Home
        </button>
      )}
    </div>
  );
};

export default ChatStylist;
