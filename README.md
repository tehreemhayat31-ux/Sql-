# SQL Agent Project

A simple SQL Agent that turns natural language questions into safe SQL (SELECT-only) against a local SQLite database using Groq API.

## Features
- Groq API integration with Llama 3.1 8B model
- Safety guard: executes only SELECT queries
- Working CLI: `python working_cli.py ask "your question here"`

## Setup

1. Create project environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file:
```bash
cat > .env << 'ENVEOF'
LLM_API_KEY=your_groq_api_key_here
LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
DATABASE_URL=sqlite:///./sample.db
ENVEOF
```

3. Initialize the SQLite database with sample data:
```bash
python -c 'from app.db import load_sample_data; import os; load_sample_data(os.getenv("DATABASE_URL","sqlite:///./sample.db"), "sample_data.sql"); print("DB initialized")'
```

## Usage

Ask a question:
```bash
python working_cli.py ask "List all customers"
python working_cli.py ask "Show me all orders"
python working_cli.py ask "What is the total amount spent by each customer?"
```

The CLI will:
- Inspect the current database schema
- Ask the LLM to generate SQL
- Print the SQL
- Execute it only if it is a SELECT (or WITH ... SELECT)

## Notes
- Uses Groq API with Llama 3.1 8B model
- The agent strips code fences from LLM responses
- Only a single statement is allowed, otherwise it is rejected
- Get your Groq API key from: https://console.groq.com/
