#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv
from app.agent import SQLAgent, AgentConfig
from app import db as db_utils

def main():
    if len(sys.argv) < 3:
        print("Usage: python working_cli.py ask 'your question here'")
        sys.exit(1)
    
    if sys.argv[1] != "ask":
        print("Usage: python working_cli.py ask 'your question here'")
        sys.exit(1)
    
    question = sys.argv[2]
    
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    api_url = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./sample.db")
    
    if not api_key:
        print("Error: LLM_API_KEY not found in environment")
        sys.exit(1)
    
    config = AgentConfig(api_key=api_key, api_url=api_url, model="llama-3.1-8b-instant")
    agent = SQLAgent(config=config)
    
    schema = db_utils.get_schema_text(database_url)
    sql, is_safe = agent.generate_sql(question, schema)
    
    print("Generated SQL:")
    print(sql)
    
    if not is_safe:
        print("\nRefusing to execute: only SELECT queries are allowed.")
        return
    
    try:
        columns, rows = db_utils.run_select(database_url, sql)
        if not rows:
            print("\nNo results.")
            return
        # Print a simple table
        header = " | ".join(columns)
        print("\n" + header)
        print("-" * len(header))
        for row in rows:
            line = " | ".join(str(v) for v in row)
            print(line)
    except Exception as exc:
        print(f"\nError executing query: {exc}")

if __name__ == "__main__":
    main()
