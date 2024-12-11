# app.py
import streamlit as st
from main import StudyBuddy
import os

# Initialize StudyBuddy (which internally initializes both TheoryAgent and CreativeAgent)
study_buddy = StudyBuddy(project_id="united-impact-440612-m8", location="global", engine_id="study-buddy_1731147577608", model_name='gemini-1.5-pro')

# Streamlit page configuration
st.set_page_config(page_title="Study Buddy AI", page_icon=":sunglasses:", layout="wide")
st.title("Study Buddy AI Chat")
