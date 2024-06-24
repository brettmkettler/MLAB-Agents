import os
import json
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage


class AzureServiceBusManager:
    def __init__(self):
        # Load the connection string from the .env file
        load_dotenv()
        self.connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("Service Bus connection string not found in .env file.")
        print(f"Connection String: {self.connection_string}")  # Debugging information
        self.servicebus_client = ServiceBusClient.from_connection_string(conn_str=self.connection_string, logging_enable=True)

    def send_message_to_queue(self, queue_name, message_content, custom_properties):
        # Get a queue sender using the provided queue name
        with self.servicebus_client:
            sender = self.servicebus_client.get_queue_sender(queue_name=queue_name)
            with sender:
                # Create a new ServiceBusMessage with custom properties
                message = ServiceBusMessage(message_content)
                if message.application_properties is None:
                    message.application_properties = {}
                
                # Add custom properties to the message
                for key, value in custom_properties.items():
                    message.application_properties[key] = value

                # Send the message to the queue
                sender.send_messages(message)
                print(f"Sent message to queue: {message_content} with properties: {custom_properties}")

    def list_all_messages_in_queue(self, queue_name):
        # Get a queue receiver using the provided queue name
        with self.servicebus_client:
            receiver = self.servicebus_client.get_queue_receiver(queue_name=queue_name)
            with receiver:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=5)
                for message in messages:
                    body = ''.join(str(section) for section in message.body)
                    properties = {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in message.application_properties.items()}
                    print(f"Queue Message: {body}")
                    print(f"  Properties: {properties}")
                    receiver.complete_message(message)

    def send_message_to_topic(self, topic_name, message_content, custom_properties):
        # Get a topic sender using the provided topic name
        with self.servicebus_client:
            sender = self.servicebus_client.get_topic_sender(topic_name=topic_name)
            with sender:
                # Create a new ServiceBusMessage with custom properties
                message = ServiceBusMessage(message_content)
                if message.application_properties is None:
                    message.application_properties = {}
                
                # Add custom properties to the message
                for key, value in custom_properties.items():
                    message.application_properties[key] = value

                # Send the message to the topic
                sender.send_messages(message)
                print(f"Sent message to topic: {message_content} with properties: {custom_properties}")

    def list_all_messages_in_subscription(self, topic_name, subscription_name):
        # Get a subscription receiver using the provided topic and subscription names
        with self.servicebus_client:
            receiver = self.servicebus_client.get_subscription_receiver(
                topic_name=topic_name,
                subscription_name=subscription_name
            )
            with receiver:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=5)
                for message in messages:
                    body = ''.join(str(section) for section in message.body)
                    properties = {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in message.application_properties.items()}
                    print(f"Subscription Message: {body}")
                    print(f"  Properties: {properties}")
                    receiver.complete_message(message)

    def pick_messages_with_topic(self, topic_name, subscription_name, filter_topic):
        # Get a subscription receiver using the provided topic and subscription names
        with self.servicebus_client:
            receiver = self.servicebus_client.get_subscription_receiver(
                topic_name=topic_name,
                subscription_name=subscription_name
            )
            with receiver:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=5)
                for message in messages:
                    body = ''.join(str(section) for section in message.body)
                    properties = {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in message.application_properties.items()}
                    if properties.get("topic") == filter_topic:
                        print(f"Picked Subscription Message: {body}")
                        print(f"  Properties: {properties}")
                        receiver.complete_message(message)

class AzureServiceBusDictManager(AzureServiceBusManager):
    def send_message_to_queue(self, queue_name, message_content, custom_properties):
        message_content = json.dumps(message_content)  # Convert dict to JSON string
        super().send_message_to_queue(queue_name, message_content, custom_properties)

    def send_message_to_topic(self, topic_name, message_content, custom_properties):
        message_content = json.dumps(message_content)  # Convert dict to JSON string
        super().send_message_to_topic(topic_name, message_content, custom_properties)

# Example usage
if __name__ == "__main__":
    queue_name = "Q1"
    topic_name = "t1"
    subscription_name = "t1s1"
   
    custom_properties = {"tag": "important", "command": "doX"}

    agent1 = AzureServiceBusDictManager()

    message_content = {"greeting": "Hello, Ash!"}
    agent1.send_message_to_queue(queue_name, message_content, custom_properties)
    
    message_content = {"greeting": "Hello, Brett2!"}
    custom_properties = {"XXX": "YYY", "command": "CallX"}
    agent1.send_message_to_queue(queue_name, message_content, custom_properties)

    print("Listing all messages in the queue:")
    agent1.list_all_messages_in_queue(queue_name)

    message_content = {"alert": "This is a topic message!"}
    agent1.send_message_to_topic(topic_name, message_content, custom_properties)

    print("Listing all messages in the subscription:")
    agent1.list_all_messages_in_subscription(topic_name, subscription_name)
