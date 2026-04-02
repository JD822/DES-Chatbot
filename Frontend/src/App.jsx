import React, { useState, useEffect, useRef } from "react";
import { askOllama } from "./Components/OllamaApi";
import { Dropdown } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import RangeSlider from "react-bootstrap-range-slider";
import { set } from "react-hook-form";

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
  const [textSize, setTextSize] = useState(16);
  const [showDropdown, setShowDropdown] = useState(false);

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

    setMessages((prevHistory) => [...prevHistory, userMsg]);

    await new Promise((r) => setTimeout(r, 200));

    setMessages((prevHistory) => [
      ...prevHistory,
      { role: "assistant", content: "Thinking..." },
    ]);

    console.log(messages);
    const currentInput = input;
    setInput("");

    try {
      const data = await askOllama(currentInput, sessionId);
      setMessages((prevHistory) => {
        const newMessages = [...prevHistory];
        newMessages.pop();
        return newMessages;
      });
      await new Promise((r) => setTimeout(r, 200));
      setMessages((prevHistory) => {
        const newMessages = [...prevHistory];
        newMessages.push({
          role: "assistant",
          content: data.response,
        });
        return newMessages;
      });
    } catch (error) {
      console.error("Failed to send message", error);
    }
  };

  const accessibilityStyles = {
    "--bubble-text-size": `${textSize}px`,
  };

  return (
    <div className="container">
      <div className="header">
        <h2>DES Support Bot</h2>
        <Dropdown
          style={{ marginLeft: "auto" }}
          show={showDropdown}
          onToggle={(isOpen, event) => {
            if (event?.source !== "select") {
              setShowDropdown(isOpen);
            }
          }}
        >
          <Dropdown.Toggle id="dropdown-basic-button">Settings</Dropdown.Toggle>

          <Dropdown.Menu>
            <Dropdown.Item href="#/action-1">
              Text Size
              <div>
                <RangeSlider
                  value={textSize || 16}
                  min={12}
                  max={24}
                  step={4}
                  onChange={(changeEvent) =>
                    setTextSize(changeEvent.target.value)
                  }
                />
              </div>
            </Dropdown.Item>
            <Dropdown.Item href="#/action-2">Another action</Dropdown.Item>
            <Dropdown.Item href="#/action-3">Something else</Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </div>

      <div className="chat-window">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message-wrapper ${msg.role} chat-pop`}
            style={accessibilityStyles}
          >
            <span className={`bubble ${msg.role}`}>{msg.content}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <input
        className="text-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder="Type here..."
      />
      <button className="btn btn-primary" onClick={handleSend}>
        Send
      </button>
    </div>
  );
}

export default App;
