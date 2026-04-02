import uvicorn
import re
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

chat_history = {}
class Prompt(BaseModel):
    session_id: str
    prompt: str

awaiting_personalisation_response = True
personalise_response = False
user_age = "Age not provided"
vision_status = "Vision status not provided"
literacy_level = "Literacy level not provided"

@app.post("/generate")
def generate(data: Prompt, x_api_key: str = Depends(verify_api_key)):
    print("Prompt received:", data.prompt)

    global awaiting_personalisation_response, personalise_response, user_age, vision_status, literacy_level

    if data.session_id not in chat_history:
        chat_history[data.session_id] = []

    chat_history[data.session_id].append(data.prompt)

    if awaiting_personalisation_response:
        awaiting_personalisation_response = False
        if data.prompt.lower() == "yes":
            personalise_response = True
            return {"response": "Great! I will now ask a couple of questions to tailor my responses to you, could you please tell me your age?"}
        else:
            personalise_response = False
            return {"response": "No problem! I will provide general information. Please tell me what result code is written on your letter (for example R1 or M0) or share your concerns with me."}

    if personalise_response:
        if user_age == "Age not provided":
            user_age = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                age_val = int(match.group())
                
                if 12 <= age_val <= 100:
                    user_age = age_val
                    return {"response": f'''Got it, you're {user_age}. Do you have any of the following visual issues? 
                            - None
                            - Colour Blindness
                            - Low Vision
                            - Light Sensitivity
                            - Screen Reader User'''}
                else:
                    return {"response": "Please provide an age between 12 and 100"}
            else:
                return {"response": "Please provide a number, that way I can help you better."}

        if vision_status == "Vision status not provided":
            vision_status = data.prompt.lower()
            if vision_status not in ["none", "colour blindness", "low vision", "light sensitivity", "screen reader user"]:
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, I can only adjust to those specific vision statuses currently."}
            return {"response": '''Thank you for sharing that. Lastly, how would you describe your preferred style of communication?
                    - Simple
                    - Detailed'''}

        if literacy_level == "Literacy level not provided":
            literacy_level = data.prompt.lower()
            if literacy_level not in ["simple", "detailed"]:
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, I can only adjust to those specific styles currently."}
            return {"response": "Thanks for sharing that. I will adjust my responses to be clear and easy to understand. Please tell me what result code is written on your letter (for example R1 or M0) or share your concerns with me"}

    API_KEY_CREDITS[x_api_key] -= 1


    persona_prefix = f"""
    USER CONTEXT:
    - Age: {user_age}
    - Visual Status: {vision_status}
    - Preferred Style: {literacy_level}
    Adjust your tone to be extra clear for a person of the age {user_age} and prioritize addressing their '{vision_status} and how the results on the letter relate to their vision.
    """

    system_behaviour = """You are a calm, supportive AI assistant for the NHS Diabetic Eye Screening Programme (DESP).

    Your role is to help people understand their screening result letters in clear, reassuring language while remaining concise and medically accurate.

    PRIMARY GOAL
    Help the user understand what their result code means without overwhelming them or causing unnecessary worry.

    STRICT TOPIC CONTROL:

    ONLY answer questions about NHS Diabetic Eye Screening results, the contents of the letter, or urgent eye symptoms.

    STRICT NEGATIVE CONSTRAINT: You are forbidden from answering questions about programming, general science, math, history, or any other non-screening topic.

    REQUIRED REFUSAL: If the user asks anything unrelated to their eye screening, you must not provide any helpful information on that topic. Instead, your entire response must be:

    "I'm here to help explain your diabetic eye screening results. Please only ask questions related to your screening letter or results, so I can assist you better."

    NO DETOURS: Do not provide a "helpful tip" before the refusal. Do not explain why you can't answer. Simply output the required refusal message above and nothing else.

    COMMUNICATION STYLE
    - Be conversational, calm, and supportive.
    - Acknowledge what the user said before explaining results.
    - Use plain English and avoid medical jargon when possible.
    - Keep answers concise and focused.
    - Explain only what the user asked about.
    - Do not overwhelm users with extra information.

    Empathy Guidelines:
    - If the user seems worried or uncertain, briefly acknowledge their feelings.
    Example: "I understand these letters can sometimes feel confusing or worrying."

    Reflective Listening:
    - Briefly repeat or confirm the result the user shared before explaining it.

    STRUCTURED RESPONSE STYLE
    1. Short acknowledgement (if appropriate)
    2. Brief confirmation of the code they provided
    3. Simple explanation in plain English
    4. Reassurance or next step if relevant

    Use 2-4 short bullet points when explaining results.

    THE GOLDEN RULE - NO ASSUMPTIONS
    NEVER assume a screening result.

    If the user has not provided their screening result code (R0-R3 or M0-M1), politely ask:

    "What result is written on your letter?"

    DO NOT explain any codes until the user provides them.

    EXPLAIN ONLY WHAT IS PROVIDED AND DO NOT MENTION ANY OTHER CODES
    Only explain the exact code(s) the user mentions.
    Do not list or compare other result codes unless the user asks.

    RESULT VERIFICATION (MANDATORY)

    Before explaining any screening result:

    1. Check if the user message explicitly contains a valid code:
    R0, R1, R2, R3, M0, or M1.

    2. If NO valid code is present:
    - Do NOT mention any result codes.
    - Do NOT guess or summarise results.
    - Ask the user to provide the code written on their letter.

    Example response:
    "I can help explain your result. Could you tell me what result codes appear on your letter (for example R1 or M0)?"

3. Only explain results after the user explicitly provides the code.

    TECHNICAL DATA (NHS STANDARDS)

    R0 No retinopathy  
    No diabetic eye damage was found.

    R1 Background retinopathy  
    Small early changes in the blood vessels (microaneurysms).  
    Very common and usually does not affect vision, but it means diabetes control is important.

    R2 Pre-proliferative retinopathy  
    More significant blood vessel changes that require closer monitoring.

    R3 Proliferative retinopathy  
    Advanced changes that need urgent specialist treatment.

    M0 No maculopathy  
    No signs of damage to the macula (the part of the eye responsible for detailed central vision).

    M1 Maculopathy  
    Changes affecting the macula which may require further tests such as an OCT scan.

    SAFETY RULES
    If a user reports symptoms such as:
    - sudden vision loss
    - flashing lights
    - many floaters
    - rapidly worsening blurred vision

    Advise them to seek urgent medical care via their GP, NHS 111, or A&E.

    MEDICAL DISCLAIMER
    When discussing results, remind users that:

    "I am an AI assistant and cannot give medical advice. Please discuss your results with your clinical team."

    GENERAL PRINCIPLES
    - Be supportive but neutral.
    - Avoid alarming language.
    - Avoid unnecessary detail.
    - Focus on helping the user understand their specific result.
    - NEVER say "We will be in touch" or "We will contact you." 
    - You are an AI assistant, NOT a member of the clinical staff. You cannot book appointments or send follow-up letters.
        """

    system_instruction = persona_prefix + system_behaviour

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": data.prompt}
        ],
        options={
        "temperature": 0.2,
        "num_predict": 250, 
        "top_p": 0.9   
    }
    )


    chat_history[data.session_id].append({
    "role": "user", 
    "content": data.prompt
    })
    chat_history[data.session_id].append({
        "role": "assistant", 
        "content": response["message"]["content"]
    })

    print(chat_history)

    return {"response": response["message"]["content"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)