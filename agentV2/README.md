Sure! Here is a `README.md` file that includes all the necessary steps and explanations for setting up and running your project:

# MLAB Agents Factory 

## Overview

This repository contains the implementation of MLAB Agents, which are designed to handle various tasks within an assembly operation using AI. The agents are set up to receive messages from RabbitMQ queues, process these messages using AI models, and perform actions based on the processed data.

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine using the following command:

```bash
git clone https://github.com/your-repo/MLAB-Agents.git
```

### 2. Move and Configure Environment Variables

Move the `template.env` file to `.env` and update it with the necessary keys and passwords:

```bash
mv template.env .env
```

Update the `.env` file with your specific configuration details for RabbitMQ, OpenAI, and other necessary services.

### 3. Install Requirements

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Setup RabbitMQ Queues

If you haven't already set up the RabbitMQ queues, run the `setup_rabbitmq.py` script. This will create all necessary queues with a specified prefix to isolate from other runs:

```bash
python setup_rabbitmq.py --prefix your_prefix
```

### 5. Run the Agents

Run the three agents using the following command (example shown for the `assembly` agent):

```bash
python agentV2/agent_autogen.py assembly
```

Repeat the above command for the other agents (`quality`, `master`, etc.) by replacing `assembly` with the respective agent names.

### 6. Run the Simulation

To simulate scenarios and test the agents, run the `simulate.py` script:

```bash
python simulate.py
```

## File Structure

- `agent_autogen.py`: Main script to run the agents.
- `agent_communication.py`: Handles RabbitMQ communication.
- `agent_tools.py`: Defines various tools and helper functions for the agents.
- `agent_llm.py`: Contains logic for running AI models and processing responses.
- `simulate.py`: Script to simulate scenarios and test the agents.
- `setup_rabbitmq.py`: Script to set up RabbitMQ queues.
- `requirements.txt`: List of Python packages required to run the project.
- `template.env`: Template for environment variables configuration.

## Configurations

### Environment Variables

Ensure that the `.env` file contains the following environment variables:

```env
RABBITMQ_USER=your_rabbitmq_user
RABBITMQ_PASS=your_rabbitmq_password
RABBITMQ_HOST=your_rabbitmq_host
RABBITMQ_PORT=5671
ASSISTANT_ID=your_assistant_id
```

### YAML Configurations

Each agent should have a corresponding YAML configuration file in the `config` directory, such as `assembly.yaml`, `quality.yaml`, and `master.yaml`. These files define the queues and prompts for each agent.

Example `assembly.yaml`:

```yaml
agent_name: assembly
queues:
  listen: "s3_ai_assembly_queue"
  listen_route: "s3_ai_assembly"
  publish: "s3_unity_assembly_queue"
  publish_route: "s3_unity_assembly"
prompts:
  system: |
    You are an assembly AI Agent named: ai_assembly. Assess incoming logs in assembly.
    ....
```

## Running the Project

1. Ensure all environment variables are set in the `.env` file.
2. Install the required Python packages.
3. Set up RabbitMQ queues if needed.
4. Run the agents.
5. Run the simulation script to test the agents.

## Contributing

Feel free to submit issues and pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
```

This `README.md` provides a comprehensive guide for setting up and running your project, ensuring users have all the necessary information to get started.