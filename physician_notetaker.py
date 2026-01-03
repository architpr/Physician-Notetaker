import json
import os
from groq import Groq

class MedicalNoteTaker:
    def __init__(self, api_key=None):
        """
        Initialize the MedicalNoteTaker with Groq API.
        
        Args:
            api_key (str): Groq API Key. If None, expects GROQ_API_KEY in env vars.
        """
        self.api_key = api_key
        # Check env var if not passed explicitly
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
            
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print("Groq Client initialized successfully.")
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
                self.client = None
        else:
            print("Warning: No Groq API Key provided. Set it in the app or environment.")
            self.client = None

    def process_transcript(self, conversation_text):
        """
        Process the transcript using Groq Llama 3 to generate all outputs in one go.
        """
        if not self.client:
            return {}, {}, {}

        # System Prompt for Structured JSON
        system_prompt = """
        You are an expert Medical Scribe and Clinical AI.
        Your task is to analyze a doctor-patient conversation and extract structured clinical data.
        
        You must output a SINGLE JSON object with the following three nested keys:
        
        1. "Task_A": {
            "Patient_Name": "Extract full name or Unknown",
            "Symptoms": ["List", "of", "exact", "symptoms"],
            "Diagnosis": ["List", "of", "diagnoses"],
            "Treatment": ["List", "of", "medications", "therapies"],
            "Current_Status": "Brief status",
            "Prognosis": "Brief prognosis"
        }
        
        2. "Task_B": {
            "Sentiment": "One of: Anxious/Concerned, Reassured/Positive, Neutral",
            "Intent": "Brief intent, e.g., Symptom Reporting, Follow-up"
        }
        
        3. "Task_C": {
            "Subjective": "Detailed summary of patient history and complaints",
            "Objective": "Physical exam findings (if any)",
            "Assessment": "Diagnosis and clinical impression",
            "Plan": "Treatment plan and follow-up instructions"
        }
        
        Ensure the JSON is valid and strictly follows this structure. Do not include markdown formatting like ```json ... ```. Just the raw JSON string.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": conversation_text,
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            response_content = chat_completion.choices[0].message.content
            print("\n--- RAW GROQ RESPONSE ---\n")
            print(response_content)
            print("\n-------------------------\n")
            
            try:
                data = json.loads(response_content)
            except json.JSONDecodeError:
                print("Error: Invalid JSON received from Groq.")
                return {}, {}, {}

            # Robust Extraction (Handle Flat vs Nested)
            if "Task_A" in data:
                return data.get("Task_A", {}), data.get("Task_B", {}), data.get("Task_C", {})
            elif "Patient_Name" in data:
                # Fallback: Model returned flat JSON
                print("Warning: Model returned flat JSON. Mapping key subsets manually.")
                task_a = {k: data.get(k) for k in ["Patient_Name", "Symptoms", "Diagnosis", "Treatment", "Current_Status", "Prognosis"]}
                task_b = {k: data.get(k) for k in ["Sentiment", "Intent"]}
                task_c = {k: data.get(k) for k in ["Subjective", "Objective", "Assessment", "Plan"]}
                return task_a, task_b, task_c
            else:
                return {}, {}, {}
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            # Return empty structure on failure
            return {}, {}, {}


# --- Input Data ---
conversation_text = """
Physician: Good morning, Ms. Jones. How are you feeling today?
Patient: Good morning, doctor. I’m doing better, but I still have some discomfort now and then.
Physician: I understand you were in a car accident last September. Can you walk me through what happened?
Patient: Yes, it was on September 1st, around 12:30 in the afternoon. I was driving from Cheadle Hulme to Manchester when I had to stop in traffic. Out of nowhere, another car hit me from behind, which pushed my car into the one in front.
Physician: That sounds like a strong impact. Were you wearing your seatbelt?
Patient: Yes, I always do.
Physician: What did you feel immediately after the accident?
Patient: At first, I was just shocked. But then I realized I had hit my head on the steering wheel, and I could feel pain in my neck and back almost right away.
Physician: Did you seek medical attention at that time?
Patient: Yes, I went to Moss Bank Accident and Emergency. They checked me over and said it was a whiplash injury, but they didn’t do any X-rays. They just gave me some advice and sent me home.
Physician: How did things progress after that?
Patient: The first four weeks were rough. My neck and back pain were really bad—I had trouble sleeping and had to take painkillers regularly. It started improving after that, but I had to go through ten sessions of physiotherapy to help with the stiffness and discomfort.
Physician: That makes sense. Are you still experiencing pain now?
Patient: It’s not constant, but I do get occasional backaches. It’s nothing like before, though.
Physician: That’s good to hear. Have you noticed any other effects, like anxiety while driving or difficulty concentrating?
Patient: No, nothing like that. I don’t feel nervous driving, and I haven’t had any emotional issues from the accident.
Physician: And how has this impacted your daily life? Work, hobbies, anything like that?
Patient: I had to take a week off work, but after that, I was back to my usual routine. It hasn’t really stopped me from doing anything.
Physician: That’s encouraging. Let’s go ahead and do a physical examination to check your mobility and any lingering pain.
[Physical Examination Conducted]
Physician: Everything looks good. Your neck and back have a full range of movement, and there’s no tenderness or signs of lasting damage. Your muscles and spine seem to be in good condition.
Patient: That’s a relief!
Physician: Yes, your recovery so far has been quite positive. Given your progress, I’d expect you to make a full recovery within six months of the accident. There are no signs of long-term damage or degeneration.
Patient: That’s great to hear. So, I don’t need to worry about this affecting me in the future?
Physician: That’s right. I don’t foresee any long-term impact on your work or daily life. If anything changes or you experience worsening symptoms, you can always come back for a follow-up. But at this point, you’re on track for a full recovery.
Patient: Thank you, doctor. I appreciate it.
Physician: You’re very welcome, Ms. Jones. Take care, and don’t hesitate to reach out if you need anything.
"""

if __name__ == "__main__":
    notetaker = MedicalNoteTaker()
    task_a, task_b, task_c = notetaker.process_transcript(conversation_text)
    
    print("\n--- Task A: Medical Entity Extraction (JSON) ---")
    print(json.dumps(task_a, indent=4))
    
    print("\n--- Task B: Sentiment & Intent Analysis (JSON) ---")
    print(json.dumps(task_b, indent=4))
    
    print("\n--- Task C: SOAP Note Generation (JSON) ---")
    print(json.dumps(task_c, indent=4))
