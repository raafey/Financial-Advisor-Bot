# Financial Research Agent

A financial research API built with **LangGraph** and **FastAPI** that routes queries, retrieves live market data, and streams back answers with citations. The agent classifies each incoming question and either searches the web for current financial data or answers directly from its knowledge base.

---

## How It Works


- **Router** — Claude Haiku classifies the query into `search`, `direct`, `greeting`, or `off_topic`
- **Search Agent** — Uses DuckDuckGo to fetch live market data, news, and financials, then synthesizes a response with numbered citations
- **Direct Answer** — Answers definitions, concepts, and general finance questions from the LLM's knowledge
- **Greeting** — Responds warmly to greetings, farewells, and small talk, then nudges the user toward finance topics
- **Off-topic** — Returns a polite rejection for non-finance queries

---

## Requirements

| Requirement | Version |
|---|---|
| Python | **3.13+** |
| Anthropic API Key | Required ([get one here](https://console.anthropic.com/)) |

### Python Dependencies

```
fastapi==0.136.1
uvicorn==0.46.0
langgraph==1.2.0
langchain==1.3.0
langchain-anthropic==1.4.3
langchain-community==0.4.1
duckduckgo-search==8.1.1
ddgs==9.14.2
python-dotenv==1.2.2
```

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd MuhammadRaafeyTariq_TestAssignment_ScalableCapital
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

- **Windows (PowerShell)**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and add your Anthropic API key:

```bash
cp .env.example .env
```

Open `.env` and set your key:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## Running with Docker

### Build the image

```bash
docker build -t financial-research-agent .
```

### Run the container

Pass your Anthropic API key via `-e`:

```bash
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_api_key_here financial-research-agent
```

The API will be available at `http://localhost:8000`.

---

## Debugging in VSCode

A launch configuration is already included at [.vscode/launch.json](.vscode/launch.json). To use it:

1. Open the project folder in VSCode (`File → Open Folder`)
2. Make sure the **Python** and **Debugpy** extensions are installed
3. Select the Python interpreter:
   - Press `Ctrl+Shift+P` to open the Command Palette
   - Type **"Python: Select Interpreter"** and press Enter
   - Choose the interpreter at `.venv\Scripts\python.exe` (it will be listed as the venv option)
4. Open the **Run and Debug** panel (`Ctrl+Shift+D`)
5. Select **"Financial Research Agent"** from the dropdown
6. Press **F5** (or click the green play button)

The debugger will launch `uvicorn` with hot reload enabled and automatically load your `.env` file. You can set breakpoints anywhere in the source — including inside the LangGraph nodes in [agent/graph.py](agent/graph.py).

> **Note:** The configuration uses `.venv/Scripts/python.exe` as the interpreter. If your virtual environment is in a different location, update the `python` field in `launch.json` accordingly.

---

## Making Requests

### Health check

```bash
curl http://localhost:8000/health
```

```json
{ "status": "online" }
```

---

### Query — streaming (default)

Streaming is enabled by default and returns tokens as Server-Sent Events.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current price of Apple stock?"}'
```

Each event looks like:

```
data: {"token": "Apple"}
data: {"token": " (AAPL)"}
data: {"token": " is currently trading..."}
...
data: [DONE]
```

---

### Query — non-streaming

Add `?stream=false` to receive the full response in one JSON object.

```bash
curl -X POST "http://localhost:8000/query?stream=false" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a P/E ratio?"}'
```

```json
{
  "answer": "A price-to-earnings (P/E) ratio is a valuation metric..."
}
```

---

### Contextual (multi-turn) chat

Pass a `session_id` string in the request body to maintain conversation history across multiple requests. The agent will remember prior messages within that session.

```bash
# First turn
curl -X POST "http://localhost:8000/query?stream=false" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Tesla'\''s current stock price?", "session_id": "user-abc-123"}'
```

```json
{
  "answer": "Tesla (TSLA) is currently trading at ...",
  "session_id": "user-abc-123"
}
```

```bash
# Follow-up turn — the agent remembers the previous question
curl -X POST "http://localhost:8000/query?stream=false" \
  -H "Content-Type: application/json" \
  -d '{"query": "How has it performed over the last month?", "session_id": "user-abc-123"}'
```

When streaming with a `session_id`, the first event confirms the session before tokens begin:

```
data: {"session_id": "user-abc-123"}
data: {"token": "Over the last month, Tesla..."}
...
data: [DONE]
```

Omitting `session_id` (or sending `null`) runs the query statelessly — no history is stored or recalled.

---

### Example queries

| Query | Route taken |
|---|---|
| `"What is Tesla's stock price today?"` | `search` |
| `"What happened in the latest Fed meeting?"` | `search` |
| `"Explain what a hedge fund is"` | `direct` |
| `"How do options work?"` | `direct` |
| `"Hello!"` / `"Thanks, bye!"` / `"What can you do?"` | `greeting` |
| `"What's the best pizza in Berlin?"` | `off_topic` |

---

## Project Structure

```
.
├── agent/
│   ├── graph.py          # LangGraph workflow definition
│   ├── prompts.py        # System prompts for each agent node
│   └── tools.py          # DuckDuckGo search tool
├── .vscode/
│   └── launch.json       # VSCode debugger configuration
├── main.py               # FastAPI app and /query endpoint
├── logger_config.py      # Logging setup
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variable template
```
