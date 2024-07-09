import random
import os
import logging
import queue
import threading
from agent import Agent
from dotenv import load_dotenv
from ai_agent_class import AI_Agent
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Setup AI Agent LLM
agent_name = "ai_assessment"
ai_agent = AI_Agent(agent_name=agent_name)

# Create a thread pool executor
executor = ThreadPoolExecutor(max_workers=5)

# Message queue for handling messages between consumer and processing threads
message_queue = queue.Queue()

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_event = threading.Event()

    def start_receiving(self):
        while not self.stop_event.is_set():
            try:
                # Simulate receiving a message and put it in the queue
                # In real implementation, this would be the actual message consumption from RabbitMQ
                message = self.receive_message()
                if message:
                    message_queue.put(message)
            except Exception as e:
                logging.error(f"[AIAssessmentAgent] Error in receiving message: {e}")
    
    def receive_message(self):
        # Simulate message reception
        # Replace this with actual message reception logic from RabbitMQ
        return {
            'message': {
                'batch': f"batch{random.randint(1, 4):04}",
                'userquestion': 'Sample question?',
                'userinfo': 'brett_kettler',
                'userlocation': 'REGION_TESTBENCH',
                'agentlocation': 'REGION_TESTBENCH'
            }
        }

def process_message():
    while not assessment_agent.stop_event.is_set() or not message_queue.empty():
        try:
            message = message_queue.get(timeout=1)
            if message:
                inner_msg = message['message']
                batch = inner_msg['batch']
                userquestion = inner_msg.get('userquestion', 'No question provided')
                userinfo = inner_msg.get('userinfo', 'brett_kettler')
                userlocation = inner_msg.get('userlocation', 'REGION_TESTBENCH')
                agentlocation = inner_msg.get('agentlocation', 'REGION_TESTBENCH')

                # Use the AI_Agent to process the message in a separate thread
                future = executor.submit(ai_agent.process_message, userquestion, userinfo, userlocation, agentlocation)
                ai_response = future.result()

                # Example of logging the AI response or processing it further
                logging.info(f"[AIAssessmentAgent] AI Response: {ai_response}")

                # Continue with your existing logic
                result = process_by_llm("AIAssessmentAgent", inner_msg)
                logging.info(f"Processed batch {batch}: {result}")

        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"[AIAssessmentAgent] Unexpected error processing message: {e}")

# Create an instance of AIAssessmentAgent
assessment_agent = AIAssessmentAgent(
    name="AIAssessmentAgent",
    exchange="agent_exchange",
    routing_key="ai_assessment",
    queue="ai_assessment_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)

# Ensure proper shutdown of executor
def shutdown_executor():
    logging.info("Shutting down executor")
    executor.shutdown(wait=True)

# Start the message consumer in a separate thread
consumer_thread = threading.Thread(target=assessment_agent.start_receiving)
consumer_thread.start()

# Start the message processor in a separate thread
processor_thread = threading.Thread(target=process_message)
processor_thread.start()

try:
    logging.info("Started message consumer and processor threads...")
    consumer_thread.join()
    processor_thread.join()
except KeyboardInterrupt:
    logging.info("Received keyboard interrupt, shutting down...")
    assessment_agent.stop_event.set()
except Exception as e:
    logging.error(f"Error in receiving messages: {e}")
finally:
    shutdown_executor()
    consumer_thread.join()
    processor_thread.join()
