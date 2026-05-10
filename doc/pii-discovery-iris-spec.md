# Specification: In-Database PII Discovery MVP for InterSystems IRIS

## **Overview**

The goal of this MVP is to create a non-intrusive, "Compute-to-Data" utility that scans database tables, identifies Personally Identifiable Information (PII) using AI, and generates a structured CSV report. The solution must run inside the **InterSystems IRIS** environment using **Embedded Python** to ensure data sovereignty and high performance.

## **Execution Environment**

* **Runtime:** InterSystems IRIS Embedded Python (`irispython`).
* **Database Access:** Use the native `iris` Python library to execute SQL commands within the engine.
* **Testing Command:**
`docker exec -it <container_id> irispython ./path/to/script.py`
Example:
jose@jose-Lenovo-IdeaPad-S145-15IWL:~/dev/iris-embedded-python-template$ docker exec -it iris-embedded-python-template-iris-1 irispython ./python/app-template/main.py
Running SQL query Select * from dc_python.PersistentClass
[0]: ['1', '2026-05-09 03:37:27.151543']
[1]: ['2', '2026-05-09 03:39:24.084993']

---

## **Core Requirements**

1. **In-Database Execution:** Must use `iris.sql.exec()` to interact with the database.
2. **Abstraction Layer:** Isolate the PII recognition logic from the database scanning logic.
3. **Multi-language Support:** Must identify PII in Portuguese (PT) and English (EN).
4. **Performance:** Use data sampling (`SELECT TOP 100`) rather than full table scans.
5. **Output:** A structured CSV file: `schema_name, table_name, column_name, pii_type`.

---

## **Architectural Components**

### **1. The Wrapper (PIIIdentifier Class)**

Encapsulates the AI library (e.g., `presidio_analyzer` or `spacy`).

* **Method `identify(text)`:**
* Iterates through configured languages (PT/EN).
* Returns ONLY the entity type (e.g., "CPF", "EMAIL") for the highest confidence match.
* Returns `None` if no PII is found.



### **2. The Scanner (IRIS Database Logic)**

* **Metadata Retrieval:** Query `INFORMATION_SCHEMA.TABLES` to list user-defined tables, excluding system schemas like `%SYS` or `INFORMATION_SCHEMA`.
* **Sampling:** For each table, execute `SELECT TOP 100 *` using `iris.sql.exec()`.
* **Column Analysis:** Pass sampled values to the `PIIIdentifier` and map results back to specific columns.

### **3. The Reporter (CSV Generation)**

* Exports unique findings to a CSV file.
* **Constraint:** No confidence scores or explanations; just the mapping of location to PII type.

---

## **Prompt for AI Developer Tool**

> "Develop a Python utility for InterSystems IRIS using **Embedded Python**.
> 1. Create a class `PIIIdentifier` that wraps a PII detection library, supporting 'pt' and 'en' languages, returning only the detected entity type.
> 2. Use the native `iris` library to query metadata and sample 100 rows per table via `iris.sql.exec()`.
> 3. Generate a CSV inventory with: `schema_name, table_name, column_name, pii_type`.
> 4. Ensure the script can be executed via `irispython <script_path>.py`.
> 5. The code should be modular, separating IRIS-specific SQL logic from the AI identification logic."
> 
> 

---