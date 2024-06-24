
import os
from azure.servicebus.management import ServiceBusAdministrationClient

connection_string = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
topic_name = "mlab-agents"

admin_client = ServiceBusAdministrationClient.from_connection_string(connection_string)

# Create topic if it doesn't exist
if not admin_client.get_topic(topic_name):
    admin_client.create_topic(topic_name)

# Create subscriptions with filters
subscription_names = ["agent1", "agent2"]
filters = [
    {"subscription_name": "agent1", "filter": "agent = 'agent1'"},
    {"subscription_name": "agent2", "filter": "agent = 'agent2'"}
]

for filter_info in filters:
    subscription_name = filter_info["subscription_name"]
    sql_filter = filter_info["filter"]

    if not admin_client.get_subscription(topic_name, subscription_name):
        admin_client.create_subscription(topic_name, subscription_name)
        admin_client.create_rule(topic_name, subscription_name, "agent_filter", sql_filter)
        admin_client.delete_rule(topic_name, subscription_name, "$Default")
