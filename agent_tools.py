import asyncio
import glob
from multiprocessing import process
from grpc import channel_ready_future
from langchain.tools import BaseTool
from typing import Optional, Type
from flask import Flask, Response, request
from pydantic import BaseModel, Field
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

import pika
import json
import os
import logging
import ssl
import re

###################################################################
# RABBITMQ
#############

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
AI_USER = os.getenv('AI_USER')
AI_PASS = os.getenv('AI_PASS')
# Set up RabbitMQ connection and channel
# SSL context setup with disabled verification
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE       
credentials = pika.PlainCredentials(AI_USER, AI_PASS)
parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials, ssl_options=pika.SSLOptions(context))
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

############################


# HELPER FUNCTION
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def process_ai_response(response):
#     """Process the AI response to extract actions."""
#     try:
#         # Check if response is a string
#         if isinstance(response, str):
#             logger.info(f"Raw AI Response: {response}")

#             # Pattern to match actions and their content
#             action_pattern = r'"action": "(\w+)", "content": "([^"]*)"'
#             actions = re.findall(action_pattern, response)

#             if not actions:
#                 logger.warning("No valid actions found in the AI response.")
#                 return {"error": "No valid actions found in the AI response."}

#             action_types = {"GOTO": "None", "POINTAT": "None", "TALK": "None"}

#             for action_type, action_content in actions:
#                 if action_type in action_types:
#                     action_types[action_type] = action_content

#             actions_list = [
#                 {"action": "GOTO", "content": action_types["GOTO"]},
#                 {"action": "POINTAT", "content": action_types["POINTAT"]},
#                 {"action": "TALK", "content": action_types["TALK"]}
#             ]

#             formatted_response = {"response": actions_list}
#             logger.info(f"Formatted Response: {formatted_response}")
#             return formatted_response
#         else:
#             logger.warning("No valid response from the AI.")
#             return {"error": "No valid response from the AI."}
#     except Exception as e:
#         logger.error(f"Error processing AI response: {e}")
#         return {"error": str(e)}
    
    
#########################################################################################################
# FUNCTION CLASSES CREATION
#######################



class capgeminiDocumentsInputs(BaseModel):
    """Input for searching for documents in the"""
    query: str = Field(..., description="The query to search for in the documents.")
    # question: str = Field(..., description="The entire question that the user asked.")
    
    


####### TOOL BUILDER

# Tool Builder
class capgeminiDocumentsTool(BaseTool):
    """Search for documents in the vector store for relevant information."""
    name = "searchDocuments"
    description = "Use this tool to search for information in the documents."

    def _run(self, query: str, *args, **kwargs):
        return searchDocuments(query)

    async def _arun(self, query: str, *args, **kwargs):
        return await asyncio.to_thread(searchDocuments, query)

    args_schema: Optional[Type[BaseModel]] = capgeminiDocumentsInputs

   



##########################
# CLASS FUNCTION CREATION

class actionInputs(BaseModel):
    """Input for actions that the agent can do"""
    
    userlocation: str = Field(..., description="The location of the user.")
    question: str = Field(..., description="The entire question that the user asked.")
    response: str = Field(..., description="The response from the agent.")
    
    


####### TOOL BUILDER

class actionTool(BaseTool):
    name = "actionTool"
    description = "Use this tool to decide what actions to take based on the user question and your response."

    def _run(self, userlocation:str, question: str, response: str, *args, **kwargs):
        return actions(userlocation, question, response)

    def _arun(self, question: str, response: str, *args, **kwargs):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = actionInputs
    
    
    
    
    
    
    


############################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################









#########################################################################################################
# FUNCTIONS 
#######################





from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory

azure_endpoint: str = "https://ai-lab-openai-poc.openai.azure.com/"
azure_openai_api_key: str = "95a6cb0196b44c0d98e6296fa8ddd13d"
azure_openai_api_version: str = "2024-02-15-preview"
azure_deployment: str = "text-embedding-ada-002"
vector_store_address: str = "https://mlab-search.search.windows.net"
vector_store_password: str = "9xFyeHTsOWJfxOg5hTytTYxEIgT0PxymospXClaZvkAzSeAKr7IZ"

embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
    azure_deployment=azure_deployment,
    openai_api_version=azure_openai_api_version,
    azure_endpoint=azure_endpoint,
    api_key=azure_openai_api_key,
)

index_name: str = "mlabagent1-index"

vector_store: AzureSearch = AzureSearch(
    azure_search_endpoint=vector_store_address,
    azure_search_key=vector_store_password,
    index_name=index_name,
    embedding_function=embeddings.embed_query,
)

print("VECTOR STORE: ", vector_store)



def actions(userlocation, userquestion, response):
    print("Deciding what actions to take...")
    
    print("User's Location: ", userlocation)
    print("User Question: ", userquestion)
    print("Response: ", response)
    
    print("Searching for documents...")
    print("User Question: ", userquestion)
    print("Response: ", response)
    
    #testbench-index
    index_name_t: str = "testbench-index"
    vector_store: AzureSearch = AzureSearch(
        azure_search_endpoint=vector_store_address,
        azure_search_key=vector_store_password,
        index_name=index_name_t,
        embedding_function=embeddings.embed_query,
    )
    
    combo = f"{userquestion} the agents response: {response}"
    
    docs_and_scores = vector_store.similarity_search_with_relevance_scores(
            query=combo,
            k=6,
            score_threshold=0.2,
        )
        
    print("Data Retrieved: ", docs_and_scores)


    results = docs_and_scores
    
    
    print("Results: ", results)

    # Do something here with openai to decide what actions to take
    
    
    return response



def searchDocuments(userquestion: str):
    """Search for documents in the vector store for relevant information."""
    print("Searching for documents...")
    print("User Question: ", userquestion)
    

    docs_and_scores = vector_store.similarity_search_with_relevance_scores(
            query=userquestion,
            k=6,
            score_threshold=0.2,
        )   
    print("Docs and Scores: ", docs_and_scores)
    results = docs_and_scores
    print("Results: ", results)






    return results



############################  TIVALY SEARCH ####################################################


import requests

from tavily import TavilyClient

def tavily(query):
    

    # Step 1. Instantiating your TavilyClient
    tavily_client = TavilyClient(api_key="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")

    # Step 2. Executing a simple search query
    response = tavily_client.search(query)

    # Step 3. That's it! You've done a Tavily Search!
    print(response)
    
    return response



def search_tavily(query, search_depth="basic", include_images=False, include_answer=True, include_raw_content=False, max_results=5, include_domains=None, exclude_domains=None):
    
    # Define the base URL for the API
    BASE_URL = "https://api.tavily.com/"
    # Example usage
    api_key = "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"
    # Define the endpoint
    endpoint = "search"

    # Define the request payload
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_images": include_images,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "max_results": max_results,
        "include_domains": include_domains if include_domains else [],
        "exclude_domains": exclude_domains if exclude_domains else []
    }

    # Make the POST request
    response = requests.post(BASE_URL + endpoint, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        
        # Parse the JSON response
        data = response.json()
        return data
    else:
        print("Error:", response.text)
        return None
   
   
######################################################################################################





  
#################################################################################################################################################
################### PHONE CALL ################################################

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
                
                # summary = f"""
                # "action": "GOTO", "content": "None"
                # "action": "POINTAT", "content": "None"
                # "action": "TALK", "content": "{summary}"
                # """
                
                # formatted_summary = process_ai_response(summary)
                
                # print("Formatted Summary: ", formatted_summary)
                
                return summary
            #########################################
            else:
                print("Failed to get call summary")
                print(response.text)
                
                
        else:
            print('Call not completed yet')
            print(response.json())
            time.sleep(5)
    
    

  
  
  
############################################################################################################
#### TOOLS 
# You can add more tools here

# NOTE: WORKING ON ADDING INTERNET SEARCH TOOL TO FIND THINGS ONLINE

class searchInputs(BaseModel):
    """Inputs for the Agent2Human tool."""
    user_id: str = Field(
        description="The name of the user you are sending the message to."
    )

    question: str = Field(
        description="The question you want to ask, be descriptive."
    )




class searchTool(BaseTool):
    name = "searchTool"
    description = "useful for when search for things on the internet."
    args_schema: Type[BaseModel] = searchInputs
    company = ""

    def _run(self, user_id:str, question: str) -> str:
        """Use the tool."""
        response = agent2human_comm(user_id, question)
        return response








# CALL
from typing import Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)



class CallToolInputs(BaseModel):
    """Inputs for the Call tool."""

    question: str = Field(
        description="The question you want to ask, be descriptive."
    )




class CallTool(BaseTool):
    name = "call-tool"
    description = "useful for when you need to make a phone call to a colleague in an emergency situation only. You will need the following inputs: question The question should be something that is easy to answer over the phone but descriptive and detailed enough to get the information you need."
    args_schema: Type[BaseModel] = CallToolInputs
    company = ""

    def _run(self, question: str) -> str:
        """Use the tool."""
        response = makeCall(question)
        return response

    # async def _arun(self, phone_number: str, question: str, company: str, name: str) -> str:
    #     """Use the tool."""
    #     return makeCall(phone_number, question, company, name)



############################################################################################################




def send_message(route, message):
    """Send a message to the specified queue."""
    
    channel.basic_publish(
        exchange='amq.topic',
        routing_key=route,
        body=json.dumps(message)
    )
    print(f"Message send to route {route}.")
    # logger.info(f"Message forwarded to {forward_queue} via route {forward_route}.")       


from dotenv import load_dotenv
from agent_mq import Agent
import os
# Define the communication function using RabbitMQ
def agent2agent_comm(fromagent, agent, question):
    """
    Ability to talk to another agent and respond back to questions from agents. The agents you can talk to are:
    1. ai_master - The master AI agent
    2. ai_assembly - The assembly AI agent
    3. ai_quality - The quality AI agent
    
    """

    try:
        
        ####
        route = agent
        
        message = {
        "userquestion": question,
        "user_id": fromagent,
        "user_location": "Lab",
        "agent_location": "Lab"
        }

        send_message(route, message)
        
        print(f"Message sent to {agent}: {question}")
        
        return {"status": "success", "message": f"Message sent to {agent} successfully."}
    
    except Exception as e:
        print(f"Error sending message to {agent}: {e}")
        return {"status": "error", "message": str(e)}
    
    
    

class Agent2AgentInputs(BaseModel):
    """Inputs for the Agent2Agent tool."""
    fromagent: str = Field(
        description="The name of the agent you are sending the message from."
    )
    agent: str = Field(
        description="The name of the agent you want to talk to."
    )
    question: str = Field(
        description="The question you want to ask, be descriptive."
    )




class Agent2AgentTool(BaseTool):
    name = "agent2agent"
    description = "useful for when you need to talk to or ask another agent a question. You will need the following inputs: question The question should be something that is easy to answer over the phone but descriptive and detailed enough to get the information you need and the agent name. Agents: ai_master, ai_assistant, ai_quality, ai_assembly."
    args_schema: Type[BaseModel] = Agent2AgentInputs
    company = ""

    def _run(self, fromagent:str, agent: str, question: str) -> str:
        """Use the tool."""
        response = agent2agent_comm(fromagent, agent, question)
        return response


##############################



# Define the communication function using RabbitMQ
def agent2human_comm(user_id, question):
    """
    Ability to talk to a human or respond back to questions from humans.
    
    """
    try:
        chat_agent = Agent(
            name=user_id,
            exchange="agent_exchange",
            routing_key=user_id,
            queue="unity_messages_queue",
            user=os.getenv('AI_USER'),
            password=os.getenv('AI_PASS')
        )
        chat_agent.send_message(message=question, target_routing_key=user_id)
        
        print(f"Message sent to {user_id}: {question}")
        return {"status": "success", "message": f"Message sent to {user_id} successfully."}
    except Exception as e:
        print(f"Error sending message to {user_id}: {e}")
        return {"status": "error", "message": str(e)}
    
    
    

class Agent2HumanInputs(BaseModel):
    """Inputs for the Agent2Human tool."""
    user_id: str = Field(
        description="The name of the user you are sending the message to."
    )

    question: str = Field(
        description="The question you want to ask, be descriptive."
    )




class Agent2HumanTool(BaseTool):
    name = "agent2human"
    description = "useful for when you need to talk to or ask a human a question. You will need the following inputs: question The question should be something that is easy to answer over the phone but descriptive and detailed enough to get the information you need and the agent name.."
    args_schema: Type[BaseModel] = Agent2AgentInputs
    company = ""

    def _run(self, user_id:str, question: str) -> str:
        """Use the tool."""
        response = agent2human_comm(user_id, question)
        return response
