export const askOllama = async (prompt, sessionId) => {
  const res = await fetch("http://localhost:8000/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": "passkey",
    },
    body: JSON.stringify({ prompt: prompt, session_id: sessionId }),
  });

  return await res.json();
};
