# 🎬 Movies Buddy Agent Workshop

An AI agent workshop demonstrating agent architecture and Model Context Protocol (MCP) integration using Google's Gemini and The TV Database (TVDB) API.

## 🏗️ Project Structure

```
movies-buddy/
├── movies_buddy/
│   ├── agent.py              # Agent configuration
│   ├── prompts.py            # System instructions (TODOS HERE)
│   └── tools/
│       ├── wikipedia_tool.py # Wikipedia summary tool
│       └── mcp_servers/
│           └── tvdb/
│               └── server.py # TVDB MCP server
├── run_agent.py              # Main entry point
└── .env                      # API keys (provided)
```

## 🔍 Key Concepts

**Agent = Instructions + Tools + Model**

- **Instructions:** System prompt that guides behavior
- **Tools:** Functions the agent can call
- **MCP:** Protocol for connecting to external services
- **Model:** The LLM (Gemini) that powers reasoning

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.12+
- API credentials (provided separately)

### Installation

**Option A: Using uv (Recommended)**
```bash
pip install uv
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

**Option B: Using pip**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### Verify Setup
```bash
python run_agent.py
# Try: "Tell me about Breaking Bad"
```

---

## 🎓 Structure

### Part 1: Agent Architecture 
Understanding how agents work through code exploration.

### Part 2: TODO #1 - Agent Personality 
Modify system prompts to add humor.

### Part 3: MCP Introduction
Learn how agents connect to external tools.

### Part 4: TODO #2 - Enable MCP Tool 
Teach the agent to use TVDB search capabilities.

---

## ✏️ TODO #1: Add Agent Personality

**File:** `movies_buddy/system_prompt.py`

**Task:** Make the agent funny when it can't find data.

**Test Query:**
```
Tell me about the TV series 'My Neighbor's Cat is Actually an Alien'
```

**Expected:** Agent makes a joke instead of boring error message.

---

## 🔧 TODO #2: Enable MCP Tool Usage

**File:** `movies_buddy/system_prompt.py`

**Task:** 
Instruct agent to use TVDB MCP Server tool to search for metadata using the provided TVDB API(movies, directors, genres, etc). And, uncomment the mcp_servers line in movies_buddy_agent.py agent creation to use the MCP server tools. 

**Test Queries:**
```
Tell me about Dune from 2021
What network aired The Sopranos?
```

**Expected:** Agent uses TVDB tool to fetch cast/metadata information.

---

## 🎉 What You'll Learn

✅ How AI agents are structured  
✅ How to modify agent behavior through prompts  
✅ What MCP is and why it matters  
✅ How to enable new agent capabilities  

---

## 🆘 Troubleshooting

**Module not found:** `pip install -e .` or `uv pip install -e .`  
**API errors:** Check `.env` file is in project root  
**Timeout:** Increase `RUN_TIMEOUT_SECONDS` in `run_agent.py`