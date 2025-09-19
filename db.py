import os
import sqlite3
from typing import Any, List, Sequence, Tuple
from urllib.parse import urlparse


def _sqlite_path_from_url(database_url: str) -> str:
	parsed = urlparse(database_url)
	# Support forms like sqlite:///./sample.db or sqlite:////absolute/path.db
	if parsed.scheme != "sqlite":
		raise ValueError("Only sqlite URLs are supported, e.g., sqlite:///./sample.db")
	path = parsed.path
	# For relative paths like /./sample.db, strip leading '/' if followed by '.'
	if path.startswith("/./"):
		path = path[1:]
	return path or "./sample.db"


def get_connection(database_url: str) -> sqlite3.Connection:
	db_path = _sqlite_path_from_url(database_url)
	os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	return conn


def load_sample_data(database_url: str, sql_path: str) -> None:
	conn = get_connection(database_url)
	with conn, open(sql_path, "r", encoding="utf-8") as f:
		conn.executescript(f.read())


def get_schema_text(database_url: str) -> str:
	conn = get_connection(database_url)
	cur = conn.cursor()
	# List tables
	cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
	tables = [row[0] for row in cur.fetchall()]
	schema_lines: List[str] = []
	for table in tables:
		cur.execute("PRAGMA table_info(" + table + ")")
		cols = cur.fetchall()
		col_defs = ", ".join(f"{c['name']} {c['type']}" for c in cols)
		schema_lines.append(f"CREATE TABLE {table} ({col_defs});")
	return "\n".join(schema_lines)


def is_select_only(sql: str) -> bool:
	candidate = sql.strip().strip(";")
	if not candidate:
		return False
	upper = candidate.upper()
	# Allow WITH ... SELECT or plain SELECT
	starts_ok = upper.startswith("SELECT ") or upper.startswith("WITH ")
	if not starts_ok:
		return False
	# Disallow dangerous keywords
	disallowed = [
		"INSERT ", "UPDATE ", "DELETE ", "DROP ", "CREATE ", "ALTER ",
		"REPLACE ", "TRUNCATE ", "ATTACH ", "DETACH ", "PRAGMA ", "VACUUM",
	]
	for word in disallowed:
		if word in upper:
			return False
	# Single statement only
	if sql.strip().count(";") > 1:
		return False
	return True


def run_select(database_url: str, sql: str, params: Sequence[Any] | None = None) -> Tuple[List[str], List[Tuple[Any, ...]]]:
	if not is_select_only(sql):
		raise ValueError("Only SELECT queries are allowed to execute.")
	conn = get_connection(database_url)
	cur = conn.cursor()
	cur.execute(sql, params or [])
	rows = cur.fetchall()
	columns = [d[0] for d in cur.description] if cur.description else []
	return columns, [tuple(row) for row in rows] 