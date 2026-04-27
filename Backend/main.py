import uvicorn
import re
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import ollama
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv() 



# 10 Message limit
API_KEY_CREDITS = {os.getenv("API_KEY"): 10}

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

class Prompt(BaseModel):
    session_id: str
    prompt: str
    onboarding: bool 

# Chat history and result store to give to LLM prompt
chat_history = {}
result_store = []

# Onboarding Variables
awaiting_personalisation_response = True
personalise_response = False
user_age = "Age not provided"
vision_status = "Vision status not provided"
literacy_level = "Literacy level not provided"
user_experience = "Experience not provided"
base_level = ""
persona_customisation = ""



@app.post("/generate")
def generate(data: Prompt, x_api_key: str = Depends(verify_api_key)):

    # Obtain Stores and Variables
    global awaiting_personalisation_response, personalise_response, user_age, vision_status, literacy_level, user_experience, persona_customisation, result_store, base_level

    # If there are no messages left return a standard message prompting to contact a professional
    if API_KEY_CREDITS[x_api_key] == 0:
        return {"response": "You have reached your messages limit, please contact your healthcare provider with any further questions you may have."}


    # If the session id is not in chat history create a new one
    if data.session_id not in chat_history:
        chat_history[data.session_id] = []

    # If onboarding make sure all variables are at default (data purge)
    if data.onboarding:
        print("Starting Onboarding")
        awaiting_personalisation_response = True
        personalise_response = False
        user_age = "Age not provided"
        vision_status = "Vision status not provided"
        user_experience = "Experience not provided"
        literacy_level = "Literacy level not provided"
        chat_history[data.session_id] = []
        result_store = []
        API_KEY_CREDITS[os.getenv("API_KEY")] = 10
    

    # If the user has not yet chose to personalise responses
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

    # If the user chooses to personalise code transitions to onboarding block
    if personalise_response:
        # Gather Age
        if user_age == "Age not provided":
            user_age = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                age_value = int(match.group())
                
                # If age is inbetween certain values accept it
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
            
        # Gather user vissual impairment (if applicable)
        if vision_status == "Vision status not provided":
            vision_status = data.prompt.lower()
            if vision_status not in ["none", "colour blindness", "low vision", "light sensitivity", "screen reader user"]:
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, "
                "I can only adjust to one of those specific vision statuses currently."}
            return {"response": '''Thank you for sharing that. Now can you please tell me how long you have been a diabetic for? Please only use a number for the amount of years e.g. 0 for a new diabetic or 20 for 20 years'''}
        
        # Gather user years of experience managing diabetes
        if user_experience == "Experience not provided":
            user_experience = data.prompt if data.prompt.isdigit() else "Age not provided"
            match = re.search(r'\d+', data.prompt)
            
            if match:
                experience_value = int(match.group())
                
                # If number between certain values
                if 0 <= experience_value <= 100:
                    user_experience = experience_value
                    return {"response": '''Lastly, please give a brief description on your knowledge on diabetic eye screening results and medical information in general, this will help me adjust my language to suit you better. You can say something like 'I have a good understanding and want detailed explanations' or 'I find medical information confusing and want simple explanations' or anything in between'''}
            else:
                return {"response": "Please provide how many years you have been a diabetic using just a number, that way I can adjust my explanations to suit you better."}

        # Gather user literacy level
        if literacy_level == "Literacy level not provided":
            literacy_level = data.prompt
            if literacy_level == "Literacy level not provided":
                return {"response": "Please choose from the previously mentioned options, as this is a proof of concept, I can only adjust to those specific styles currently."}
            
            # User data input to act as user side for prompt chaining response 1 (adaptive rules)
            user_data_input = f'''
            User Inputs:
            Age: {user_age}
            Visual impairment: {vision_status} 
            Years managing diabetes: {user_experience}
            Literacy: {literacy_level}
        '''
            

            # Depending on the user visual impairment or age alter UI theme
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

            # Get a base experience level based on user experience level 
            def experience_level_calculation(experience_level):
                if experience_level <= 3:
                    base_level = 'novice'
                elif experience_level <= 10:
                    base_level = 'intermediate'
                else:
                    base_level = 'expert'
                return base_level

            base_level = experience_level_calculation(user_experience)

            # Health literacy indicators
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
                # Indexes: 0 = Low, 1 = Moderate, 2 = High
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

                # Find most indicators
                max_score = max(literacy_indicators)

                # Index will find the first occurence of the max score, picking applicable lowest literacy level 
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

            # Apply shift based on literacy level
            if literacy_calculation == 'LOW':
                if base_level == 'expert':
                    base_level = 'intermediate'
                if base_level == 'intermediate':
                    base_level = 'novice'

            # Reasoning examples based on base level

            reasoning_examples  = {
            "novice": '''
                TONE: Warm and encouraging.
                SENTENCES: Max 12 words. One idea per sentence. New paragraph per concept
                TERMINOLOGY: Plain term first followed by clinical in brackets. EXAMPLE: "back of eye (retina)".
                KNOWLEDGE: Explain from scratch, assume nothing.
                EMPATHY: Weave reassurance throughout response, not just at beggining or end.
            ''',

            "intermediate": '''
                TONE: Collborative, treat them as an active partner not a recipient
                SENTENCES: Compound sentences linking cause and effect
                TERMINOLOGY: Clinical term first, brief definition after EXAMPLE: "Maculopathy - changes in the central retina". Skip basic deinitions 
                KNOWLEDGE: Skip diabetes basics. Assume understanding, not grading detail
                EMPATHY: Acknowledge for management effort once only
            ''',

            "expert": '''
                TONE: Peer-to-peer. Direct and efficient
                SENTENCES: Information-rich. Lead with finding, then implication
                TERMINOLOGY: Standard clinical terms only - HbA1c, VEGF, OCT, No plain subsititutes
                KNOWLEDGE: Assume full mastery. Only explain context if asked
                EMPATHY: Brief acknowledgement 
            '''
            }
        
            communication_example = reasoning_examples[base_level]

            # System instruction for the Adaptive rules creation
            prompt_chaining_instructions =f''' You are a Prompt Engineer. Your task is to generate a 'Persona Supplement' based on user data to bridge the gap between the user's context and their medical results.

            This user fits into the {base_level} group. The following rules 
            describe how to communicate to a user in that group

            {communication_example}

            TASK:
            Using the baseline template above as a structural guide only, generate 
            4-5 formatting and tone instructions that are specific to this individual 
            user. Each rule must reflect at least one detail from their inputs — such 
            as their age, stated literacy, specific confusion, or experience level. 

            HARD CONSTRAINTS, these apply to every rule you generate:
            - Never use "we" or "our", use "I" only
            - Never reference booking appointments
            - Never imply you are part of the clinical team
            - Use "the results show" and "the screening programme", never possessive equivalents
            - Do not include example sentences in your rules, state the instruction only

            OUTPUT FORMAT:
            Respond Strictly in the following format you are PROHIBITED from deviating from this format. YOU MUST NOT output any self-check or reasoning steps, only the final instructions and customisations:

            ADAPTIVE RULES:
            - Rule 1 
            - Rule 2
            - Rule 3
            - Rule 4
            - Rule 5
            '''
        
            # Generate personalised communication rules
            response = ollama.chat(
                model='llama3.1',
                messages=[
                    {"role": "system", "content": prompt_chaining_instructions},
                    {"role": "user", "content": user_data_input}
                ],
               options={
                    "temperature": 0.1,
                    "num_predict": 300,  
                    "top_p": 0.85,
                    "repeat_penalty": 1.3,  
                    "top_k": 20,            
                    "num_ctx": 4096,
}
            )

            # Append user data to the history so the LLM has base context in future calls
            chat_history[data.session_id].append({
            "role": "user", 
            "content": user_data_input
            })

            # Extract adaptive rules response
            persona_customisation = response["message"]["content"]

            # Set text size based on user age
            if user_age > 60:
                text_size = "20"
            else:
                text_size = "16"

            # Return message to user after customisation complete, return theme and text size to be applied automatically
            return {
                "theme": theme_selection,
                "text_size": text_size,
                "response": "Thanks for sharing that. I will adjust my responses to your specific needs! Please tell me what result code / descriptive phrase is written on your letter or share your concerns with me"
                }
        

    API_KEY_CREDITS[x_api_key] -= 1

    # Append user prompt to history for conversation persistence 
    chat_history[data.session_id].append(data.prompt)

    # Baseline communication rules if the user did not personalise 
    baseline_communication = '''
            TONE: Warm and Clear. Write as if exlaining to sensible young adult.
            SENTENCES: Short sentences only. One idea per sentence, maximum 12 words per. Start a new paragraph for each new idea.
            KNOWLEDGE: Assume the user has basic diabetes knowledge. Explain everything else from scratch
            EMPATHY: Acknowledge result before explaining it. Weave reassurance in naturally
            READING LEVEL: Every sentence must be understandable to a 12 year old without re-reading.

''' 


    
    # Selective Injection Logic 

    # Result code meanings based of leaflet letter provided
    # With translations for descriptive phrases from older letters if that is applicable instead

    results = {
    "R0": '''No diabetic retinopathy: No changes in the eye due to diabetes. People with no retinopathy 
            are at low risk of developing any sight-threatening changes and will be recalled for screening 
            in one to two years. Screening intervals are changing in this group because the evidence 
            shows there is very little risk of sight-threatening retinopathy developing. Therefore 
            current 12-month screening will extend to two years. The user does not have diabetic retinopathy''',
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
            growing. The user requires urgent refferal to it is important they do not delay their follow up. ''',
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

    # Checking for specific phrases from letter

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
    
    # Checking for user phrase to indicate reporting a result

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

    # If one of the phrases is found the user is reporting a result

    def is_reporting_result(prompt):
        for phrase in result_reporting_indicators:
            if phrase in prompt.lower():
                return True
    

    def find_result_in_prompt(prompt):
        found_results = []
        found_keys = []

        p = prompt.lower()
        
        # Regex to find results in prompt if reporting a result 

        matches = re.findall(r"\b[RM][0-3]\b", p, re.IGNORECASE)
        for match in matches:
            code = match.upper()
            if code not in found_results:
                found_results.append(code)
        
        # Looks for each potential phrase in a users message if a descriptive phrase is mentioned
        for phrase, key in phrase_to_key.items():
            if phrase in p and key not in found_keys:
                found_keys.append(key)

        # Return findings
        return [found_results, found_keys]


    
    reporting_result = is_reporting_result(data.prompt) 

    # code = find_result_in_prompt(data.prompt)

    if reporting_result:
        code = find_result_in_prompt(data.prompt)
        # Prefer coded results over descriptive phrases
        if len(code[0]) > 0:
            for i in range(len(code[0])):
                content = results[code[0][i]]
                if content not in result_store:
                    result_store.append(content)
        else:
            if len(code[1]) > 0:
                for i in range(len(code[1])):
                    content = results[code[1][i]]
                    # Only add if it's not already in the store
                    if content not in result_store:
                        result_store.append(content)
    

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

        if reporting_result:
            unique_results = list(set(result_store))
            definitions_block = "\n\n".join(unique_results)
            if is_reporting_result:
                if len(result_store) > 0:
                    result_injection = f'''
                    VERIFIED RESULTS:
                    Use the following to inform your explanation. Do not reproduce it verbatim, translate it 
                    into language appropriate for this user. Adress all results present. R indicates Retinopathy
                    M indicates Maculopathy

                    {definitions_block}


                    Only explain the results listed above never assume clincal detail. If the user asks about anything not covered here,
                    direct them to their clinical team. Limit responses to the necesary information from the definitons block.

                    - Always begin by stating the result code and its meaning in the first sentence (e.g. “R1 means background diabetic retinopathy”).
                    - Always include: severity (mild/early stage), “not sight-threatening”, and “will not affect your vision” when applicable.
                    - Do not speculate about causes or contributing factors unless explicitly stated in the context.
                    - Explain in line with the users communication rules below
                    - When discussing management, use neutral phrasing such as “taking good care of your diabetes”. Do not use language that implies poor control (e.g. “better self-care”).
                    - End with a neutral, supportive question (e.g. “Does that make sense, or is there anything you'd like me to explain further?”).
                   
                    '''

                else:
                    # User signalled reporting but nothing was extracted
                    result_injection = '''
                    NO VALID RESULTS FOUND:
                    The user indicated they are sharing a result but no recognised 
                    result code or phrase was identified. Ask them to share the 
                    exact wording or code from their screening letter.
                    '''
        else:
            if len(result_store) > 0:
                # User is asking a general question but has results in history
                unique_results = list(set(result_store))
                definitions_block = "\n\n".join(unique_results)
                result_injection = f'''
                CONTEXT:
                The user is asking a question about their results. Use only 
                the following information to respond. Do not introduce or assume any 
                new clinical detail not present here.

                {definitions_block}

                If their question cannot be answered from the above, say:
                "For more detail on this I would recommend speaking with 
                your clinical team."

                - State the effect on vision for this diagnosis
                - Do not speculate about causes or contributing factors unless explicitly stated in the context.
                - When interpreting repeated results, describe them as “stable” rather than assuming no progression unless explicitly stated.
                - If the user asks why something has happened and the reason is not explicitly stated above, 
                  acknowledge the uncertainty and explain only what is known from the provided information before offering the fallback.
                - When discussing results over time (e.g. stable, unchanged, or progression), always restate the severity and vision impact 
                  using the provided information (e.g. mild, not sight-threatening, no effect on vision).
                - When discussing management, use neutral phrasing such as “taking good care of your diabetes”. Do not use language that implies poor control (e.g. “better self-care”).
                - End with a neutral, supportive question (e.g. “Does that make sense, or is there anything you'd like me to explain further?”).
                '''

            else:
                # No results anywhere — ask for the letter
                result_injection = '''
                NO RESULTS PROVIDED:
                The user has not shared any screening results. Ask them to 
                share the exact wording or code from their screening letter 
                before proceeding. Do not explain, assume, or imply any results.
                '''

        if persona_customisation:
            user_data_injection = f'''

            Below is data input by the user during their personalisation, if applicable in your answer refer to this data

            User Inputs:
            Age: {user_age}
            Visual impairment: {vision_status} 
            Years managing diabetes: {user_experience}
            Literacy: {literacy_level}
        '''
        else:
            user_data_injection =''''''

        communication_injection = persona_customisation if persona_customisation else baseline_communication



        distress_indicators = [
        "worried", "scared", "frightened", "anxious", "nervous",
        "upset", "concerned", "afraid", "terrified", "panic"
        ]

        user_distressed = any(word in prompt.lower() for word in distress_indicators)

        if user_distressed:
            empathy_injection = '''
            EMPATHY: The user has expressed worry or distress. Open with brief, 
            natural reassurance before explaining anything. Even if the result is positive.
            Weave reassurance into framing throughout
            '''
        else:
            empathy_injection = '''
            EMPATHY: The user has not expressed distress. Respond warmly and directly.
            Do not open with reassurance or project any emotions they have not expressed'''
        
        
        next_step_indicators = [
        "what can i do",
        "what else can i do",
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
            NEXT STEPS: The user has asked what they can do, use the following:

            ways to help improve the management of diabetes to limit the risk of diabetic retinopathy are as follows,
            
            - A 1% (11mmol/mol) HbA1c drop reduces eye risk by 40%.
            - A 10mmHg blood pressure drop reduces eye risk by 35%.
            - Always attend your screening and eye appointments.

            use all of this information when giving your response to the user
            '''
        else:
            next_step_injection = ''''''

        rules_injection='''
        RULES:
        - Refer to yourself as "I" only, never "we" or "our"
        - Never imply you are part of the clinical team. Use "the screening programme" and "the results show"
        - Never imply you can book appointments
        - Do not use posessive clinical interpretation. Only use general or conditional language
        - Do not downplay a serious result
        - Do not end abruptly on a clinical fact close with something forward-looking or human
        - Never make promises on behalf of the screnning programme
        - Never state, imply, or estimate recall intervals or appointment timelines unless 
          they are explicitly present in the verified results block
        - Maximum of 12 words per sentence

        If the user mentions any of the following symptoms or concerns:
        - Sudden or gradual vision loss / "vision getting worse"
        - New floaters, flashes of light, or black spots
        - Blurred, distorted, or "patchy" vision
        - Pain in the eye

        YOU MUST:
        1. Immediately advise them to contact their clinical team, GP, or an eye specialist (optometrist) urgently.
        2. Prioritise this advice over any standard result explanation.
        3. Even if their result is R0, do not tell them "there is nothing to worry about" if they have these symptoms.
        4. Use the phrase: "Because you mentioned changes in your vision, it is very important that you speak with a medical professional as soon as possible."
    '"
        '''

        prompt = f'''
        {role_injection}
        {topic_injection}
        {result_injection}
        {user_data_injection}
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
        model='llama3.1',
        messages=[
            {"role": "system", "content": system_instruction},
            *history,
            {"role": "user", "content": data.prompt}
        ],
        options={
        "temperature": 0.2,
        "num_predict": 400, 
        "top_p": 0.9,
        "repeat_penalty": 1.2,  
        "top_k": 40,          
        "num_ctx": 4096, 
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