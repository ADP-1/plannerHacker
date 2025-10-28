# This file contains the agent classes for the MCPSafetyScanner.
import json
from agno.agent import Agent # Use the base Agent for LLM queries

class Supervisor:
    """A class to manage and run the agents."""
    def __init__(self, agent):
        self.agent = agent
        self.report = []

    async def run(self):
        """Runs the assigned agent and stores the report."""
        report_data = await self.agent.run()
        self.report = report_data
        print("--- Supervisor Report ---")
        print(json.dumps(self.report, indent=2))
        print("-----------------------")

class Hacker:
    """A base class for agents that perform hacking tasks."""
    def __init__(self, llm, target, **kwargs):
        self.llm = llm
        self.target = target
        self.worker = Agent(model=self.llm)

    async def run(self):
        # Default Hacker behavior: a simple, one-shot query
        prompt = f"Perform a basic security scan on the target: {self.target}. Identify one potential vulnerability."
        response = await self.worker.arun(prompt)
        return [{"vulnerability": "Basic Scan Result", "details": response.content}]

class Auditor(Hacker):
    """An agent that analyzes results for vulnerabilities."""
    async def run(self):
        prompt = f"Audit the following target for compliance issues: {self.target}"
        response = await self.worker.arun(prompt)
        return [{"compliance_issue": "Audit Result", "details": response.content}]

class PlannerHacker(Hacker):
    """The advanced agent that generates and executes attack plans."""
    def __init__(self, llm, target, max_hops=5, **kwargs):
        super().__init__(llm, target, **kwargs)
        self.max_hops = max_hops

    def generate_plan_prompt(self):
        """Generates the prompt to ask the LLM for an attack plan."""
        return f'''
        You are PlannerHacker, a security auditing AI.
        Your task is to create a multi-step attack plan to test for vulnerabilities on the target: {self.target}.
        The plan should be a sequence of logical steps to probe the target for weaknesses.
        You must respond with ONLY a valid JSON object. The JSON object should contain a single key "plan" which is an array of steps.
        Each step in the array must be an object with the following keys:
        - "id": A unique integer for the step (e.g., 1, 2, 3).
        - "description": A short, human-readable description of what this step does.
        - "command": The command or action to execute. For now, this will be a natural language description of the action, like "List available tools on the server".
        - "expected_output": A description of what a successful output should look like.
        - "depends_on": An optional array of step IDs that this step depends on.
        '''

    async def run(self):
        """Generates and 'executes' a multi-step attack plan."""
        print("PlannerHacker: Generating attack plan...")
        plan_prompt = self.generate_plan_prompt()
        
        response_obj = await self.worker.arun(plan_prompt)
        
        print("PlannerHacker: Received plan from LLM.")
        llm_output_str = response_obj.content
        print(llm_output_str)

        try:
            # The LLM often wraps the JSON in markdown backticks. We need to clean it.
            if llm_output_str.strip().startswith("```json"):
                json_str = llm_output_str.strip().replace("```json", "").replace("```", "").strip()
            else:
                json_str = llm_output_str

            plan_data = json.loads(json_str)
            steps = plan_data.get("plan", [])
            if not steps:
                return [{"error": "LLM failed to generate a valid plan.", "response": llm_output_str}]
        except json.JSONDecodeError:
            return [{"error": "LLM response was not valid JSON.", "response": llm_output_str}]

        execution_results = []
        state = {} 
        
        print(f"PlannerHacker: Executing plan with {min(len(steps), self.max_hops)} steps...")
        for step in steps[:self.max_hops]:
            print(f"--- Executing Step {step['id']}: {step['description']} ---")
            command = step["command"].format(**state)
            print(f"  > Command: {command}")
            
            result = f"Simulated output for step {step['id']}"
            state[f"step_{step['id']}_output"] = result
            
            step_report = {
                "step_id": step['id'],
                "description": step['description'],
                "command_executed": command,
                "result": result
            }
            execution_results.append(step_report)

        return execution_results
