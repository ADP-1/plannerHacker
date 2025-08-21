# Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the enhanced MCP-XPLORER Static Auditor, an extension of the open-source **mcpSafetyScanner** tool. The primary enhancement is the implementation of an **Advanced Adversarial Agent** that performs multi-step, chain-of-thought vulnerability discovery on Model Context Protocol (MCP) servers.

### 1.2 Scope

* **Product**: MCP-XPLORER Static Auditor with Advanced Adversarial Agent
* **Target Audience**: Security researchers, penetration testers, DevSecOps teams, and academic reviewers in AI security.
* **Key Features**:

  * Multi-step attack planning (chain-of-thought)
  * Comparative evaluation against baseline scanner
  * JSON transcript generation for audit trails
* **Exclusions**: Real-time (Dynamic Guardian) monitoring, automated remediation, and benchmarking suite (MCP-VulnSuite).

### 1.3 Definitions, Acronyms, and Abbreviations

* **MCP**: Model Context Protocol
* **LLM**: Large Language Model
* **API**: Application Programming Interface
* **CLI**: Command-Line Interface
* **COTS**: Commercial-Off-The-Shelf

## 2. Overall Description

### 2.1 Product Perspective

The Enhanced Static Auditor is built upon the existing **mcpSafetyScanner**. It replaces the single-step Hacker agent with a chain-of-thought multi-step planner, enabling deeper vulnerability discovery.

### 2.2 Product Functions

* Parse MCP server configurations from JSON
* Initialize MCP server connections
* Perform tool enumeration
* Execute chain-of-thought attack planning (n hops)
* Invoke ordered tool calls and collect responses
* Generate human-readable and machine-readable reports

### 2.3 User Characteristics

* Proficient with Python 3.11+
* Familiar with MCP servers and CLI tools
* Understand basic cybersecurity concepts

### 2.4 Constraints

* Must run offline (no real-time callbacks)
* Limit chain-of-thought hops to configurable maximum (default: 3)
* Compatible with Python 3.11+, Linux/MacOS environments

### 2.5 Assumptions and Dependencies

* Availability of `mcpSafetyScanner` dependencies (agno, mcp-client, etc.)
* Access to MCP servers via stdio (e.g., `npx ...`)
* Valid API keys for OpenAI or alternative LLM

## 3. Specific Requirements

### 3.1 Functional Requirements

#### FR-1: Configuration Loading

* **Description**: Load and validate `config.json` for MCP servers.
* **Input**: Path to JSON file
* **Output**: List of `StdioServerParameters`
* **Error Handling**: Exit with message on invalid/missing config

#### FR-2: Tool Enumeration

* **Description**: Query each MCP server for available tools
* **Input**: Server URL list
* **Output**: `{tool_list}` for each server

#### FR-3: Chain-of-Thought Prompt Generation

* **Description**: Generate a prompt that instructs the Hacker agent to produce a numbered multi-step plan.
* **Parameters**:

  * `max_hops` (int, default=3)
  * `few_shot_examples` (list of strings)
* **Output**: Formatted prompt string inserted into Agent instantiation

#### FR-4: Attack Plan Execution

* **Description**: Execute each step sequentially via `call_tool`
* **Input**: Numbered plan, tool calls
* **Output**: JSON responses and intermediate logs
* **Error Handling**: Halt on critical failure, log partial results

#### FR-5: Report Generation

* **Description**: Synthesize findings into a final audit report
* **Formats**: Markdown console output + JSON transcript file
* **Content**:

  * Plan steps
  * Tool call results
  * Discovered vulnerabilities
  * Recommendations (future work placeholder)

### 3.2 Non-Functional Requirements

#### NFR-1: Performance

* **Description**: Complete a 3-hop scan on a minimal test server within 30 seconds

#### NFR-2: Usability

* **Description**: Clear CLI flags (`--config`, `--hops`, `--output`)

#### NFR-3: Maintainability

* **Description**: Modular code with clear separation of prompt templates

#### NFR-4: Portability

* **Description**: Support Python 3.11+ on Linux and MacOS

### 3.3 Interface Requirements

#### 3.3.1 User Interfaces

* CLI: `python scan.py --config example_config.json --hops 3 --output report.md`

#### 3.3.2 Software Interfaces

* **MCP Client**: `mcp.client.session.ClientSession`
* **LLM Interface**: OpenAIChat or AzureOpenAI via `agno.models`

#### 3.3.3 Data Formats

* **Input**: JSON (`config.json`)
* **Output**: Markdown (`.md`), JSON transcript

## 4. Appendix

* **References**:

  * MCP specification: [https://docs.anthropic.com/en/docs/agents-and-tools/mcp](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
  * mcpSafetyScanner GitHub repository
