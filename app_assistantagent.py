#####################################################################################################################
#
#  ________                                   __  .__                  _____  .___  
# /  _____/  ____   ____   ________________ _/  |_|__|__  __ ____     /  _  \ |   | 
#/   \  ____/ __ \ /    \_/ __ \_  __ \__  \\   __\  \  \/ // __ \   /  /_\  \|   | 
#\    \_\  \  ___/|   |  \  ___/|  | \// __ \|  | |  |\   /\  ___/  /    |    \   | 
# \______  /\___  >___|  /\___  >__|  (____  /__| |__| \_/  \___  > \____|__  /___| 
#        \/     \/     \/     \/           \/                   \/          \/      
# .____          ___.                        __                                     
# |    |   _____ \_ |__   ________________ _/  |_  ___________ ___.__.              
# |    |   \__  \ | __ \ /  _ \_  __ \__  \\   __\/  _ \_  __ <   |  |              
# |    |___ / __ \| \_\ (  <_> )  | \// __ \|  | (  <_> )  | \/\___  |              
# |_______ (____  /___  /\____/|__|  (____  /__|  \____/|__|   / ____|              
#         \/    \/    \/                  \/                   \/                
#         
#         
#####################################################################################################################
# INTRODUCTION:
#
#
#
#
# DISCLAIMER: 
# 
# Changing of the code in this file voids the warranty of the code. This code is provided as is
# and is not guaranteed to work for your use case. This code is provided as a starting point for your own projects and
# should be used as such. Feel free to take inspiration from this code and use it in your own projects. If you would like
# a session to understand further ... sorry we are not able to provide that at this time.
#
#
# Generative AI Laboratory - Capgemini
#
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
# 1. flask --app app_qualityagent run  
#
# Test (New Terminal):
# 1. python test.py


#####################################################################################


from ast import Call
import os
import sys
from unittest import result

from regex import P
from sqlalchemy import null

from agent_mq import Agent
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

from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool


import openai
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory




    
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

print("LLM: ", llm)


#tools = [capgeminiDocumentsTool(), actionTool(), CallTool()]

tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool()]

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

            Use the searchDocuments tool to look up items about the lab. Use the Agent2Agent tool to ask other agents questions.
            
            
            
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
            
            print("Prompt: ", prompt)
            
            # Construct the Tools agent
            agent = create_tool_calling_agent(llm, tools, prompt)

            print("Agent: ", agent)
            
            print("=======================================")
            print("")
            
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            print("Agent Executor: ", agent_executor)
            print("=======================================")
            print("")
            
            try:
                message_history = RedisChatMessageHistory(
                        url="redis://default:aKo1aAx6uSMFIKG0v0EYLDH5sOf9zFSR@redis-15294.c56.east-us.azure.redns.redis-cloud.com:15294", ttl=100, session_id=session_id
            
            )
            except Exception as e:
                return {"error": str(e)}
            

                            
            print("Message History: ", message_history)

            print("m=======================================")
            print("")
            
            try:
                agent_with_chat_history = RunnableWithMessageHistory(
                    agent_executor,
                    # This is needed because in most real world scenarios, a session id is needed
                    # It isn't really used here because we are using a simple in memory ChatMessageHistory
                    lambda session_id: message_history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                )
            except Exception as e:
                return {"error": str(e)}

            try:
                response = agent_with_chat_history.invoke(
                    {"input": f"{userquestion}"},
                    config={"configurable": {"session_id": session_id}},
                )
            except Exception as e:
                return {"error": str(e)}
            
            print("Response: ", response)
            
            if 'output' in response:
                ai_response = response['output']
                print("==========> AI Response: ", ai_response)
            else:
                print(response)
                return {"error": "No valid response from the AI."}
            
            return {"response": ai_response}
            # formatted_response = process_ai_response(response)

            # return formatted_response
        
        except Exception as e:
            return {"error": str(e)}


if __name__ == '__main__':
    # # Define the custom IP address and port
    custom_ip = '0.0.0.0'  # Set to the desired IP address (e.g., '127.0.0.1' for localhost)
    custom_port = 8000     # Set to the desired port number (e.g., 8080)

    # Run the Flask app with custom IP and port
    app.run(debug=True)


