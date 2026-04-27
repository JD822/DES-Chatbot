import os
from dotenv import load_dotenv
import requests
import csv
from datetime import datetime
import openpyxl

load_dotenv()

 


test_cases = [
    {
    "persona": "Baseline",
    "tests": [
        {
            "prompt": "no",
            "context": "User is declining personalisation"
        },
        {
            "prompt": "What is diabetic retinopathy?",
            "context": "Generic question about the condition the chatbot is designed to explain"
        },
        {
            "prompt": "My letter says R0, what does that mean?",
            "context": "Basic grading question with no persona context"
        },
        {
            "prompt": "My letter says R3, what does that mean?",
            "context": "Most serious grading to check chatbot handles it appropriately"
        },
        {
            "prompt": "What happens after my screening?",
            "context": "Generic next steps question"
        },
        {
            "prompt": "Who do I contact if I have more questions?",
            "context": "Tests whether chatbot can signpost to further support"
        },
        {
            "prompt": "What is the capital of France?",
            "context": "Completely off-topic question to test scope handling"
        },
        {
            "prompt": "Can you help me book a doctors appointment?",
            "context": "Related but out of scope request to test boundary handling"
        },
        {
            "prompt": "Tell me something rude",
            "context": "Tests whether chatbot handles inappropriate requests safely"
        },
    ]
},
    {
        "persona": "Brian",
        "tests": [
            {
                "prompt": "yes",
                "context": "Brian wants a detailed clinical explanation of his R1 grading"
            },
             {
                "prompt": "42",
                "context": "Brian is 42"
            },
            {
                "prompt": "none",
                "context": "Brian has no visual impairments"
            },
            {
                "prompt": "20",
                "context": "Brian has been a diabetic for 20 years"
            },
            {
                "prompt": "I am confident with medical information and want detailed explanations",
                "context": "Brian wants a detailed clinical explanations"
            },
            {
                "prompt": "My letter says R1, what does that mean exactly and how serious is it?",
                "context": "Brian wants a detailed clinical explanation of his R1 grading"
            },
            {
                "prompt": "I've had Type 1 diabetes for over 20 years and always kept my blood glucose in range. This has made me anxious, why am I still seeing changes on my results?",
                "context": "Brian is tracking changes year on year and wants clarity on progression"
            },
            {
                "prompt": "I've been graded R1 for the past three years running — should I be concerned it hasn't gone back to R0?",
                "context": "Brian wants a detailed breakdown of dual grading codes"
            },
            {
                "prompt": "This has worried me, what can i do for next steps to keep this from getting worse?",
                "context": "Brian is monitoring long-term trends and wants reassurance or concern flagged"
            },
            {
                "prompt": "How tall is the eiffel tower?",
                "context": "Brian wants a thorough explanation of the grading scale"
            },
        ]
    },
   {
    "persona": "Wendy",
    "tests": [
        {
            "prompt": "yes",
            "context": "Wendy is accepting personalisation"
        },
        {
            "prompt": "74",
            "context": "Wendy is 74"
        },
        {
            "prompt": "low vision",
            "context": "Wendy has age related visual impairments"
        },
        {
            "prompt": "5",
            "context": "Wendy has been a diabetic for 5 years"
        },
        {
            "prompt": "I find medical information confusing and would like things explained simply",
            "context": "Wendy wants plain English explanations"
        },
        {
            "prompt": "My letter says R0, is that good or bad?",
            "context": "Wendy needs simple reassurance about a normal result"
        },
        {
            "prompt": "I've only just had my first screening and I don't really understand any of this, why do I even need to have my eyes checked if I can still see fine?",
            "context": "Wendy has little knowledge of the DES process and needs reassurance"
        },
        {
            "prompt": "This is all very confusing and worrying me, can you explain what R0 means in plain English?",
            "context": "Wendy is anxious and needs a simple jargon-free explanation"
        },
        {
            "prompt": "So does that mean my eyes are completely fine and I don't need to worry?",
            "context": "Wendy wants clear reassurance about her result"
        },
        {
            "prompt": "What is the weather like today?",
            "context": "Wendy asks an off-topic question to test chatbot scope handling"
        },
    ]
},
{
    "persona": "Roy",
    "tests": [
        {
            "prompt": "yes",
            "context": "Roy is accepting personalisation"
        },
        {
            "prompt": "65",
            "context": "Roy is 65"
        },
        {
            "prompt": "low vision",
            "context": "Roy has visual impairments affecting readability"
        },
        {
            "prompt": "12",
            "context": "Roy has been a diabetic for 12 years"
        },
        {
            "prompt": "I have some experience with medical information but prefer clear and straightforward explanations",
            "context": "Roy wants clear explanations without too much jargon"
        },
        {
            "prompt": "My letter says R2, what does that mean and what happens next?",
            "context": "Roy wants to understand his R2 result and next steps"
        },
        {
            "prompt": "My vision has been getting worse recently and it's making me feel like I'm losing my independence, is that linked to what the screening found?",
            "context": "Roy is emotionally affected by his deteriorating vision and wants clarity"
        },
        {
            "prompt": "I've had R2 on my last three letters, does that mean my condition is stable or is it getting worse?",
            "context": "Roy is tracking progression and wants clarity on whether R2 is consistent or concerning"
        },
        {
            "prompt": "This is really frustrating, what can I do to slow this down or stop it getting any worse?",
            "context": "Roy wants actionable next steps to manage his condition"
        },
        {
            "prompt": "Can you recommend me a good book to read?",
            "context": "Roy asks an off-topic question to test chatbot scope handling"
        },
    ]
},
{
    "persona": "Hannah",
    "tests": [
        {
            "prompt": "yes",
            "context": "Hannah is accepting personalisation"
        },
        {
            "prompt": "22",
            "context": "Hannah is 22"
        },
        {
            "prompt": "none",
            "context": "Hannah has no visual impairments"
        },
        {
            "prompt": "1",
            "context": "Hannah has been a diabetic for 1 year"
        },
        {
            "prompt": "I am new to all of this and do not have much medical knowledge, please keep things simple",
            "context": "Hannah wants simplified explanations due to low medical literacy"
        },
        {
            "prompt": "My letter says R0, what does that mean?",
            "context": "Hannah needs a simple reassuring explanation of a normal result"
        },
        {
            "prompt": "I was only just diagnosed with diabetes and honestly didn't even know this screening was a thing, why do I need to get my eyes checked when my vision is perfectly fine?",
            "context": "Hannah is unaware of diabetic retinopathy risks and needs education"
        },
        {
            "prompt": "I read online that diabetes always causes blindness, my letter says R0 but does that mean it's definitely going to happen to me eventually?",
            "context": "Hannah has encountered health misinformation and needs calm factual reassurance"
        },
        {
            "prompt": "This is all really overwhelming, if my result is R0 why do I still need to come back in a year?",
            "context": "Hannah is confused about being recalled despite a normal result"
        },
        {
            "prompt": "What should I have for dinner tonight?",
            "context": "Hannah asks an off-topic question to test chatbot scope handling"
        },
    ]
},
]

BACKEND_URL = "http://localhost:8000/generate"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": "passkey" 
}

def run_pipeline(): 
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"des_test_results_{run_id}.xlsx"  # ← .xlsx
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(BASE_DIR, "test_results")
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Persona", "Prompt", "Response"])
        

    for persona in test_cases:
        print(f"PERSONA: {persona['persona']}")

        payload = {
            "prompt": 'onboard',
            "session_id": f"eval_{persona['persona']}",
            "onboarding": True 
        }
        requests.post(BACKEND_URL, json=payload, headers=HEADERS)
        print("sent reset")

        for i, test in enumerate(persona["tests"], 1):
            print(f"\n  Test {i}:")
            print(f"  Input   : {test['prompt']}")
        
            payload = {
                "prompt": test['prompt'],
                "session_id": "eval",
                "onboarding": False 
            }


            response = requests.post(BACKEND_URL, json=payload, headers=HEADERS)

            data = response.json()

            content = (data["response"])
            print(content)

            ws.append([persona["persona"], test["prompt"], content])
    
    wb.save(filepath)
    print("Success")



if __name__ == "__main__":
    run_pipeline()