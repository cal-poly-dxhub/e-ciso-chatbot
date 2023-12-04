import sys
#Imports and installations
import boto3
from urllib.parse import urlparse
import re
import unicodedata
import math
import json
import time
import asyncio
import streamlit as st
s3 = boto3.client('s3')
bedrock = boto3.client(service_name='bedrock',region_name='us-west-2',endpoint_url='https://bedrock.us-west-2.amazonaws.com')
    


def claude(inp, context, temperature=1, max_tokens=4000, top_p=1):
    prompt = context + "\n\nHuman:" + inp + "\n\nAssistant:"
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stop_sequences": ["\n\nHuman:"]
    })

    modelId = "anthropic.claude-v1"
    accept = "*/*"
    contentType = "application/json"

    response = bedrock.invoke_model_with_response_stream(body=body, modelId=modelId, accept=accept, contentType=contentType)
    
    return response.get('body')

def simulate_chat(persona1, persona2, conversation_length):
    # Starting context for the two personas
    # context1 = f"Human: Act as {persona1} and answer based on that. Start with Hi my name is ....\n\nAssistant:"
    # context2 = f"Human: Act as {persona2} and answer based on that. Start with  Hello, my name is ... \n\nAssistant:"
    context1 = f"Human: {persona1}\n\nAssistant:"
    context2 = f"Human: {persona2} \n\nAssistant:"
    
    # Start the conversation with the introduction from persona1
    stream1 = claude(context1, "")
    response1 = stream_and_extract_response(stream1, persona1)
    
    # context1 = ""
    # Update the context for persona1 with its response
    context1 += "\n\n" + response1 + "\n\nHuman:"
    
    # Now get the introduction from persona2
    stream2 = claude(context2, "")
    response2 = stream_and_extract_response(stream2, persona2)
    
    # context2 = ""
    # Update the context for persona2 with its response and persona1's response
    context2 += "\n\n" + response2 + "\n\nHuman:" + response1 + "\n\nAssistant:"

    # Initialize with the response of persona2
    last_response = response2

    # Alternate messages between the two personas
    for i in range(2, conversation_length):
        if i % 2 == 0:  # even, persona1's turn
            stream = claude(context1 + last_response, "")
            response = stream_and_extract_response(stream, persona1)
            
            # Update the context for persona1
            context1 += response + "\n\nHuman:"
            
            # Update the context for persona2 with persona1's new response
            context2 += "\n\nHuman:" + response + "\n\nAssistant:"
        else:  # odd, persona2's turn
            stream = claude(context2, "")
            response = stream_and_extract_response(stream, persona2)
            
            # Update the context for persona2
            context2 += response + "\n\nHuman:"
            
            # Update the context for persona1 with persona2's new response
            context1 += "\n\nHuman:" + response + "\n\nAssistant:"
        
        last_response = response


# Helper function to stream the entire response and display in real-time
def stream_and_extract_response(stream, persona):
    full_response = ""
    with st.chat_message(persona):
        message_placeholder = st.empty()

        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_obj = json.loads(chunk.get('bytes').decode())
                    text = chunk_obj['completion']

                    # Simulate stream of response with milliseconds delay and preserve new line characters
                    for char in text:
                        full_response += char
                        time.sleep(0.015)

                        # Add a blinking cursor to simulate typing and replace new line characters with <br> for markdown rendering
                        message_placeholder.markdown(full_response.replace('\n', '<br>') + "▌", unsafe_allow_html=True)

                    message_placeholder.markdown(full_response[:-1].replace('\n', '<br>'), unsafe_allow_html=True)
    return full_response



def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Initialize context in session_state
    if "context" not in st.session_state:
        st.session_state.context = ""

    # Sidebar for hyperparameters
    st.sidebar.title("Hyperparameters")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.01)
    max_tokens = st.sidebar.slider("Max Tokens", 50, 4000, 4000, 50)
    top_p = st.sidebar.slider("Top P", 0.0, 1.0, 1.0, 0.01)
    explicit = st.sidebar.checkbox("Explicit")
    
#     # UI Components for Simulating Conversation
    st.sidebar.subheader("Simulate Conversation")
    persona1 = st.sidebar.text_area("Enter Persona 1 (e.g., Nikola Tesla):")
    persona2 = st.sidebar.text_area("Enter Persona 2 (e.g., Thomas Edison):")
    conversation_length = st.sidebar.slider("Set Conversation Length", 2, 50, 10)

    # Check if both personas are set and the start button is pressed
    if st.sidebar.button("Start Simulation"):
        if persona1 and persona2:
            # Placeholder for future logic to initiate the conversation simulation
            st.sidebar.success("Starting conversation between {} and {}.".format(persona1, persona2))

            simulate_chat(persona1, persona2, conversation_length)

            st.sidebar.success("Simulation completed!")

        else:
            st.sidebar.warning("Please set both personas before starting the simulation.")

if __name__ == "__main__":
    main()