"""PII report writer that deduplicates findings and outputs a CSV file.

Provides the PIIReporter class that takes raw findings from PIIScanner,
removes duplicates, and writes a structured CSV report with columns:
schema_name, table_name, column_name, pii_type, confidence.
"""

import csv


CSV_FIELDS = ["schema_name", "table_name", "column_name", "pii_type", "confidence"]

DEFAULT_OUTPUT = "/home/irisowner/dev/pii_report.csv"


class PIIReporter:
    """Deduplicates PII findings and writes them to a CSV file.

    Takes a list of finding dicts from PIIScanner.scan(), removes
    duplicate entries (same schema, table, column, type, and confidence),
    and writes the unique findings to a CSV file.
    """

    def __init__(self, output_path=DEFAULT_OUTPUT):
        """Initialize PIIReporter with the output file path.

        Args:
            output_path: File system path for the CSV report.
                Defaults to DEFAULT_OUTPUT.
        """
        self.output_path = output_path

    def deduplicate(self, findings):
        """Remove duplicate findings based on all field values.

        Two findings are considered duplicates if they share the same
        schema_name, table_name, column_name, pii_type, and confidence.

        Args:
            findings: List of finding dicts with keys matching CSV_FIELDS.

        Returns:
            List of unique finding dicts, preserving first-occurrence order.
        """
        seen = set()
        unique = []
        for f in findings:
            key = (f["schema_name"], f["table_name"], f["column_name"], f["pii_type"], f["confidence"])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def write_csv(self, findings):
        """Deduplicate findings and write them to a CSV file.

        Args:
            findings: List of finding dicts with keys matching CSV_FIELDS.

        Returns:
            The output_path of the written CSV file.
        """
        unique = self.deduplicate(findings)
        with open(self.output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(unique)
        print(f"Report written to {self.output_path} ({len(unique)} findings)")
        return self.output_path
