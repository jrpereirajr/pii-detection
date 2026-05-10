"""PII Discovery package for InterSystems IRIS.

Exports the three core components and the sample data utility:
    PIIIdentifier — PII detection engine (Microsoft Presidio + spaCy)
    PIIScanner — IRIS database table scanner
    PIIReporter — CSV report writer
    populate — Sample database creation function
"""

from .pii_identifier import PIIIdentifier
from .pii_scanner import PIIScanner
from .pii_reporter import PIIReporter
from .sample_data import populate
