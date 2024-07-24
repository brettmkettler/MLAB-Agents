import json
import logging
import requests
import time
import asyncio
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional, Type

logger = logging.getLogger(__name__)

class CapgeminiDocumentsInputs(BaseModel):
    """Input for searching for documents in the Capgemini vector store"""
    query: str = Field(..., description="The query to search for in the documents.")

class ActionInputs(BaseModel):
    """Input for actions that the agent can do"""
    userlocation: str = Field(..., description="The location of the user.")
    question: str = Field(..., description="The entire question that the user asked.")
    response: str = Field(..., description="The response from the agent.")

class CapgeminiDocumentsTool(BaseTool):
    """Search for documents in the vector store for relevant information."""
    name = "searchDocuments"
    description = "Use this tool to search for information in the documents."
    args_schema: Optional[Type[BaseModel]] = CapgeminiDocumentsInputs

    def _run(self, query: str, *args, **kwargs):
        return self.search_documents(query)

    async def _arun(self, query: str, *args, **kwargs):
        return await asyncio.to_thread(self.search_documents, query)

    def search_documents(self, query):
        logger.info(f"Searching documents for query: {query}")
        # Implement the actual search logic here
        return []

class ActionTool(BaseTool):
    """Tool to decide what actions to take based on the user question and your response."""
    name = "actionTool"
    description = "Use this tool to decide what actions to take based on the user question and your response."
    args_schema: Optional[Type[BaseModel]] = ActionInputs

    def _run(self, userlocation:str, question: str, response: str, *args, **kwargs):
        return self.decide_actions(userlocation, question, response)

    async def _arun(self, question: str, response: str, *args, **kwargs):
        raise NotImplementedError("This tool does not support async")

    def decide_actions(self, userlocation, question, response):
        logger.info(f"Deciding actions based on userlocation: {userlocation}, question: {question}, response: {response}")
        # Implement the actual action decision logic here
        return response

class CallTool(BaseTool):
    """Tool to make phone calls for additional information."""
    name = "callTool"
    description = "Use this tool to make phone calls to gather more information."
    args_schema: Optional[Type[BaseModel]] = None  # Define this if needed

    def _run(self, question: str, *args, **kwargs):
        return self.make_call(question)

    async def _arun(self, question: str, *args, **kwargs):
        return await asyncio.to_thread(self.make_call, question)

    def make_call(self, question):
        logger.info(f"Making a call for question: {question}")
        # Implement the actual call logic here
        return "Call made successfully."

class Agent2AgentInputs(BaseModel):
    """Inputs for the Agent2Agent tool."""
    fromagent: str = Field(description="The name of the agent you are sending the message from.")
    agent: str = Field(description="The name of the agent you want to talk to.")
    question: str = Field(description="The question you want to ask, be descriptive.")

class Agent2AgentTool(BaseTool):
    """Tool to communicate with another agent."""
    name = "agent2agent"
    description = "Use this tool to talk to another agent to ask questions or get information."
    args_schema: Optional[Type[BaseModel]] = Agent2AgentInputs

    def _run(self, fromagent: str, agent: str, question: str, *args, **kwargs):
        return self.agent2agent_comm(fromagent, agent, question)

    async def _arun(self, fromagent: str, agent: str, question: str, *args, **kwargs):
        return await asyncio.to_thread(self.agent2agent_comm, fromagent, agent, question)

    def agent2agent_comm(self, fromagent: str, agent: str, question: str):
        logger.info(f"Sending message from {fromagent} to {agent}: {question}")
        # Implement the actual communication logic here
        return "Message sent to the agent successfully."

def makeCall(question: str):
    print("Making phone call.")
    import requests
    import time

    # Your Vapi API Authorization token
    auth_token = '7f65584b-a416-498c-b532-ac843cb200af'
    # The Phone Number ID, and the Customer details for the call
    phone_number_id = 'dd0216d4-22ad-49ac-8bbb-61b31fa08357'
    
    company = "Capgemini Lab" 
    user_name = "Brett Kettler"
    phone_number = "+31625223187"
    
    # customer_number = f"{phone_number}" # Brett
    # customer_name = f"{user_name}"
    
    customer_number = f"{phone_number}" # Brett
    customer_name = f"{user_name}"


    print("Phone Number to call: ", customer_number)
    print("Customer Name: ", customer_name)
    print("Company: ", company)
    print("Question: ", question)

    firstmessage = f"{question}"

    # Create the header with Authorization token
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    # Create the data payload for the API request
    data = {

        "assistant": {
            "backgroundSound": "off",
            "model": {
                "model": "gpt-3.5-turbo-0613",
                "provider": "openai",
                "semanticCachingEnabled": True,
                "temperature": 0,
                "messages": [
                {
                    "content": f"Your name is Phil and you are a virtual metaverse avatar for {company}. You are calling a customer named {customer_name} to ask them a question regarding to the Digital Twin Laboratory. The question is: {question}",
                    "role": "system",

                }
                ]
            },
            "transcriber": {
                "provider": "deepgram",
                "language": "en",
                "model": "nova-2"
            },
            "voice": {
                "model": "eleven_turbo_v2",
                "provider": "11labs",
                "voiceId": "burt"
            },
            "firstMessage": firstmessage,   
        },
        "phoneNumberId": phone_number_id,
        "type": "outboundPhoneCall",
        'customer': {
            'number': customer_number,
            'name': customer_name,
        },
        
        }


    # Make the POST request to Vapi to create the phone call
    response = requests.post(
        'https://api.vapi.ai/call/phone', headers=headers, json=data)

    # Check if the request was successful and print the response
    if response.status_code == 201:
        print('Call created successfully')
        print(response.json())
    else:
        print('Failed to create call')
        print(response.text)
        
    print(response)

    # Get Call Loop

    # Get the call ID from the response
    id = response.json()['id']

    # start loop until the call is completed
    while True:
        response = requests.get(
            f'https://api.vapi.ai/call/{id}', headers=headers)
        
        if response.json()['status'] == 'ended':
            print('Call completed')
            print(response.json())
            
            # Get the summary of the call
            response = requests.get(
                f'https://api.vapi.ai/call/{id}', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                summary = data.get('summary', 'No summary available')
                print('Summary of the call:')
                print(summary)
                
                summary = f"""
                "action": "GOTO", "content": "None"
                "action": "POINTAT", "content": "None"
                "action": "TALK", "content": "{summary}"
                """
                
                formatted_summary = process_ai_response(summary)
                
                print("Formatted Summary: ", formatted_summary)
                
                return formatted_summary
            #########################################
            else:
                print("Failed to get call summary")
                print(response.text)
                
                
        else:
            print('Call not completed yet')
            print(response.json())
            time.sleep(5)
    
    

  
  
  

class Tools:
    def __init__(self):
        self.capgemini_documents_tool = CapgeminiDocumentsTool()
        self.action_tool = ActionTool()