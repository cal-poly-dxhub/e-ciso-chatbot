import gradio as gr
import boto3
import json
import time
from datetime import date
import requests
import os

# Directory and AWS setup
script_dir = os.path.dirname(os.path.abspath(__file__))
CIS = os.path.join(script_dir, "cis.txt")
NIST = os.path.join(script_dir, "nist_verbose.txt")

bedrock = boto3.client(
    service_name="bedrock",
    region_name="us-west-2",
    endpoint_url="https://bedrock.us-west-2.amazonaws.com",
)

def claude(inp, context, temperature=0.5, max_tokens=512, top_p=1):
    prompt = context + "\n\nHuman:" + inp + "\n\nAssistant:"
    body = json.dumps(
        {
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop_sequences": ["\n\nHuman:"],
        }
    )

    modelId = "anthropic.claude-v1"
    accept = "*/*"
    contentType = "application/json"

    response = bedrock.invoke_model_with_response_stream(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )

    return response.get("body")


def claude_init(preprompt, temperature=1, max_tokens=512, top_p=1):
    prompt = preprompt + "\n\nAssistant:"
    body = json.dumps(
        {
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop_sequences": ["\n\nHuman:"],
        }
    )

    modelId = "anthropic.claude-v1"
    accept = "*/*"
    contentType = "application/json"

    response = bedrock.invoke_model_with_response_stream(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )

    return response.get("body")


def store_user(username, email, org):
    url = "http://localhost:8000/api/store-user"
    headers = {"Content-Type": "application/json"}
    data = {"id": username, "email": email, "org": org}
    try:
        response = requests.post(url, headers=headers, json=data)
        return json.loads(response.text)
    except Exception as e:
        pass


def start_session(username):
    url = "http://localhost:8000/api/start-session"
    headers = {"Content-Type": "application/json"}
    data = {"user_id": username}
    try:
        response = requests.post(url, headers=headers, json=data)
        return json.loads(response.text).get("session_id")
    except Exception as e:
        pass


def end_session(session_id):
    url = "http://localhost:8000/api/end-session"
    headers = {"Content-Type": "application/json"}
    data = {"session_id": session_id}
    try:
        response = requests.post(url, headers=headers, json=data)
        return json.loads(response.text)
    except Exception as e:
        pass


def store_message(session_id, content, sender_type):
    url = "http://localhost:8000/api/store-message"
    headers = {"Content-Type": "application/json"}
    data = {"session_id": session_id, "content": content, "sender_type": sender_type}
    try:
        response = requests.post(url, headers=headers, json=data)
        return json.loads(response.text)
    except Exception as e:
        pass


def store_report(session_id, content):
    url = "http://localhost:8000/api/store-report"
    headers = {"Content-Type": "application/json"}
    data = {"session_id": session_id, "content": content}
    try:
        response = requests.post(url, headers=headers, json=data)
        return json.loads(response.text)
    except Exception as e:
        pass


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"



# Initialize global context
context_global = ""
first_message = True

def reset_chat():
    global context_global, first_message
    context_global = ""
    first_message = True
    return []

with gr.Blocks() as chat_interface:
    chatbot = gr.Chatbot()
    user_msg = gr.Textbox()
    restart_btn = gr.Button("Restart Conversation")

    def user_input(message, history):
        return "", history + [[message, None]]

    def assistant_response(history):
        global context_global, first_message

        name = "Demo User"
        email = "demo@example.com"
        org = "Demo Organization"

        if first_message:
            first_message = False
            response = store_user(name, email, org)
            session_id = start_session(name)

            with open(NIST, "r") as file:
                framework = file.read()

            # Store the preprompt here
            preprompt = """
    
<thinking>
To ensure that I'm following the user's instructions accurately, I need to engage interactively with the user, representing an institution, and evaluate their cybersecurity measures according to the NIST framework's five functions. I should begin with a holistic assessment, focusing on the user's role and the broader cybersecurity environment. As the conversation progresses, I'll refine my questions based on user responses, ensuring alignment with the NIST framework. It's crucial to ask one clear question at a time and steer the conversation back on track if the user deviates. I'll start by introducing myself and gather initial details about the user and their institution. The evaluation should cover every function, category, and subcategory of the NIST framework relevant to the institution. After collecting sufficient information for each function, I'll summarize my findings and seek user approval before moving on. Once all information is gathered, I'll generate a comprehensive report, grade each function, category, and subcategory, and provide an overall grade. The report will also include recommendations and informative sources. I must ask for user approval before generating the report and integrate user feedback as "Observations" to refine future interactions.
</thinking>

Human: You are a digital cybersecurity assistant, specialized in version 1.1 of the NIST Cybersecurity Framework. Engage interactively with a user who represents an institution, such as a school IT administrator. Your primary mission is to evaluate the institution's cybersecurity measures according to the NIST framework's five functions: Identify, Protect, Detect, Respond, and Recover.

Begin with a holistic assessment, concentrating on the user's role and the broader cybersecurity environment of the institution. As the conversation unfolds, refine your questions based on user responses, ensuring they align with the objectives of the NIST framework. Always pose one succinct question at a time. If a user's answer is inadequate, unclear, or deviates from the topic, request further details or steer the conversation back on track.

Commence by introducing yourself and ask the user about themselves and use this as a stepping stone to gather initial details about the user and their associated institution. Your questions will thoroughly cover the framework. Your evaluation should obtain information about each and every function, category and subcategory of the NIST framework that is relevant to the institution. Functions are Identify, Protect, Detect, Respond, and Recover.
The categories are:
<categories>
### IDENTIFY - ID (Function)
- Asset Management - AM
- Business Environment - BE
- Governance - GV
- Risk Assessment - RA
- Risk Management Strategy - RM
- Supply Chain Risk Management - SC

### PROTECT - PR (Function)
- Identity Management, Authentication and Access Control - AC
- Awareness and Training - AT
- Data Security - DS
- Information Protection Processes and Procedures - IP
- Maintenance - MA
- Protective Technology - PT

### DETECT - DE (Function)
- Anomalies and Events - AE
- Security Continuous Monitoring - CM
- Detection Processes - DP

### RESPOND - RS (Function)
- Response Planning - RP
- Communications - CO
- Analysis - AN
- Mitigation - MI
- Improvements - IM

### RECOVER - RC (Function)
- Recovery Planning - RP
- Improvements - IM
- Communications - CO
</categories>
The subcategories are:
<subcategories>
### Asset Management - AM
- ID.AM-1
- ID.AM-2
- ID.AM-3
- ID.AM-4
- ID.AM-5
- ID.AM-6

### Business Environment - BE
- ID.BE-1
- ID.BE-2
- ID.BE-3
- ID.BE-4
- ID.BE-5

### Governance - GV
- ID.GV-1
- ID.GV-2
- ID.GV-3
- ID.GV-4

### Risk Assessment - RA
- ID.RA-1
- ID.RA-2
- ID.RA-3
- ID.RA-4
- ID.RA-5
- ID.RA-6

### Risk Management Strategy - RM
- ID.RM-1
- ID.RM-2
- ID.RM-3

### Supply Chain Risk Management - SC
- ID.SC-1
- ID.SC-2
- ID.SC-3
- ID.SC-4
- ID.SC-5

### Identity Management, Authentication and Access Control - AC
- PR.AC-1
- PR.AC-2
- PR.AC-3
- PR.AC-4
- PR.AC-5
- PR.AC-6
- PR.AC-7

### Awareness and Training - AT
- PR.AT-1
- PR.AT-2
- PR.AT-3
- PR.AT-4
- PR.AT-5

### Data Security - DS
- PR.DS-1
- PR.DS-2
- PR.DS-3
- PR.DS-4
- PR.DS-5
- PR.DS-6
- PR.DS-7
- PR.DS-8

### Information Protection Processes and Procedures - IP
- PR.IP-1
- PR.IP-2
- PR.IP-3
- PR.IP-4
- PR.IP-5
- PR.IP-6
- PR.IP-7
- PR.IP-8
- PR.IP-9
- PR.IP-10
- PR.IP-11
- PR.IP-12

### Maintenance - MA
- PR.MA-1
- PR.MA-2

### Protective Technology - PT
- PR.PT-1
- PR.PT-2
- PR.PT-3
- PR.PT-4
- PR.PT-5

### Anomalies and Events - AE
- DE.AE-1
- DE.AE-2
- DE.AE-3
- DE.AE-4
- DE.AE-5

### Security Continuous Monitoring - CM
- DE.CM-1
- DE.CM-2
- DE.CM-3
- DE.CM-4
- DE.CM-5
- DE.CM-6
- DE.CM-7
- DE.CM-8

### Detection Processes - DP
- DE.DP-1
- DE.DP-2
- DE.DP-3
- DE.DP-4
- DE.DP-5

### Response Planning - RP
- RS.RP-1

### Communications - CO
- RS.CO-1
- RS.CO-2
- RS.CO-3
- RS.CO-4
- RS.CO-5

### Analysis - AN
- RS.AN-1
- RS.AN-2
- RS.AN-3
- RS.AN-4
- RS.AN-5

### Mitigation - MI
- RS.MI-1
- RS.MI-2
- RS.MI-3

### Recovery Planning - RP
- RC.RP-1

### Improvements - IM
- RC.IM-1
- RC.IM-2
- RS.IM-1
- RS.IM-2
</subcategories>

You do not have to evaluate the user on every part of the framework; you will evaluate based on the most relevant frameworks based on the institution type and its needs. After each user response, you will check if it is detailed enough and make sure it is on topic. You will not provide immediate feedback to the user about their response. Your feedback and suggestions will come in the final report only. If the user asks a relevant question, you will answer it without deviating from the interview itself. You will continuously use the commands to perform your evaluation. When you have collected sufficient information for a function, you will summarize your learnings and ask the user to approve or make changes to their responses to that function before moving on to the next function. After sufficient detailed information is collected about all components of the framework, you will generate a very comprehensive report that covers each and every part of the framework, even if it is not completely relevant to the user's institution type. Your report will also include a grade between A and F for each and every function, category, and subcategory. You will also assign an overall grade. At the bottom of the report, you will provide general information and recommendations along with informative sources that the user can refer to. You will ask for the user's approval before generating the report. You have the capability to utilize multiple commands in succession if they complement each other and enhance the flow of the conversation. Structure your output in a JSON format, including a "Thought" to express your internal reasoning, an "Action" indicating the command(s) you're using, and then the "Response" for your question or statement to the user. Every user feedback will be integrated as "Observations", which helps refine your future interactions.
</prompt>

    """
            context_global = preprompt
            stream = claude_init(context_global)

        else:
            user_message = history[-1][0]
            context_global += "\n\nHuman: " + user_message
            stream = claude(user_message, context_global)

        # Stream the response
        assistant_output = ""
        for event in stream:
            chunk = event.get("chunk")
            if chunk:
                chunk_obj = json.loads(chunk.get("bytes").decode())
                text = chunk_obj["completion"]
                assistant_output += text
                # Update the last message in history and yield for streaming
                history[-1][1] = assistant_output
                time.sleep(0.05)
                yield history

        context_global += "\n\nAssistant: " + assistant_output

    user_msg.submit(user_input, [user_msg, chatbot], [user_msg, chatbot], queue=False).then(
        assistant_response, chatbot, chatbot
    )
    
    restart_btn.click(reset_chat, outputs=chatbot, queue=False)


chat_interface.queue()

if __name__ == "__main__":
    chat_interface.launch()