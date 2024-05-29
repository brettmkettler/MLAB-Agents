import requests

def chat_with_bot():
    # Define the API endpoint URL
    #url = 'http://127.0.0.1:5000/chat'
    url = 'https://mlab-moveagent1.azurewebsites.net/chat'
    #url = 'https://mlab-agent1.azurewebsites.net/chat'

    # Static information about the user
    user_id = 'Brett Kettler'
    user_location = 'Netherlands'
    agent_location = 'Lab'

    while True:
        # Get user input
        userquestion = input("You: ")
        if userquestion.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            break

        # Define the JSON payload for the POST request
        data = {
            'userquestion': userquestion,
            'user_id': user_id,
            'user_location': user_location,
            'agent_location': agent_location
        }

        # Send a POST request to the API endpoint
        response = requests.post(url, json=data)
        
        #print(response.json())

        # Handle the response from the server
        if response.status_code == 200:
            
            #print(response.json())
            # Extract the AI's response from the API's JSON output
            api_response = response.json().get('response')
            
            print(f"Gemi: {api_response}")
            
            
        else:
            print(f"Failed to get a response: {response.status_code}")

if __name__ == '__main__':
    chat_with_bot()
