# Factory Simulation with RabbitMQ

This project simulates various scenarios in a factory environment, utilizing RabbitMQ for message queuing and distribution.

## Setup and Usage

### 1. Setup Queues

Before running the simulation, you need to set up the RabbitMQ queues. This should be done the first time you run the simulation or if there are any changes to the queue configuration.

```sh
python setup_rabbitmq_s3.py
```

### 2. Run Agents

Start the agents to handle the simulation messages. Run three instances of the agent script with different roles.

Example command to run an agent:

```sh
& c:/repo/MLAB-Agents/mlab/Scripts/python.exe c:/repo/MLAB-Agents/factory_simulation3/AMQP_ai_agent_autogen.py assembly
```

Repeat the above command for each agent you want to run, changing the last argument to match the specific agent role.

### 3. Start Simulation

Run the simulation script to start processing the scenarios.

```sh
python simulate_scenarios.py
```

### 4. Modify Scenario Input Data

To change the input data for the scenarios, edit the `scenarios.json` file.


Update the scenarios and details as required.

## Project Structure

- `setup_rabbitmq_s3.py`: Script to set up RabbitMQ queues.
- `AMQP_ai_agent_autogen.py`: Script to run AI agents for handling messages.
- `simulate_scenarios.py`: Script to start the simulation.
- `scenarios.json`: JSON file containing the scenario input data.

## Environment Variables

Ensure the following environment variables are set, typically through a `.env` file:

- `RABBITMQ_USER`
- `RABBITMQ_PASS`
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`

Example `.env` file:

```
RABBITMQ_USER=your_user
RABBITMQ_PASS=your_pass
RABBITMQ_HOST=your_host
RABBITMQ_PORT=your_port
```

## Requirements

- Python 3.x
- `pika` library
- `python-dotenv` library

Install the required libraries using pip:

```sh
pip install pika python-dotenv
```

## Notes

- Ensure RabbitMQ is properly configured and running before starting the simulation.
- Adjust the agent scripts and simulation parameters as needed to fit your specific use case.
