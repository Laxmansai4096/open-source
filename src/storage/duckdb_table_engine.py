"""DuckDB In-Memory Relational Table-RAG Engine.

Converts semi-structured contract markdown tables into real relational SQL schemas.
Executes exact SQL analytical queries for pricing tiers, SLA calculations, and spend sums,
eliminating LLM mathematical hallucinations.
"""

import re
from typing import List, Dict, Any, Optional
import duckdb


class DuckDBTableEngine:
    """Enterprise In-Memory Relational Table Engine powered by DuckDB."""

    def __init__(self):
        # In-memory DuckDB connection
        self.conn = duckdb.connect(database=":memory:")
        self.registered_tables: List[str] = []

    def ingest_markdown_table(self, table_markdown: str, table_name: str = "volume_pricing_matrix"):
        """Parses a markdown table and creates a structured DuckDB table."""
        lines = [line.strip() for line in table_markdown.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            return

        # Header row
        headers = [h.strip() for h in lines[0].split("|") if h.strip()]
        clean_headers = [re.sub(r"[^\w]", "_", h.lower()).strip("_") for h in headers]

        # Skip separator line (line[1])
        data_rows = []
        for line in lines[2:]:
            if "|" in line:
                cols = [c.strip() for c in line.split("|") if c.strip()]
                if len(cols) == len(clean_headers):
                    data_rows.append(cols)

        if not data_rows:
            return

        # Build CREATE TABLE schema
        # For our Volume Pricing Matrix:
        # Tier | Monthly Compute Units | Unit Price (USD) | Guaranteed SLA | Support Tier
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")

        create_sql = f"""
        CREATE TABLE {table_name} (
            volume_tier VARCHAR,
            min_units BIGINT,
            max_units BIGINT,
            unit_price_usd DOUBLE,
            guaranteed_sla VARCHAR,
            support_tier VARCHAR
        );
        """
        self.conn.execute(create_sql)

        # Insert parsed data
        for row in data_rows:
            tier_name = row[0]
            unit_range = row[1]
            price_str = row[2]
            sla = row[3]
            support = row[4]

            # Parse unit range (e.g. "100,001 to 500,000" or "Greater than 1,000,000")
            min_u, max_u = self._parse_range(unit_range)
            # Parse price (e.g. "$0.125 / unit")
            price_val = self._parse_price(price_str)

            self.conn.execute(
                f"INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?)",
                (tier_name, min_u, max_u, price_val, sla, support)
            )

        self.registered_tables.append(table_name)

    def _parse_range(self, range_text: str) -> tuple[int, int]:
        """Parses range text into integer min and max."""
        clean = range_text.replace(",", "")
        numbers = re.findall(r"\d+", clean)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            if "greater" in range_text.lower() or "over" in range_text.lower():
                return int(numbers[0]) + 1, 999999999999
            return 0, int(numbers[0])
        return 0, 999999999999

    def _parse_price(self, price_text: str) -> float:
        """Extracts floating point dollar value from price string."""
        match = re.search(r"(\d+\.?\d*)", price_text)
        return float(match.group(1)) if match else 0.0

    def query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Executes exact analytical SQL query and returns results as dicts."""
        cursor = self.conn.execute(sql_query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
