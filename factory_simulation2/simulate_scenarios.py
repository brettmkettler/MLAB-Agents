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
        exchange="amq.topic",  # This should match the existing exchange type in RabbitMQ
        routing_key="ai_assembly",
        queue="ai_assembly_queue",
        user=os.getenv('AI_USER'),
        password=os.getenv('AI_PASS')
    )
    # Correctly structure the message
    message = {
        'message': data,
        'user_id': 'test_user',  # Assuming a user_id for the example
        'user_location': 'test_location',
        'agent_location': 'test_agent_location'
    }
    assembly_agent.send_message(message, "ai_assembly")
    print(f"Sent data to Assembly Agent")

def main():
    scenarios = load_scenarios('scenarios.json')

    while True:
        for details in scenarios:
            print(f"Simulating scenario with details: {details}")
            simulate_scenario(details)
            time.sleep(10)

if __name__ == "__main__":
    main()
