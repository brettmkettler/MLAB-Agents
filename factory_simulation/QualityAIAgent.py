from agent_mq import Agent
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class QualityAI(Agent):
    def process_message(self, message):
        try:
            inner_msg = message['message']
            result = inner_msg['result']
            batch = inner_msg['batch']
        except KeyError as e:
            print(f"[QualityAI] KeyError: {e}. Message: {message}")
            return

        ## LLM AI Function
        if result == "Step missing":
            self.send_message(f"Go to testBench and inform them about the missing step in batch {batch}", "unity_quality")
            self.send_message(f"something is wrong about step 9 in {batch}", "ai_master")
        elif result == "Suspicious step 9":
            self.send_message(f"Go to Digital Pokoyoko and Inspect part X of the board in batch {batch}", "unity_quality")
            self.send_message({"batch":"{batch}" , "scanPart" : [9]}, "DigitalPokaYoke_bot")
        else:
            #self.send_message(f"All steps OK in batch {batch}", "unity_quality")
            print(f"All steps OK in batch {batch}, nothing need to be done")

        ## LLM AI Function END

quality_ai = QualityAI(
    name="QualityAI",
    exchange="agent_exchange",
    routing_key="ai_quality",
    queue="ai_quality_queue",
    user=os.getenv('AI_USER'),
    password=os.getenv('AI_PASS')
)
quality_ai.start_receiving()
