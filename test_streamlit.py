import streamlit as st
import requests

def chat_with_bot(userquestion, user_id, user_location, agent_location):
    # Define the API endpoint URL
    #url = 'https://mlab-moveagent1.azurewebsites.net/chat'
    url = 'http://127.0.0.1:5000/chat'
    
    
    # Define the JSON payload for the POST request
    data = {
        'userquestion': userquestion,
        'user_id': user_id,
        'user_location': user_location,
        'agent_location': agent_location
    }

    # Send a POST request to the API endpoint
    response = requests.post(url, json=data)
    
    # Handle the response from the server
    if response.status_code == 200:
        api_response = response.json().get('response')
        return api_response
    else:
        return f"Failed to get a response: {response.status_code}"

def display_response(response):
    for action in response:
        if action['action'] == 'GOTO' and action['content'] != 'None':
            st.write("🚶")
            st.write(f"Location: {action['content']}")
        elif action['action'] == 'POINTAT' and action['content'] != 'None':
            st.write("👉")
            st.write(f"Pointing at: {action['content']}")
        elif action['action'] == 'TALK':
            st.write(f"Gemi: {action['content']}")

def main():
    st.title("Chat with Gemi")

    # Input fields for user information
    user_id = st.text_input("User ID", "Brett Kettler")

    # Dropdown for selecting region
    regions = [
        'REGION_VR', 'REGION_DIGITALPOKAYOKE', 'REGION_COBOT', 
        'REGION_TESTBENCH', 'REGION_UR3', 'REGION_SPEECH'
    ]
    
    user_location = st.selectbox("Select User's Region", regions)
    agent_location = st.selectbox("Select Agent's Region", regions)
    
    user_input = st.text_input("You:", "")

    if user_input:
        response = chat_with_bot(user_input, user_id, user_location, agent_location)
        
        if isinstance(response, list):
            display_response(response)
        else:
            st.write(response)
        
        # Expander to show raw response data
        with st.expander("Show raw response data"):
            st.json(response)

if __name__ == '__main__':
    main()
