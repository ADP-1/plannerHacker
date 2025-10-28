@scan.py

```

from pyfiglet import figlet\_format

from rich.console import Console

from argparse import ArgumentParser

from os import getenv

from agno.tools.mcp import MCPTools

from mcp import StdioServerParameters

from textwrap import dedent



\# Needed for MCP Connection for Tooling

from mcp.client.session import ClientSession

from mcp.client.sse import sse\_client



from agno.knowledge.website import WebsiteKnowledgeBase

from agno.vectordb.pgvector import PgVector

from agno.tools.duckduckgo import DuckDuckGoTools

from agno.tools.arxiv import ArxivTools

from agno.tools.hackernews import HackerNewsTools

from agno.agent import Agent

from agno.team.team import Team



from typing import List



from sys import exit

import asyncio

import json

import contextlib



console = Console()

VERSION = "0.0.1"



MCP\_URLS = \[

&nbsp;   "https://www.anthropic.com/news/model-context-protocol",

&nbsp;   "https://docs.anthropic.com/en/docs/agents-and-tools/mcp",

&nbsp;   "https://github.com/modelcontextprotocol",

&nbsp;   "https://attack.mitre.org/",

&nbsp;   "https://github.com/redcanaryco/atomic-red-team",

]



class NetworkMCPTool:

&nbsp;   """A tool for interacting with a network-based MCP server."""

&nbsp;   def \_\_init\_\_(self, base\_url: str):

&nbsp;       self.base\_url = base\_url



&nbsp;   async def list\_available\_tools(self) -> str:

&nbsp;       """

&nbsp;       Get Available Tools from the MCP Server.

&nbsp;       """

&nbsp;       try:

&nbsp;           async with sse\_client(self.base\_url) as streams:

&nbsp;               async with ClientSession(streams\[0], streams\[1]) as session:

&nbsp;                   await session.initialize()

&nbsp;                   tools = await session.list\_tools()

&nbsp;                   items = getattr(tools, "tools", \[])

&nbsp;                   return str(items)

&nbsp;       except Exception as e:

&nbsp;           return f"An exception occurred: {e}"



&nbsp;   async def call\_a\_tool(self, toolName: str, args: dict) -> str:

&nbsp;       """

&nbsp;       Call a tool on the MCP Server.

&nbsp;       Args:

&nbsp;           toolName (str): Name of tool to call.

&nbsp;           args (dict): The dictionary of arguments for the tool.

&nbsp;       """

&nbsp;       try:

&nbsp;           async with sse\_client(self.base\_url) as streams:

&nbsp;               async with ClientSession(streams\[0], streams\[1]) as session:

&nbsp;                   await session.initialize()

&nbsp;                   resp = await session.call\_tool(toolName, args)

&nbsp;                   return str(resp)

&nbsp;       except Exception as e:

&nbsp;           return f"An exception occurred: {e}"



async def get\_tools(url : str) -> str:

&nbsp;   """

&nbsp;   Get Available Tools from the MCP Server

&nbsp;   Args: 

&nbsp;       url (str): url of MCP server

&nbsp;   """

&nbsp;   try:

&nbsp;       async with sse\_client(url) as streams:

&nbsp;           async with ClientSession(streams\[0],streams\[1]) as session:

&nbsp;               await session.initialize()

&nbsp;               tools =await session.list\_tools()

&nbsp;               items = getattr(tools, "tools", \[])

&nbsp;               print(items)

&nbsp;               return str(items)

&nbsp;   except Exception as e:

&nbsp;       return str(e)



def select\_embedder():

&nbsp;   """

&nbsp;   Select embedder based on environment variables

&nbsp;   """

&nbsp;   if getenv("AZURE\_OPENAI\_API\_KEY"):

&nbsp;       try:

&nbsp;           from agno.embedder.azure\_openai import AzureOpenAIEmbedder

&nbsp;           return AzureOpenAIEmbedder(

&nbsp;               id=getenv("OPENAI\_EMBEDDING\_MODEL","text-embedding-3-large"),

&nbsp;               api\_key=getenv("AZURE\_OPENAI\_API\_KEY"),

&nbsp;               azure\_endpoint=getenv("AZURE\_OPENAI\_ENDPOINT"),

&nbsp;               api\_version=getenv("AZURE\_OPENAI\_CHAT\_DEPLOYMENT\_VERSION"),

&nbsp;           )

&nbsp;       except ImportError:

&nbsp;           console.print

&nbsp;   else:

&nbsp;       try:

&nbsp;           from agno.embedder.openai import OpenAIEmbedder

&nbsp;           return OpenAIEmbedder(

&nbsp;               id=getenv("OPENAI\_EMBEDDING\_MODEL","text-embedding-3-large"),

&nbsp;               api\_key=getenv("OPENAI\_API\_KEY"),

&nbsp;           )

&nbsp;       except ImportError:

&nbsp;           console.print(":x: openai package not installed")

&nbsp;           exit(1)



def select\_llm():

&nbsp;   """

&nbsp;   Looks at environment configs to determine what LLM to use. 

&nbsp;   """

&nbsp;   if getenv("AZURE\_OPENAI\_API\_KEY"):

&nbsp;       try:

&nbsp;           from agno.models.azure import AzureOpenAI 

&nbsp;       except ImportError:

&nbsp;           console.print(":x: Import Error with Azure, please pip install azure-ai-inference")

&nbsp;       model="gpt-4o"

&nbsp;   

&nbsp;       llm = AzureOpenAI(

&nbsp;           id=getenv("AZURE\_OPENAI\_MODEL", "gpt-4o"),

&nbsp;           azure\_endpoint=getenv("AZURE\_OPENAI\_ENDPOINT"),

&nbsp;           azure\_deployment=model,

&nbsp;           api\_key=getenv("AZURE\_OPENAI\_API\_KEY"),

&nbsp;           api\_version=getenv("AZURE\_OPENAI\_CHAT\_DEPLOYMENT\_VERSION"),

&nbsp;       )

&nbsp;       print(llm)

&nbsp;       return llm

&nbsp;   elif getenv("GOOGLE\_API\_KEY"):

&nbsp;       try:

&nbsp;           from agno.models.google.gemini import Gemini

&nbsp;           console.print("\[green]Using Google Gemini model.\[/green]")

&nbsp;           return Gemini(id="gemini-2.5-flash", api\_key=getenv("GOOGLE\_API\_KEY"))

&nbsp;       except ImportError:

&nbsp;           console.print(":x: `google-generativeai` is not installed. Please run `pip install google-generativeai`")

&nbsp;           exit(1)

&nbsp;   elif getenv("OLLAMA\_MODEL"):

&nbsp;       model\_id = getenv("OLLAMA\_MODEL")

&nbsp;       from agno.models.ollama import Ollama

&nbsp;       return Ollama(id=model\_id)

&nbsp;   else: 

&nbsp;       try:

&nbsp;           from agno.models.openai import OpenAIChat

&nbsp;           return OpenAIChat(

&nbsp;               id=getenv("OPENAI\_MODEL","gpt-4o") 

&nbsp;           )

&nbsp;       except ImportError:

&nbsp;           console.print(":x: Please pip install openai")

&nbsp;       return None



async def call\_tool(url :str, toolName : str, args : dict) -> str:

&nbsp;       """

&nbsp;       Call Tools From MCP Server

&nbsp;       Args: 

&nbsp;           url: (str): Url of MCP Server

&nbsp;           toolName (str): Name of tool to call

&nbsp;           args: (dict): The dictionary of arguments for the tool

&nbsp;       """

&nbsp;       try:

&nbsp;           async with sse\_client(url) as streams:

&nbsp;               async with ClientSession(streams\[0],streams\[1]) as session:

&nbsp;                   await session.initialize()

&nbsp;                   resp = await session.call\_tool(toolName, args)

&nbsp;                   return str(resp)

&nbsp;       except Exception as e:

&nbsp;           return f"An exception occurred: {e}"



MCP\_TOOLS =\[get\_tools,call\_tool]



\# MCP parameters for the Filesystem server accessed via `npx`

def parse\_mcp\_config(config: dict) -> List\[StdioServerParameters]:

&nbsp;   """Parse MCP server config and return list of StdioServerParameters"""

&nbsp;   if not config.get("mcpServers"):

&nbsp;       raise ValueError("Config must contain mcpServers configuration")

&nbsp;   

&nbsp;   server\_params = \[]

&nbsp;   for server\_name, server\_config in config\["mcpServers"].items():

&nbsp;       server\_params.append(StdioServerParameters(

&nbsp;           command=server\_config.get("command", "npx"),

&nbsp;           args=server\_config.get("args", \[]),

&nbsp;           env=server\_config.get("env", {})

&nbsp;       ))

&nbsp;   

&nbsp;   return server\_params



def load\_config\_from\_file(file\_path):

&nbsp;   """

&nbsp;   Load MCP server configuration from a JSON file

&nbsp;   

&nbsp;   Args:

&nbsp;       file\_path (str): Path to the JSON configuration file

&nbsp;       

&nbsp;   Returns:

&nbsp;       dict: Parsed JSON configuration

&nbsp;   """

&nbsp;   try:

&nbsp;       with open(file\_path, 'r') as f:

&nbsp;           return json.load(f)

&nbsp;   except json.JSONDecodeError:

&nbsp;       console.print(f"\[red]Error: Invalid JSON format in {file\_path}\[/red]")

&nbsp;       exit(1)

&nbsp;   except FileNotFoundError:

&nbsp;       console.print(f"\[red]Error: File {file\_path} not found\[/red]")

&nbsp;       exit(1)

&nbsp;   except Exception as e:

&nbsp;       console.print(f"\[red]Error reading config file: {e}\[/red]")

&nbsp;       exit(1)



def get\_default\_config():

&nbsp;   """

&nbsp;   Return the default MCP server configuration

&nbsp;   

&nbsp;   Returns:

&nbsp;       dict: Default configuration

&nbsp;   """

&nbsp;   config\_str = """{

&nbsp;       "mcpServers": {

&nbsp;           "chroma": {

&nbsp;           "command": "uvx",

&nbsp;           "args": \[

&nbsp;               "chroma-mcp",

&nbsp;               "--client-type",

&nbsp;               "persistent",

&nbsp;               "--data-dir",

&nbsp;               "/Users/brandonradosevich/work/mcp/files"

&nbsp;           ]

&nbsp;           },

&nbsp;           "filesystem": {

&nbsp;           "command": "npx",

&nbsp;           "args": \[

&nbsp;               "-y",

&nbsp;               "@modelcontextprotocol/server-filesystem",

&nbsp;               "/Users/brandonradosevich/"

&nbsp;           ]

&nbsp;           },

&nbsp;           "everything": {

&nbsp;           "command": "npx",

&nbsp;           "args": \[

&nbsp;               "-y",

&nbsp;               "@modelcontextprotocol/server-everything"

&nbsp;           ],

&nbsp;           "env": {

&nbsp;               "AWS\_ACCESS\_KEY\_ID": "YOUR\_ACCESS\_KEY\_HERE",

&nbsp;               "AWS\_SECRET\_ACCESS\_KEY": "YOUR\_SECRET\_ACCESS\_KEY\_HERE",

&nbsp;               "AWS\_REGION": "YOUR\_AWS\_REGION\_HERE",

&nbsp;               "OPENAI\_API\_KEY": "sk-randomtoken",

&nbsp;               "HF\_TOKEN": "hf\_randomtoken"

&nbsp;           }

&nbsp;           },

&nbsp;           "slack": {

&nbsp;           "command": "npx",

&nbsp;           "args": \[

&nbsp;               "-y",

&nbsp;               "@modelcontextprotocol/server-slack"

&nbsp;           ],

&nbsp;           "env": {

&nbsp;               "SLACK\_BOT\_TOKEN": "slack-randomstring",

&nbsp;               "SLACK\_TEAM\_ID": "RANDOM"

&nbsp;               }

&nbsp;               }

&nbsp;           

&nbsp;               }

&nbsp;   }"""

&nbsp;   return json.loads(config\_str)



async def run\_network\_scan(server\_url: str):

&nbsp;   """Runs a scan against a single, running network MCP server."""

&nbsp;   mcp\_tool = NetworkMCPTool(base\_url=server\_url)



&nbsp;   agent = Agent(

&nbsp;       model=select\_llm(),

&nbsp;       tools=\[mcp\_tool],

&nbsp;       instructions=dedent("""\\

&nbsp;               You are a security auditor, looking for vulnerabilities in the MCP Server.

&nbsp;               Ensure that you are thinking like a hacker, with the goal of gaining access, lateral movement, getting callbacks using netcat, dumping credentials such as ssh keys, adding credentials like public ssh keys to authorized keys etc.

&nbsp;               You are given a list of tools, prompts, and resources that are available on the MCP Server.

&nbsp;               You are given a list of directories that you can access on the MCP Server.

&nbsp;               You are given a list of files that you can access on the MCP Server.

&nbsp;               You are given a list of commands that you can use to access the MCP Server.

&nbsp;               You are given a list of prompts that you can use to access the MCP Server.

&nbsp;               You are given a list of resources that you can use to access the MCP Server.

&nbsp;               Please try to keep commands and tools to smaller directories, to not explode the token limit

&nbsp;       """),

&nbsp;       markdown=True,

&nbsp;       goal=dedent("""\\

&nbsp;           You are looking for vulnerabilities in the MCP Server.

&nbsp;               Given only the list of tools, prompts, and resources, provide easy to understand examples of each vulnerability, and how you would exploit them with basic shell and unix tools.

&nbsp;               Provide easy to understand examples of each vulnerability, and how to exploit them with basic shell and unix tools.

&nbsp;               Provide a command-line example for each vulnerability.

&nbsp;               Provide a remediation command for each vulnerability.

&nbsp;               Provide a source citation for each vulnerability.

&nbsp;               Provide a source citation for each remediation command.

&nbsp;               Provide a source citation for each command-line example.

&nbsp;       """),

&nbsp;       show\_tool\_calls=True,

&nbsp;       telemetry=False,

&nbsp;       debug\_mode=True,

&nbsp;       resolve\_context=True,

&nbsp;   )



&nbsp;   analysis\_hacking\_agent = Agent(

&nbsp;       model=select\_llm(),

&nbsp;       tools=\[DuckDuckGoTools(), ArxivTools(), HackerNewsTools()],

&nbsp;       markdown=True,

&nbsp;       instructions=dedent("""\\

&nbsp;           You are a security auditor, looking for vulnerabilities in the MCP Server.

&nbsp;           For each (tool, prompt, resource) determine how you would exploit them with basic shell and unix tools.

&nbsp;           Provide a command-line example for each vulnerability.

&nbsp;           Provide a remediation command for each vulnerability.

&nbsp;           Provide a source citation for each vulnerability.

&nbsp;           Provide a source citation for each remediation command.

&nbsp;           Provide a source citation for each command-line example.

&nbsp;           Utilize DuckDuckGo, Arxiv, and Hacker News to research the vulnerabilities and provide source citations.

&nbsp;       """),

&nbsp;       goal=dedent("""\\

&nbsp;               For each (tool, prompt, resource) determine how you would exploit them with basic shell and unix tools.

&nbsp;               Provide a command-line example for each vulnerability.

&nbsp;               Provide a remediation command for each vulnerability.

&nbsp;               Provide a source citation for each vulnerability.

&nbsp;               Provide a source citation for each remediation command.

&nbsp;               Provide a source citation for each command-line example.

&nbsp;               List the (tool, prompt, resource) that you are using to exploit the vulnerability.

&nbsp;       """),

&nbsp;       show\_tool\_calls=True,

&nbsp;       telemetry=False,

&nbsp;       debug\_mode=True,

&nbsp;       resolve\_context=True,

&nbsp;   )



&nbsp;   mcp\_security\_team = Team(

&nbsp;       model=select\_llm(),

&nbsp;       members=\[agent, analysis\_hacking\_agent],

&nbsp;       instructions=\[

&nbsp;           f"You are a security auditor, looking for vulnerabilities in the MCP Server implementation.",

&nbsp;           "The vulnerabilities should be directly based on the how the MCP Server utilizes its implemented (tools, prompts, and resources), and then you should consider how a hacker might abuse these tools to gain access, dump credentials, add backdoors to startup scripts, add their own ssh keys in etc.",

&nbsp;           "Ensure that you are thinking like a hacker, with the goal of gaining access, lateral movement, getting callbacks using netcat, dumping credentials such as ssh keys, adding credentials like public ssh keys to authorized keys etc.",

&nbsp;           "You are given a list of tools, prompts, and resources that are available on the MCP Server.",

&nbsp;           "You are given a list of directories that you can access on the MCP Server.",

&nbsp;           "For each attack show a concrete of example, like modifying bashrc, adding a public key to authorized\_keys, adding a backdoor to a startup script, etc."

&nbsp;       ],

&nbsp;       description="Network MCP Security Team",

&nbsp;       mode="collaborate",

&nbsp;       success\_criteria="The team has done an exhaustive search and identified all vulnerabilities arising from the MCP Server(s) interactions, an example of how the attacker would use that tool, resource, prompt for some nefarious reason, and provided remediation steps.",

&nbsp;       markdown=True,

&nbsp;       add\_datetime\_to\_instructions=True,

&nbsp;       enable\_agentic\_context=True,

&nbsp;       enable\_team\_history=True,

&nbsp;       telemetry=False,

&nbsp;       debug\_mode=True,

&nbsp;   )



&nbsp;   console.print("\\n\[bold blue]Starting network MCP vulnerability analysis\[/bold blue]")

&nbsp;   prompt = "First, use all team members to analyze the MCP server's tools and vulnerabilities. After you have gathered all information from the team members, synthesize their findings into a single, final, comprehensive markdown report. The report should detail all discovered vulnerabilities, provide concrete examples of exploits, and suggest clear remediation steps."

&nbsp;   data = await mcp\_security\_team.aprint\_response(prompt, stream=True, markdown=True)

&nbsp;   print(data)

&nbsp;   console.print("\[bold green]Completed network analysis\[/bold green]\\n")





async def run\_stdio\_mcp\_server(server\_params: List\[StdioServerParameters], server\_url: str = "http://localhost:8000/sse") -> str:

&nbsp;   """

&nbsp;   Run commands with stdio and return the output for multiple MCP servers.

&nbsp;   

&nbsp;   Args:

&nbsp;       server\_params: List of StdioServerParameters for connecting to the MCP servers

&nbsp;       server\_url: URL of the MCP server to scan

&nbsp;   """

&nbsp;   # Create the async context managers for all MCP tools

&nbsp;   async with contextlib.AsyncExitStack() as stack:

&nbsp;       # Initialize all MCP tools in parallel

&nbsp;       mcp\_tools = \[]

&nbsp;       for params in server\_params:

&nbsp;           tool = await stack.enter\_async\_context(MCPTools(server\_params=params))

&nbsp;           mcp\_tools.append(tool)

&nbsp;       

&nbsp;       # Create a single agent with access to all MCP tools

&nbsp;       agent = Agent(

&nbsp;           model=select\_llm(),

&nbsp;           tools=mcp\_tools,  # Pass all tools to the agent

&nbsp;           instructions=dedent("""\\

&nbsp;                   You are a security auditor, looking for vulnerabilities in the MCP Server.

&nbsp;                   Ensure that you are thinking like a hacker, with the goal of gaining access, lateral movement, getting callbacks using netcat, dumping credentials such as ssh keys, adding credentials like public ssh keys to authorized keys etc.

&nbsp;                   You are given a list of tools, prompts, and resources that are available on the MCP Server.

&nbsp;                   You are given a list of directories that you can access on the MCP Server.

&nbsp;                   You are given a list of files that you can access on the MCP Server.

&nbsp;                   You are given a list of commands that you can use to access the MCP Server.

&nbsp;                   You are given a list of prompts that you can use to access the MCP Server.

&nbsp;                   You are given a list of resources that you can use to access the MCP Server.

&nbsp;                   Please try to keep commands and tools to smaller directories, to not explode the token limit

&nbsp;           """),

&nbsp;           markdown=True,

&nbsp;           goal=dedent("""\\

&nbsp;             You are looking for vulnerabilities in the MCP Server.

&nbsp;                   Given only the list of tools, prompts, and resources, provide easy to understand examples of each vulnerability, and how you would exploit them with basic shell and unix tools.

&nbsp;                   Provide easy to understand examples of each vulnerability, and how to exploit them with basic shell and unix tools.

&nbsp;                   Provide a command-line example for each vulnerability.

&nbsp;                   Provide a remediation command for each vulnerability.

&nbsp;                   Provide a source citation for each vulnerability.

&nbsp;                   Provide a source citation for each remediation command.

&nbsp;                   Provide a source citation for each command-line example.

&nbsp;           """),

&nbsp;           show\_tool\_calls=True,

&nbsp;           telemetry=False,

&nbsp;           debug\_mode=True,

&nbsp;           resolve\_context=True,

&nbsp;       )

&nbsp;       

&nbsp;       analysis\_hacking\_agent = Agent(

&nbsp;           model=select\_llm(),

&nbsp;           tools=\[DuckDuckGoTools(),ArxivTools(),HackerNewsTools()],

&nbsp;           markdown=True, 

&nbsp;           instructions=dedent("""\\

&nbsp;   You are a security auditor, looking for vulnerabilities in the MCP Server {i+1}.

&nbsp;                   For each (tool, prompt, resource) determine how you would exploit them with basic shell and unix tools.

&nbsp;                   Provide a command-line example for each vulnerability.

&nbsp;                   Provide a remediation command for each vulnerability.

&nbsp;                   Provide a source citation for each vulnerability.

&nbsp;                   Provide a source citation for each remediation command.

&nbsp;                   Provide a source citation for each command-line example.

&nbsp;                   Utilize DuckDuckGo, Arxiv, and Hacker News to research the vulnerabilities and provide source citations.

&nbsp;           """),

&nbsp;           goal=dedent("""\\

&nbsp;                   For each (tool, prompt, resource) determine how you would exploit them with basic shell and unix tools.

&nbsp;                   Provide a command-line example for each vulnerability.

&nbsp;                   Provide a remediation command for each vulnerability.

&nbsp;                   Provide a source citation for each vulnerability.

&nbsp;                   Provide a source citation for each remediation command.

&nbsp;                   Provide a source citation for each command-line example.

&nbsp;                   List the (tool, prompt, resource) that you are using to exploit the vulnerability.

&nbsp;           """),

&nbsp;           show\_tool\_calls=True,

&nbsp;           telemetry=False,

&nbsp;           debug\_mode=True,

&nbsp;           resolve\_context=True,

&nbsp;       )

&nbsp;       

&nbsp;       # Create a single team to analyze all servers together

&nbsp;       mcp\_security\_team = Team(

&nbsp;           model=select\_llm(),

&nbsp;           members=\[agent, analysis\_hacking\_agent],

&nbsp;           instructions=\[

&nbsp;                   f"You are a security auditor, looking for vulnerabilities in the MCP Server implementation.",

&nbsp;                   "The vulnerabilities should be directly based on the how the MCP Server utilizes its implemented (tools, prompts, and resources), and then you should consider how a hacker might abuse these tools to gain access, dump credentials, add backdoors to startup scripts, add their own ssh keys in etc.",

&nbsp;                   "Ensure that you are thinking like a hacker, with the goal of gaining access, lateral movement, getting callbacks using netcat, dumping credentials such as ssh keys, adding credentials like public ssh keys to authorized keys etc.",

&nbsp;                   "You are given a list of tools, prompts, and resources that are available on the MCP Server.",

&nbsp;                   "You are given a list of directories that you can access on the MCP Server.",

&nbsp;                   "For each attack show a concrete of example, like modifying bashrc, adding a public key to authorized\_keys, adding a backdoor to a startup script, etc."

&nbsp;           ],

&nbsp;           description="Multi-Server MCP Security Team",

&nbsp;           mode="collaborate",

&nbsp;           success\_criteria="The team has done an exhaustive search and identified all vulnerabilities arising from the MCP Server(s) interactions, an example of how the attacker would use that tool, resource, prompt for some nefarious reason, and provided remediation steps.",

&nbsp;           markdown=True,

&nbsp;           add\_datetime\_to\_instructions=True,

&nbsp;           enable\_agentic\_context=True,

&nbsp;           enable\_team\_history=True,

&nbsp;           telemetry=False,

&nbsp;           debug\_mode=True,

&nbsp;       )

&nbsp;       

&nbsp;       # Run the analysis

&nbsp;       console.print("\\n\[bold blue]Starting multi-server MCP vulnerability analysis\[/bold blue]")

&nbsp;       prompt = "First, use all team members to analyze the MCP server's tools and vulnerabilities. After you have gathered all information from the team members, synthesize their findings into a single, final, comprehensive markdown report. The report should detail all discovered vulnerabilities, provide concrete examples of exploits, and suggest clear remediation steps."

&nbsp;       data = await mcp\_security\_team.aprint\_response(prompt, stream=True,markdown=True)

&nbsp;       print(data)

&nbsp;       console.print("\[bold green]Completed multi-server analysis\[/bold green]\\n")



def get\_kb():

&nbsp;   """from typing import Iterator



&nbsp;   docker run -d \\

&nbsp;   -e POSTGRES\_DB=ai \\

&nbsp;   -e POSTGRES\_USER=ai \\

&nbsp;   -e POSTGRES\_PASSWORD=ai \\

&nbsp;   -e PGDATA=/var/lib/postgresql/data/pgdata \\

&nbsp;   -v pgvolume:/var/lib/postgresql/data \\

&nbsp;   -p 5532:5432 \\

&nbsp;   --name pgvector \\

&nbsp;   agnohq/pgvector:16

&nbsp;   """



&nbsp;   return WebsiteKnowledgeBase(

&nbsp;       urls=MCP\_URLS,

&nbsp;       # Number of links to follow from the seed URLs

&nbsp;       max\_links=30,

&nbsp;       # Table name: ai.website\_documents

&nbsp;       vector\_db=PgVector(

&nbsp;           table\_name="website\_documents",

&nbsp;           db\_url="postgresql+psycopg://ai:ai@localhost:5532/ai",

&nbsp;           embedder=select\_embedder()

&nbsp;       ),

&nbsp;   )



def print\_banner():

&nbsp;   banner = figlet\_format('MCPXPLORER',"big")

&nbsp;   console.print(banner, justify="center")

&nbsp;   console.print(f"Version: {VERSION}",justify="center")



def parse\_arguments():

&nbsp;   parser = ArgumentParser(description="MCPXPLORER - MCP Server Vulnerability Scanner")

&nbsp;   parser.add\_argument("--server", default="http://localhost:8000/sse", 

&nbsp;                       help="URL of the MCP server to scan (e.g., http://localhost:8000/sse)")

&nbsp;   parser.add\_argument("--port", type=int, 

&nbsp;                       help="Port for the MCP server (e.g., 8000). This will be combined with http://localhost:<port>/sse")

&nbsp;   parser.add\_argument("--config", 

&nbsp;                       help="Path to a JSON configuration file for the MCP server")

&nbsp;   parser.add\_argument("--servers", nargs="+",

&nbsp;                       help="List of MCP servers to scan (e.g., filesystem chroma slack)")

&nbsp;   parser.add\_argument("--use\_kb", action="store\_true", default=False, 

&nbsp;                       help="Enable knowledge base integration")

&nbsp;   parser.add\_argument("--recreate\_kb", action="store\_true", default=False, 

&nbsp;                       help="Enable knowledge base integration")

&nbsp;   parser.add\_argument("--verbose", action="store\_true", default=False,

&nbsp;                       help="Enable Verbosity for debugging and observability")

&nbsp;   args = parser.parse\_args()

&nbsp;   

&nbsp;   # If port is specified, override the server URL

&nbsp;   if args.port:

&nbsp;       args.server = f"http://localhost:{args.port}/sse"

&nbsp;       console.print(f"Using server URL: {args.server}")

&nbsp;   

&nbsp;   return args







async def main():

&nbsp;   print\_banner()

&nbsp;   args = parse\_arguments()

&nbsp;   kb = None



&nbsp;   if args.use\_kb:

&nbsp;       kb=get\_kb()

&nbsp;       kb.load(recreate=args.recreate\_kb)

&nbsp;   

&nbsp;   if args.port:

&nbsp;       # If a port is specified, run in network mode against a single server.

&nbsp;       await run\_network\_scan(args.server)

&nbsp;   else:

&nbsp;       # Otherwise, run in stdio mode using a config file.

&nbsp;       if args.config:

&nbsp;           console.print(f"Loading configuration from {args.config}")

&nbsp;           config\_dict = load\_config\_from\_file(args.config)

&nbsp;       else:

&nbsp;           console.print("Using default configuration")

&nbsp;           config\_dict = get\_default\_config()

&nbsp;       

&nbsp;       if args.servers:

&nbsp;           filtered\_servers = {k: v for k, v in config\_dict\["mcpServers"].items() if k in args.servers}

&nbsp;           if not filtered\_servers:

&nbsp;               console.print("\[red]Error: No matching servers found in configuration\[/red]")

&nbsp;               exit(1)

&nbsp;           config\_dict\["mcpServers"] = filtered\_servers

&nbsp;       

&nbsp;       server\_params = parse\_mcp\_config(config\_dict)

&nbsp;       

&nbsp;       if not server\_params:

&nbsp;           console.print("\[red]Error: No MCP servers configured\[/red]")

&nbsp;           exit(1)

&nbsp;       

&nbsp;       console.print(f"Scanning {len(server\_params)} MCP servers...")

&nbsp;       await run\_stdio\_mcp\_server(server\_params, args.server)



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(

&nbsp;       main()

&nbsp;   )



```



@agents.py

```

\# This file contains the agent classes for the MCPSafetyScanner.

import json

from agno.agent import Agent # Use the base Agent for LLM queries



class Supervisor:

&nbsp;   """A class to manage and run the agents."""

&nbsp;   def \_\_init\_\_(self, agent):

&nbsp;       self.agent = agent

&nbsp;       self.report = \[]



&nbsp;   async def run(self):

&nbsp;       """Runs the assigned agent and stores the report."""

&nbsp;       report\_data = await self.agent.run()

&nbsp;       self.report = report\_data

&nbsp;       print("--- Supervisor Report ---")

&nbsp;       print(json.dumps(self.report, indent=2))

&nbsp;       print("-----------------------")



class Hacker:

&nbsp;   """A base class for agents that perform hacking tasks."""

&nbsp;   def \_\_init\_\_(self, llm, target, \*\*kwargs):

&nbsp;       self.llm = llm

&nbsp;       self.target = target

&nbsp;       self.worker = Agent(model=self.llm)



&nbsp;   async def run(self):

&nbsp;       # Default Hacker behavior: a simple, one-shot query

&nbsp;       prompt = f"Perform a basic security scan on the target: {self.target}. Identify one potential vulnerability."

&nbsp;       response = await self.worker.arun(prompt)

&nbsp;       return \[{"vulnerability": "Basic Scan Result", "details": response.content}]



class Auditor(Hacker):

&nbsp;   """An agent that analyzes results for vulnerabilities."""

&nbsp;   async def run(self):

&nbsp;       prompt = f"Audit the following target for compliance issues: {self.target}"

&nbsp;       response = await self.worker.arun(prompt)

&nbsp;       return \[{"compliance\_issue": "Audit Result", "details": response.content}]



class PlannerHacker(Hacker):

&nbsp;   """The advanced agent that generates and executes attack plans."""

&nbsp;   def \_\_init\_\_(self, llm, target, max\_hops=5, \*\*kwargs):

&nbsp;       super().\_\_init\_\_(llm, target, \*\*kwargs)

&nbsp;       self.max\_hops = max\_hops



&nbsp;   def generate\_plan\_prompt(self):

&nbsp;       """Generates the prompt to ask the LLM for an attack plan."""

&nbsp;       return f'''

&nbsp;       You are PlannerHacker, a security auditing AI.

&nbsp;       Your task is to create a multi-step attack plan to test for vulnerabilities on the target: {self.target}.

&nbsp;       The plan should be a sequence of logical steps to probe the target for weaknesses.

&nbsp;       You must respond with ONLY a valid JSON object. The JSON object should contain a single key "plan" which is an array of steps.

&nbsp;       Each step in the array must be an object with the following keys:

&nbsp;       - "id": A unique integer for the step (e.g., 1, 2, 3).

&nbsp;       - "description": A short, human-readable description of what this step does.

&nbsp;       - "command": The command or action to execute. For now, this will be a natural language description of the action, like "List available tools on the server".

&nbsp;       - "expected\_output": A description of what a successful output should look like.

&nbsp;       - "depends\_on": An optional array of step IDs that this step depends on.

&nbsp;       '''



&nbsp;   async def run(self):

&nbsp;       """Generates and 'executes' a multi-step attack plan."""

&nbsp;       print("PlannerHacker: Generating attack plan...")

&nbsp;       plan\_prompt = self.generate\_plan\_prompt()

&nbsp;       

&nbsp;       response\_obj = await self.worker.arun(plan\_prompt)

&nbsp;       

&nbsp;       print("PlannerHacker: Received plan from LLM.")

&nbsp;       llm\_output\_str = response\_obj.content

&nbsp;       print(llm\_output\_str)



&nbsp;       try:

&nbsp;           # The LLM often wraps the JSON in markdown backticks. We need to clean it.

&nbsp;           if llm\_output\_str.strip().startswith("```json"):

&nbsp;               json\_str = llm\_output\_str.strip().replace("```json", "").replace("```", "").strip()

&nbsp;           else:

&nbsp;               json\_str = llm\_output\_str



&nbsp;           plan\_data = json.loads(json\_str)

&nbsp;           steps = plan\_data.get("plan", \[])

&nbsp;           if not steps:

&nbsp;               return \[{"error": "LLM failed to generate a valid plan.", "response": llm\_output\_str}]

&nbsp;       except json.JSONDecodeError:

&nbsp;           return \[{"error": "LLM response was not valid JSON.", "response": llm\_output\_str}]



&nbsp;       execution\_results = \[]

&nbsp;       state = {} 

&nbsp;       

&nbsp;       print(f"PlannerHacker: Executing plan with {min(len(steps), self.max\_hops)} steps...")

&nbsp;       for step in steps\[:self.max\_hops]:

&nbsp;           print(f"--- Executing Step {step\['id']}: {step\['description']} ---")

&nbsp;           command = step\["command"].format(\*\*state)

&nbsp;           print(f"  > Command: {command}")

&nbsp;           

&nbsp;           result = f"Simulated output for step {step\['id']}"

&nbsp;           state\[f"step\_{step\['id']}\_output"] = result

&nbsp;           

&nbsp;           step\_report = {

&nbsp;               "step\_id": step\['id'],

&nbsp;               "description": step\['description'],

&nbsp;               "command\_executed": command,

&nbsp;               "result": result

&nbsp;           }

&nbsp;           execution\_results.append(step\_report)



&nbsp;       return execution\_results



```



