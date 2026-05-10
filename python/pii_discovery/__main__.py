"""CLI entry point for PII Discovery scan.

Orchestrates the full PII discovery pipeline: optionally populates
sample data, creates a PIIIdentifier, scans the database with
PIIScanner, and writes the CSV report with PIIReporter.

Usage:
    irispython -m irisapp.pii_discovery
    irispython -m irisapp.pii_discovery -n USER -s 50
    irispython -m irisapp.pii_discovery --populate
"""

import argparse
import iris

from .pii_identifier import PIIIdentifier
from .pii_scanner import PIIScanner
from .pii_reporter import PIIReporter
from .sample_data import populate

DEFAULT_OUTPUT = "/home/irisowner/dev/pii_report.csv"


def run(output_path=DEFAULT_OUTPUT, sample_size=100, namespace=None, init_db=False):
    """Run the PII discovery pipeline.

    Optionally switches namespace and populates sample data, then
    scans all user tables for PII and writes findings to a CSV file.

    Args:
        output_path: File system path for the CSV report.
            Defaults to DEFAULT_OUTPUT.
        sample_size: Maximum number of rows to sample per table.
            Defaults to 100.
        namespace: IRIS namespace to scan. If None, uses the
            current process namespace.
        init_db: If True, populates the sample database before
            scanning.
    """
    if namespace:
        iris.system.Process.SetNamespace(namespace)
    active_namespace = iris.system.Process.NameSpace()
    print(f"PII Discovery starting... (namespace: {active_namespace})")
    if init_db:
        populate()
    identifier = PIIIdentifier()
    scanner = PIIScanner(identifier=identifier, sample_size=sample_size)
    findings = scanner.scan()
    reporter = PIIReporter(output_path=output_path)
    reporter.write_csv(findings)
    print("PII Discovery complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PII Discovery for InterSystems IRIS")
    parser.add_argument("-n", "--namespace", default=None, help="IRIS namespace (default: current process namespace)")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="CSV output path")
    parser.add_argument("-s", "--sample-size", type=int, default=100, help="Number of rows to sample per table")
    parser.add_argument("--populate", action="store_true", help="Populate sample database before scanning")
    args = parser.parse_args()
    run(output_path=args.output, sample_size=args.sample_size, namespace=args.namespace, init_db=args.populate)
