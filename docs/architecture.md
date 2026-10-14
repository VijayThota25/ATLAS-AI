

# ATLAS AI - System Architecture



ATLAS AI is a local-first prototype for investigating synthetic payment incidents.



\## Logical component architecture



```mermaid

flowchart TD

&#x20;   UI\["Local Dashboard<br/>HTML / JavaScript"]

&#x20;   API\["Local HTTP API<br/>server.py"]

&#x20;   ENGINE\["Incident Engine<br/>engine.py"]

&#x20;   AGENT\["Agent Pipeline<br/>agent\_pipeline.py"]

&#x20;   RCA\["Root-Cause Analysis<br/>root\_cause.py"]

&#x20;   SIM\["Recovery Simulation<br/>digital\_twin.py"]

&#x20;   COMP\["Incident Comparison<br/>incident\_comparison.py"]

&#x20;   EVAL\["Report Evaluation<br/>report\_evaluator.py"]

&#x20;   ARCH\["Investigation Archive<br/>investigation\_archive.py"]

&#x20;   DB\[("SQLite Database")]

&#x20;   LG\["LangGraph<br/>Optional"]

&#x20;   SP\["SimPy<br/>Optional"]

&#x20;   OL\["Local Ollama<br/>Optional"]



&#x20;   UI <--> API

&#x20;   API --> ENGINE

&#x20;   API --> AGENT

&#x20;   API --> RCA

&#x20;   API --> SIM

&#x20;   API --> COMP

&#x20;   API --> EVAL

&#x20;   API --> ARCH



&#x20;   AGENT -.-> LG

&#x20;   AGENT -.-> OL

&#x20;   SIM -.-> SP



&#x20;   ARCH --> DB

```



The diagram represents logical components and integrations, not a mandatory execution order for every API request.



\## Investigation workflow



```mermaid

flowchart TD

&#x20;   A\["Synthetic Incident"]

&#x20;   B\["Detect"]

&#x20;   C\["Reason"]

&#x20;   D\["Recommend"]

&#x20;   E\["Human Review"]

&#x20;   F\["Synthetic Recovery Experiment"]

&#x20;   G\["Report Evaluation"]

&#x20;   H\["Explicit Archive Save"]



&#x20;   A --> B --> C --> D --> E

&#x20;   E --> F --> G --> H

```



The workflow diagram illustrates a demonstration path. Human review and archive saving are separate controls; neither executes a real payment recovery action.



\## Orchestration



LangGraph can orchestrate three deterministic stages:



\- Detect

\- Reason

\- Recommend



If LangGraph is unavailable, ATLAS AI uses sequential execution.



The reasoning stage produces unverified hypotheses rather than confirmed diagnoses.



\## Simulation



The recovery simulator uses seeded Monte Carlo trials to estimate illustrative success-rate changes.



When SimPy is installed, the system additionally simulates request-completion timing.



These are synthetic experiments, not calibrated payment-provider forecasts.



\## Persistence



ATLAS AI uses SQLite for workflow and investigation history.



Investigation archiving requires an evaluated synthetic report and an explicit save operation.



Saving a report does not execute a recovery action.



\## Safety boundaries



\- Synthetic incidents and metrics only

\- No real payment-provider integrations

\- No real payment execution

\- Human approval controls represented in simulation

\- Local HTTP server without production authentication

\- Not intended for public internet exposure

\- Not production-ready financial infrastructure
