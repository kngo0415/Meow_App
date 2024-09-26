import streamlit as st
from typing import Generator
from groq import Groq
import re

st.set_page_config(page_icon="🦈", layout="wide", 
                page_title="Groq rok rok")

# Define valid usernames and passwords
VALID_CREDENTIALS = {
    "k_test": "MissMonday"
}

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

# Function to check if the entered credentials are valid
def check_credentials(username, password):
    if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password:
        return True
    return False

# Authentication State in session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# If the user is not authenticated, show the login form
if not st.session_state.authenticated:
    st.title("Login to Access Meow Configurator")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state.authenticated = True
            st.success("Login successful!")
        else:
            st.error("Invalid username or password.")

# If user is authenticated, show the app's main content
if st.session_state.authenticated:
    icon("🐈")

    col1, col2 = st.columns([8, 2])

    with col1:
        st.subheader("Welcome to the Private Meow Chatbot!")

    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False  # Log the user out by clearing session state
            st.info("You have been logged out.")

    st.divider()

    def icon(emoji: str):
        """Shows an emoji as a Notion-style page icon."""
        st.write(
            f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
            unsafe_allow_html=True,
        )

    st.subheader("Meow Configurator", divider="red", anchor=False)
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    
        # List available secret keys
        st.write("Available secret keys:", list(st.secrets.keys()))

        client = Groq(api_key=api_key)
    except KeyError:
        st.error("GROQ_API_KEY is not found in secrets.")

    # Initialize chat history and selected model
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "normal_response_mode" not in st.session_state:
        st.session_state.normal_response_mode = False

    selected_model = "mixtral-8x7b-32768"

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        avatar = '🐱' if message["role"] == "assistant" else '👨‍💻'
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    def generate_chat_responses(chat_completion, meow_mode=True) -> str:
        """Replace all words in the response with 'meow'."""
        # Assume the response from the API is a string we need to modify
        response_text = "".join([
            chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
            for chunk in chat_completion
        ])

        if meow_mode:
            # Replace every word in the response with 'meow'
            response_text = re.sub(r'\b\w+\b', 'meow', response_text)

        return response_text

    if prompt := st.chat_input("Enter your prompt here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar='👨‍💻'):
            st.markdown(prompt)

        # Check if "woof" is in the user prompt
        if "woof" in prompt.lower():
            st.session_state.normal_response_mode = True
            full_response = "Ah, you got me! How can I help you?"
        else:
            meow_mode = not st.session_state.normal_response_mode

            # Fetch response from Groq API
            try:
                chat_completion = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {
                            "role": m["role"],
                            "content": m["content"]
                        }
                        for m in st.session_state.messages
                    ],
                    max_tokens=32768,
                    stream=True
                )

                # Generate either a normal response or the meowed response
                full_response = generate_chat_responses(chat_completion, meow_mode=meow_mode)

            except Exception as e:
                st.error(e, icon="🚨")

        # Display and append the response
        with st.chat_message("assistant", avatar="🐱"):
            st.markdown(full_response )

        # Append the full response to session_state.messages
        st.session_state.messages.append({"role": "assistant", "content": full_response})

