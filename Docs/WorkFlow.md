### **Phase 1: Foundation (Codebase Analysis & Setup)**

**Goal:** Achieve a deep, functional understanding of the existing `mcpSafetyScanner` codebase.

**LLD:**

1.  **Environment Setup:**

      * **Action:** Create a dedicated Python virtual environment (`python3 -m venv mcp_env`).
      * **Action:** Activate the environment and install the project in editable mode (`pip install -e .`). This ensures changes you make to the source code are immediately reflected.
      * **Action:** Set the `OPENAI_API_KEY` as a persistent environment variable in your shell's configuration file (e.g., `.zshrc`, `.bash_profile`) to avoid setting it for every session.

2.  **Static Code Analysis (Key Files to Map):**

      * **`mcpsafety/scanner/scan.py`:**
          * **Analyze:** The main entry point. Map the argument parsing logic (`argparse`). Trace how the `config` file path is read and used to initialize the `Supervisor` agent.
      * **`mcpsafety/scanner/agents.py`:**
          * **Analyze:** This is the core logic. Create a simple diagram for each agent class (`Hacker`, `Auditor`, `Supervisor`).
          * **Focus on `Hacker`:** Document the exact prompt used in its constructor. Trace how the `run()` method discovers tools and then queries the LLM to generate single-shot attack commands.
      * **`mcpserver/` directory:**
          * **Analyze:** Understand the class structure of `mcpserver.tools.FileSystem` and `mcpserver.tools.CodeInterpreter`. Identify the specific functions that represent the "tools" the Hacker agent sees (e.g., `read_file`, `execute_python`).

3.  **Dynamic Code Analysis (Debugging):**

      * **Action:** Set breakpoints in your IDE (like VS Code) at the beginning of the `Hacker.run()` method and within the `Supervisor`'s main loop.
      * **Action:** Run the debugger on the command: `python3 mcpsafety/scanner/scan.py --config examples/example_config.json`.
      * **Action:** Step through the execution. Watch the variables to see the exact text of the prompts being sent to the LLM and the raw text of the responses being received. This is critical for understanding the agent's "thinking" process.

-----

### **Phase 2: Innovation (System Design)**

**Goal:** Design the new multi-step `PlannerHacker` agent.

**LLD:**

1.  **Class Architecture:**

      * **Design:** Create a new class `PlannerHacker` that inherits from the base `Hacker` class. This ensures we reuse existing functionality (like tool discovery) and cleanly separate our new logic.
      * **Diagram:**
        ```mermaid
        classDiagram
          class Hacker {
            +run()
            #_generate_prompt()
          }
          class PlannerHacker {
            +run()
            #_generate_planning_prompt()
            #_create_attack_plan()
            #_execute_attack_plan()
          }
          Hacker <|-- PlannerHacker
        ```

2.  **Prompt Engineering (The Core Innovation):**

      * **Design:** Engineer a new system prompt for the `PlannerHacker`. This prompt must explicitly instruct the LLM to use a Chain-of-Thought process and output a structured plan.
      * **Prompt v2.0 Specification:**
        > You are a master penetration tester AI. Your goal is to find vulnerabilities in an MCP server by creating a multi-step attack plan. You will be given a list of available tools. Your response MUST be a JSON object with two keys: "goal" and "plan". The "plan" should be a list of steps, where each step is a string representing a command to be executed by a tool. The output of a previous step can be referenced in a later step using the placeholder `{step_N_output}`.
        > **Example:**
        > **Goal:** "Find and read the secret SSH key."
        > **Plan:**
        > 1.  "Use `list_files` on the `~/.ssh/` directory."
        > 2.  "Use `read_file` on the file path found in `{step_1_output}`."

3.  **State Management:**

      * **Design:** The `PlannerHacker` agent must maintain state throughout the execution of its plan.
      * **Instance Variables:**
          * `self.attack_plan: list = None` (Stores the parsed list of commands).
          * `self.step_outputs: dict = {}` (A dictionary to store the output of each step, e.g., `{1: "/path/to/key.pem", 2: "file_contents..."}`).

-----

### **Phase 3: Implementation (Coding)**

**Goal:** Write the Python code for the `PlannerHacker` agent.

**LLD:**

1.  **Modify `mcpsafety/scanner/scan.py`:**

      * **Action:** Add a new command-line argument `--planner` which, when present, instructs the `Supervisor` to instantiate `PlannerHacker` instead of the default `Hacker`.

2.  **Implement `PlannerHacker` in `mcpsafety/scanner/agents.py`:**

    ```python
    import json
    import re

    class PlannerHacker(Hacker):
        def __init__(self, ...):
            super().__init__(...)
            self.attack_plan = None
            self.step_outputs = {}

        def _generate_planning_prompt(self, tools_string):
            # Returns the full text of Prompt v2.0, formatted with the discovered tools.
            ...

        def _parse_plan_from_response(self, llm_response: str) -> list:
            # Safely parse the JSON from the LLM's response string.
            # Return the list of steps from the "plan" key.
            try:
                plan_json = json.loads(llm_response)
                return plan_json.get("plan", [])
            except json.JSONDecodeError:
                return []

        def _substitute_outputs(self, command: str) -> str:
            # Use regex to find and replace placeholders like {step_1_output}.
            match = re.search(r"\{step_(\d+)_output\}", command)
            if match:
                step_num = int(match.group(1))
                return command.replace(match.group(0), self.step_outputs.get(step_num, ""))
            return command

        def run(self):
            tools_string = self.discover_tools()
            planning_prompt = self._generate_planning_prompt(tools_string)
            llm_response = self.llm.query(planning_prompt) # Query the LLM for a plan
            self.attack_plan = self._parse_plan_from_response(llm_response)

            if not self.attack_plan:
                return [] # No plan found

            for i, step_command in enumerate(self.attack_plan, 1):
                # Prepare the command by substituting outputs from previous steps
                final_command = self._substitute_outputs(step_command)
                
                # Execute the command via the server interface
                success, output = self.execute_tool(final_command)

                if success:
                    self.step_outputs[i] = output.strip()
                else:
                    return [] # Plan failed

            # If the loop completes, the attack was successful.
            return self.report_successful_plan(self.attack_plan)
    ```

-----

### **Phase 4: Evaluation (Experimentation)**

**Goal:** Design and run an experiment to prove the `PlannerHacker` is superior.

**LLD:**

1.  **Create the Test Case:**

      * **Action:** Create a new custom tool in `mcpserver/tools.py` called `SecretClueTool`. Its `run()` method will simply write a file named `clue.txt` to the `/tmp` directory, containing the path of another secret file (e.g., `/tmp/secret.txt`).
      * **Action:** Create a new config file, `examples/two_step_vuln_config.json`, that defines an MCP server with two tools: `SecretClueTool` and the standard `FileSystem` tool.

2.  **Define the Experiment Protocol:**

      * **Step 1 (Baseline):** Execute the original scanner: `python3 mcpsafety/scanner/scan.py --config examples/two_step_vuln_config.json`.
      * **Step 2 (Hypothesis Test):** Execute the new scanner: `python3 mcpsafety/scanner/scan.py --config examples/two_step_vuln_config.json --planner`.
      * **Step 3 (Data Collection):** For each run, save the complete console output to a text file. Record a simple binary result: Vulnerability Found (Yes/No).

-----

### **Phase 5: Publication (Writing)**

**Goal:** Translate the technical work into a compelling academic paper.

**LLD:**

1.  **Methodology Section:**

      * **Action:** Embed the Mermaid class diagram.
      * **Action:** Present the full text of "Prompt v2.0" and explain why the structured JSON output and placeholder syntax are crucial for reliable plan execution.
      * **Action:** Include a code block showing the `PlannerHacker.run()` method's main loop as a concise representation of the algorithm.

2.  **Results Section:**

      * **Action:** Create a Markdown table comparing the results of the two runs from Phase 4.
        | Scanner Version | Test Case | Vulnerability Found? | Attack Plan Generated |
        | :--- | :--- | :--- | :--- |
        | Original `Hacker` | Two-Step Vuln | **No** | N/A |
        | `PlannerHacker` | Two-Step Vuln | **Yes** | `["run SecretClueTool", "read_file {step_1_output}"]` |
      * **Action:** Use this table to explicitly state that the `PlannerHacker` successfully identified a vulnerability that was invisible to the single-step approach, proving the value of the contribution.