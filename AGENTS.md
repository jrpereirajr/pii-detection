# AGENTS.md — Guidance for Agentic Coding Agents

## Project Overview

In-Database PII Discovery utility for InterSystems IRIS. Scans database tables, identifies
Personally Identifiable Information using AI (Microsoft Presidio), and generates a structured
CSV report. Runs inside IRIS via Embedded Python to ensure data sovereignty.

- **Languages:** Python (Embedded Python), ObjectScript
- **Platform:** InterSystems IRIS Community Edition (Docker)
- **PII library:** `presidio_analyzer` with spaCy NLP models (`pt_core_news_sm`, `en_core_web_sm`)
- **Supported languages:** Portuguese (PT) and English (EN)
- **Python packages:** pip3 via `requirements.txt`
- **IRIS packages:** ZPM/IPM via `module.xml` (package name: `iris-python-template`)
- **Working namespace:** `IRISAPP`, SuperUser password: `SYS`

## Repository Structure

```
python/                       Python modules (live-mounted at /usr/irissys/mgr/python/irisapp/)
  pii_discovery/              PII Discovery app (importable as irisapp.pii_discovery)
    __init__.py               Package init — exports PIIIdentifier, PIIScanner, PIIReporter
    __main__.py               Entry point — orchestrates scan and report generation
    pii_identifier.py         Wrapper — PIIIdentifier class wrapping presidio_analyzer
    pii_scanner.py            Scanner — IRIS metadata queries + sampling via iris.sql.exec()
    pii_reporter.py           Reporter — deduplicates findings and writes CSV
    tests/                    pytest tests for PIIIdentifier, PIIScanner, PIIReporter
  irisapp.py                  Legacy demo: iris.cls, iris.sql.exec, iris.gref
  helloworld.py               Simple hello-world module
  sample.py                   Utility functions (hello, meanage, dividezero)
  flask/app.py                Flask REST API
  app-template/               Template with SQL helper
src/dc/python/                ObjectScript classes (require Docker rebuild to update)
  HelloWorld.cls              Calls Python from ObjectScript
  ObjectScript.cls            Pure ObjectScript classmethod
  PersistentClass.cls         %Persistent class with ObjectScript + Python methods
  test.cls                    Test class with Python exception-handling demos
data/                         Sample data (titanic.csv) loaded at build time
doc/                          Specifications
  pii-discovery-iris-spec.md  PII Discovery MVP specification
module.xml                    ZPM/IPM package definition (SourcesRoot=src)
merge.cpf                     IRIS config: creates IRISAPP namespace/databases
iris.script                   ObjectScript init script (runs during Docker build)
```

## Build and Run

```bash
docker compose build # Build Docker image
docker compose build --no-cache --progress=plain # Full rebuild (needed after requirements.txt or Dockerfile changes)
docker compose up -d # Start container
docker compose down # Stop container
docker system prune -f                            # Clean up Docker disk space

# Open IRIS terminal
docker compose exec iris iris session iris -U IRISAPP

# Run the PII Discovery scan (primary app)
docker compose exec iris irispython -m irisapp.pii_discovery

# Run legacy demo script
docker compose exec iris irispython /home/irisowner/dev/python/irisapp.py

# Run Flask app inside container
docker compose exec iris irispython /home/irisowner/dev/python/flask/app.py
```

## Test Commands

### pytest (PII Discovery unit tests)

```bash
# Run all pytest tests (inside container)
docker compose exec iris irispython -m pytest python/pii_discovery/tests/ -v

# Run a single test file
docker compose exec iris irispython -m pytest python/pii_discovery/tests/test_pii_discovery.py -v

# Run a single test method
docker compose exec iris irispython -m pytest python/pii_discovery/tests/test_pii_discovery.py::TestPIIIdentifier::test_identify_returns_entity_type -v
```

### ZPM (IRIS integration tests)

```bash
# Run all ZPM tests (inside IRIS terminal)
zpm
load /home/irisowner/dev
test iris-python-template

# Run all ZPM tests in one line
iris session iris -U IRISAPP '##class(%ZPM.PackageManager).Shell("test iris-python-template -v -only",1,1)'

# Run a single ZPM test method
zpm
load /home/irisowner/dev
test iris-python-template -only -t TestMethodName

# CI: build with TESTS=1
docker compose build --build-arg TESTS=1
```

## Linting and Formatting

No Python linting or formatting tools are configured (no ruff, black, flake8, isort,
pre-commit, or pyproject.toml). Run `python -m py_compile <file>` to check syntax.

ObjectScript quality: CI runs an external check via `.github/workflows/objectscript-quality.yml`.

## Code Style — Python

- **Imports:** Standard library → third-party → `import iris`. Use relative imports
  within `pii_discovery/` (e.g., `from .pii_identifier import PIIIdentifier`).
- **Indentation:** 4 spaces.
- **Naming:** `snake_case` for functions and variables (e.g., `create_rec`, `mean_age`).
  `PascalCase` for classes (e.g., `PIIIdentifier`, `PIIScanner`).
- **Type annotations:** Not used. Do not add unless requested.
- **Docstrings:** Not used. Method descriptions go in ObjectScript `///` comments only.
- **Spacing around `=`:** Inconsistent — `obj=iris.cls(...)` (no spaces) is common for
  IRIS API calls; regular assignments sometimes use spaces. Match surrounding code.
- **String formatting:** f-strings (e.g., `f"key={key}: {value}"`).
- **No comments** unless explicitly requested.

## Code Style — ObjectScript

- **Class format:** `Class dc.python.ClassName Extends BaseClass { ... }`
- **Package:** `dc.python`
- **Methods:** `ClassMethod Name(args) As %Status { ... }` or with `[ Language = python ]`
- **Doc comments:** `/// Description` on the line before the method/property.
- **Error handling:** `%Status` pattern — `set sc=$$$OK`, check `sc`, return it.
  Try/catch: `#dim ex as %Exception.PythonException`.
- **Capitalization:** Prefer lowercase `set`/`write`/`return` (majority style).

## Code Style — Embedded Python in .cls files

- Imports at top of method body: `import iris`, `import traceback`, etc.
- Use `__name__` to reference the current class: `iris.cls(__name__)._New()`.
- Error handling: Catch Python exceptions → convert to
  `iris.cls("%Exception.General")._New(error_name, 2603, iris_error)` → call `.Log()`.
  Error code `2603` = standard Python exception code. `iris_error` format:
  `func_name+line_no^filename`.

## PII Discovery Architecture

Three decoupled components per the spec (`doc/pii-discovery-iris-spec.md`):

1. **PIIIdentifier** (`pii_identifier.py`) — Wraps `presidio_analyzer`. No IRIS dependency.
   `identify(text)` iterates PT+EN analyzers, returns the highest-confidence entity type
   (e.g., `"EMAIL_ADDRESS"`, `"CPF"`) or `None`.

2. **PIIScanner** (`pii_scanner.py`) — The only component that uses `import iris`.
   Queries `INFORMATION_SCHEMA.TABLES` for user tables (excluding system schemas),
   samples `SELECT TOP 100 *` per table, passes column values to `PIIIdentifier`,
   collects findings as `[{schema_name, table_name, column_name, pii_type}]`.

3. **PIIReporter** (`pii_reporter.py`) — Deduplicates findings and writes CSV:
   `schema_name,table_name,column_name,pii_type`. No confidence scores.

## IRIS Python API Quick Reference

```python
import iris
iris.cls("Package.Class").Method()              # Call class method
obj = iris.cls("Package.Class")._New()          # Create persistent object
obj._Save(); id = obj._Id()                     # Save and get ID
obj = iris.cls("Package.Class")._OpenId(id)     # Open by ID
iris.cls("Package.Class")._ExistsId(id)         # Check existence
rs = iris.sql.exec("SELECT * FROM table")       # Execute SQL
for idx, row in enumerate(rs): print(row)       # Iterate SQL result
gl = iris.gref("^GlobalName")                   # Access global
gl.set([key], value)                            # Set global node
for key, value in gl.query([]): print(key)      # Iterate global
key = gl.order([key])                           # Next subscript
iris.system.Process.SetNamespace("IRISAPP")     # Set namespace
```

## Key Conventions

- **Namespace:** Always `IRISAPP`.
- **Docker-first:** All dev/testing in Docker. `python/` is live-mounted; `src/` and
  `requirements.txt`/`Dockerfile` changes require rebuild (`docker compose build`).
- **Volume mounts:** `./` → `/home/irisowner/dev`, `./python` → `/usr/irissys/mgr/python/irisapp:rw`.
- **Python module resolution:** Files in `python/` are importable as `irisapp.module_name`.
  The PII app is `irisapp.pii_discovery`.
- **ObjectScript→Python:** `##class(%SYS.Python).Import("module_name")`.
- **Persistent classes:** Use `Extends %Persistent` with a `Storage Default` block.
- **module.xml:** Version auto-bumped by CI on push to main/master. Don't edit manually.
- **Ports:** 1972 (superserver), 52773→55038 (web API), 53773 (IRIS), 5000→55030 (Flask).
- **PII CSV output:** Default path `/home/irisowner/dev/pii_report.csv` (mounted to host `./`).
