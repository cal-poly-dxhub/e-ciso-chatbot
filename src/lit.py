import re
import streamlit as st
import json
import time
import boto3
from urllib3.exceptions import ProtocolError
import os
import requests
import base64
import subprocess

# Your Claude functions and other necessary functions...
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "new_prompt.txt")

with open(file_path, "r") as f:
    PREPROMPT = f.read()

session = boto3.session.Session()
s3 = session.client("s3", "us-west-2")


def extract_response(text):
    # Extract content between <Response> and </Response> tags
    response_contents = []
    start_idx = text.find("<Response>")
    while start_idx != -1:
        end_idx = text.find("</Response>", start_idx)
        if end_idx == -1:
            break
        response_contents.append(text[start_idx + 10 : end_idx])
        start_idx = text.find("<Response>", end_idx)

    # Extract content not enclosed in any XML tags only if no <Response> content found
    if not response_contents:
        outside_xml_content = []
        prev_end_idx = 0
        while prev_end_idx < len(text):
            start_idx = text.find("<", prev_end_idx)
            if start_idx == -1:
                outside_xml_content.append(text[prev_end_idx:].strip())
                break
            elif start_idx > prev_end_idx:
                outside_xml_content.append(text[prev_end_idx:start_idx].strip())
            end_idx = text.find(">", start_idx)
            prev_end_idx = end_idx + 1
        response_contents = outside_xml_content

    # Combine extracted content
    combined_content = "\n".join(response_contents).strip()
    return combined_content


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


bedrock = boto3.client(
    service_name="bedrock",
    region_name="us-west-2",
    endpoint_url="https://bedrock.us-west-2.amazonaws.com",
)


def claude(inp, context, temperature=0, max_tokens=512, top_p=0):
    prompt = "\n\nHuman:" + context + inp + "\n\nAssistant:"
    body = json.dumps(
        {
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop_sequences": ["\n\nHuman:"],
        }
    )

    modelId = "anthropic.claude-v2"
    accept = "*/*"
    contentType = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )

    return response


def generate_report(context):
    # Create the new prompt for report generation
    prompt = """
        Based on the above conversation detailing the evaluation of the cybersecurity posture of an institution using the NIST (National Institute of Standards and Technology) Cybersecurity Framework, generate a comprehensive report. The conversation provides information on various aspects of the institution's cybersecurity practices. The report should be formatted using Markdown and should include:

Introduction: A brief overview of the cybersecurity evaluation and the relevance of the NIST framework to the institution.
Evaluation based on NIST Framework:
Identify:
Asset Management: Evaluation of how the institution identifies and manages its cyber-related assets.
Business Environment: Assessment of the institution's understanding of its business context and cybersecurity role.
Governance: Analysis of the institution's policies and procedures in relation to cybersecurity.
Risk Assessment: How the institution assesses cybersecurity risks.
Risk Management Strategy: Review of how the institution manages cybersecurity risks.
Identify Grade: [Based on conversation, grade from A to F]
Protect:
Access Control: Evaluation of controls that limit access to critical information and systems.
Training and Awareness: Analysis of the institution's cybersecurity training programs.
Data Security: Review of how data is protected both in transit and at rest.
Maintenance: Evaluation of system and software maintenance practices.
Protective Technology: Assessment of technological solutions employed for cybersecurity.
Protect Grade: [Based on conversation, grade from A to F]
Detect:
Anomalies and Events: How the institution detects unusual and potentially harmful activities.
Monitoring: Assessment of continuous monitoring capabilities.
Detection Processes: Analysis of processes that assist in the detection of cybersecurity events.
Detect Grade: [Based on conversation, grade from A to F]
Respond:
Response Planning: Evaluation of plans in place for cybersecurity incidents.
Mitigation: How the institution works to minimize the impact of cybersecurity incidents.
Improvements: Assessment of processes to improve response capabilities after an event.
Respond Grade: [Based on conversation, grade from A to F]
Recover:
Recovery Planning: Evaluation of the institution's recovery plans post-cybersecurity incident.
Improvements: Analysis of post-event recovery improvements and lessons learned.
Communication: How the institution communicates recovery processes internally and externally.
Recover Grade: [Based on conversation, grade from A to F]
Grading Criteria:
A: Excellent practices, meets or exceeds all best standards.
B: Above average, meets most standards but has minor areas of improvement.
C: Average, meets baseline standards but has significant areas for improvement.
D: Below average, fails to meet many standards and requires considerable improvement.
F: Poor, does not meet minimum standards and requires immediate action.
Overall Grade: [Based on conversation, grade from A to F]
Suggestions/Recommendations: A list of actionable insights based on the weaknesses identified during the evaluation.
Generate the report.
        """
    response = claude(prompt, context, temperature=0.5, max_tokens=8000)
    assistant_output = ""
    try:
        assistant_output = json.loads(response.get('body').read()).get('completion')
    except ProtocolError as e:
        return "Error generating report: " + str(e)
    return assistant_output

  
def main():
    # Set the title
    st.set_page_config(page_title="MyeCISO", page_icon=":globe_with_meridians:")
    st.title("My eCISO.")
    st.image("/home/ec2-user/eciso-poc/src/dxlogo.png")

    if "details_collected" not in st.session_state:
        st.session_state.details_collected = False
    if "disclaimer_accepted" not in st.session_state:
        st.session_state.disclaimer_accepted = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    if "context" not in st.session_state:
        st.session_state.context = PREPROMPT
        st.session_state.first_time = True

    form_placeholder = st.empty()
    disclaimer_placeholder = st.empty()
    disclaimer_checkbox_placeholder = st.empty()

    if not st.session_state.details_collected:
        with form_placeholder.form("my_form"):
            username = st.text_input("Username: ")
            email = st.text_input("Email: ")
            org = st.text_input("Organization: ")

            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.username = username
                st.session_state.email = email
                st.session_state.org = org

                # Store the user
                response = store_user(
                    st.session_state.username,
                    st.session_state.email,
                    st.session_state.org,
                )
                # Start the session with the username

                st.session_state.id = start_session(st.session_state.username)
                st.session_state.details_collected = True

                form_placeholder.empty()

    if not st.session_state.disclaimer_accepted and st.session_state.details_collected:
        with disclaimer_placeholder:
            st.warning(
                "DISCLAIMER: MyCISO strives to provide accurate information on cyberecurity frameworks however this application provides content that is educational and for informational purposes only. It is recommended that you conduct additional research and verify the accuracy of this infromation via trusted sources and additional review by cybersecurity experts."
            )

        with disclaimer_checkbox_placeholder:
            if st.checkbox("I accept the terms and conditions."):
                st.session_state.disclaimer_accepted = True

                disclaimer_checkbox_placeholder.empty()
                disclaimer_placeholder.empty()

    if st.session_state.disclaimer_accepted:
        if st.session_state.first_time:
            # Immediately fetch Claude's response to the preprompt and display it.
            current_chunk = ""
            response_content = ""
            inside_response = False
            stream = claude(
                "", st.session_state.context
            )  # Empty user input to start with pre-prompt.
            assistant_output = []

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    if stream:
                        full_response = json.loads(stream.get('body').read()).get('completion')
                        # for event in stream:
                        #     chunk = event.get("chunk")
                        #     if chunk:
                        #         chunk_obj = json.loads(chunk.get("bytes").decode())
                        #         text = chunk_obj["completion"]
                        #         full_response += text
                                # Append the new chunk to the current_chunk string

                            # # If we detect the start of the <Response> tag, set the flag
                            # if "<Response>" in current_chunk:
                            #     inside_response = True
                            #     current_chunk = current_chunk.split("<Response>", 1)[1]  # Remove the <Response> tag from current_chunk

                            # # If we are inside the response, accumulate the content
                            # if inside_response:
                            #     response_content += current_chunk
                            #     current_chunk = ""  # Reset the current_chunk

                            # # If we detect the end of the </Response> tag, clear the flag and display the content
                            # if "</Response>" in response_content:
                            #     response_content, _ = response_content.split("</Response>", 1)  # Split at the first occurrence of the </Response> tag
                            #     inside_response = False
                        response_content = extract_response(full_response)
                        if response_content:
                            st.markdown(response_content)

                            # Store the assistant's response
                            response = store_message(
                                st.session_state.id,
                                full_response,
                                sender_type="Assistant",
                            )

                            # Add assistant response to chat history and context
                            st.session_state.display_messages.append(
                                {"role": "assistant", "content": response_content}
                            )
                            st.session_state.messages.append(
                                {"role": "assistant", "content": full_response}
                            )
                            st.session_state.context += (
                                "\n\nAssistant: " + response_content
                            )

                            # Reset response_content for any subsequent responses
                            response_content = ""

                except ProtocolError as e:
                    st.write("Sorry I'm too tired to continue :(")

            # Add assistant response to chat history.
            st.session_state.messages.append(
                {"role": "assistant", "content": "".join(assistant_output)}
            )
            # Add to context
            st.session_state.context += "\n\nAssistant: " + "".join(assistant_output)

            # Set first_time to False after displaying Claude's initial response
            st.session_state.first_time = False

            response = store_message(
                st.session_state.id, assistant_output, sender_type="Assistant"
            )

        # User input
        user_input = st.chat_input("Type your message...")
        if user_input:
            response = store_message(
                st.session_state.id, user_input, sender_type="Human"
            )
            st.session_state.display_messages.append(
                {"role": "user", "content": user_input}
            )
            st.session_state.messages.append({"role": "user", "content": user_input})

            for message in st.session_state.display_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            current_chunk = ""
            response_content = ""
            full_response = ""
            inside_response = False
            # Get Chatbot response
            stream = claude(user_input, st.session_state.context)
            try:
                if stream:
                    full_response = json.loads(stream.get('body').read()).get('completion')
                    # for event in stream:
                    #     chunk = event.get("chunk")
                    #     if chunk:
                    #         chunk_obj = json.loads(chunk.get("bytes").decode())
                    #         text = chunk_obj["completion"]
                    #         full_response += text

                    # Applying the refined extraction logic
                    response_content = extract_response(full_response)

                    if response_content:
                        with st.chat_message("assistant"):
                            st.markdown(response_content)

                        # Store the assistant's response
                        response = store_message(
                            st.session_state.id,
                            full_response,
                            sender_type="Assistant",
                        )

                        # Add assistant response to chat history and context
                        st.session_state.display_messages.append(
                            {"role": "assistant", "content": response_content}
                        )
                        st.session_state.messages.append(
                            {"role": "assistant", "content": full_response}
                        )
                        st.session_state.context += (
                            "\n\nHuman: "
                            + user_input
                            + "\n\nAssistant: "
                            + response_content
                        )

            except ProtocolError as e:
                st.write("Sorry I'm too tired to continue :(")

        # Generate Report button
        if st.sidebar.button("Generate Report"):
            report_placeholder = st.empty()
            with st.chat_message("assistant"):
                st.markdown("Generating report...")
            report = generate_report(st.session_state.context)
            response = store_report(st.session_state.id, report)
            # response = store_report(st.session_state.id, report)
            response = end_session(st.session_state.id)
            # report_bytes = report.encode("utf-8")
            bucket_name = "eciso-temp"
            with open("temp.md", "w") as file:
                file.write(report)

            output_pdf_path = f"report-{st.session_state.id}.pdf"
            result = subprocess.run(["mdpdf", "temp.md", "--output", output_pdf_path])

            if result.returncode == 0:
                with open(output_pdf_path, "rb") as file:
                    s3.put_object(
                        Bucket=bucket_name,
                        Key=output_pdf_path,
                        Body=file,
                        ContentType="application/pdf",
                    )
                # s3.put_object(
                #     Bucket=bucket_name,
                #     Key=f"report-{st.session_state.id}.txt",
                #     Body=report_bytes,
                # )

                expiration_time = 3600
                presigned_url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": bucket_name,
                        "Key": f"report-{st.session_state.id}.pdf",
                    },
                    ExpiresIn=expiration_time,
                )

                os.remove("temp.md")
                os.remove(output_pdf_path)

                with st.chat_message("assistant"):
                    st.markdown(
                        f"Download the report at [https://eciso-temp.s3.amazonaws.com/report-{st.session_state.id}.pdf]({presigned_url})\n\nPlease submit feedback at https://forms.gle/MHayovD4D9xycMU39. Use the session ID {st.session_state.id} in the form."
                    )
            else:
                st.error("Failed to generate report. Please try again.")
                st.markdown(f"This is the report that was generated: \n\n {report}")


if __name__ == "__main__":
    main()
