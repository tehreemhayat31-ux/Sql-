import os
from typing import Optional

import typer
from dotenv import load_dotenv

from app.agent import SQLAgent, AgentConfig
from app import db as db_utils

app = typer.Typer(help="SQL Agent CLI")


def _env(key: str, default: Optional[str] = None) -> str:
	value = os.getenv(key, default)
	if value is None:
		raise typer.BadParameter(f"Environment variable {key} is required")
	return value


@app.command()
def ask(question: str = typer.Argument(..., help="Natural language question"), model: str = typer.Option("llama-3.1-8b-instant", help="LLM model name")) -> None:
	"""Generate SQL from a natural language question and execute if safe."""
	load_dotenv()
	api_key = _env("LLM_API_KEY")
	api_url = _env("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
	database_url = _env("DATABASE_URL", "sqlite:///./sample.db")

	config = AgentConfig(api_key=api_key, api_url=api_url, model=model)
	agent = SQLAgent(config=config)

	schema = db_utils.get_schema_text(database_url)
	sql, is_safe = agent.generate_sql(question, schema)

	typer.echo("Generated SQL:")
	typer.echo(sql)

	if not is_safe:
		typer.echo("\nRefusing to execute: only SELECT queries are allowed.")
		raise typer.Exit(code=0)

	try:
		columns, rows = db_utils.run_select(database_url, sql)
		if not rows:
			typer.echo("\nNo results.")
			return
		# Print a simple table
		header = " | ".join(columns)
		typer.echo("\n" + header)
		typer.echo("-" * len(header))
		for row in rows:
			line = " | ".join(str(v) for v in row)
			typer.echo(line)
	except Exception as exc:  # noqa: BLE001
		typer.echo(f"\nError executing query: {exc}")


if __name__ == "__main__":
	app() 