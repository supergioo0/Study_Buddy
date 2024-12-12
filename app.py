import streamlit as st
from main import StudyBuddy  # Import from study_buddy.py
import os

# Get environment variables for API configuration
project_id = os.getenv('PROJECT_ID')
engine_id = os.getenv('ENGINE_ID')

# Initialize StudyBuddy (which internally initializes both TheoryAgent and CreativeAgent)
study_buddy = StudyBuddy(project_id=project_id, location="global", engine_id=engine_id, model_name="gemini-1.5-flash") #Problem while importing study_buddy

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

    # Pass the query along with chat history to the Creative Agent
    with st.spinner("Thinking..."):
        try:
            # Response from the Creative Agent
            creative_response = study_buddy.get_study_buddy_response(prompt)  # Pass the prompt to the Creative Agent
        except Exception as e:
            creative_response = f"Error: {e}"

    # Display response from the Creative Agent
    with st.chat_message("assistant"):
        st.markdown(f"**Creative Agent:** {creative_response}")

    # Add the Creative Agent's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": creative_response})

    # Store the last answer for future context
    st.session_state.last_answer = creative_response