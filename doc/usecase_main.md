### Scenario: Electric Panel Assembly Process with AI and XR Assistance

**1. Start:**
- The process begins when the assembly operator starts working on version X of the electric panel assembly.

**2. XR DigitalPokaYoke Assists and Guides Operation:**
- The XR (Extended Reality) DigitalPokaYoke system assists and guides the assembly operator through the operation.

**3. Assembly Operator Performs the Assembly:**
- The assembly operator performs the assembly task following the guidance provided by the XR DigitalPokaYoke.

**4. Monitoring by Assembly Agent:**
- The assembly agent monitors the operation through the DigitalPokaYoke logs to ensure everything is proceeding correctly.

**5. Incident Management:**
    - **If an incident occurs:**
      - The assembly operator reviews the incident.
      - The assembly agent contacts the assembly operator using Teams.
      - The assembly agent determines if the incident is relevant.
          - **If the incident is relevant:**
            - A log entry is made in the operation report.
          - **If the incident is not relevant:**
            - The process continues without logging the incident.
    - **If no incident occurs:**
      - The process proceeds without interruption.

**6. Is the Assembly Finished?**
- The assembly operator checks if the assembly is completed.
    - **If the assembly is not finished:**
      - The operator continues the assembly process.
    - **If the assembly is finished:**
      - The operator delivers the electric panel to the AGV (Automated Guided Vehicle) or a logistics person.

**7. AGV/Logistics Person Transport:**
- The AGV or logistics person transports the electric panel to the Quality Inspection Station.

**8. Quality Inspection:**
- The quality inspection starts the programs defined by the quality agent (selected from a pool of programs) to reduce inspection time.
- **Issues Detected:**
    - **If any issues are detected:**
      - A log entry is made in the operation report.
    - **If no issues are detected:**
      - The process proceeds without logging.

**9. Removal and Delivery to Next Station:**
- The UR Robot (or logistics person) removes the electric panel and delivers it to the next station, which could be for transport or packing.

### Roles:
- **Assembly Operator:** Performs the actual assembly of the electric panel.
- **XR Operation Node:** Provides XR assistance and guidance to the operator.
- **Assembly Agent:** Monitors the operation and handles incident management.
- **Quality Agent:** Defines and monitors the quality inspection programs.
- **Logistics Person:** Transports the electric panel between stations.
- **Master Agent:** Oversees all operation processes, suggests optimizations, and reports to the Factory Manager.
- **Factory Manager:** Connects to any agent using XR on-site or in the virtual space and receives reports from the Master Agent.

### Additional Information:
- The Master Agent is aware of all the processes and can oversee and suggest process optimizations.
- The Factory Manager can connect to any agent using XR, either on-site or in the virtual space, and receives reports from the Master Agent.
