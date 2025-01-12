import streamlit as st
from main import StudyBuddy  # Import from study_buddy.py
import google.generativeai as genai
import os
import uuid

user_pseudo_id = str(uuid.uuid4())
project_id = "united-impact-440612-m8"
engine_id = "study-buddy_1731147577608"
model = "gemini-1.5-pro"

# Initialize StudyBuddy (which internally initializes both TheoryAgent and CreativeAgent)
study_buddy = StudyBuddy(
    project_id=project_id,
    location="global",
    engine_id=engine_id,
    model_name=model,
    user_pseudo_id=user_pseudo_id
)

# Streamlit page configuration
st.set_page_config(page_title="Study Buddy AI", page_icon=":sunglasses:", layout="wide")
st.title("Study Buddy AI Chat")

# Initialize chat history if not already present in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your Study Buddy AI. How can I help you today?"}]
    st.session_state.last_answer = ""  # Track the last answer provided

# Function to display chat history
def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Display chat messages from history
display_chat_history()

# Accept user input
if prompt := st.chat_input("Ask me anything about study tips or math concepts:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare context by joining the previous messages
    context = "\n".join([message["content"] for message in st.session_state.messages])

    # Pass the query along with the entire context to the Creative Agent
    with st.spinner("Thinking..."):
        try:
            # Pass both the prompt and the context to the response function
            creative_response = study_buddy.get_study_buddy_response(f"{context}\n{prompt}")
        except Exception as e:
            creative_response = f"Error: {e}"

    # Display response from the Creative Agent
    with st.chat_message("assistant"):
        st.markdown(f"**Creative Agent:** {creative_response}")

    # Add the Creative Agent's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": creative_response})

    # Store the last answer for future context
    st.session_state.last_answer = creative_response