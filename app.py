import streamlit as st
import json
import time
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Physician Notetaker AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Real Backend Integration ---
from physician_notetaker import MedicalNoteTaker

# --- UI Layout ---

# Sidebar
with st.sidebar:
    st.title("Settings")
    
    # Internal Hardcoded Key (Hidden from UI)
    # Using python-dotenv to load from .env file to prevent GitHub Secret Scanning errors
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    show_debug = st.checkbox("Show Raw Debug Data", value=False)
    
    st.markdown("---")
    st.header("About")
    st.info(
        """
        **Physician Notetaker AI** uses **Groq Llama 3** to process doctor-patient conversations with high accuracy.
        
        **Features:**
        - High-Speed Inference
        - Clinical Summarization
        - SOAP Note Generation
        """
    )
    st.caption("v2.1.0 | Powered by Groq")

# Initialize Backend with API Key
if "notetaker" not in st.session_state or st.session_state.get("api_key") != groq_api_key:
    if groq_api_key:
        st.session_state["notetaker"] = MedicalNoteTaker(api_key=groq_api_key)
        st.session_state["api_key"] = groq_api_key
    else:
        st.session_state["notetaker"] = None

# Main Page
st.title("🩺 Physician Notetaker AI")
st.markdown("Automated clinical documentation and entity extraction.")

# Default Text
default_text = """
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
""".strip()

# Input Area
st.subheader("Conversation Transcript")
transcript_input = st.text_area("Paste the doctor-patient dialogue here:", value=default_text, height=300)

if st.button("Analyze Conversation", type="primary"):
    if not transcript_input:
        st.warning("Please enter a conversation transcript.")
    else:
        with st.spinner("Analyzing with Groq Llama 3..."):
            
            # Real Backend Call
            summary_data, sentiment_data, soap_data = st.session_state["notetaker"].process_transcript(transcript_input)
        
        st.success("Analysis Complete!")

        
        # --- Results Tabs ---
        tab1, tab2, tab3 = st.tabs(["📋 Medical Summary", "😊 Sentiment Analysis", "📝 SOAP Note"])
        
        with tab1:
            st.markdown("### Structural Findings")
            # Using columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Patient Identification**")
                st.info(f"Name: {summary_data.get('Patient_Name', 'Unknown')}")
                
                st.markdown("**Diagnosis**")
                for d in summary_data.get("Diagnosis", []):
                    st.warning(f"• {d}")
                    
                st.markdown("**Symptoms**")
                for s in summary_data.get("Symptoms", []):
                    st.error(f"• {s}")

            with col2:
                st.markdown("**Treatment Plan**")
                for t in summary_data.get("Treatment", []):
                    st.success(f"• {t}")
                    
                st.markdown("**Prognosis**")
                st.caption(summary_data.get("Prognosis"))

            if show_debug:
                st.json(summary_data)
                
            # Download Button
            st.download_button(
                label="Download Summary JSON",
                data=json.dumps(summary_data, indent=4),
                file_name="medical_summary.json",
                mime="application/json"
            )

        with tab2:
            st.markdown("### Patient State Analysis")
            
            sent = sentiment_data.get("Sentiment", "Neutral")
            intent = sentiment_data.get("Intent", "Unknown")
            
            # Dynamic coloring logic
            if "Reassured" in sent or "Positive" in sent:
                metric_color = "normal" 
            elif "Anxious" in sent or "Concerned" in sent:
                metric_color = "off" # Streamlit metric doesn't strictly support color kwarg in all themes, using delta_color
            
            c1, c2 = st.columns(2)
            c1.metric("Detected Sentiment", sent)
            c2.metric("Visit Intent", intent)
            
            if show_debug:
                st.json(sentiment_data)

        with tab3:
            st.markdown("### Generated SOAP Note")
            
            # Safety Check
            if not soap_data or "Subjective" not in soap_data:
                st.error("Error: Could not generate SOAP note. Please try again or check debug data.")
            else:
                soap_markdown = f"""
                **SUBJECTIVE**  
                {soap_data.get('Subjective', 'N/A')}
                
                **OBJECTIVE**  
                {soap_data.get('Objective', 'N/A')}
                
                **ASSESSMENT**  
                {soap_data.get('Assessment', 'N/A')}
                
                **PLAN**  
                {soap_data.get('Plan', 'N/A')}
                """
                
                st.markdown(soap_markdown)
                
                st.divider()
                
                # Download Button with Timestamp
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Download SOAP Note JSON",
                    data=json.dumps(soap_data, indent=4),
                    file_name=f"soap_note_{ts}.json",
                    mime="application/json"
                )
            
            if show_debug:
                st.json(soap_data)
