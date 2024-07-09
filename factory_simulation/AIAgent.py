import os
import logging
import json
from dotenv import load_dotenv
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

# Initialize the LLM and tools
llm = ChatOpenAI(model="gpt-4")

# Replace these with actual tool implementations
tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool(), Agent2HumanTool()]

class BaseAgent:
    def __init__(self, name, exchange, routing_key, queue, user, password):
        self.agent = Agent(name=name, exchange=exchange, routing_key=routing_key, queue=queue, user=user, password=password)

    def setup_prompt(self, userinfo, agentlocation, userlocation):
        logging.info("Setting up prompt")
        return ChatPromptTemplate.from_messages([
            ("system", f"""
                You are a helpful metaverse lab assistant named: {self.agent.name}. You are talking to {userinfo}.
                You are located here: {agentlocation}.
                The user is located here: {userlocation}.
                Use the searchDocuments tool to look up items about the lab. Use the Agent2Agent tool to ask other agents questions and respond back to agents that ask questions.
                If you receive a response from ai_master, ai_quality, or ai_assistant, forward the response to the user if needed.
            """),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

    def process_message(self, message):
        try:
            logging.info(f"Processing message: {message}")
            userquestion = message['message']
            userinfo = message['sender']
            userlocation = "Unknown"
            agentlocation = "Metaverse Lab"

            session_id = userinfo
            prompt = self.setup_prompt(userinfo, agentlocation, userlocation)
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
            self.agent.send_message(ai_response, target_routing_key=userinfo)

            logging.info(f"Sent response back to {userinfo} through the queue.")

        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def start_message_listener(self):
        try:
            def callback(ch, method, properties, body):
                try:
                    logging.info(f"Received message: {body}")
                    message = json.loads(body)
                    self.process_message(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logging.error(f"Failed to process message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag)

            self.agent.channel.basic_consume(queue=self.agent.queue, on_message_callback=callback, auto_ack=False)
            logging.info("Started listening to message queue...")
            self.agent.channel.start_consuming()
        except Exception as e:
            logging.error(f"Failed to start message listener: {e}")

