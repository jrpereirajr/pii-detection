# Discovering PII Inside InterSystems IRIS: A Compute-to-Data Approach with Embedded Python

Data privacy regulations such as GDPR, LGPD, and HIPAA demand that organizations know exactly where Personally Identifiable Information (PII) lives inside their databases. Yet in practice, most teams rely on manual inventories, tribal knowledge, or external scanning tools that require data to leave the database engine — a process that itself creates privacy and security risks.

This article presents an MVP that takes a different approach: it runs PII detection **inside** InterSystems IRIS using Embedded Python, analyzing data where it lives and never exporting it to an external process. The result is a lightweight, non-intrusive utility that scans your tables, identifies PII using AI, and produces a structured CSV report — all without data ever leaving the IRIS process.

## The Problem: PII You Don't Know You Have

Organizations today face a painful blind spot. A typical IRIS instance may contain hundreds of tables across dozens of schemas, some holding decades of accumulated data. Columns named `ContactInfo`, `Notes`, or `Description` might silently contain social security numbers, email addresses, or government IDs — sometimes intentionally, sometimes as a side effect of free-text fields that capture whatever users type in.

Traditional approaches to PII discovery share a common flaw: they require data extraction. You export samples, send them to an external service, or pipe them through a standalone tool. Every step in that pipeline is an additional attack surface and a potential compliance violation.

The principle of **data sovereignty** — keeping data within its jurisdiction and under controlled access — suggests a better path: bring the analysis to the data, not the data to the analysis.

This is not just a technical preference; it is a governance requirement. Under GDPR, any transfer of personal data to a new processor triggers obligations around data processing agreements, cross-border restrictions, and breach notification. Under LGPD, Brazil's data protection law, the same principle applies with additional requirements around data officer appointment and impact assessments. HIPAA's Security Rule mandates that electronic protected health information (ePHI) be safeguarded during any transmission. Running the scan inside the database engine eliminates the transmission step entirely, simplifying compliance and reducing risk.

## Architecture: Three Decoupled Components

The utility follows a simple but deliberate separation of concerns. Three independent components cooperate in a pipeline:

```
PIIScanner  →  PIIIdentifier  →  PIIReporter
(database)     (AI detection)     (reporting)
```

**PIIIdentifier** — Wraps the AI detection library. It has zero knowledge of IRIS, SQL, or database schemas. Its single method, `identify(text)`, takes a string and returns the highest-confidence PII entity type (e.g., `"EMAIL_ADDRESS"`, `"PERSON"`, `"CPF"`) or `None`. This isolation means the detection logic can be tested, swapped, or upgraded without touching the database layer.

**PIIScanner** — The only component that interacts with IRIS. It queries `INFORMATION_SCHEMA.TABLES` to discover user tables, samples up to N rows per table via `SELECT TOP N *`, feeds each column's values to the identifier, and collects findings. It respects schema exclusion patterns (exact match and wildcard prefix like `"Ens*"`) and lets the caller configure the sample size.

**PIIReporter** — Deduplicates findings and writes a CSV with four columns: `schema_name, table_name, column_name, pii_type`. No confidence scores, no explanations — just a clean inventory of where PII was detected.

This separation is not accidental. It means the identifier could be replaced with a more powerful model tomorrow without changing a single line of scanner or reporter code.

## Microsoft Presidio and spaCy: The Detection Engine

The PIIIdentifier is powered by [Microsoft Presidio](https://microsoft.github.io/presidio/), an open-source data protection and de-identification framework. Presidio's analyzer combines two detection strategies:

1. **Pattern-based recognizers** — Regular expressions and checksum validators for structured identifiers: email addresses, phone numbers, SSNs, credit card numbers, CPF, and dozens more. These recognizers are deterministic and language-agnostic.

2. **NLP-based recognizers** — Machine learning models that detect entity types like PERSON, LOCATION, and ORGANIZATION from natural language context. This is where spaCy comes in.

The utility configures Presidio with two spaCy models:

- `en_core_web_sm` — English small model (~12 MB)
- `pt_core_news_sm` — Portuguese small model (~13 MB)

Each row of data is analyzed against both languages, and the highest-confidence result wins. This bilingual approach is particularly relevant for organizations operating in Latin America, where databases commonly mix Portuguese and English content — for instance, a Brazilian healthcare system with patient records in Portuguese and system metadata in English.

For every text input, the `identify()` method iterates through both language analyzers, collects all results, and returns the entity type with the highest confidence score:

```python
def identify(self, text):
    best_entity = None
    best_score = 0.0
    for lang in self.languages:
        results = self._analyzer.analyze(text=text, language=lang)
        for result in results:
            if result.score > best_score:
                best_score = result.score
                best_entity = result.entity_type
    return best_entity
```

This design means a Brazilian CPF mentioned in an English sentence will still be caught by the PT analyzer's pattern recognizer, even though the surrounding text is English.

## Running Inside IRIS: The Embedded Python Advantage

The entire utility runs as a Python module inside the IRIS process via `irispython`. No external API calls, no data exports, no network transfers. The scanner uses `iris.sql.exec()` — IRIS's native Python SQL interface — to query metadata and sample data directly within the engine.

```bash
irispython -m irisapp.pii_discovery
```

A single command starts the scan. The output is a CSV file written to the mounted volume, immediately available on the host machine.

The utility also integrates with IRIS's built-in Task Scheduler. A `%SYS.Task.Definition` subclass (`PIIScannerTask`) exposes configurable `OutputPath` and `SampleSize` properties in the Admin Portal, and its `OnTask()` method invokes the Python module via `%SYS.Python.Import()`. The task is registered automatically during Docker build and can be scheduled to run periodically — for instance, a weekly PII inventory scan that appends results to a central compliance report.

```bash
# One-shot scan from the command line
docker compose exec iris irispython -m irisapp.pii_discovery

# Scan with custom namespace and sample size
docker compose exec iris irispython -m irisapp.pii_discovery -n USER -s 50

# Populate sample data + scan in one command
docker compose exec iris irispython -m irisapp.pii_discovery --populate
```

## The Sample Database: Testing with Realistic Data

To make the utility immediately testable, the project includes a sample database in the `PIISample` schema with three tables that cover the main PII patterns:

**PIISample.Patients** — Structured single-field PII. Each column holds one type of personal data: full names, email addresses, phone numbers, SSNs/CPFs, and street addresses. The table deliberately mixes US and Brazilian records to exercise both NLP models. Non-PII columns (Diagnosis, AdmissionDate) serve as internal controls.

**PIISample.CustomerFeedback** — Free-text PII. Narrative paragraphs contain PII embedded in natural language — the hardest detection pattern. Examples include *"My SSN is 111-22-3333 for insurance verification"* and *"Meu CPF é 345.678.901-22"*. Two rows contain no PII at all, acting as negative controls within the table.

**PIISample.Products** — No PII. A clean control table with product names, categories, prices, and stock quantities. The scanner should produce zero findings here.

The sample data is populated by a Python function (`populate()`) that runs during Docker build and can be re-invoked at any time. It uses `DROP TABLE IF EXISTS` before each `CREATE TABLE`, making it idempotent and safe to call repeatedly.

## Results: What the Scanner Found — and What It Got Wrong

Running the scanner against the sample database produces the following report:

```csv
schema_name,table_name,column_name,pii_type
PIISample,Patients,FullName,PERSON
PIISample,Patients,Email,EMAIL_ADDRESS
PIISample,Patients,Phone,PHONE_NUMBER
PIISample,Patients,SSN,PHONE_NUMBER
PIISample,Patients,DateOfBirth,DATE_TIME
PIISample,Patients,Address,LOCATION
PIISample,Patients,AdmissionDate,DATE_TIME
PIISample,CustomerFeedback,CustomerName,PERSON
PIISample,CustomerFeedback,FeedbackText,EMAIL_ADDRESS
```

**Products** — zero findings. The control table passes cleanly.

The true positives are clear: names detected as PERSON, emails as EMAIL_ADDRESS, phone numbers as PHONE_NUMBER, addresses as LOCATION. The free-text column FeedbackText correctly identifies at least EMAIL_ADDRESS from embedded email strings.

But the results also reveal the limitations of the current approach:

**SSN detected as PHONE_NUMBER.** The Patients.SSN column contains values like `123-45-6789` (US SSN) and `123.456.789-00` (Brazilian CPF). Presidio has dedicated recognizers for both `US_SSN` and `CPF`, but the small spaCy models sometimes assign a higher confidence score to the PHONE_NUMBER recognizer for these digit-heavy patterns. The scanner reports the highest-scoring entity — which in this case is the wrong one.

**Date columns flagged as DATE_TIME.** Values like `1985-03-15` trigger the DATE_TIME recognizer. Whether dates of birth and admission dates constitute PII is context-dependent: under HIPAA they are, under some interpretations of GDPR they might not be (on their own). The scanner makes no policy judgment — it reports what it finds.

**One PII type per column.** The scanner's `scan_column()` method returns the first PII type found in a column. If a column contains both email addresses and phone numbers (as FeedbackText does), only the first type detected gets reported. This is by design for the MVP — a full inventory might list all detected types per column.

## The spaCy Small Model Trade-off

The false positives and misclassifications stem from a deliberate architectural choice: using spaCy's **small** models (`_sm` suffix) rather than medium (`_md`) or large (`_lg`) variants.

| Variant | Size (EN) | Accuracy | Memory | Load Time |
|---|---|---|---|---|
| `en_core_web_sm` | ~12 MB | Lower | ~100 MB | Fast |
| `en_core_web_md` | ~40 MB | Higher | ~300 MB | Moderate |
| `en_core_web_lg` | ~560 MB | Highest | ~1 GB | Slow |

The small models were chosen for the MVP because they keep the Docker image lean, startup fast, and run comfortably within the memory constraints of a containerized IRIS instance. For a proof-of-concept that needs to demonstrate feasibility, this is the right trade-off.

But the trade-off is real. Small models have less training data, fewer word vectors, and coarser entity boundaries. In practice, this means:

- **More false positives** — Common nouns in product names (`Wireless Mouse`) or category labels (`Sports`) can be misidentified as PERSON or LOCATION entities by the NLP recognizer.
- **More misclassifications** — SSN and CPF patterns, while matched by Presidio's regex recognizers, can be out-scored by the NLP-based PHONE_NUMBER recognizer when the model's confidence calibration is off.
- **Poorer context understanding** — The small model may fail to distinguish *"My name is John"* (PERSON) from *"John Deere Equipment"* (ORGANIZATION) without sufficient surrounding context.

Upgrading to medium or large models would improve accuracy significantly, but at a cost:

- **Memory** — The large English model alone requires ~1 GB of RAM at runtime, plus a similar footprint for Portuguese. In a containerized environment, this constrains how many workloads can run alongside IRIS.
- **Latency** — Loading large models adds 5–10 seconds of startup time per scan. For a scheduled task running at 2 AM, this is acceptable. For an interactive scan triggered from a UI, it may not be.
- **Image size** — The Docker image would grow by hundreds of megabytes, increasing build times and storage requirements.

An alternative path is replacing spaCy with transformer-based models (e.g., HuggingFace BERT or RoBERTa fine-tuned for NER), which offer state-of-the-art accuracy. Presidio supports this via its `NlpEngineProvider` — you can configure a Transformers-backed engine instead of spaCy. But transformer models carry even heavier resource requirements: GPU inference for acceptable latency, multiple gigabytes of memory, and significantly longer processing times per text.

The architecture of this MVP — with the PIIIdentifier fully isolated from the scanner — makes this upgrade path straightforward. Swap the NLP engine configuration, and the rest of the pipeline continues to work unchanged.

## Pros and Cons

### Strengths

- **Data sovereignty.** Data never leaves the IRIS process. No external APIs, no network transfers, no intermediate files containing raw PII. The analysis happens where the data lives.
- **Zero-friction deployment.** Runs inside the same Docker container as IRIS. No separate service to deploy, monitor, or secure. One command to scan, one CSV file as output.
- **Bilingual detection.** Dual-language support (English + Portuguese) out of the box, with a clean pattern for adding more languages.
- **Non-intrusive.** Uses sampling (`SELECT TOP N`) rather than full table scans. Configurable sample size and schema exclusions let you control scope and impact.
- **Task Scheduler integration.** Automatic periodic scans via the IRIS Admin Portal, with configurable output path and sample size — no cron jobs or external schedulers needed.
- **Modular architecture.** AI detection, database scanning, and reporting are fully decoupled. Upgrading the detection engine is a one-file change.

### Limitations

- **Small model accuracy.** As discussed, the spaCy small models produce false positives and misclassifications. This is the most significant limitation for production use.
- **One PII type per column.** The current scanner reports only the highest-confidence entity type per column, not the full set of PII types present. A column containing both emails and phone numbers will only report one.
- **No confidence scores in output.** The CSV report intentionally omits confidence scores, which makes it harder for a human reviewer to prioritize findings. A future version could include a confidence threshold parameter.
- **No column-level exclusion.** You can exclude schemas, but not individual columns. A `notes` column that is known to contain PII might be intentionally excluded from the report to avoid noise.
- **No incremental scanning.** Every run scans all tables from scratch. There is no tracking of previously scanned tables or columns, which limits scalability for large databases.
- **Sample-based detection.** If PII exists only in row 101 and beyond, a `SELECT TOP 100` sample will miss it. Random sampling (e.g., `TABLESAMPLE`) would be more robust but is not yet implemented.
- **Docker build time.** Installing Presidio, spaCy, and downloading two NLP models adds significant time to the Docker build. This is a one-time cost but can be painful during development iterations.

## What Comes Next

This MVP establishes the foundation. The modular architecture was designed so that each limitation above can be addressed incrementally:

1. **Better NLP models** — Switching to spaCy medium/large models or transformer-based engines for higher accuracy, accepting the resource trade-off. The PIIIdentifier wrapper makes this a configuration change, not a rewrite.
2. **Multi-type column reporting** — Returning all detected PII types per column, not just the first.
3. **Confidence thresholds** — Letting the user set a minimum confidence score to filter low-certainty findings.
4. **Random sampling** — Using `TABLESAMPLE` or `ORDER BY %ID` with random offsets instead of `SELECT TOP N`.
5. **Incremental scanning** — Storing scan history so only new or modified tables are re-analyzed.
6. **Column-level exclusions** — Allowing users to skip specific columns by name.
7. **Dashboard integration** — Writing findings to an IRIS persistent class instead of (or in addition to) CSV, enabling visualization via IRIS Native API, InterSystems Reports, or a web UI.

## Getting Started

The project runs on InterSystems IRIS Community Edition in Docker. Clone the repository, build the image, and start the container:

```bash
docker compose build
docker compose up -d
```

The sample database is populated automatically during the build. To run your first scan:

```bash
docker compose exec iris irispython -m irisapp.pii_discovery
```

The report will be written to `pii_report.csv` in the project root. Open it, review the findings, and compare them against the sample data to understand what the scanner catches — and what it doesn't.

From there, try the `--populate` flag to reset the sample data, change the sample size with `-s`, or point the scanner at a different namespace with `-n`. The `--populate` flag is particularly useful: it resets the sample tables and runs the scan in one step, making iteration fast.

---

*This is an MVP — a proof of concept that demonstrates the compute-to-data approach for PII discovery inside InterSystems IRIS. The small NLP models are a starting point, not a ceiling. The architecture is built to grow.*
