from AIAgent import BaseAgent
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MasterAIAgent(BaseAgent):
    def process_message(self, message):
        try:
            inner_msg = message['message']
            result = inner_msg['result']
            batch = inner_msg['batch']
        except KeyError as e:
            print(f"[MasterAIAgent] KeyError: {e}. Message: {message}")
            return

        ## LLM AI Function
        if re.search(r"Abnormal time gap", inner_msg, re.IGNORECASE):
            self.agent.send_message(f"Go to Testbench and ask what happened in batch {batch}", "unity_master")
            self.agent.send_message(f"Call Supervisor via MS Teams and inform about the situation in batch {batch}", "call_ms_teams")  

        elif re.search(r"something is wrong about", inner_msg, re.IGNORECASE):
            self.agent.send_message(f"Go to Testbench and ask what happened in batch {batch}", "unity_master")
            self.agent.send_message(f"Call Supervisor via MS Teams and inform about the situation in batch {batch}", "call_ms_teams")
        ## LLM AI Function END

master_ai = MasterAIAgent(
    name="MasterAIAgent",
    exchange="agent_exchange",
    routing_key="ai_master",
    queue="ai_master_queue",
    user=os.getenv('AI_USER'),
    password=os.getenv('AI_PASS')
)
master_ai.start_message_listener()
