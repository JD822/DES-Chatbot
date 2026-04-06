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
    # if credits <= 0:
    #     raise HTTPException(status_code=401, detail="Invalid API Key or insufficient credits")
    
    return x_api_key

chat_history = {}
class Prompt(BaseModel):
    session_id: str
    prompt: str
    onboarding: bool 

awaiting_personalisation_response = True
personalise_response = False
user_age = "Age not provided"
vision_status = "Vision status not provided"
literacy_level = "Literacy level not provided"
user_experience = "Experience not provided"
persona_customisation = ""

@app.post("/generate")
def generate(data: Prompt, x_api_key: str = Depends(verify_api_key)):

    global awaiting_personalisation_response, personalise_response, user_age, vision_status, literacy_level, user_experience, persona_customisation

    if data.session_id not in chat_history:
        chat_history[data.session_id] = []

    if data.onboarding:
        awaiting_personalisation_response = True
        personalise_response = False
        user_age = "Age not provided"
        vision_status = "Vision status not provided"
        user_experience = "Experience not provided"
        literacy_level = "Literacy level not provided"

    chat_history[data.session_id].append(data.prompt)

    if awaiting_personalisation_response:
        awaiting_personalisation_response = False
        if data.prompt.lower() == "yes":
            personalise_response = True
            return {"response": "Great! I will now ask a couple of questions to tailor my responses to you, could you please tell me your age?"}
        if data.prompt.lower() == "no":
            personalise_response = False
            return {"response": "No problem! I will provide general information. Please tell me what result code is written on your letter (for example R1 or M0) or share your concerns with me."}
        else:
            awaiting_personalisation_response = True
            return {"response": "Please answer with 'Yes' or 'No' to help me personalise your experience. Do you want me to tailor my responses to you?"}

    if personalise_response:
        if user_age == "Age not provided":
            user_age = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                age_val = int(match.group())
                
                if 12 <= age_val <= 100:
                    user_age = age_val
                    return {"response": f'''Got it, you're {user_age}. Do you have any of the following visual impairments? 
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
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, "
                "I can only adjust to one of those specific vision statuses currently."}
            return {"response": '''Thank you for sharing that. Now can you please tell me how long you have been a diabetic for? 
                    you can say something like 'I have been managing my condition for 5 years' or 'I am new to diabetes management'. '''}
        
        if user_experience == "Experience not provided":
            user_experience = data.prompt
            if user_experience == "Experience not provided":
                return {"response": "Please provide your experience level, that way I can adjust my explanations to suit you better."}
            return {"response": '''Lastly, please give a brief description on your knowledge on diabetic eye screening results and medical information in general, 
                    this will help me adjust my language to suit you better. You can say something like 'I have a good understanding and want detailed explanations' or 'I find medical information 
                    confusing and want simple explanations' or anything in between'''}

        if literacy_level == "Literacy level not provided":
            literacy_level = data.prompt
            if literacy_level == "Literacy level not provided":
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, I can only adjust to those specific styles currently."}
            
            user_data_input = f'''
            User Inputs:
            Age: {user_age}
            Visual impairment: {vision_status} 
            Experience Managing Diabetes: {user_experience}
            Literacy: {literacy_level}
        '''
            print ("User Data Input for Persona Supplement:", user_data_input)

            prompt_chaining_instructions =f''' You are a Prompt Engineer. Your task is to generate a 'Persona Supplement' based on user data to bridge the gap between the user's context and their medical results.

            CRITICAL RULES:
            - Experience vs. Literacy: Prioritise "Years of Experience" as the primary driver for terminology.
                - Expert (10+ years), use a collaborative, clinical tone. You are PROHIBITED from using basic analogies 
                - Intermediate (2-10 years) use an informative, neutral tone. Balance explanation with implications  
                - Novice (<2 years), use a supportive, educational tone. Focus on explaining what the result is
            - NEVER apply novice rules to an expert. NEVER apply expert rules to a novice.
            - Do NOT mix simple language with professional terminology. Choose ONE path and apply it consistently.
            - ADAPTIVE RULES must contain NO UI properties. Theme and Text Size belong ONLY in FRONTEND CUSTOMISATIONS.
            - Provde 4-5 specific, actionable formatting and tone instructions based on the user's data. Do not include category labels without directives.

            SELF-CHECK (run this before generating output):
            - What is the user's experience level? → [Expert / Intermediate / Novice]
            - Which tone path does this trigger? → [Clinical / Neutral / Educational]
            - Are all 4-5 rules actionable directives, not category labels?
            - Do any ADAPTIVE RULES contain UI properties? If yes, remove them.
            
            TASK:
            Strictly based on the user inputs, generate 4-5 strict formatting and tone instructions.

            RULES:
            - Be written as a behavioural instruction, not a label
            - Cover one of: sentence complexity, terminology usage, explanation depth, use of analogies (if applicable), emotional register

            FRONTEND LOGIC:

            Theme: Select the UI Theme strictly based on user data: If 'Visual impairment' is 'none', you are prohibited from using 'High Contrast' or 'Color Blind Friendly'—instead, YOU MUST choose 'Dark' for users over 40 or 'Light' for users 40 and under; trigger 'High Contrast' only when a specific visual impairment is explicitly stated (e.g., 'Colour Blindness' = 'Color Blind Friendly', 'Low Vision' = 'High Contrast').
            Text Size: Standard is 16. Increase (18-24) only if visual impairment or age > 65 is indicated.

            OUTPUT FORMAT:
            Respond Strictly in the following format you are PROHIBITED from deviating from this format. YOU MUST NOT output any self-check or reasoning steps, only the final instructions and customisations:

            ADAPTIVE RULES:
            - Rule 1 
            - Rule 2
            - Rule 3
            - Rule 4
            - Rule 5 (if applicable)

            FRONTEND CUSTOMISATIONS:
            Theme: [Value]
            Text Size: [Number]
            '''
        
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": prompt_chaining_instructions},
                    {"role": "user", "content": user_data_input}
                ],
                options={
                    "temperature": 0.2,
                    "num_predict": 250, 
                    "top_p": 0.9   
                }
            )

            persona_customisation = response["message"]["content"]
            print("Persona Customisation Instructions:", persona_customisation)
            
            theme_value = "default"
            if "Theme:" in persona_customisation:
                theme_line = [line for line in persona_customisation.split('\n') if "Theme:" in line][0]
                theme_value = theme_line.split(":")[1].strip().lower()


            text_size = "16"
            if "Text Size:" in persona_customisation:
                size_line = [line for line in persona_customisation.split('\n') if "Text Size:" in line][0]
                text_size = size_line.split(":")[1].strip()
            return {
                "theme": theme_value,
                "text_size": text_size,
                "response": "Thanks for sharing that. I will adjust my responses to be clear and easy to understand. Please tell me what result code is written on your letter (for example R1 or M0) or share your concerns with me"
                }
        

    API_KEY_CREDITS[x_api_key] -= 1


    system_behaviour = """You are a calm, supportive AI assistant for the NHS Diabetic Eye Screening Programme (DESP).
    Your role is to help people understand their screening result letters in clear, reassuring language while remaining concise and medically accurate.

    PRIMARY GOAL
    Help the user understand what their result code means without overwhelming them or causing unnecessary worry.

    STRICT TOPIC CONTROL:
    - ONLY answer questions about NHS Diabetic Eye Screening results, the contents of the letter, or urgent eye symptoms.
    - STRICT NEGATIVE CONSTRAINT: You are strictly forbidden from answering, discussing, or even acknowledging the content of questions about any non-screening topic.

    REQUIRED REFUSAL: If the user asks anything unrelated to their eye screening, you must completely ignore the subject matter of their question. You are prohibited from asking follow-up questions about their unrelated topic

    "I'm here to help explain your diabetic eye screening results. Please only ask questions related to your screening letter or results, so I can assist you better."

    NO DETOURS: If the topic is not NHS Diabetic Eye Screening, output the required refusal message above and terminate the response immediately.

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

    STRICTLY NO ASSUMPTIONS
    NEVER assume a screening result.

    If the user has not provided their screening result code (R0-R3 or M0-M1) or a descriptive phrase from a letter, politely ask:

    "What result is written on your letter?"

    DO NOT explain any codes until the user provides them.

    EXPLAIN ONLY WHAT IS PROVIDED AND DO NOT MENTION ANY OTHER CODES
    Only explain the exact code(s) the user mentions.
    Do not list or compare other result codes unless the user asks.

    RESULT VERIFICATION (MANDATORY)

    Before explaining any screening result:

    1. Check if the user message explicitly contains a valid code:
    R0, R1, R2, R3, M0, or M1.

    or a descriptive phrase:
     
    Examples of descriptive phrases:
    - Some changes due to diabetes were seen but these do not need any treatment at present
    - Due to an existing eye condition, it may not be necessary for you to be screened by the DRSSW (Diabetic Retinopathy Screening Service Wales)
    - No changes due to diabetes were seen
    - Changes due to diabetes were seen which require further examination by a hospital eye specialist
    - Changes due to diabetes were seen which require further examination by a hospital eye specialist
    - Unfortunately, the photographs we obtained did not allow us to see the back of your eyes (Retina)
    - Due to the presence of a cataract, we were unable to photograph the back of one or both eyes. Therefore, further examination by a hospital eye specialist is needed

    DO NOT match it to a code, simply explain the meaning of the phrase in clear language

    2. If NO valid code is present:
    - Do NOT mention any result codes or descriptive phrases.
    - Do NOT guess or summarise results.
    - Ask the user to provide the code written on their letter.

    Example response:
    "I can help explain your result. Could you tell me what result codes appear on your letter (for example R1 or M0)?"

3. Only explain results after the user explicitly provides the code.

    TECHNICAL DATA (NHS STANDARDS)

    R0 No retinopathy  
    No changes in the eye due to diabetes. People with no retinopathy are at low risk of 
    developing any sight-threatening changes and will be recalled for screening in one 
    to two years.

    R1 Background retinopathy  
    Vessels become blocked or leaky causing blood and other fluid to become visible on 
    the retina. These changes are not sight-threatening and will not affect your vision but 
    improvements in self-care may help to reduce the risk of retinopathy getting worse. 
    People with background retinopathy will be recalled in one year for screening. 

    R2 Pre-proliferative retinopathy  
    More changes due to diabetes are visible on the back of the eye. This could be more 
    bleeds, as well as signs of a lack of oxygen and changes in the shape of blood vessels 
    themselves. The risk of sight-threatening changes developing have increased. Therefore, 
    you could be screened more often, every three to six months or would be referred to a 
    specialist for more testing and closer monitoring. These 
    changes will not affect your vision but improvements in self-care may help to reduce the 
    risk of retinopathy getting worse.

    R3 Proliferative retinopathy  
    At this stage the growth hormone known as VEGF is increased and abnormal blood 
    vessels grow on the retina. These new vessels grow into the gel in the middle of the 
    eye and bleed. Once they bleed, they will begin to affect sight causing black spots in 
    your vision or an increase in floaters. You will be referred to a specialist for testing (see 
    Additional healthcare) and possibly need treatment to stop the new vessels from 
    growing.

    M0 No maculopathy  
    No changes due to diabetes within the macular area (see Figure 1). If the retinopathy 
    level is R0 or R1, screening recall would be based on the retinopathy level

    M1 Maculopathy  
    Changes due to diabetes can be seen within the macular area. Vessels in or around the 
    macula area become blocked or leaky. When blood and fluid leaks into the macular 
    it can cause swelling called oedema. Because the fovea is responsible for our central 
    vision and being able to read, swelling in this area has a higher risk of threatening sight. 
    However, not all screening programmes have the test available (known as ocular surface 
    temperature, or OCT imaging) to check for swelling and therefore this level would be 
    referred to a specialist for further tests and monitoring (see Additional healthcare). If 
    swelling is detected, then treatment would be needed to reduce the swelling and limit 
    the effect on vision.

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

    if personalise_response:
        print("Persona Supplement:", persona_customisation)
        system_instruction = persona_customisation + "\n\n" + system_behaviour
    else:
        system_instruction = system_behaviour

    history = [msg for msg in chat_history[data.session_id] if isinstance(msg, dict)]

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_instruction},
            *history,
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