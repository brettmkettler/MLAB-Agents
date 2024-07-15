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

def simulate_scenario(data):
    assembly_agent = Agent(
        name="AssemblyAgent",
        exchange="agent_exchange",
        routing_key="assembly",
        queue="assembly_queue",
        user=os.getenv('AI_USER'),
        password=os.getenv('AI_PASS')
    )
    # Correctly structure the message
    assembly_agent.send_message(json.dumps(data), "assembly")
    print(f"Sent data to Assembly Agent")

def main():
    scenarios = load_scenarios('scenarios.json')

    while True:
        for details in scenarios:
            print(f"Simulating scenario...")
            simulate_scenario(details)
            time.sleep(10)

if __name__ == "__main__":
    main()
