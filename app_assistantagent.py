from ast import Call
import os
import logging
import json
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from threading import Thread
from dotenv import load_dotenv


from agent_mq import Agent
from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool, Agent2HumanTool


from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app and API
app = Flask(__name__)
api = Api(app, version='1.0', title='Metaverse Lab - Move Agent 1',
          description='This is the Metaverse Lab virtual agent orchestrator.', doc='/api/doc')

# Define the chat model for the API
chat_model = api.model('Chat', {
    'userquestion': fields.String('The user question'),
    'user_id': fields.String('The user information'),
    'user_location': fields.String('The user\'s location'),
    'agent_location': fields.String('The agent\'s location'),
})

# Initialize the LLM and tools
llm = ChatOpenAI(model="gpt-4")

# Replace these with actual tool implementations
tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool(), Agent2HumanTool()]

# Set up the prompt template
def setup_prompt(userinfo, agentlocation, userlocation):
    logging.info("Setting up prompt")
    return ChatPromptTemplate.from_messages([
        ("system", f"""
            You are a helpful metaverse lab assistant named: ai_assistant. You are talking to {userinfo}.
            You are located here: {agentlocation}.
            The user is located here: {userlocation}.
            Use the searchDocuments tool to look up items about the lab. Use the Agent2Agent tool to ask other agents questions and respond back to agents that ask questions.
            If you receive a response from ai_master, ai_quality, or ai_assistant, forward the response to the user if needed.
        """),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

# Define the Chat resource for the API
@api.route('/chat')
class Chat(Resource):
    @api.expect(chat_model)
    def post(self):
        try:
            data = request.json
            userquestion = data['userquestion']
            userinfo = data['user_id']
            userlocation = data['user_location']
            agentlocation = data['agent_location']
            
            session_id = userinfo
            logging.info(f"Received request: {data}")
            
            prompt = setup_prompt(userinfo, agentlocation, userlocation)
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            message_history = RedisChatMessageHistory(
                url=os.getenv("REDIS_URL"), ttl=100, session_id=session_id
            )
            
            logging.info(f"Message history initialized: {message_history}")
            
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: message_history,
                input_messages_key="input",
                history_messages_key="chat_history"
            )
            
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
        userquestion = message['message']
        userinfo = message['sender']
        userlocation = "Unknown"  # You might want to include user location in the message
        agentlocation = "Metaverse Lab"

        session_id = userinfo
        
        prompt = setup_prompt(userinfo, agentlocation, userlocation)
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        message_history = RedisChatMessageHistory(
            url=os.getenv("REDIS_URL"), ttl=100, session_id=session_id
        )
        
        logging.info(f"Message history initialized: {message_history}")
        
        agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: message_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        response = agent_with_chat_history.invoke({"input": userquestion}, config={"configurable": {"session_id": session_id}})
        ai_response = response.get('output', "No valid response from the AI.")
        
        logging.info(f"AI Response: {ai_response}")
        
        # Send the response back to the sender through the queue (assuming master_ai.send_message exists)
        master_ai.send_message(ai_response, target_routing_key=userinfo)
        
        logging.info(f"Sent response back to {userinfo} through the queue.")
        
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# Function to start listening to the message queue
def start_message_listener():
    try:
        global master_ai
        master_ai = Agent(
            name="AssistantAgent",
            exchange="agent_exchange",
            routing_key="ai_assistant",
            queue="ai_assistant_queue",
            user=os.getenv('AI_USER'),
            password=os.getenv('AI_PASS')
        )
        
        def callback(ch, method, properties, body):
            try:
                logging.info(f"Received message: {body}")
                message = json.loads(body)
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
