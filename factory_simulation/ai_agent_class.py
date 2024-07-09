import os
import logging
from dotenv import load_dotenv

from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool, Agent2HumanTool

from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

class AI_Agent:
    def __init__(self, agent_name):
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        
        self.agent_name = agent_name
        self.llm = ChatOpenAI(model="gpt-4")
        self.tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool(), Agent2HumanTool()]

    def setup_prompt(self, userinfo, agentlocation, userlocation):
        logging.info("Setting up prompt")
        return ChatPromptTemplate.from_messages([
            ("system", f"""
                You are a helpful metaverse lab assistant named: {self.agent_name}. You are talking to {userinfo}.
                You are located here: {agentlocation}.
                The user is located here: {userlocation}.
                Use the searchDocuments tool to look up items about the lab. Use the Agent2Agent tool to ask other agents questions and respond back to agents that ask questions.
                If you receive a response from ai_master, ai_quality, or ai_assistant, forward the response to the user if needed.
            """),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

    def process_message(self, userquestion, userinfo, userlocation, agentlocation):
        try:
            logging.info(f"Processing message from user: {userinfo}")
            
            session_id = userinfo
            
            prompt = self.setup_prompt(userinfo, agentlocation, userlocation)
            print(prompt)
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            print(agent)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            print(agent_executor)
            try:
                message_history = RedisChatMessageHistory(
                    url=os.getenv("REDIS_URL"), ttl=100, session_id=session_id
                )
            except Exception as e:
                logging.error(f"Failed to initialize message history: {e}")
                message_history = None
            
            logging.info(f"Message history initialized for session: {session_id}")
            
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: message_history,
                input_messages_key="input",
                history_messages_key="chat_history"
            )
            
            response = agent_with_chat_history.invoke({"input": userquestion}, config={"configurable": {"session_id": session_id}})
            ai_response = response.get('output', "No valid response from the AI.")
            
            logging.info(f"AI Response: {ai_response}")
            return ai_response
            
        except RuntimeError as e:
            if "cannot schedule new futures" in str(e):
                logging.error("Interpreter shutdown detected, cannot schedule new futures.")
            else:
                logging.error(f"RuntimeError processing message: {e}")
            return {"error": str(e)}
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return {"error": str(e)}

if __name__ == '__main__':
    agent = AI_Agent(agent_name="AssistantAgent")
    userquestion = "What is the latest update on the project?"
    userinfo = "User123"
    userlocation = "Office"
    agentlocation = "Metaverse Lab"
    
    response = agent.process_message(userquestion, userinfo, userlocation, agentlocation)
    print(response)
