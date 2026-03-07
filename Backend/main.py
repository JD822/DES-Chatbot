import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import ollama
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# Potentially limit user credits to prevent going down rabbit hole
# Once credits are used up, prompt to seek help from a healthcare professional
API_KEY_CREDITS = {os.getenv("API_KEY"): 100}

app = FastAPI()

origins = [
    "http://localhost:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_api_key(x_api_key: str = Header(None)):
    credits = API_KEY_CREDITS.get(x_api_key, 0)
    if credits <= 0:
        raise HTTPException(status_code=401, detail="Invalid API Key or insufficient credits")
    
    return x_api_key

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
def generate(data: Prompt, x_api_key: str = Depends(verify_api_key)):
    print("Prompt received:", data.prompt)

    API_KEY_CREDITS[x_api_key] -= 1

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": data.prompt}]
    )

    return {"response": response["message"]["content"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)