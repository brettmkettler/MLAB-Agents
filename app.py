
#
######################################################
# SETUP:
#
# Setup venv and install the requirements
# 1. Create a virtual environment -> python -m venv mlab
# 2. Activate the virtual environment -> .\mlab\Scripts\Activate
# 3. Install the requirements -> pip install -r requirements.txt
# 
#
#
# RUN:
# 1. flask --app app run  
#
# Test (New Terminal):
# 1. streamlit run test_streamlit.py


#####################################################################################


import os
import sys
from unittest import result

from regex import P
from sqlalchemy import null
print(sys.path)
from langchain.tools import BaseTool
from typing import Optional, Type
from langchain.agents import AgentType

from langchain.agents import AgentExecutor
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from flask import Flask, Response, request
from pydantic import BaseModel, Field
from flask_restx import Api, Resource, fields
from flask import Flask, request, jsonify
from langchain.agents import initialize_agent

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


########
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()


# Tools
# from langchain_community.tools import DuckDuckGoSearchRun




#########################################################################################################
# FUNCTIONS
#######################

import openai
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
    
    
    # Mapping
    # REGION_VR has these POIs:
    # POI_EQUIPMENT,
    # POI_SAFE_AREA
    
    # REGION_DIGITALPOKAYOKE has these POIs:
    # POI_ELECTRIC_FRAME,
    # POI_CONTROL_PC,
    # POI_SERIAL_NUMBER_CAMERA,
    # POI_DEPTH_CAMERA,
    
    # REGION_COBOT has these POIs:
    # POI_UR10,
    # POI_ENGINE,
    
    # REGION_TESTBENCH has these POIs:
    # POI_FANUC,
    # POI_TEST_TARGET,
    # POI_MAINTENANCE,
    
    # REGION_UR3 has these POIs:
    # POI_ROBOT,
    
    # REGION_SPEECH has these POIs:
    # POI_LECTERN,
    # POI_PROJECTOR
    
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



def searchDocuments(userquestion):
    
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
    
     
##########################
# CLASS FUNCTION CREATION

class capgeminiDocumentsInputs(BaseModel):
    """Input for searching for documents in the"""
    
    question: str = Field(..., description="The entire question that the user asked.")
    
    


####### TOOL BUILDER

class capgeminiDocumentsTool(BaseTool):
    name = "searchDocuments"
    description = "Use this tool to search for information in the documents."

    def _run(self, question: str, *args, **kwargs):
        return searchDocuments(question)

    def _arun(self, question: str, *args, **kwargs):
        raise NotImplementedError("This tool does not support async")

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
    
    



    
##################
    
  ##########
  # MAIN
  ###########  
    
    
    
#userquestion='Create a service request for a new laptop for Brett Kettler in the AMO Assignment Group.'    
    
app = Flask(__name__)  
    

# Initialize Flask-RESTx
api = Api(app, version='1.0', title='Metaverse Lab - Move Agent 1', description='''c
          This is the Metaverse Lab virtual agent orchestrator.
          
          The response from the agent will include the actions to take based on the user question and the response from the agent.
          
          Example:
          [
              {
                    "action": "GOTO", "content": "REGION_VR",
                    "action": "POINTAT", "content": "POI_EQUIPMENT",
                    "action": "TALK", "content": "The equipment is located in the VR region."
              }
          ]
          
          ''', doc='/api/doc')



chat_model = api.model('Chat', {
    'userquestion': fields.String('The user question'),
    'user_id': fields.String('The user information'),
    'user_location': fields.String('The users location'),
    'agent_location': fields.String('The agents location'),
})



#llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")

# llm = ChatGroq(
#     model="llama3-70b-8192",
# )

llm = ChatOpenAI(model="gpt-4")


tools = [capgeminiDocumentsTool(), actionTool()]

def setupPrompt(userinfo, agentlocation, userlocation):
    
    print ("setting up prompt")
    
    return ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            You are a helpful metaverse lab assistant named Gemi. You are talking to {userinfo}.

            You are located here: {agentlocation}.
            
            The user is located here: {userlocation}.

            Use the searchDocuments tool to look up items about the lab. Use the actionTool to decide what actions to take and what to point at. You will need to use both tools.

            <REGION> is the location of the virtual location in the lab. <POI> is the object to point at. <RESPONSE> is the response to the user.

            The format of your response should be like this:
            
            "action": "GOTO", "content": "<REGION>"
            "action": "POINTAT", "content": "<POI>"
            "action": "TALK", "content": "<RESPONSE>" 
            

            Fill in the <REGION>, <POI>, and <RESPONSE> with the appropriate information if available:

            REGION_VR has these POIs:
            POI_EQUIPMENT
            POI_SAFE_AREA

            REGION_DIGITALPOKAYOKE has these POIs:
            POI_ELECTRIC_FRAME
            POI_CONTROL_PC
            POI_SERIAL_NUMBER_CAMERA
            POI_DEPTH_CAMERA

            REGION_COBOT has these POIs:
            POI_UR10
            POI_ENGINE

            REGION_TESTBENCH has these POIs:
            POI_FANUC
            POI_TEST_TARGET
            POI_MAINTENANCE

            REGION_UR3 has these POIs:
            POI_ROBOT

            REGION_SPEECH has these POIs:
            POI_LECTERN
            POI_PROJECTOR

            Note: All 3 actions must be included in the response. If there is no action to take, then use "None" for the content.
            
            Example:
            
            "action": "GOTO", "content": "None"
            "action": "POINTAT", "content": "None"
            "action": "TALK", "content": "<RESPONSE>" 
            
            
            "action": "GOTO", "content": "<REGION>"
            "action": "POINTAT", "content": "<POI>"
            "action": "TALK", "content": "<RESPONSE>"
            
            
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


import re

# Process / FORMAT RESPONSE
def process_ai_response(response):
    try:
        # Ensure the response contains the 'output' key
        if 'output' in response:
            ai_response = response['output']
            print("==========> AI Response: ", ai_response)
        else:
            print(response)
            return {"error": "No valid response from the AI."}

        # Extract action-content pairs using regex
        action_pattern = r'"action": "(\w+)", "content": "([^"]*)"'
        actions = re.findall(action_pattern, ai_response)
        action_types = {"GOTO": "None", "POINTAT": "None", "TALK": "None"}

        for action_type, action_content in actions:
            action_types[action_type] = action_content

        actions_list = [
            {"action": "GOTO", "content": action_types["GOTO"]},
            {"action": "POINTAT", "content": action_types["POINTAT"]},
            {"action": "TALK", "content": action_types["TALK"]}
        ]

        formatted_response = {"response": actions_list}

        print("Formatted Response: ", formatted_response)

        return formatted_response
    except Exception as e:
        return {"error": str(e)}



@api.route('/chat')
class Chat(Resource):
    @api.expect(chat_model)
    def post(self):
        try:
            userquestion = request.json['userquestion']
            userinfo = request.json['user_id']
            userlocation = request.json['user_location']
            agentlocation = request.json['agent_location']
            
            session_id = userinfo

            print("User Info: ", userinfo)
            print("User Location: ", userlocation)
            print("Agent Location: ", agentlocation)
            print("User Question: ", userquestion)
            
            prompt = setupPrompt(userinfo, agentlocation, userlocation)
            
            # Construct the Tools agent
            agent = create_tool_calling_agent(llm, tools, prompt)

            print("Agent: ", agent)
            
            print("=======================================")
            print("")
            
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            print("Agent Executor: ", agent_executor)
            print("=======================================")
            print("")
            
            message_history = RedisChatMessageHistory(
                        url="redis://default:aKo1aAx6uSMFIKG0v0EYLDH5sOf9zFSR@redis-15294.c56.east-us.azure.redns.redis-cloud.com:15294", ttl=100, session_id=session_id
            
            )
            

                            
            print("Message History: ", message_history)

            print("m=======================================")
            print("")
            
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                # This is needed because in most real world scenarios, a session id is needed
                # It isn't really used here because we are using a simple in memory ChatMessageHistory
                lambda session_id: message_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )

            try:
                response = agent_with_chat_history.invoke(
                    {"input": f"{userquestion}"},
                    config={"configurable": {"session_id": session_id}},
                )
            except Exception as e:
                return {"error": str(e)}
            

            
            # print to console
            print(response)
            

            formatted_response = process_ai_response(response)

            return formatted_response
        
        except Exception as e:
            return {"error": str(e)}


if __name__ == '__main__':
    # # Define the custom IP address and port
    custom_ip = '0.0.0.0'  # Set to the desired IP address (e.g., '127.0.0.1' for localhost)
    custom_port = 8000     # Set to the desired port number (e.g., 8080)

    # Run the Flask app with custom IP and port
    app.run(debug=True)


