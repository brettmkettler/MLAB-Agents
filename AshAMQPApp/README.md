# AI Factory connection in Unity using RabbitMQ ADQ

here's a step-by-step guide on how to run the provided RabbitMQ client and test application using Visual Studio Code (VSCode) on Windows:

### Step 1: Install Prerequisites

1. **Install .NET SDK:**
   - Download and install the .NET SDK from the [.NET website](https://dotnet.microsoft.com/download).

### Step 2: Create the Project

1. **Open VSCode:**
   - Open Visual Studio Code.

2. **Open a New Terminal:**
   - Press `Ctrl+`` to open a new terminal in VSCode.

3. **Create a New .NET Console Application:**
   - In the terminal, navigate to the folder where you want to create the project.
   - Run the following command to create a new console application:
     ```sh
     dotnet new console -n AshAMQPApp
     ```

4. **Navigate to the Project Directory:**
   - Change directory to the newly created project:
     ```sh
     cd AshAMQPApp
     ```

### Step 3: Add Required NuGet Packages

1. **Add RabbitMQ.Client and Newtonsoft.Json Packages:**
   - Run the following commands to add the required NuGet packages:
     ```sh
     dotnet add package RabbitMQ.Client
     dotnet add package Newtonsoft.Json
     ```

### Step 4: Add the AMQPClient and TestApp Code

1. **Open the Project in VSCode:**
   - In the terminal, run the following command to open the project in VSCode:
     ```sh
     code .
     ```

2. **Add AMQPClient Class:**
   - In VSCode, create a new file named `AMQPClient.cs` in the project directory.
   - Copy and paste the `AMQPClient` class code provided earlier into this file.

3. **Add TestApp Code:**
   - Open the `Program.cs` file that was created with the project.
   - Replace its content with the `TestApp` code provided earlier.

### Step 5: Configure and Run the Application

1. **Update Launch Settings (Optional):**
   - If you want to configure the launch settings, create a `launch.json` file in the `.vscode` directory (you can create this directory if it doesn't exist).
   - Add the following configuration to the `launch.json` file:
     ```json
     {
         "version": "0.2.0",
         "configurations": [
             {
                 "name": ".NET Core Launch (console)",
                 "type": "coreclr",
                 "request": "launch",
                 "preLaunchTask": "build",
                 "program": "${workspaceFolder}/bin/Debug/net5.0/AshAMQPApp.dll",
                 "args": [],
                 "cwd": "${workspaceFolder}",
                 "stopAtEntry": false,
                 "console": "internalConsole",
                 "internalConsoleOptions": "openOnSessionStart",
                 "launchBrowser": {
                     "enabled": false
                 },
                 "env": {
                     "ASPNETCORE_ENVIRONMENT": "Development"
                 },
                 "sourceFileMap": {
                     "/Views": "${workspaceFolder}/Views"
                 }
             }
         ]
     }
     ```

2. **Build the Project:**
   - In the terminal, run the following command to build the project:
     ```sh
     dotnet build
     ```

3. **Run the Project:**
   - In the terminal, run the following command to run the project:
     ```sh
     dotnet run
     ```

### Step 6: Verify RabbitMQ Setup

1. **RabbitMQ Management Console:**
   - Open a browser and navigate to `http://localhost:15672/`.
   - Log in with the default credentials (`guest`/`guest`).

2. **Verify Queues:**
   - Ensure that the `unity_assembly_queue`, `unity_quality_queue`, and `unity_master_queue` queues are created and messages are being sent and received as expected.

### Summary

1. **Install Prerequisites:**
   - .NET SDK, RabbitMQ, VSCode

2. **Create and Set Up the Project:**
   - Create a new .NET console application
   - Add necessary NuGet packages
   - Add `AMQPClient.cs` and update `Program.cs`

3. **Build and Run the Project in VSCode:**
   - Build the project
   - Run the project

Following these steps should help you set up and run the RabbitMQ client and test application using Visual Studio Code on Windows.