import streamlit as st  
import openai
import os
from typing import Tuple
from datetime import datetime, timedelta
# from validate import validate_input
from prompts import SYSTEM_PROMPT

def check_rate_limit() -> Tuple[bool, str]:
    if 'rate_limit' not in st.session_state:
        st.session_state.rate_limit = {'count': 0, 'reset_time': datetime.now() + timedelta(minutes=10)}
    
    if datetime.now() > st.session_state.rate_limit['reset_time']:
        st.session_state.rate_limit = {'count': 0, 'reset_time': datetime.now() + timedelta(minutes=10)}
        return True, None

    if st.session_state.rate_limit['count'] >= 20:
        time_left = (st.session_state.rate_limit['reset_time'] - datetime.now()).seconds // 60
        return False, time_left
    
    st.session_state.rate_limit['count'] += 1
    
    return True, None

# Set up OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = api_key

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="Mock Interview with AI", page_icon="🤖")
st.title("Practice Job Interviews with AI")
st.text("This app allows you to practice job interview questions with an AI interviewer. Simply enter your name, job role you are applying and AI interviewer style to get started.")
st.text("**NOTE**: Do not share any personal identifiable information (PII) such as your full name, address, phone number, or any sensitive data during the interview.")
st.text("Streamlit does not support guardrails validation at the moment, so please be cautious.")

# User input: Name and job role
user_name = st.text_input("Enter your name:")
job_role = st.text_input("Enter the job role you are applying for:")
system_prompt = st.selectbox("Select System Prompts", ["Zero-Shot", "Few-Shot", "Chain-of-Thought", "Least-to-Most", "Generated Knowledge"])

# Start the interview process
if st.button("(Re-)Start Interview"):
    if not user_name or not job_role:
        st.error("Please enter both your name and the job role.")
    else:
        # name_valid, name_error = validate_input(user_name)
        # role_valid, role_error = validate_input(job_role)
        # if not name_valid or not role_valid:
        #     st.error(f"Guardrail violation: {name_error} {role_error}")
        #     st.stop()

        # Set session state for interview
        st.session_state.system_prompt = system_prompt
        st.session_state.user_name = user_name
        st.session_state.job_role = job_role
        st.session_state.openai_model = "gpt-4.1-nano-2025-04-14"
        # Initialize messages with proper format for OpenAI API
        system_message = SYSTEM_PROMPT[system_prompt.lower().replace(" ", "-")](job_role, user_name)
        initial_user_message = f"Hello, my name is {user_name}, and I want to practice mock interview for {job_role}. Let's get started!"
        
        # Store messages in two formats: one for OpenAI API, one for display
        st.session_state.api_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": initial_user_message}
        ]
        st.session_state.display_messages = []

        # Send initial messages to OpenAI for a response
        response = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=st.session_state.api_messages,
            temperature=0.4,
            max_completion_tokens=200
        )

        ai_message = response.choices[0].message.content
        st.session_state.api_messages.append({"role": "assistant", "content": ai_message})
        st.session_state.display_messages.append({"role": "assistant", "content": ai_message})

        # Display the assistant's message
        st.chat_message("assistant").markdown(ai_message)

        # Trigger rerun after response
        st.rerun()

# Display the conversation so far
if 'display_messages' in st.session_state:
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message['content'])

# User input for new answer
if 'user_name' in st.session_state:
    prompt = st.chat_input(
        f"{st.session_state.get('user_name', 'User')}, please enter your answer here:", 
        key="user_input",
        accept_file="multiple"
    )

    # Process the user input
    if prompt:
        # Extract text content
        time_valid, time_left = check_rate_limit()
        if not time_valid:
            st.warning(f"Rate limit exceeded. Please wait {time_left} minutes before trying again.")
            st.info(f"Your rate limit will reset at {st.session_state.rate_limit['reset_time'].strftime('%H:%M:%S')}.")
        # is_valid, error_message = validate_input(prompt.text if hasattr(prompt, 'text') else str(prompt))
        # if not is_valid:
        #     st.error(f"Guardrail violation: {error_message}")
        visible_content = ""
        api_content = ""
        
        # Check if prompt is a ChatInputResult object with text and files
        if hasattr(prompt, 'text'):
            visible_content = prompt.text if prompt.text else ""
            api_content = prompt.text if prompt.text else ""
        else:
            # If it's just a string (backward compatibility)
            visible_content = str(prompt)
            api_content = str(prompt)
        
        # Process uploaded files if any
        if hasattr(prompt, 'files') and prompt.files:
            file_summaries = []
            for file in prompt.files:
                try:
                    # Read file content
                    file_content = file.read().decode("utf-8")
                    # Add to API content (internal processing)
                    api_content += f"\n\n--- File: {file.name} ---\n{file_content}"
                    # Add summary for display
                    file_summaries.append(f"📎 {file.name}")
                except Exception as e:
                    st.error(f"Error reading file {file.name}: {str(e)}")
            
            # Add file info to visible content
            if file_summaries:
                visible_content += "\n\n" + "\n".join(file_summaries)
        
        # Only proceed if there's actual content
        if visible_content.strip() or api_content.strip():
            # Append to both message lists
            st.session_state.api_messages.append({"role": "user", "content": api_content})
            st.session_state.display_messages.append({"role": "user", "content": visible_content})

            # Display the user message
            with st.chat_message("user"):
                st.markdown(visible_content)

        # Generate the assistant's response
        with st.chat_message('assistant'):
            message_placeholder = st.empty()
            full_response = ""

            stream = client.chat.completions.create(
                model=st.session_state['openai_model'],
                messages=st.session_state.api_messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            # Show the full response
            message_placeholder.markdown(full_response)

        # Append the assistant's response to both lists
        st.session_state.api_messages.append({"role": "assistant", "content": full_response})
        st.session_state.display_messages.append({"role": "assistant", "content": full_response})

        # Trigger rerun to update the UI
        st.rerun()