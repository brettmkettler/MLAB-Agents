import asyncio
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


# Define the base URL for the API
BASE_URL = "https://api.tavily.com/"
# Example usage
api_key = "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"


def search_tavily(api_key, query, search_depth="basic", include_images=False, include_answer=True,
                  include_raw_content=False, max_results=5, include_domains=None, exclude_domains=None):
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
    
    company = "Capgemini" 
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
    description = "useful for when you need to make a phone call to a colleague to get more information from a employee. You will need the following inputs: question The question should be something that is easy to answer over the phone but descriptive and detailed enough to get the information you need."
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
