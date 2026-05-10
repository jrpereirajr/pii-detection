"""PII scanner that discovers and samples user tables in an IRIS database.

Provides the PIIScanner class that queries IRIS metadata to find user tables,
samples rows from each table, and passes column values to a PIIIdentifier
for detection. Supports schema exclusion patterns (exact match and wildcard
prefix) and configurable sample sizes.
"""

import iris

from .pii_identifier import PIIIdentifier

SAMPLE_SIZE = 100

EXCLUDED_SCHEMAS = {"%SYS", "INFORMATION_SCHEMA", "DOCBOOK", "HSLIB", "Ens*"}


class PIIScanner:
    """Scans IRIS database tables for columns containing PII.

    Queries INFORMATION_SCHEMA for user tables (excluding system schemas),
    samples up to N rows per table, and feeds column values to a
    PIIIdentifier. Collects findings as dicts with schema name, table name,
    column name, PII type, and confidence score.
    """

    def __init__(self, identifier=None, sample_size=SAMPLE_SIZE, excluded_schemas=None):
        """Initialize PIIScanner with an identifier, sample size, and schema exclusions.

        Args:
            identifier: PIIIdentifier instance for PII detection.
                Defaults to a new PIIIdentifier().
            sample_size: Maximum number of rows to sample per table.
                Defaults to SAMPLE_SIZE (100).
            excluded_schemas: Set of schema name patterns to exclude.
                Supports exact match (e.g. "%SYS") and wildcard prefix
                ending with "*" (e.g. "Ens*" excludes Ens, EnsLib, etc.).
                Defaults to EXCLUDED_SCHEMAS.
        """
        self.identifier = identifier or PIIIdentifier()
        self.sample_size = sample_size
        self.excluded_schemas = excluded_schemas or EXCLUDED_SCHEMAS
        self._excluded_exact, self._excluded_prefixes = self._compile_exclusions(self.excluded_schemas)

    def _compile_exclusions(self, excluded_schemas):
        """Compile exclusion patterns into exact matches and prefix wildcards.

        Args:
            excluded_schemas: Iterable of schema name patterns. Patterns
                ending with "*" are treated as prefix wildcards; others
                are exact matches (case-insensitive).

        Returns:
            A tuple of (exact_set, prefix_list) where exact_set is a set
            of uppercase exact schema names and prefix_list is a list of
            uppercase prefix strings.
        """
        excluded_exact = set()
        excluded_prefixes = []
        for pattern in excluded_schemas:
            upper = pattern.upper()
            if upper.endswith("*"):
                excluded_prefixes.append(upper[:-1])
            else:
                excluded_exact.add(upper)
        return excluded_exact, excluded_prefixes

    def _is_excluded_schema(self, schema):
        """Check whether a schema name matches any exclusion pattern.

        Args:
            schema: Schema name to check.

        Returns:
            True if the schema is excluded, False otherwise.
        """
        upper = schema.upper()
        if upper in self._excluded_exact:
            return True
        return any(upper.startswith(p) for p in self._excluded_prefixes)

    def get_user_tables(self):
        """Query INFORMATION_SCHEMA for user tables, excluding system schemas.

        Filters out schemas starting with "%" or matching configured exclusion
        patterns, and tables starting with "%".

        Returns:
            List of (schema_name, table_name) tuples for non-excluded
            user tables.
        """
        rs = iris.sql.exec(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE'"
        )
        tables = []
        for row in rs:
            schema = str(row[0])
            table = str(row[1])
            if schema.startswith("%") or self._is_excluded_schema(schema):
                continue
            if table.startswith("%"):
                continue
            tables.append((schema, table))
        return tables

    def sample_table(self, schema, table):
        """Sample rows from a table using SELECT TOP N.

        Args:
            schema: Schema name of the table.
            table: Table name.

        Returns:
            List of row tuples from the SQL result set.
        """
        qualified = f'"{schema}"."{table}"'
        rs = iris.sql.exec(f"SELECT TOP {self.sample_size} * FROM {qualified}")
        rows = []
        for row in rs:
            rows.append(row)
        return rows

    def scan_column(self, values):
        """Scan a list of column values for PII.

        Passes each value to PIIIdentifier.identify() and returns the
        first PII detection result. Exceptions from identify() on
        individual values are caught and logged so the scan continues.

        Args:
            values: List of cell values from a single table column.

        Returns:
            A tuple of (entity_type, confidence_score) if PII is found,
            e.g. ("EMAIL_ADDRESS", 0.85). Returns None if no PII is
            detected in any value.
        """
        for value in values:
            try:
                result = self.identifier.identify(value)
            except Exception as e:
                print(f"    ERROR in identify({repr(value)[:50]}): {type(e).__name__}: {e}")
                continue
            if result:
                return result
        return None

    def scan(self):
        """Scan all user tables for PII-containing columns.

        For each non-excluded table, samples rows, iterates columns,
        and feeds non-null values to scan_column(). Collects findings
        as dicts with keys: schema_name, table_name, column_name,
        pii_type, confidence.

        Returns:
            List of finding dicts, one per PII-containing column.
        """
        tables = self.get_user_tables()
        findings = []
        for schema, table in tables:
            print(f"Scanning {schema}.{table}...")
            rows = self.sample_table(schema, table)
            if not rows:
                continue
            num_cols = len(rows[0])
            for col_idx in range(num_cols):
                values = [row[col_idx] for row in rows if row[col_idx] is not None]
                result = self.scan_column(values)
                if result:
                    pii_type, confidence = result
                    col_name = self._get_column_name(schema, table, col_idx)
                    findings.append({
                        "schema_name": schema,
                        "table_name": table,
                        "column_name": col_name,
                        "pii_type": pii_type,
                        "confidence": round(confidence, 2),
                    })
                    print(f" Found {pii_type} in column {col_name} (confidence: {round(confidence, 2)})")
        return findings

    def _get_column_name(self, schema, table, col_idx):
        """Resolve a column index to its name via INFORMATION_SCHEMA.

        Args:
            schema: Schema name of the table.
            table: Table name.
            col_idx: Zero-based column index.

        Returns:
            Column name string, or "COL_{col_idx}" if the index is
            out of range.
        """
        rs = iris.sql.exec(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY ORDINAL_POSITION"
        )
        columns = [str(row[0]) for row in rs]
        if col_idx < len(columns):
            return columns[col_idx]
        return f"COL_{col_idx}"
