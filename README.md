# MCP Safety Scanner

This project is a security scanner for MCP (Morpheus Cyber Protector) servers. It scans for vulnerabilities and generates a report.

## Features

- Scans for common vulnerabilities
- Generates a markdown report
- Configurable scan settings

## 🚀 Running the Project (Current Status)

Right now, the scanner connects manually to an MCP server.  
Here’s how to run it:

### 1. Start the MCP Server
In a new terminal, run:

```bash
npx -y @modelcontextprotocol/server-everything streamableHttp --port 8000
```
```bash 
python mcpsafety/scanner/scan.py --port 8000
```