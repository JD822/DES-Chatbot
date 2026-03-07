import React, { useState } from "react";

function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");

  const askOllama = async () => {
    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": "passkey",
      },
      body: JSON.stringify({ prompt: input }),
    });

    const data = await res.json();
    setResponse(data.response);
  };

  return (
    <div style={{ padding: "20px" }}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something..."
      />
      <button onClick={askOllama}>Send</button>
      <p>
        <strong>Ollama:</strong> {response}
      </p>
    </div>
  );
}

export default App;
