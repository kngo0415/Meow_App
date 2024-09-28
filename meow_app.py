import streamlit as st
from typing import Generator
from groq import Groq
import re
import os
import toml

st.set_page_config(page_icon="😻", layout="wide", page_title="CatGPT")

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

TESTING_MODE = False

VALID_CREDENTIALS = {
    "k": "123"
}

def check_credentials(username, password):
    if TESTING_MODE:
        return username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password
    else:
        try:
            cloud_username = st.secrets["username"]
            cloud_password = st.secrets["password"]
            return username == cloud_username and password == cloud_password
        except KeyError:
            st.error("Missing username or password in secrets.")
            return False

def get_groq_client():
    try:
        if TESTING_MODE:
            return Groq(api_key="meow meow meow meow meow meow meow")
        else:
            return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except KeyError:
        st.error("GROQ_API_KEY is not found in secrets.")
        st.stop()  # Stop execution if API key is missing

def login_page():
    icon("🐈")
    st.title("Login to CatGPT")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state['logged_in'] = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def main_page():
    icon("🐈")

    col1, col2 = st.columns([8, 2])

    with col1:
        st.subheader("ONLY MEOW")

    with col2:
        if st.button("Logout"):
            st.session_state['logged_in'] = False  # Log the user out by clearing session state
            st.info("You have been logged out.")
            st.rerun()

    st.markdown("---")

    st.subheader("CatGPT", divider="red", anchor=False)

    client = get_groq_client()

    # Initialize chat history and selected model
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "normal_response_mode" not in st.session_state:
        st.session_state.normal_response_mode = False

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # Define AI models:
    models = {
        "gemma-7b-it": {"name": "Gemma-7b-it", "tokens": 8192, "developer": "Google"},
        "llama2-70b-4096": {"name": "LLaMA2-70b-chat", "tokens": 4096, "developer": "Meta"},
        "llama3-70b-8192": {"name": "LLaMA3-70b-8192", "tokens": 8192, "developer": "Meta"},
        "llama3-8b-8192": {"name": "LLaMA3-8b-8192", "tokens": 8192, "developer": "Meta"},
        "mixtral-8x7b-32768": {"name": "Mixtral-8x7b-Instruct-v0.1", "tokens": 32768, "developer": "Mistral"},
    }

    # selected_model = "mixtral-8x7b-32768"

    model_option = st.selectbox(
        "Choose a model:",
        options=list(models.keys()),
        format_func=lambda x: models[x]["name"],
        index=4  # Default to mixtral
    )

    # Detect model change and clear chat history if model has changed
    if st.session_state.selected_model != model_option:
        st.session_state.messages = []
        st.session_state.selected_model = model_option

    max_tokens_range = models[model_option]["tokens"]

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

    if prompt := st.chat_input("Let talk right meow!..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar='😸'):
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
                    model=model_option,
                    messages=[
                        {
                            "role": m["role"],
                            "content": m["content"]
                        }
                        for m in st.session_state.messages
                    ],
                    max_tokens=max_tokens_range,
                    stream=True
                )

                # Generate either a normal response or the meowed response
                full_response = generate_chat_responses(chat_completion, meow_mode=meow_mode)
            except Exception as e:
                # Check if the error is a model-not-found error
                if 'model_not_found' in str(e):
                    st.error(f"Model {model_option} not found. Using default model: Mixtral.")
                    # Fallback to Mixtral if the selected model is unavailable
                    st.session_state.selected_model = "mixtral-8x7b-32768"
                    chat_completion = client.chat.completions.create(
                        model=st.session_state.selected_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        max_tokens=models["mixtral-8x7b-32768"]["tokens"],
                        stream=True
                    )
                    full_response = generate_chat_responses(chat_completion, meow_mode=meow_mode)
                else:
                    st.error(e, icon="🚨")

        # Display and append the response
        with st.chat_message("assistant", avatar="🐱"):
            st.markdown(full_response )

        # Append the full response to session_state.messages
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def main():
    if not TESTING_MODE and ("credentials" not in st.secrets or "GROQ_API_KEY" not in st.secrets):
        st.error("Credentials or API key missing from secrets.")
        st.stop()
    
    if TESTING_MODE:
        # Bypass login page for testing
        st.session_state['logged_in'] = True
        main_page()
    else:
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
        if st.session_state['logged_in']:
            main_page()
        else:
            login_page()

if __name__ == "__main__":
    main()