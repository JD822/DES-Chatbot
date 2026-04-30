import React, { useState, useEffect, useRef } from "react";
import { askOllama } from "./Components/OllamaApi";
import { Dropdown } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import RangeSlider from "react-bootstrap-range-slider";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi there! I'm your DES Support Bot. How can I assist you today? If you want to get the best experience, just say 'Yes' to personalise my responses to you.",
    },
  ]);
  const messagesEndRef = useRef(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [textSize, setTextSize] = useState(16);
  const [theme, setTheme] = useState("light");
  const [isLoading, setIsLoading] = useState(false);
  const [userConfirmation, setUserConfirmation] = useState(false);
  const [sessionId, setSessionId] = useState(() => {
    let id = sessionStorage.getItem("chat_session_id");

    if (!id) {
      id = `chat_${Date.now()}`;
      sessionStorage.setItem("chat_session_id", id);
    }

    return id;
  });

  useEffect(() => {
    const syncWithBackend = async () => {
      await askOllama("Start_Onboarding", sessionId, true);
    };

    syncWithBackend();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    setIsLoading(true);

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
      console.log("Sending prompt to backend:", currentInput);
      console.log("Session ID:", sessionId);
      const data = await askOllama(currentInput, sessionId, false);
      if (data.theme) {
        setTheme(data.theme);
      }
      if (data.text_size) {
        setTextSize(data.text_size);
      }
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
          content: "Sorry, something went wrong. Please try again.",
        });
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExternalLinkClick = (e, url) => {
    e.preventDefault();

    const newWindow = window.confirm(
      "You are about to open an external link. Do you want to proceed?",
    );

    if (newWindow) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
  };

  const accessibilityStyles = {
    "--bubble-text-size": `${textSize}px`,
  };

  return (
    <div className="container">
      <div className="header">
        <Dropdown
          className="settings-dropdown"
          show={showDropdown}
          onToggle={(isOpen, event) => {
            if (event?.source !== "select") {
              setShowDropdown(isOpen);
            }
          }}
        >
          <Dropdown.Toggle
            id="dropdown-basic-button"
            className="settings-button"
          >
            Settings
          </Dropdown.Toggle>

          <Dropdown.Menu>
            <Dropdown.Item href="#/action-1">
              Text Size
              <div>
                <RangeSlider
                  value={textSize || 16}
                  min={12}
                  max={24}
                  step={2}
                  onChange={(changeEvent) =>
                    setTextSize(changeEvent.target.value)
                  }
                />
              </div>
            </Dropdown.Item>
            <Dropdown.Item href="#/action-2">
              <div>
                Themes
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="radio"
                    name="themeRadios"
                    id="lightModeRadio"
                    value="option1"
                    checked={theme === "light"}
                    onChange={() => handleThemeChange("light")}
                  />
                  <label className="form-check-label" htmlFor="lightModeRadio">
                    Light mode
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="radio"
                    name="themeRadios"
                    id="darkModeRadio"
                    value="option2"
                    checked={theme === "dark"}
                    onChange={() => handleThemeChange("dark")}
                  />
                  <label className="form-check-label" htmlFor="darkModeRadio">
                    Dark mode
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="radio"
                    name="themeRadios"
                    id="deuteranopiaRadio"
                    value="option3"
                    checked={theme === "colourblind friendly"}
                    onChange={() => handleThemeChange("colourblind friendly")}
                  />
                  <label
                    className="form-check-label"
                    htmlFor="deuteranopiaRadio"
                  >
                    Colourblind Friendly
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="radio"
                    name="themeRadios"
                    id="protanopiaRadio"
                    value="option4"
                    checked={theme === "high contrast"}
                    onChange={() => handleThemeChange("high contrast")}
                  />
                  <label className="form-check-label" htmlFor="protanopiaRadio">
                    High Contrast
                  </label>
                </div>
              </div>
            </Dropdown.Item>
            <Dropdown.Item href="#/action-3">
              <button
                className="btn btn-danger reset-button"
                onClick={() => {
                  setMessages([
                    {
                      role: "assistant",
                      content:
                        "Hi there! I'm your DES Support Bot. How can I assist you today? If you want to get the best experience, just say 'Yes' to personalise my responses to you.",
                    },
                  ]);
                  askOllama("Start_Onboarding", sessionId, true);
                }}
              >
                Reset Conversation
              </button>
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </div>
      <div className="chat-window" aria-live="polite">
        {userConfirmation === false ? (
          <div
            className="welcome-card"
            role="dialog"
            aria-labelledby="confirm-title"
          >
            <h4 id="confirm-title">
              Welcome to the Diabetic Eye Screening Results Letter Bot!
            </h4>

            <p>
              I can help answer questions about your Diabetic Eye Screening
              results letter and guide you through common next steps.
            </p>

            <div className="info-panel">
              <h5>How personalisation works</h5>
              <ul>
                <li>
                  After confirming, you can choose to answer a few onboarding
                  questions.
                </li>
                <li>Using this, I can provide more relevant information.</li>
                <li>You can still use the bot without personalisation.</li>
              </ul>
            </div>
            <div className="info-panel">
              <h5>Further Help Links</h5>
              <ul>
                <li>
                  <a
                    href="https://www.nhs.uk/tests-and-treatments/diabetic-eye-screening/"
                    onClick={(e) =>
                      handleExternalLinkClick(
                        e,
                        "https://www.nhs.uk/tests-and-treatments/diabetic-eye-screening/",
                      )
                    }
                  >
                    NHS - Diabetic Eye Screening Information
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.diabetes.org.uk/about-diabetes/looking-after-diabetes/diabetic-eye-screening"
                    onClick={(e) =>
                      handleExternalLinkClick(
                        e,
                        "https://www.diabetes.org.uk/about-diabetes/looking-after-diabetes/diabetic-eye-screening",
                      )
                    }
                  >
                    Diabetes org - Diabetic Eye Screening Information
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.diabetes.org.uk/about-diabetes/looking-after-diabetes"
                    onClick={(e) =>
                      handleExternalLinkClick(
                        e,
                        "https://www.diabetes.org.uk/about-diabetes/looking-after-diabetes",
                      )
                    }
                  >
                    Diabetes org - Looking After Diabetes
                  </a>
                </li>
              </ul>
              <h5>Urgent Medical Advice</h5>
              <ul>
                <li>
                  If you experience any sudden changes in vision, eye pain, or
                  other concerning symptoms, seek immediate medical attention
                  from a healthcare professional
                </li>
              </ul>
            </div>
            <div className="button-group">
              <button
                className="btn btn-primary confirm-button"
                onClick={() => setUserConfirmation(true)}
              >
                Confirm and continue
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`message-wrapper ${msg.role} chat-pop`}
              style={accessibilityStyles}
            >
              <span className={`bubble ${msg.role}`}>{msg.content}</span>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      <small className="disclaimer">
        This is an AI assistant therefore can make mistakes. Always refer to a
        healthcare professional for medical advice.
      </small>
      <input
        aria-label="Type your message"
        className="text-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        disabled={isLoading || userConfirmation === false}
        placeholder={
          userConfirmation
            ? "Type here... "
            : "Please confirm to start chatting"
        }
      />
      <button
        className={`btn btn-primary send-button ${isLoading ? "loading" : ""}`}
        onClick={handleSend}
        disabled={isLoading || userConfirmation === false}
      >
        {isLoading ? "" : "Send"}
      </button>
    </div>
  );
}

export default App;
