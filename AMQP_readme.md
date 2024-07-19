# AMQP AI Agent Scripts

## Overview

This repository contains scripts to manage AI agents that communicate via RabbitMQ using AMQP. These agents perform specific roles and communicate through specified queues. Additionally, a listener script is included to monitor and print messages from the `unity_X` queues.

## Contents

- `AMQP_ai_agent.py`: Main script for running the AI agents.
- `AMQP_ai_agent_listten.py`: Script to listen and print messages from the `unity_X` queues.
- `assemblyAgent.yaml`, `qualityAgent.yaml`, `masterAgent.yaml`: Configuration files for each AI agent.
- `.env`: Environment file containing RabbitMQ credentials.

## Prerequisites

- Python 3.7+
- RabbitMQ server
- Required Python packages (listed in `requirements.txt`)

## Setup

1. **Clone the repository**:
   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create and activate a virtual environment**:
   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory with the following content:
   ```env
   RABBITMQ_USER=your_rabbitmq_username
   RABBITMQ_PASS=your_rabbitmq_password
   RABBITMQ_HOST=your_rabbitmq_host
   RABBITMQ_PORT=your_rabbitmq_port
   ```

5. **Ensure RabbitMQ queues and exchange**:
   Make sure the RabbitMQ server has the required queues and exchanges set up. The queues should be bound to the `amq.topic` exchange with appropriate routing keys.

## Configuration

### `assemblyAgent.yaml`
```yaml
agent_name: assembly
queues:
  listen: "ai_assembly_queue"
  listen_route: "ai_assembly"
  publish: "unity_assembly_queue"
  publish_route: "unity_assembly"
  forward: "ai_quality_queue"
  forward_route: "ai_quality"
prompts:
  system: |
    You are an assembly assistant named Gemi. Assess incoming logs in assembly and send messages to the quality agent if required. You are located here: {agentlocation}. The user is located here: {userlocation}.
```

### `qualityAgent.yaml`
```yaml
agent_name: quality
queues:
  listen: "ai_quality_queue"
  listen_route: "ai_quality"
  publish: "unity_quality_queue"
  publish_route: "unity_quality"
  forward: "ai_master_queue"
  forward_route: "ai_master"
prompts:
  system: |
    You are a quality control assistant named Gemi. Configure DigiPokoyoko bot if there is a quality issue in assembly and report to the master agent. You are located here: {agentlocation}. The user is located here: {userlocation}.
```

### `masterAgent.yaml`
```yaml
agent_name: master
queues:
  listen: "ai_master_queue"
  listen_route: "ai_master"
  publish: "unity_master_queue"
  publish_route: "unity_master"
prompts:
  system: |
    You are a master assistant named Gemi. Visit and inform or ask workers in the factory about issues. You are located here: {agentlocation}. The user is located here: {userlocation}.
```

## Running the AI Agents

1. **Run the assembly Agent**:
   ```sh
   python AMQP_ai_agent.py assembly
   ```

2. **Run the Quality Agent**:
   ```sh
   python AMQP_ai_agent.py quality
   ```

3. **Run the Master Agent**:
   ```sh
   python AMQP_ai_agent.py master
   ```

Each command will start the respective agent which will listen to its designated queue, process messages, and forward or publish responses as configured.

## Running the Listener Script

To listen and print messages from the `unity_X` queues:

```sh
python AMQP_ai_agent_listten.py
```

This script will listen for new messages on the `unity_assembly_queue`, `unity_quality_queue`, and `unity_master_queue`, and print any new messages that arrive.

