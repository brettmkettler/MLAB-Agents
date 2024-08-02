import requests
from websocket import send

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
headers = {
    'Authorization': f'Bearer {access_token}'
}


#######################################################################

# Request the stations overview



def get_station_overview():
    """
    Get the overview of all stations
    """
    stations_url = "https://testpctbackend.azurewebsites.net/view/station/overview"
    response = requests.get(stations_url, headers=headers)
    stations_overview = response.json()

    # Print in blue
    print("\033[94mStations Overview:", stations_overview)
    
    return stations_overview


##########################################################################

def get_robot_status(robot_id):
    """
    Get status of a robot
    """
    
    # Define the robot status endpoint (example for robot id 3)
    robot_status_url = f"https://testpctbackend.azurewebsites.net/robot/{robot_id}"
    
    # Request the robot status
    response = requests.get(robot_status_url, headers=headers)
    robot_status = response.json()

    # Print in green
    print("\033[92mRobot Status:", robot_status)
    
    return robot_status

##########################################################################

def get_robot_programs(robot_id):
    """
    Get the list of programs available for a robot
    """
    # Define the robot program list endpoint (example for robot id 3)
    robot_program_url = f"https://testpctbackend.azurewebsites.net/robot/program/{robot_id}"
    
    # Request the robot program list
    response = requests.get(robot_program_url, headers=headers)
    robot_programs = response.json()

    # Print in blue
    print("\033[94mRobot Programs:", robot_programs)
    
    return robot_programs


##########################################################################
# SEND PROGRAM TO ROBOT

def send_program_to_robot(robot_id, program_id, operation):
    """
    Send program to a robot
    """
    # Define the endpoint to send a program to the robot (example for robot id 3)
    send_program_url = f"https://testpctbackend.azurewebsites.net/robot/program/{robot_id}"
    
    # Define the program data to be sent
    program_data = {
        "programId": program_id,  # Example program ID
        "operation": operation  # Example operation
    }
    
    # Send the program to the robot
    response = requests.post(send_program_url, headers=headers, json=program_data)
    
    # Check for errors
    if response.status_code == 405:
        print("\033[91mError: Method Not Allowed. Verify the HTTP method and endpoint.")
        print(response)
        return "Error: Method Not Allowed. Verify the HTTP method and endpoint."
    elif response.status_code != 200:
        print(f"\033[91mError: {response.status_code} - {response.json().get('error', 'Unknown error')}")
        return f"Error: {response.status_code} - {response.json().get('error', 'Unknown error')}"
    else:
        try:
            send_program_response = response.json()
            # Print in green
            print("\033[92mSend Program Response:", send_program_response)
            
            response_text = f"Program sent to robot {robot_id} with program ID {program_id} and operation {operation}. Operation is starting."
            return response_text
        except:
            print("\033[91mError: Failed to parse response.")
            response_text = f"Program sent to robot {robot_id} with program ID {program_id} and operation {operation}."
            return response_text

# make text white
print("\033[97m")



####################
# LANGCHAIN
import asyncio
import glob
from multiprocessing import process
from grpc import channel_ready_future
from langchain.tools import BaseTool
from typing import Optional, Type
from flask import Flask, Response, request
from pydantic import BaseModel, Field
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel


class GetStationOverviewInputs(BaseModel):
    """Inputs for the Agent2Human tool."""
    

class GetStationOverview(BaseTool):
    name = "get_station_overview"
    description = "useful for when you need to talk to or ask a human a question. You will need the following inputs: question The question should be something that is easy to answer over the phone but descriptive and detailed enough to get the information you need and the agent name.."
    args_schema: Type[BaseModel] = GetStationOverviewInputs
    company = ""

    def _run(self):
        """Use the tool."""
        response = get_station_overview()
        return response


#####



class GetRobotStationStatusInputs(BaseModel):
    """Inputs for the GetRobotStationStatus tool."""
    robotStation: str = Field(..., description="The robot or station number ID. Number only.")

class GetRobotStationStatusOverview(BaseTool):
    name = "get_robot_status"
    description = "Useful for when you need to get the status or various sensor data of a particular robot or station like temperatures and data points of the robots. You will need the following inputs: robotStation The robot or station number ID. Here are the mappings of the stations: Station 2: Assembly Bench, Station 3: Testbench FANUC Robot, Station 10: Training Area. Only put the number of the station in the input."
    args_schema: Type[BaseModel] = GetRobotStationStatusInputs
    company = ""

    def _run(self, robotStation: str):
        """Use the tool."""
        response = get_robot_status(robotStation)
        return response
    
    

###


class RunFANUCInputs(BaseModel):
    """Inputs for the GetRobotStationStatus tool."""
    regionNumber: str = Field(..., description="The region of the part to look at on examining part.")
    
    action: str = Field(..., description="The action to perform on the robot. Options are: EXECUTE, STOP, PAUSE, RESUME")

class RunFANUC(BaseTool):
    name = "RunFANUC"
    description = "Useful for when you need to run, stop, pause, or resume a program on the FANUC robot to examine a particular area on the part for defects. You will need the following inputs: regionNumber The region of the part to look at on examining part, and action The action to perform on the robot. Options are: EXECUTE, STOP, PAUSE, RESUME."
    args_schema: Type[BaseModel] = RunFANUCInputs
    company = ""

    def _run(self, regionNumber: str, action: str):
        """Use the tool."""
        response = send_program_to_robot(3, regionNumber, action)
        return response