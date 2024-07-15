import os
from agent import Agent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

quality_agent = Agent(
    name="QualityAgent",
    exchange="agent_exchange",
    routing_key="quality",
    queue="quality_queue",
    user=os.getenv('AI_USER'),
    password=os.getenv('AI_PASS')
)
quality_agent.start_receiving()
