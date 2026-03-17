import React, { useState, useEffect, useRef } from "react";
import { askOllama } from "./Components/OllamaApi";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi there! I'm your DES Support Bot. How can I assist you today? If you want to get the best experience, just say 'Yes' to personalise my responses to you.",
    },
  ]);
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
    const syncWithBackend = async () => {
      await askOllama("Start_Onboarding", id);
      setSessionId(id);
    };

    syncWithBackend();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };

    setMessages((prevHistory) => [
      ...prevHistory,
      userMsg,
      { role: "assistant", content: "Thinking..." },
    ]);

    const currentInput = input;
    setInput("");

    try {
      const data = await askOllama(currentInput, sessionId);
      setMessages((prevHistory) => {
        const newMessages = [...prevHistory];
        newMessages[newMessages.length - 1] = {
          role: "assistant",
          content: data.response,
        };
        return newMessages;
      });
    } catch (error) {
      console.error("Failed to send message", error);
    }
  };

  return (
    <div className="container">
      <h2>DES Support Bot</h2>

      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message-wrapper ${msg.role}`}>
            <span className={`bubble ${msg.role}`}>{msg.content}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder="Type here..."
      />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}

export default App;
