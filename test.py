import json
import os
from queue import Queue, Empty
from threading import Thread
from dotenv import load_dotenv
from agent import Agent  # Ensure this is the correct path to your Agent class

# Load environment variables from .env file
load_dotenv()

class ChatAgent(Agent):
    def __init__(self, name, exchange, routing_key, queue, user, password):
        super().__init__(name, exchange, routing_key, queue, user, password)
        self.message_queue = Queue()

    def process_message(self, message):
        # Check if the message is from the agent itself
        sender = message.get('sender')
        if sender is None:
            # Assuming if there is no sender, it's a response from the AI agent
            self.message_queue.put(message['message'])
            print(f"Debug: AI agent response added to queue: {message['message']}")
        elif sender != self.name:
            self.message_queue.put(message['message'])
            print(f"Debug: Message received and added to queue: {message['message']}")
        else:
            print(f"Debug: Message ignored from self: {message}")

def chat_with_bot():
    # Static information about the user
    user_id = 'Brett Kettler'
    user_location = 'Netherlands'
    agent_location = 'Lab'
    
    # Who are you talking to?
    agent = 'master'
    

    # Create the agent
    chat_agent = ChatAgent(
        name=user_id,
        exchange="agent_exchange",
        routing_key=user_id,
        queue=f"unity_{agent}_queue",
        user=os.getenv('AI_USER'),
        password=os.getenv('AI_PASS')
    )

    # Start a thread to receive messages
    receive_thread = Thread(target=chat_agent.start_receiving)
    receive_thread.start()

    def print_responses():
        while True:
            try:
                # Wait for a message to arrive for up to 1 second
                response_message = chat_agent.message_queue.get(timeout=1)
                print(f"{agent}: {response_message}")
            except Empty:
                # No message received within timeout, continue waiting
                continue

    # Start a thread to print responses
    response_thread = Thread(target=print_responses)
    response_thread.daemon = True  # This makes sure the thread will close when the main program exits
    response_thread.start()

    try:
        while True:
            userquestion = input("You: ")
            if userquestion.lower() in ['exit', 'quit']:
                print("Exiting chat...")
                break

            # Send the user question to the AI agent
            chat_agent.send_message({
                'userquestion': userquestion,
                'user_id': user_id,
                'user_location': user_location,
                'agent_location': agent_location
            }, f"ai_{agent}")
            print("Debug: Message sent to AI agent.")
    except KeyboardInterrupt:
        print("Exiting chat due to keyboard interrupt...")

    # Graceful shutdown
    chat_agent.close_connection()
    receive_thread.join()

if __name__ == '__main__':
    chat_with_bot()
