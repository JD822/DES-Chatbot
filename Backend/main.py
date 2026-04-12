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
result_store = []

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

    global awaiting_personalisation_response, personalise_response, user_age, vision_status, literacy_level, user_experience, persona_customisation, result_store

    if data.session_id not in chat_history:
        chat_history[data.session_id] = []

    if data.onboarding:
        awaiting_personalisation_response = True
        personalise_response = False
        user_age = "Age not provided"
        vision_status = "Vision status not provided"
        user_experience = "Experience not provided"
        literacy_level = "Literacy level not provided"
        chat_history[data.session_id] = []
        result_store = []

    chat_history[data.session_id].append(data.prompt)

    if awaiting_personalisation_response:
        awaiting_personalisation_response = False
        if data.prompt.lower() == "yes":
            personalise_response = True
            return {"response": "Great! I will now ask a couple of questions to tailor my responses to you, could you please tell me your age?"}
        if data.prompt.lower() == "no":
            personalise_response = False
            return {"response": "No problem! I will provide general information. Please tell me what result code or descriptive phrase that is written on your letter. I can also answer any general concerns!"}
        else:
            awaiting_personalisation_response = True
            return {"response": "Please answer with 'Yes' or 'No' to help me personalise your experience. Do you want me to tailor my responses to you?"}

    if personalise_response:
        if user_age == "Age not provided":
            user_age = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                age_value = int(match.group())
                
                if 12 <= age_value <= 100:
                    user_age = age_value
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
            return {"response": '''Thank you for sharing that. Now can you please tell me how long you have been a diabetic for? Please only use a number for the amount of years e.g. 0 for a new diabetic or 20 for 20 years'''}
        
        if user_experience == "Experience not provided":
            user_experience = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                experience_value = int(match.group())
                
                if 0 <= experience_value <= 100:
                    user_experience = experience_value
                    return {"response": '''Lastly, please give a brief description on your knowledge on diabetic eye screening results and medical information in general, this will help me adjust my language to suit you better. You can say something like 'I have a good understanding and want detailed explanations' or 'I find medical information confusing and want simple explanations' or anything in between'''}
            else:
                return {"response": "Please provide how many years you have been a diabetic using just a number, that way I can adjust my explanations to suit you better."}

        if literacy_level == "Literacy level not provided":
            literacy_level = data.prompt
            if literacy_level == "Literacy level not provided":
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, I can only adjust to those specific styles currently."}
            
            user_data_input = f'''
            User Inputs:
            Age: {user_age}
            Visual impairment: {vision_status} 
            Years managing diabetes: {user_experience}
            Literacy: {literacy_level}
        '''
            #print("User Data Input for Persona Supplement:", user_data_input)

            def customise_interface(age, impairment):
                if impairment.lower() == 'colour blindness':
                    return 'colourblind friendly'
                if impairment.lower() == 'low vision':
                    return 'high contrast'
                if impairment.lower() == 'light sensitivity':
                    return 'dark'
                if age <= 40:
                    return 'light'
                if age > 40:
                    return 'dark'
            
            theme_selection = customise_interface(user_age,vision_status)

            def experience_level_calculation(experience_level):
                if experience_level <= 3:
                    base_level = 'novice'
                elif experience_level <= 10:
                    base_level = 'intermediate'
                else:
                    base_level = 'expert'
                return base_level

            base_level = experience_level_calculation(user_experience)


            low_indicators = [
            "confusing",
            "confused",
            "difficult",
            "overwhelming",
            "overwhelmed",
            "hard to understand",
            "don't understand",
            "do not understand",
            "struggle",
            "struggling",
            "lost",
            "no idea",
            "don't know",
            "do not know",
            "new to this",
            "not sure",
            "unsure",
            "complicated",
            "complex",
            "too much information",
            "hard to follow",
            "makes no sense",
            "doesn't make sense",
            "does not make sense",
            "can't understand",
            "cannot understand",
            "finding it hard",
            "finding it difficult"
            ]

            moderate_indicators = [
            "some understanding",
            "basic understanding",
            "getting there",
            "most of it",
            "most terms",
            "generally understand",
            "fairly comfortable",
            "mostly understand",
            "starting to understand",
            "beginning to understand",
            "learning",
            "picking it up",
            "getting used to",
            "need context",
            "need help with",
            "need clarification",
            "sometimes need",
            "occasionally need",
            "not always sure",
            "not always clear",
            "need numbers explained",
            "need results explained"
            ]

            high_indicators = [
            "comfortable",
            "very comfortable",
            "confident",
            "fully understand",
            "good understanding",
            "strong understanding",
            "detailed explanations",
            "clinical",
            "technical",
            "healthcare",
            "medical professional",
            "work in healthcare",
            "nurse",
            "doctor",
            "pharmacist",
            "clinician",
            "specialist",
            "in depth",
            "in-depth",
            "advanced",
            "expert",
            "experienced",
            "well versed",
            "well-versed",
            "familiar with",
            "no need to simplify",
            "don't need it simplified",
            "do not need it simplified",
            "understand medical terms",
            "understand clinical terms",
            "comfortable with jargon"
            ]


            def literacy_level_calculation(prompt):
                literacy_indicators = [0,0,0]
                for phrase in low_indicators:
                    if phrase in prompt.lower():
                        literacy_indicators[0] += 1
                for phrase in moderate_indicators:
                    if phrase in prompt.lower():
                        literacy_indicators[1] += 1
                for phrase in high_indicators:
                    if phrase in prompt.lower():
                        literacy_indicators[2] += 1

                max_score = max(literacy_indicators)

                if max_score == 0:
                    literacy = "MODERATE"
                elif literacy_indicators.index(max_score) == 0:
                    literacy = "LOW"
                elif literacy_indicators.index(max_score) == 1:
                    literacy = "MODERATE"
                else:
                    literacy = "HIGH"

                return literacy
        
            literacy_calculation = literacy_level_calculation(data.prompt)
            #print(literacy_calculation)

            if literacy_calculation == 'LOW':
                if base_level == 'expert':
                    base_level = 'intermediate'
                if base_level == 'intermediate':
                    base_level = 'novice'

            #print(base_level)

            reasoning_examples = {
            "novice": '''RULES:
            - TONE: Warm and encouraging. Write as if speaking to someone new to this. Never clinical, never rushed.
            - SENTENCES: Maximum 12 words per sentence. One idea per sentence. 
            Start a new paragraph for each new concept.
            - TERMINOLOGY: Always use the plain term first. Add the clinical 
            term in brackets immediately after. Never use a clinical term 
            alone. Example: "the back of your eye (retina)" not "the retina".
            - ANALOGIES: Use one simple everyday analogy if applicable.
            - KNOWLEDGE: Explain everything from scratch. Never reference
            prior knowledge, or assume they remember anything from before.
            - EMPATHY: Weave reassurance into every sentence naturally. 
            Never save it for the end. Never skip it because the result 
            is good news.
            - READING LEVEL: Every sentence must be understandable to a 
            12 year old without re-reading. If a sentence requires 
            prior knowledge to parse, rewrite it.
            ''',

            "intermediate": '''RULES:
            - TONE: Collaborative and empowering. Treat them as an active 
            partner in managing their condition, not a passive recipient 
            of information. Use "your result shows" not "the result shows".
            - SENTENCES: Use compound sentences that connect cause and effect. 
            Example: "Because the vessels are leaking, fluid builds up 
            which can affect your vision over time." Never use short 
            choppy sentences — these feel patronising at this level.
            - TERMINOLOGY: Lead with the clinical term, follow immediately 
            with a brief functional definition. Example: "maculopathy — 
            where changes occur in the central area responsible for 
            reading vision". Never define basic terms like retina or diabetes.
            - ANALOGIES: Use mechanical or functional analogies only 
            - KNOWLEDGE: Skip all introductory context about diabetes. 
            Assume they understand the basics but may not recall 
            specific grading details.
            - EMPATHY: Acknowledge the effort of long term management 
            directly. One acknowledgement only — do not repeat.
            ''',

            "expert": '''RULES:
            - TONE: Peer to peer. Direct and efficient. Treat them as a 
            clinical equal. Never explain what they already know. 
            Never soften findings unnecessarily.
            - SENTENCES: Dense, information rich sentences are appropriate. 
            Prioritise precision over readability. Lead with the finding, 
            follow with the implication.
            - TERMINOLOGY: Use standard clinical terminology exclusively — 
            HbA1c, euglycaemia, VEGF, vitreous haemorrhage, OCT imaging. 
            Never substitute a plain language term for a clinical one. 
            Never define standard terms.
            - ANALOGIES: Prohibited. State the physiological fact directly. 
            - KNOWLEDGE: Assume complete mastery. Skip all preparation 
            context, basic definitions, and standard next step 
            explanations they will already know. Focus only on 
            what is specific to their result.
            - EMPATHY: Express through precision and respect for autonomy 
            only. One brief acknowledgement maximum — never repeated, 
            never emotional. Example: "This result warrants prompt 
            review" not "I know this might be worrying for you".
            '''
            }
        
            communication_example = reasoning_examples[base_level]


            prompt_chaining_instructions =f''' You are a Prompt Engineer. Your task is to generate a 'Persona Supplement' based on user data to bridge the gap between the user's context and their medical results.

            This user fits into the {base_level} group. The following rules 
            describe how to communicate to a user in that group

            {communication_example}

            TASK:
            Using the baseline template above as a structural guide only, generate 
            4-5 formatting and tone instructions that are specific to this individual 
            user. Each rule must reflect at least one detail from their inputs — such 
            as their age, stated literacy, specific confusion, or experience level. 

            RULES:
            - Be written as a behavioural instruction, not a label
            - Cover one of: sentence complexity, terminology usage, explanation depth, use of analogies (if applicable), emotional register
            - You are a solo AI assistant, not part of a team or service.
            - Never use wording that implies you are part of the clinical team. Use "the screening programme" and "the results show" instead.
            - You CANNOT book appointments so do not imply that you can

            OUTPUT FORMAT:
            Respond Strictly in the following format you are PROHIBITED from deviating from this format. YOU MUST NOT output any self-check or reasoning steps, only the final instructions and customisations:

            ADAPTIVE RULES:
            - Rule 1 
            - Rule 2
            - Rule 3
            - Rule 4
            - Rule 5
            '''
        
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": prompt_chaining_instructions},
                    {"role": "user", "content": user_data_input}
                ],
                options={
                    "temperature": 0.2,
                    "num_predict": 500, 
                    "top_p": 0.9   
                }
            )

            chat_history[data.session_id].append({
            "role": "user", 
            "content": user_data_input
            })

            persona_customisation = response["message"]["content"]
            #print("Persona Customisation Instructions:", persona_customisation)

            if user_age > 60:
                text_size = "20"
            else:
                text_size = "16"

            return {
                "theme": theme_selection,
                "text_size": text_size,
                "response": "Thanks for sharing that. I will adjust my responses to your specific needs! Please tell me what result code / descriptive phrase is written on your letter or share your concerns with me"
                }
        

    API_KEY_CREDITS[x_api_key] -= 1

    baseline_communication = '''You are a warm, supportive assistant. Read the emotional tone of each 
    message before responding.

    If the message sounds anxious, uncertain, or distressed, you must reassure the user and
    explain their results in a way to not further overwhelm them

    If the message is calm, factual, or practical, respond in kind.

    Empathy should surface naturally throughout a response when appropriate, 
    not as an opening ritual.

    Never start with "I want to acknowledge" or any similar meta-phrase. 
    Never label or announce what you are doing emotionally.

    Never manufacture warmth that the moment does not call for.

    Acknowledge the user's feeling, not the input.
    
    Make sure the information provided would be suitable for a person with a reading age of 12'''

    communication_injection = ''''''
    if persona_customisation:
        communication_injection = persona_customisation
    else:
        communication_injection = baseline_communication

    # print(communication_injection)

    
    #Selective Injection Logic 

    results = {
    "R0": '''No diabetic retinopathy: No changes in the eye due to diabetes. People with no retinopathy 
            are at low risk of developing any sight-threatening changes and will be recalled for screening 
            in one to two years. Screening intervals are changing in this group because the evidence 
            shows there is very little risk of sight-threatening retinopathy developing. Therefore 
            current 12-month screening will extend to two years and allow those at greater risk 
            to be screened more often. The user does not have diabetic retinopathy''',
    "R1": '''Background diabetic retinopathy (mild non proliferative retinopathy): Vessels become blocked 
            or leaky causing blood and other fluid to become visible on the retina. These changes are not 
            sight-threatening and will not affect your vision but improvements in self-care may help to reduce 
            the risk of retinopathy getting worse. People with background retinopathy will be recalled in one year 
            for screening. 
            ''',
    "R2": '''Pre-proliferative diabetic retinopathy (moderate/severe non proliferative retinopathy). 
            More changes due to diabetes are visible on the back of the eye. This could be more 
            bleeds, as well as signs of a lack of oxygen and changes in the shape of blood vessels 
            themselves. The risk of sight-threatening changes developing have increased. Therefore, 
            you could be screened more often, every three to six months or would be referred to a 
            specialist for more testing and closer monitoring (see Additional healthcare). These 
            changes will not affect your vision but improvements in self-care may help to reduce the 
            risk of retinopathy getting worse.''',
    "R3": '''Proliferative diabetic retinopathy (R3): At this stage the growth hormone known as VEGF is increased and abnormal blood 
            vessels grow on the retina. These new vessels grow into the gel in the middle of the 
            eye and bleed. Once they bleed, they will begin to affect sight causing black spots in 
            your vision or an increase in floaters. You will be referred to a specialist for testing (see 
            Additional healthcare) and possibly need treatment to stop the new vessels from 
            growing''',
    "M0": '''No maculopathy (M0): No changes due to diabetes within the macular area. If the retinopathy 
            level is R0 or R1, screening recall would be based on the retinopathy level.''',
    "M1": '''Maculopathy (M1): Changes due to diabetes can be seen within the macular area. Vessels in or around the 
            macula area become blocked or leaky. When blood and fluid leaks into the macular 
            it can cause swelling called oedema. Because the fovea is responsible for our central 
            vision and being able to read, swelling in this area has a higher risk of threatening sight. 
            However, not all screening programmes have the test available (known as ocular surface 
            temperature, or OCT imaging) to check for swelling and therefore this level would be 
            referred to a specialist for further tests and monitoring (see Additional healthcare). If 
            swelling is detected, then treatment would be needed to reduce the swelling and limit 
            the effect on vision.''',
    "no_changes": '''
            The screening found no changes to the back of the eye related to 
            diabetes. This is a clear result and no treatment is needed at 
            this time. The patient will be recalled for routine screening.''',
    "some_changes_no_treatment": ''' 
            Some changes related to diabetes were found during screening but 
            these do not currently require treatment. The patient should 
            continue to manage their diabetes and attend future screenings. 
            Self-care improvements may help prevent further changes.''',
    "further_examination": '''
            Changes were found that require closer examination by a hospital 
            eye specialist. This does not necessarily mean treatment is needed 
            but a referral has been made so a specialist can assess the eyes 
            in more detail.''',
    "inconclusive_photographs": '''
        The photographs taken during screening were not clear enough to 
        assess the back of the eye. This is not a result about the 
        patient's eye health — it means the screening could not be 
        completed and will need to be repeated.''',
    "cataract_referral": '''
        A cataract prevented clear photographs of the back of the eye 
        during screening. Because the retina could not be assessed, a 
        referral to a hospital eye specialist has been made to examine 
        the eye more closely. The referral is due to the incomplete 
        screening, not necessarily because a problem has been found.
    ''',
    "existing_condition": '''
        Due to an existing eye condition, standard diabetic eye screening 
        may not be appropriate. The patient may be monitored through 
        another pathway such as a hospital eye service instead of the 
        routine screening programme.
    '''
    }

    phrase_to_key = {
    "no changes due to diabetes": "no_changes",
    "some changes": "some_changes_no_treatment",
    "do not need any treatment": "some_changes_no_treatment",
    "does not need any treatment": "some_changes_no_treatment",
    "further examination": "further_examination",
    "hospital eye specialist": "further_examination",
    "did not allow us to see": "inconclusive_photographs",
    "unable to photograph": "inconclusive_photographs",
    "presence of a cataract": "cataract_referral",
    "existing eye condition": "existing_condition",
    "not be necessary for you to be screened": "existing_condition"
}
    
    result_reporting_indicators = [
        "my letter says",
        "my letter states",
        "the letter says",
        "my result says",
        "my result is",
        "my results say",
        "my results are",
        "it says on my letter",
        "the screening letter says",
        "i got my results",
        "i received my results",
        "my screening says",
        "the result on my letter",
        "it says",
        "mine says",
        "mine is"
    ]

    def is_reporting_result(prompt):
        for phrase in result_reporting_indicators:
            if phrase in prompt.lower():
                return True
    

    def find_result_in_prompt(prompt):
        found_results = []
        found_keys = []

        p = prompt.lower()
        
        matches = re.findall(r"\b[RM][0-3]\b", p, re.IGNORECASE)
        for match in matches:
            code = match.upper()
            if code not in found_results:
                found_results.append(code)
        
        for phrase, key in phrase_to_key.items():
            if phrase in p and key not in found_keys:
                found_keys.append(key)

        return [found_results, found_keys]


    
    reporting_result = is_reporting_result(data.prompt)
    # print(reporting_result)
    code = find_result_in_prompt(data.prompt)

    if reporting_result:
        if len(code[0]) > 0:
            for i in range(len(code[0])):
                result_store.append(results[code[0][i]])
        else:
            if len(code[1]) > 0:
                for i in range(len(code[1])):
                    result_store.append(results[code[1][i]])
    
    # print(code[0])
    # print(code[1])

    def prompt_builder(prompt, is_reporting_result):

        role_injection = '''
        You are a warm, knowledgeable assistant who helps diabetic eye screening patients 
        understand their screening results. Assume the users know that diabetic retinopathy is a complication of diabetes.
        '''

        topic_injection = '''
        You may ONLY answer questions about diabetic eye screening 
        results, screening letters, and what results mean. For ANY 
        other topic, say: "I'm only able to help with diabetic eye 
        screening questions."
        '''

        communication_injection = persona_customisation if persona_customisation else baseline_communication
        
        #print(result_store)

        if reporting_result:
            definitions_block = "\n\n".join(result_store)
            if is_reporting_result:
                if len(result_store) > 0:
                    result_injection = f'''
                    VERIFIED RESULTS:
                    The following result(s) have been identified from the user's input.

                    CLINICAL REFERENCE — FOR YOUR USE ONLY:
                    Use the following to inform your explanation. Do NOT reproduce 
                    it verbatim — translate it into language appropriate for this 
                    user's communication rules. Address all results present.

                    {definitions_block}

                    CRITICAL: You may ONLY explain the results listed above. Do not 
                    reference, imply, or explain any result not covered here. If the 
                    user asks about something not covered above, direct them to their 
                    clinical team.
                    '''

                elif len(result_store) > 0:
                    result_injection = f'''
                    CONTEXT:
                    The user has already shared their results earlier in this 
                    conversation. Use only the following to respond to their 
                    message. Do not introduce any new clinical detail.

                    {definitions_block}

                    If their message cannot be addressed from the above, say:
                    "For more detail on this I would recommend speaking with 
                    your clinical team."

                    '''
                else:
                    # User signalled reporting but nothing was extracted
                    result_injection = '''
                    NO VALID RESULTS FOUND:
                    The user indicated they are sharing a result but no recognised 
                    result code or phrase was identified. Ask them to share the 
                    exact wording or code from their screening letter.3
                    '''
        else:
            if len(result_store) > 0:
                # User is asking a general question but has results in history
                definitions_block = "\n\n".join(result_store)
                result_injection = f'''
                CONTEXT:
                The user is asking a question about their results. Use only 
                the following information to respond. Do not introduce any 
                new clinical detail not present here.

                {definitions_block}

                If their question cannot be answered from the above, say:
                "For more detail on this I would recommend speaking with 
                your clinical team."
                '''

            else:
                # No results anywhere — ask for the letter
                result_injection = '''
                NO RESULTS PROVIDED:
                The user has not shared any screening results. Ask them to 
                share the exact wording or code from their screening letter 
                before proceeding. Do not explain, assume, or imply any results.
                '''

        distress_indicators = [
        "worried", "scared", "frightened", "anxious", "nervous",
        "upset", "concerned", "afraid", "terrified", "panic"
        ]
        user_distressed = any(word in prompt.lower() for word in distress_indicators)

        if user_distressed:
            empathy_injection = '''
            EMPATHY:
            The user has expressed worry or distress. Open with brief, 
            natural reassurance before explaining anything. Do not skip 
            this because the result is positive. Reassurance should live 
            in the framing throughout, not saved for one sentence.
            '''
        else:
            empathy_injection = '''
            EMPATHY:
            The user has not expressed any worry or distress. Do NOT 
            open with reassurance or imply they are concerned. Respond 
            warmly and directly. Do not project emotions onto the user 
            that they have not expressed.'''
        
        
        next_step_indicators = [
        "what can i do",
        "what should i do",
        "how can i",
        "how do i",
        "what are my options",
        "what happens next",
        "next steps",
        "what now",
        "where do i go",
        "what do i do now",
        "can i do anything",
        "is there anything i can do",
        "how to manage",
        "how do i manage",
        "what can i change",
        "will it get worse",
        ]

        user_wants_next_step = any(phrase in prompt.lower() for phrase in next_step_indicators)

        if user_wants_next_step and len(result_store) > 0:
            next_step_injection = '''
            The user has asked what they can do in the future to help manage their condition

            ways to help improve the management of diabetes to limit the risk of diabetic retinopathy are as follows,
            
            - 1 percent or 11mmol/mol reduction in HbA1c gives a 40 percent reduction in risk of eye complications
            - 10mmHg reduction in blood pressure gives a 35 percent reduction in risk of eye complications
            - Making sure to attend screening appointments and ophthalmology appointments

            use this information when giving your response to the user
            '''
        else:
            next_step_injection = ''''''

        rules_injection='''
        RULES:
        
        If the patient explicitly signals worry or distress, open with brief natural 
        reassurance before explaining. Do not skip this because the answer is positive.

        It is essential to provide empathy towards the user if they show signs of worry or distress, 
        DO NOT skip this stage

        Never end abruptly with a clinical fact. Close with something forward-looking 
        or human.

        Reassurance should live in the framing throughout, not saved for one 
        "good news" sentence.

        ALWAYS refer to yourself as "I" you are FORBIDDEN from saying "we" or "our". You are a solo AI 
        assistant, not part of a team or service.

        Never use wording that implies you are part of the clinical team. 
        Use "the screening programme" and "the results show" instead.

        You CANNOT book appointments so do not imply that you can

        If the user provides a result with an R it stands for Retinopathy, M for Maculopathy
        '''

        prompt = f'''
        {role_injection}

        {topic_injection}

        {result_injection}

        {communication_injection}

        {empathy_injection}

        {next_step_injection}

        {rules_injection}
        '''

        return prompt
        

    system_instruction = prompt_builder(data.prompt, reporting_result)

    print(system_instruction)

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
        "num_predict": 400, 
        "top_p": 0.9   
    }
    )

    REFUSAL_TRIGGER = "I'm only able to help with diabetic eye screening questions."

    if response["message"]["content"].startswith(REFUSAL_TRIGGER):
        response["message"]["content"] = REFUSAL_TRIGGER + " Please only ask questions related to your screening letter or results, so I can assist you better."

    # print(response["message"]["content"])

    chat_history[data.session_id].append({
    "role": "user", 
    "content": data.prompt
    })
    chat_history[data.session_id].append({
        "role": "assistant", 
        "content": response["message"]["content"]
    })

    # print(chat_history)

    return {"response": response["message"]["content"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)