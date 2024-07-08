import os
import json
import logging
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from threading import Thread
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from agent_mq import Agent
from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory



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

# Load environment variables
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# SETUP AGENT
agent_name = "ai_master"



# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app and API
app = Flask(__name__)
api = Api(app, version='1.0', title='Metaverse Lab - Move Agent 1', description='This is the Metaverse Lab virtual agent orchestrator.', doc='/api/doc')

# Define the chat model for the API
chat_model = api.model('Chat', {
    'userquestion': fields.String('The user question'),
    'user_id': fields.String('The user information'),
    'user_location': fields.String('The user\'s location'),
    'agent_location': fields.String('The agent\'s location'),
})

# Initialize the LLM and tools
llm = ChatOpenAI(model="gpt-4")

tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool()]

# Set up the prompt template

def setupPrompt(userinfo, agentlocation, userlocation):
    
    print ("setting up prompt")
    
    return ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            You are a helpful metaverse lab assistant named: {agent_name}. You are talking to {userinfo}.

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

# Define the Chat resource for the API
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
            logging.info(f"Received request: userquestion={userquestion}, userinfo={userinfo}, userlocation={userlocation}, agentlocation={agentlocation}")
            
            prompt = setupPrompt(userinfo, agentlocation, userlocation)
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            try:
                message_history = RedisChatMessageHistory(
                        url="redis://default:aKo1aAx6uSMFIKG0v0EYLDH5sOf9zFSR@redis-15294.c56.east-us.azure.redns.redis-cloud.com:15294", ttl=100, session_id=session_id
            
            )
            except Exception as e:
                return {"error": str(e)}
            
            logging.info(f"Message history initialized: {message_history}")
            
            agent_with_chat_history = RunnableWithMessageHistory(agent_executor, lambda session_id: message_history, input_messages_key="input", history_messages_key="chat_history")
            
            response = agent_with_chat_history.invoke({"input": userquestion}, config={"configurable": {"session_id": session_id}})
            ai_response = response.get('output', "No valid response from the AI.")
            
            logging.info(f"AI Response: {ai_response}")
            return {"response": ai_response}
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            return {"error": str(e)}

# Function to process incoming messages
def process_message(message):
    try:
        logging.info(f"Processing message: {message}")
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
        
        
        # Send the response back to the sender through the queue
        master_ai.send_message(ai_response, target_routing_key=userinfo)
        
        logging.info(f"Sent response back to {userinfo} through the queue.")
        
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# Function to start listening to the message queue
def start_message_listener():
    try:
        global master_ai
        master_ai = Agent(
            name="MasterAIAgent",
            exchange="agent_exchange",
            routing_key="ai_master",
            queue="ai_master_queue",
            user=os.getenv('AI_USER'),
            password=os.getenv('AI_PASS')
        )
        
        def callback(ch, method, properties, body):
            try:
                logging.info(f"Received message: {body}")
                message = json.loads(body)
                print(message)
                process_message(message)
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.error(f"Failed to process message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)

        master_ai.channel.basic_consume(queue=master_ai.queue, on_message_callback=callback, auto_ack=False)
        logging.info("Started listening to message queue...")
        master_ai.channel.start_consuming()
    except Exception as e:
        logging.error(f"Failed to start message listener: {e}")

if __name__ == '__main__':
    # Start the message listener in a separate thread
    listener_thread = Thread(target=start_message_listener)
    listener_thread.start()

    # Run the Flask app
    custom_ip = '0.0.0.0'
    custom_port = 8001
    app.run(debug=True, host=custom_ip, port=custom_port)
