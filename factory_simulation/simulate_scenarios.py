import json
import time
from agent import Agent
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def load_scenarios(file_path):
    with open(file_path, 'r') as file:
        scenarios = json.load(file)
    return scenarios

def simulate_scenario(data, batch):
    assessment_agent = Agent(
        name="AssessmentAgent",
        exchange="agent_exchange",
        routing_key="assessment",
        queue="ai_assessment_queue",
        user=os.getenv('AI_USER'),
        password=os.getenv('AI_PASS')
    )
    # Correctly structure the message
    assessment_agent.send_message({'data': data, 'batch': batch}, "ai_assessment")
    print(f"Sent data for batch {batch} to AI Assessment Agent")

def main():
    scenarios = load_scenarios('factory_simulation/scenarios.json')

    while True:
        for batch, details in scenarios.items():
            data = details['data']
            print(f"Simulating {batch}...")
            simulate_scenario(data, batch)
            time.sleep(10)

if __name__ == "__main__":
    main()
