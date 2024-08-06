import requests

robot = "3"

# Define the credentials and endpoint for obtaining the access token
token_url = "https://login.microsoftonline.com/e93297b0-7859-4ea6-a657-c30554499842/oauth2/token"
client_id = "d4854d13-9054-481f-8113-24b959fc46e5"
client_secret = "qbw8Q~D5IXKtoPcviB8hcODVybG0VBaJAj3Uqcc."
resource = "api://9ed56e47-1aa4-494e-ad9b-744a53c3743a"

# Prepare the data for the token request
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'resource': resource,
}

# Request the token
response = requests.post(token_url, data=token_data)
token_response = response.json()
access_token = token_response.get('access_token')

if not access_token:
    raise Exception("Failed to obtain access token")

print("Access Token:", access_token)

# Define the API endpoint and headers
stations_url = "https://testpctbackend.azurewebsites.net/view/station/overview"
headers = {
    'Authorization': f'Bearer {access_token}'
}

###########################################################################
# Request the stations overview
response = requests.get(stations_url, headers=headers)
stations_overview = response.json()

# Print in blue
print("\033[94mStations Overview:", stations_overview)

##########################################################################

# Define the robot status endpoint (example for robot id 3)
robot_status_url = f"https://testpctbackend.azurewebsites.net/robot/{robot}"

# Request the robot status
response = requests.get(robot_status_url, headers=headers)
robot_status = response.json()

# Print in green
print("\033[92mRobot Status:", robot_status)

##########################################################################

# Define the robot program list endpoint (example for robot id 3)
robot_program_url = f"https://testpctbackend.azurewebsites.net/robot/program/{robot}"

# Request the robot program list
response = requests.get(robot_program_url, headers=headers)
robot_programs = response.json()

# format json to easy read
import json
robot_programs = json.dumps(robot_programs, indent=4)  

# Print in blue
print("\033[94mRobot Programs:", robot_programs)

##########################################################################
# SEND PROGRAM TO ROBOT

# # Define the endpoint to send a program to the robot (example for robot id 3)
send_program_url = f"https://testpctbackend.azurewebsites.net/robot/program/{robot}"

# Define the program data to be sent
program_data = {
    "programId": 12,  # Example program ID
    "operation": "EXECUTE"  # Example operation
}

# Send the program to the robot
response = requests.post(send_program_url, headers=headers, json=program_data)

# Print the status code and response text for debugging
print(f"\033[97mStatus Code: {response.status_code}")
print(f"Response Text: {response.text}")



# Make text white
print("\033[97m")
