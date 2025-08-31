# MCP Safety Scanner

This project is a security scanner for MCP (Morpheus Cyber Protector) servers. It scans for vulnerabilities and generates a report.

## Features

- Scans for common vulnerabilities
- Generates a markdown report
- Configurable scan settings

## 🚀 Running the Project (Current Status)

Right now, the scanner connects manually to an MCP server.  
Here’s how to run it:

Open Terminal A (server):
```bash
# start an HTTP/SSE MCP server (server-everything streamableHttp)
npx -y @modelcontextprotocol/server-everything streamableHttp --port 3001
# Expect: "MCP Streamable HTTP Server listening on port 3001"
```


Open Terminal B (scanner, with your .venv active):

``` bash
python mcpsafety/scanner/scan.py --port 3001
```
```