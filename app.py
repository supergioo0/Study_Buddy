# app.py
import streamlit as st
from main import StudyBuddy  # Import from study_buddy.py

# Initialize StudyBuddy (which internally initializes both TheoryAgent and CreativeAgent)
study_buddy = StudyBuddy(project_id=st.secrets['PROJECT_ID'], location="global", engine_id=st.secrets['ENGINE_ID'], model_name=st.secrets['MODEL_NAME'])

# Streamlit page configuration
st.set_page_config(page_title="Study Buddy AI", page_icon=":sunglasses:", layout="wide")
st.title("Study Buddy AI Chat")
