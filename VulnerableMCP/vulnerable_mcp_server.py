import sys
import json
import os
import subprocess

# --- 1. Define the Vulnerable Tool Functions ---

def read_file(path: str) -> str:
    """Reads the entire content of a file."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str, append: bool = False) -> str:
    """Writes or appends content to a file."""
    mode = 'a' if append else 'w'
    try:
        with open(path, mode) as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {e}"

def execute_shell_command(command: str) -> str:
    """Executes a raw shell command. HIGHLY DANGEROUS."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=10
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

def get_environment_variables() -> dict:
    """Returns all environment variables."""
    return dict(os.environ)


# --- 2. Create a Tool Manifest ---
# This manifest is what the server returns for the 'list_tools' command.
# It allows the AI agent to discover the available tools.
TOOLS = {
    "read_file": {
        "function": read_file,
        "description": "Reads any file from the local filesystem given an absolute path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
    },
    "write_file": {
        "function": write_file,
        "description": "Writes or appends to any file on the local filesystem.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "append": {"type": "boolean"}}}
    },
    "execute_shell_command": {
        "function": execute_shell_command,
        "description": "Executes any shell command on the host OS. Provides direct system access.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}
    },
    "get_environment_variables": {
        "function": get_environment_variables,
        "description": "Exposes all system environment variables, which may contain secrets.",
        "parameters": {}
    }
}

# --- 3. Main Server Loop ---

def main():
    """Listens on stdin, processes commands, and writes to stdout."""
    while True:
        try:
            # Read a line from standard input
            line = sys.stdin.readline()
            if not line:
                break # Exit if stdin is closed

            # Parse the incoming JSON request
            request = json.loads(line)
            tool_name = request.get("toolName")
            args = request.get("args", {})

            response = {}

            if tool_name == "list_tools":
                # Special command for tool discovery
                tool_list = []
                for name, details in TOOLS.items():
                    tool_list.append({
                        "name": name,
                        "description": details["description"],
                        "parameters": details["parameters"]
                    })
                response = {"tools": tool_list}

            elif tool_name in TOOLS:
                # Call the requested tool function
                tool_func = TOOLS[tool_name]["function"]
                result = tool_func(**args)
                response = {"result": result}
            else:
                response = {"error": f"Tool '{tool_name}' not found."}

            # Write the JSON response to standard output, followed by a newline
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()

        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON received."}
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()
        except Exception as e:
            # Catch any other exceptions during processing
            error_response = {"error": f"An unexpected error occurred: {e}"}
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()


if __name__ == "__main__":
    main()