import random
from agent_mq import Agent
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Black-box function for LLM processing
def process_by_llm(agent_name, data):
    possible_results = ["All steps OK", "Step missing", "Suspicious step 9"]
    if data['batch'] == "batch0001":
        return "All steps OK"
    elif data['batch'] == "batch0002":
        return "Step missing"
    elif data['batch'] == "batch0003":
        return "Suspicious step 9"
    
    return random.choice(possible_results)

class AIAssessmentAgent(Agent):
    def process_message(self, message):
        try:
            inner_msg = message['message']
            
            batch = inner_msg['batch']
        except KeyError as e:
            print(f"[AIAssessmentAgent] KeyError: {e}. Message: {message}")
            return

        self.send_message({"talk": f"checking batch {batch}", "goto": "testBench"} , "unity_assessment") 
        result = process_by_llm("AIAssessmentAgent", inner_msg)
        self.send_message({"talk": f"{result} for batch {batch}", "goto": "testBench"} , "unity_assessment")
        self.send_message({"result": result, "batch": batch}, "ai_quality")

assessment_agent = AIAssessmentAgent(
    name="AIAssessmentAgent",
    exchange="agent_exchange",
    routing_key="ai_assessment",
    queue="ai_assessment_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)
assessment_agent.start_receiving()
