# My eCiso Chatbot

## Overview
My eCiso is an innovative chatbot designed to conduct comprehensive interviews about the cybersecurity posture of public sector organizations, particularly focusing on IT personnel from public schools. It leverages the widely recognized NIST framework to evaluate and provide personalized suggestions for enhancing cyber resilience. The public version is available at [myeciso.calpoly.io](http://myeciso.calpoly.io).

## Key Features
- **Dynamic Interviewing**: Tailored conversation lasting 30 minutes to 2 hours, depending on the user's background and organization type.
- **Personalized Experience**: Adapts the complexity of questions based on the user's cybersecurity knowledge.
- **Report Generation**: Provides a detailed PDF report with actionable steps for improving cybersecurity.
- **LLM Integration**: Utilizes ClaudeV2 from Anthropic AI for a conversational and personalized experience.

## Technologies
- **Programming Language**: Python
- **Framework**: Streamlit
- **Cloud Services**: AWS (including Bedrock, DynamoDB, S3)
- **Database**: DynamoDB
- **LLM API**: AWS Bedrock

## Installation and Setup
1. Install Bedrock wheels.
2. Clone the repository.
3. Run `sh setup.sh` and `sh streamlit_run.sh` from the scripts directory.
4. Access the chatbot via the localhost endpoint configured.

## Usage
- Users are encouraged to interact thoroughly and honestly with My eCiso.
- For a tailored conversation, users can request specific topics or a particular approach to the interview.
- Generate a detailed report at the end of the conversation by clicking the "Generate Report" button.

## Customization
- My eCiso primarily uses the Claude v2 model, but it's flexible to accommodate other LLMs.
- To switch models, modify the `claude.py` function in the main file.

## Contributing
- Contributions are welcome! Please make a pull request to propose changes.
- For more information, reach out to schidraw@calpoly.edu.

## Support and Feedback
- Users will be prompted to provide feedback at the end of the interview.
- Use the feedback form to report issues or seek support.

