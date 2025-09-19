from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import httpx
from pydantic import BaseModel

from .db import is_select_only


class AgentConfig(BaseModel):
	api_url: str
	api_key: str
	model: str = "llama-3.1-8b-instant"
	timeout_seconds: float = 30.0


class SQLAgent:
	def __init__(self, config: AgentConfig, client: Optional[httpx.Client] = None) -> None:
		self.config = config
		self._client = client or httpx.Client(timeout=self.config.timeout_seconds)

	def _build_messages(self, question: str, schema: str) -> list[dict[str, str]]:
		instructions = (
			"You are an expert SQL generator. Given a database schema and a question, "
			"produce a single SQLite-compatible SELECT statement that answers the question. "
			"Only output the SQL code without explanations. Use table and column names exactly as given."
		)
		user = (
			f"Schema:\n{schema}\n\n"
			f"Question: {question}\n\n"
			"Return only the SQL."
		)
		return [
			{"role": "system", "content": instructions},
			{"role": "user", "content": user},
		]

	def _headers(self) -> Dict[str, str]:
		return {
			"Authorization": f"Bearer {self.config.api_key}",
			"Content-Type": "application/json",
		}

	def _body(self, messages: list[dict[str, str]]) -> Dict[str, Any]:
		return {
			"model": self.config.model,
			"messages": messages,
			"temperature": 0.0,
		}

	def generate_sql(self, question: str, schema: str) -> Tuple[str, bool]:
		messages = self._build_messages(question, schema)
		resp = self._client.post(self.config.api_url, headers=self._headers(), json=self._body(messages))
		resp.raise_for_status()
		data = resp.json()
		# OpenAI-style response extraction
		try:
			content = data["choices"][0]["message"]["content"]
		except Exception as exc:  # noqa: BLE001
			raise RuntimeError(f"Unexpected LLM response: {data}") from exc

		# Strip code fences if present
		sql = content.strip()
		if sql.startswith("```"):
			lines = [line for line in sql.splitlines() if not line.strip().startswith("```")]
			sql = "\n".join(lines).strip()

		is_safe = is_select_only(sql)
		return sql, is_safe 