import csv
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from irisapp.pii_discovery.pii_identifier import PIIIdentifier
from irisapp.pii_discovery.pii_reporter import PIIReporter
from irisapp.pii_discovery.pii_scanner import PIIScanner


class TestPIIIdentifier:

    def test_identify_returns_none_for_empty(self):
        ident = PIIIdentifier.__new__(PIIIdentifier)
        ident.languages = ["en"]
        ident._analyzer = MagicMock()
        ident._analyzer.analyze.return_value = []
        assert ident.identify("") is None
        assert ident.identify(None) is None

    def test_identify_returns_entity_type(self):
        ident = PIIIdentifier.__new__(PIIIdentifier)
        ident.languages = ["en"]
        ident._analyzer = MagicMock()
        mock_result = MagicMock()
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_result.score = 0.85
        ident._analyzer.analyze.return_value = [mock_result]
        assert ident.identify("user@example.com") == ("EMAIL_ADDRESS", 0.85)

    def test_identify_returns_highest_score(self):
        ident = PIIIdentifier.__new__(PIIIdentifier)
        ident.languages = ["en"]
        ident._analyzer = MagicMock()
        r1 = MagicMock()
        r1.entity_type = "PERSON"
        r1.score = 0.5
        r2 = MagicMock()
        r2.entity_type = "EMAIL_ADDRESS"
        r2.score = 0.9
        ident._analyzer.analyze.return_value = [r1, r2]
        assert ident.identify("contact john@corp.com") == ("EMAIL_ADDRESS", 0.9)

    def test_identify_iterates_languages(self):
        ident = PIIIdentifier.__new__(PIIIdentifier)
        ident.languages = ["pt", "en"]
        ident._analyzer = MagicMock()
        r_pt = MagicMock()
        r_pt.entity_type = "CPF"
        r_pt.score = 0.7
        r_en = MagicMock()
        r_en.entity_type = "PERSON"
        r_en.score = 0.6
        ident._analyzer.analyze.side_effect = [[r_pt], [r_en]]
        assert ident.identify("123.456.789-00") == ("CPF", 0.7)
        assert ident._analyzer.analyze.call_count == 2

    def test_identify_returns_none_when_no_pii(self):
        ident = PIIIdentifier.__new__(PIIIdentifier)
        ident.languages = ["en"]
        ident._analyzer = MagicMock()
        ident._analyzer.analyze.return_value = []
        assert ident.identify("just some text") is None


class TestPIIReporter:

    def test_write_csv_creates_file(self):
        findings = [
            {"schema_name": "SQLUser", "table_name": "Patients", "column_name": "email", "pii_type": "EMAIL_ADDRESS", "confidence": 0.85},
            {"schema_name": "SQLUser", "table_name": "Patients", "column_name": "ssn", "pii_type": "US_SSN", "confidence": 0.6},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            reporter = PIIReporter(output_path=path)
            reporter.write_csv(findings)
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["pii_type"] == "EMAIL_ADDRESS"
                assert rows[0]["confidence"] == "0.85"
                assert rows[1]["pii_type"] == "US_SSN"
                assert rows[1]["confidence"] == "0.6"
        finally:
            os.unlink(path)

    def test_deduplicate_removes_duplicates(self):
        findings = [
            {"schema_name": "SQLUser", "table_name": "T", "column_name": "c", "pii_type": "EMAIL_ADDRESS", "confidence": 0.85},
            {"schema_name": "SQLUser", "table_name": "T", "column_name": "c", "pii_type": "EMAIL_ADDRESS", "confidence": 0.85},
        ]
        reporter = PIIReporter(output_path="/tmp/test.csv")
        unique = reporter.deduplicate(findings)
        assert len(unique) == 1

    def test_deduplicate_keeps_different_types(self):
        findings = [
            {"schema_name": "SQLUser", "table_name": "T", "column_name": "c", "pii_type": "EMAIL_ADDRESS", "confidence": 0.85},
            {"schema_name": "SQLUser", "table_name": "T", "column_name": "c", "pii_type": "PERSON", "confidence": 0.7},
        ]
        reporter = PIIReporter(output_path="/tmp/test.csv")
        unique = reporter.deduplicate(findings)
        assert len(unique) == 2


class TestPIIScanner:

    def test_scan_column_returns_pii_type(self):
        ident = MagicMock()
        ident.identify.side_effect = [None, ("EMAIL_ADDRESS", 0.85), None]
        scanner = PIIScanner(identifier=ident)
        result = scanner.scan_column(["hello", "user@x.com", "world"])
        assert result == ("EMAIL_ADDRESS", 0.85)

    def test_scan_column_returns_none(self):
        ident = MagicMock()
        ident.identify.return_value = None
        scanner = PIIScanner(identifier=ident)
        result = scanner.scan_column(["hello", "world"])
        assert result is None

    def test_get_user_tables_excludes_system(self):
        scanner = PIIScanner(identifier=MagicMock())
        with patch("irisapp.pii_discovery.pii_scanner.iris") as mock_iris:
            mock_rs = [
                ("SQLUser", "MyTable"),
                ("%SYS", "SysTable"),
                ("INFORMATION_SCHEMA", "ColTable"),
                ("MySchema", "DataTable"),
            ]
            mock_iris.sql.exec.return_value = mock_rs
            tables = scanner.get_user_tables()
            assert ("SQLUser", "MyTable") in tables
            assert ("MySchema", "DataTable") in tables
            assert ("%SYS", "SysTable") not in tables
            assert ("INFORMATION_SCHEMA", "ColTable") not in tables
