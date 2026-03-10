import React, { useState, useEffect, useRef } from "react";

function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    let id = sessionStorage.getItem("chat_session_id");

    if (!id) {
      id = `chat_${Date.now()}`;
      sessionStorage.setItem("chat_session_id", id);
    }

    setSessionId(id);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askOllama = async () => {
    if (!input.trim()) return;

    // 1. Create the user message object
    const userMsg = { role: "user", content: input };

    // 2. IMPORTANT: Add user message to the UI immediately
    // Use the (prev) => [...prev, new] syntax to keep old messages
    setMessages((prevHistory) => [...prevHistory, userMsg]);

    const currentInput = input;
    setInput("");
    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": "passkey",
      },
      body: JSON.stringify({ prompt: input, session_id: sessionId }),
    });

    const data = await res.json();
    const aiMsg = { role: "assistant", content: data.response };
    setMessages((prev) => [...prev, aiMsg]);
  };

  // const messagesEndRef = useRef(null);

  // const scrollToBottom = () => {
  //   messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  // };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "auto" }}>
      <h2>Eye Screening Chat</h2>

      {/* 4. Display the messages */}
      <div
        style={{
          height: "400px",
          overflowY: "auto",
          border: "1px solid #ccc",
          padding: "10px",
          marginBottom: "10px",
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              margin: "10px 0",
            }}
          >
            <span
              style={{
                background: msg.role === "user" ? "#007bff" : "#e9e9eb",
                color: msg.role === "user" ? "white" : "black",
                padding: "8px 12px",
                borderRadius: "10px",
                display: "inline-block",
                whiteSpace: "pre-wrap",
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && askOllama()}
        placeholder="Type here..."
      />
      <button onClick={askOllama}>Send</button>
    </div>
  );
}

export default App;
