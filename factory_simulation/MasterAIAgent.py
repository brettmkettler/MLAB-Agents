from agent import Agent
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env file
load_dotenv()

class MasterAIAgent(Agent):
    def process_message(self, message):
        try:
            inner_msg = message['message']
            result = inner_msg['result']
            batch = inner_msg['batch']
        except KeyError as e:
            print(f"[QualityAI] KeyError: {e}. Message: {message}")
            return

            ## LLM AI Function
            if re.search(r"Abnormal time gap", inner_msg, re.IGNORECASE):
                self.send_message(f"Go to Testbench and ask what happened in batch {batch}", "unity_master")
                self.send_message(f"Call Supervisor via MS Teams and inform about the situation in batch {batch}", "call_ms_teams")  

            # Assuming `message` is a dictionary with a 'message' key containing the text to be checked
            elif re.search(r"something is wrong about", inner_msg, re.IGNORECASE):
                self.send_message(f"Go to Testbench and ask what happened in batch {batch}", "unity_master")
                self.send_message(f"Call Supervisor via MS Teams and inform about the situation in batch {batch}", "call_ms_teams")
        
        ## LLM AI Function END


master_ai = MasterAIAgent(
    name="MasterAIAgent",
    exchange="agent_exchange",
    routing_key="ai_master",
    queue="ai_master_queue",
    user=os.getenv('AI_USER'),
    password=os.getenv('AI_PASS')
)
master_ai.start_receiving()
