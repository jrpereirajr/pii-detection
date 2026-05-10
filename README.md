# PII Discovery for InterSystems IRIS

In-database PII scanning utility that runs inside InterSystems IRIS via Embedded Python. Uses Microsoft Presidio and spaCy NLP models to identify Personally Identifiable Information across database tables and generates a structured CSV report — all without data leaving the IRIS engine.

## Overview

- **Non-intrusive** — reads metadata and samples data via SQL, no schema changes
- **Data sovereignty** — runs entirely inside the IRIS process using Embedded Python
- **Multi-language** — supports Portuguese (PT) and English (EN) PII detection
- **Sampled scanning** — analyzes up to 100 rows per table by default
- **Structured output** — CSV report: `schema_name,table_name,column_name,pii_type`

## Architecture

Three decoupled components:

| Component | File | Role |
|---|---|---|
| **PIIIdentifier** | `python/pii_discovery/pii_identifier.py` | Wraps `presidio_analyzer` with spaCy NLP models. `identify(text)` returns the highest-confidence PII entity type or `None`. No IRIS dependency. |
| **PIIScanner** | `python/pii_discovery/pii_scanner.py` | Queries `INFORMATION_SCHEMA` for user tables, samples `SELECT TOP N *` per table via `iris.sql.exec()`, passes column values to `PIIIdentifier`. Only component that uses `import iris`. |
| **PIIReporter** | `python/pii_discovery/pii_reporter.py` | Deduplicates findings and writes CSV. No confidence scores. No IRIS dependency. |

## Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Docker](https://www.docker.com/products/docker-desktop)

## Installation

Clone the repo and build the Docker image:

```bash
git clone https://github.com/intersystems-community/iris-embedded-python-template.git
cd iris-embedded-python-template
docker compose build
docker compose up -d
```

The build installs all Python dependencies including `presidio-analyzer`, spaCy, and the NLP models (`pt_core_news_sm`, `en_core_web_sm`).

## Running the Scan

### Default (current namespace, default output path)

```bash
docker compose exec iris irispython -m irisapp.pii_discovery
```

### Specify namespace and output path

```bash
docker compose exec iris irispython -m irisapp.pii_discovery -n USER -o /tmp/report.csv
```

### CLI Reference

| Flag | Short | Default | Description |
|---|---|---|---|
| `--namespace` | `-n` | Current process namespace | IRIS namespace to scan |
| `--output` | `-o` | `/home/irisowner/dev/pii_report.csv` | CSV output file path |

### Help

```bash
docker compose exec iris irispython -m irisapp.pii_discovery --help
```

## Output

The scan produces a CSV file with the following columns:

```
schema_name,table_name,column_name,pii_type
```

Example:

```csv
schema_name,table_name,column_name,pii_type
SQLUser,Patients,email,EMAIL_ADDRESS
SQLUser,Patients,ssn,US_SSN
SQLUser,Customers,phone,PHONE_NUMBER
```

## Configuration

### Excluded Schemas

System schemas are excluded to avoid scanning IRIS internals. The default set supports **wildcard patterns** using `*` suffix:

```python
EXCLUDED_SCHEMAS = {"%SYS", "INFORMATION_SCHEMA", "DOCBOOK", "HSLIB", "Ens*"}
```

| Pattern | Match type | Example exclusions |
|---|---|---|
| `%SYS` | Exact | `%SYS` |
| `INFORMATION_SCHEMA` | Exact | `INFORMATION_SCHEMA` |
| `Ens*` | Wildcard (prefix) | `Ens`, `EnsLib`, `Ens_Config`, `EnsLib_MsgRouter`, ... |

Schemas starting with `%` are always excluded.

### Sample Size

Default is 100 rows per table. Override via `PIIScanner` constructor:

```python
scanner = PIIScanner(identifier=identifier, sample_size=50)
```

### NLP Models

| Language | spaCy Model |
|---|---|
| Portuguese | `pt_core_news_sm` |
| English | `en_core_web_sm` |

## Running Tests

```bash
docker compose exec iris irispython -m pytest python/pii_discovery/tests/ -v
```

## Project Structure

```
python/pii_discovery/
├── __init__.py          Package init — exports PIIIdentifier, PIIScanner, PIIReporter
├── __main__.py          Entry point — CLI with argparse, orchestrates scan and report
├── pii_identifier.py    PIIIdentifier — wraps presidio_analyzer
├── pii_scanner.py       PIIScanner — IRIS metadata queries + sampling
├── pii_reporter.py      PIIReporter — deduplicates findings and writes CSV
└── tests/
    └── test_pii_discovery.py  Unit tests with mocked dependencies
```

## Ports

| Port | Purpose |
|---|---|
| 1972 | IRIS superserver |
| 52773 | IRIS web API (mapped to 55038) |
| 53773 | IRIS terminal |

## Credits

- [Microsoft Presidio](https://microsoft.github.io/presidio/) — PII detection engine
- [spaCy](https://spacy.io/) — NLP models for Portuguese and English
- [InterSystems IRIS Community Edition](https://hub.docker.com/r/intersystemsdc/iris-community) — Database platform with Embedded Python
