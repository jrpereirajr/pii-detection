# Sample Database for PII Discovery

## Overview

The sample database provides ready-to-use test data for the PII Discovery utility. It lives in the `PIISample` schema and contains three tables designed to demonstrate the two main PII patterns the scanner detects — structured single-field PII and free-text PII — plus a clean control table with no PII at all.

The data is populated by the `populate()` function in `irisapp.pii_discovery.sample_data`. It runs automatically during Docker build via `iris.script`. The function is idempotent: it drops and recreates every table on each call, so you can safely re-run it at any time.

## How to Populate

**Automatic** — Runs during `docker compose build` (via `iris.script`).

**Manual** — Three options:

```bash
# Option 1: Populate + scan in one command
docker compose exec iris irispython -m irisapp.pii_discovery --populate

# Option 2: Populate only (Python one-liner)
docker compose exec iris irispython -c "from irisapp.pii_discovery.sample_data import populate; populate()"

# Option 3: From an IRIS terminal
do ##class(%SYS.Python).Import("irisapp.pii_discovery.sample_data").populate()
```

## Tables

### PIISample.Patients

Structured single-field PII. Each column holds one type of personal data, making it straightforward for the scanner to attribute a PII type per column. Mixes US and Brazilian records to exercise both English and Portuguese NLP models.

| Column | Type | Description | PII |
|---|---|---|---|
| PatientID | INT | Primary key | No |
| FullName | VARCHAR(100) | Patient full name | Yes — PERSON |
| Email | VARCHAR(150) | Email address | Yes — EMAIL_ADDRESS |
| Phone | VARCHAR(50) | Phone number (US and BR formats) | Yes — PHONE_NUMBER |
| SSN | VARCHAR(50) | US SSN (`123-45-6789`) or Brazilian CPF (`123.456.789-00`) | Yes — US_SSN / CPF |
| DateOfBirth | VARCHAR(20) | Date of birth (`YYYY-MM-DD`) | Depends on threshold — DATE_TIME |
| Address | VARCHAR(200) | Street address with city/state/zip | Yes — LOCATION |
| Diagnosis | VARCHAR(100) | Medical diagnosis | No (control) |
| AdmissionDate | VARCHAR(20) | Hospital admission date | Depends on threshold — DATE_TIME |

**Sample data:**

| PatientID | FullName | Email | Phone | SSN | DateOfBirth | Address | Diagnosis | AdmissionDate |
|---|---|---|---|---|---|---|---|---|
| 1 | John Smith | john.smith@email.com | 555-123-4567 | 123-45-6789 | 1985-03-15 | 123 Main St, Springfield, IL 62701 | Hypertension | 2024-01-10 |
| 2 | Maria Silva | maria.silva@email.com | (11) 99999-1234 | 123.456.789-00 | 1990-07-22 | Rua Augusta 1200, São Paulo, SP | Diabetes Type 2 | 2024-02-05 |
| 3 | Robert Johnson | robert.johnson@company.org | 555-987-6543 | 987-65-4321 | 1978-11-30 | 456 Oak Avenue, Portland, OR 97201 | Asthma | 2024-03-12 |
| 4 | Ana Carolina Santos | ana.santos@email.com.br | (21) 98888-5678 | 987.654.321-00 | 1995-05-10 | Av. Paulista 1500, São Paulo, SP | Migraine | 2024-04-01 |
| 5 | Emily Davis | emily.davis@hospital.net | 555-456-7890 | 456-78-9012 | 1982-09-18 | 789 Pine Road, Austin, TX 73301 | Fracture | 2024-05-20 |
| 6 | Carlos Eduardo Oliveira | carlos.oliveira@empresa.com | (31) 97777-4321 | 456.789.012-34 | 1988-12-05 | Rua da Assembleia 100, Rio de Janeiro, RJ | Pneumonia | 2024-06-15 |

### PIISample.CustomerFeedback

Free-text PII. PII is embedded inside narrative paragraphs — the hardest pattern to detect because names, emails, phone numbers, and government IDs appear inline within natural language. Some rows contain no PII at all, serving as negative controls within the table.

| Column | Type | Description | PII |
|---|---|---|---|
| FeedbackID | INT | Primary key | No |
| CustomerName | VARCHAR(100) | Customer name | Yes — PERSON |
| FeedbackText | VARCHAR(2000) | Free-text feedback with embedded PII | Yes — varies (PERSON, EMAIL_ADDRESS, PHONE_NUMBER, US_SSN, CPF, LOCATION) |
| CreatedAt | VARCHAR(20) | Feedback date | No (control) |

**Sample data:**

| FeedbackID | CustomerName | FeedbackText | CreatedAt |
|---|---|---|---|
| 1 | James Wilson | My name is James Wilson and I had an excellent experience at the Springfield clinic. Please send follow-up information to james.wilson@email.com or call me at 555-222-3333. My address is 321 Elm Street, Springfield, IL 62704. | 2024-03-01 |
| 2 | Fernanda Costa | Olá, sou Fernanda Costa, CPF 234.567.890-11. Gostaria de reclamar sobre o atendimento. Meu telefone é (11) 96666-7890 e moro na Rua Consolação 500, São Paulo. Enviem resposta para fernanda.costa@bol.com.br. | 2024-03-05 |
| 3 | Sarah Thompson | The product quality is outstanding. I have been a loyal customer for 3 years and never had any issues. No complaints from me! | 2024-03-10 |
| 4 | Paulo Mendes | Preciso atualizar meus dados. Meu CPF é 345.678.901-22 e meu novo email é paulo.mendes@outlook.com. Telefone: (21) 95555-1234. Endereço atual: Av. Atlantica 2000, Copacabana, Rio de Janeiro. | 2024-03-15 |
| 5 | Michael Brown | I would like to schedule an appointment. You can reach me at michael.brown@email.com or at my cell 555-444-5555. My SSN is 111-22-3333 for insurance verification. I live at 567 Maple Drive, Denver, CO 80201. | 2024-03-20 |
| 6 | Juliana Rocha | Gostei muito do serviço. Recomendo a todos. Nada a reclamar. | 2024-03-25 |

Rows 3 and 6 contain no PII — they serve as negative controls within the feedback table.

### PIISample.Products

No-PII control table. Contains only product and inventory data. The scanner should report zero findings for this table, demonstrating that the tool does not produce false positives on non-personal data.

| Column | Type | Description | PII |
|---|---|---|---|
| ProductID | INT | Primary key | No |
| ProductName | VARCHAR(100) | Product name | No |
| Category | VARCHAR(50) | Product category | No |
| Price | DECIMAL(10,2) | Unit price | No |
| StockQuantity | INT | Units in stock | No |

**Sample data:**

| ProductID | ProductName | Category | Price | StockQuantity |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 29.99 | 150 |
| 2 | Office Chair | Furniture | 249.00 | 45 |
| 3 | Running Shoes | Sports | 89.50 | 200 |
| 4 | Coffee Maker | Kitchen | 79.99 | 80 |
| 5 | Notebook | Stationery | 4.50 | 500 |

## Scan Results

Running the PII scanner against the sample database produces the following output:

```
schema_name,table_name,column_name,pii_type
PIISample,CustomerFeedback,CustomerName,PERSON
PIISample,CustomerFeedback,FeedbackText,EMAIL_ADDRESS
PIISample,Patients,FullName,PERSON
PIISample,Patients,Email,EMAIL_ADDRESS
PIISample,Patients,Phone,PHONE_NUMBER
PIISample,Patients,SSN,PHONE_NUMBER
PIISample,Patients,DateOfBirth,DATE_TIME
PIISample,Patients,Address,LOCATION
PIISample,Patients,AdmissionDate,DATE_TIME
```

### Analysis of findings

**True positives (high confidence):**

| Table | Column | Detected | Expected | Notes |
|---|---|---|---|---|
| Patients | FullName | PERSON | PERSON | Correct |
| Patients | Email | EMAIL_ADDRESS | EMAIL_ADDRESS | Correct |
| Patients | Phone | PHONE_NUMBER | PHONE_NUMBER | Correct |
| Patients | Address | LOCATION | LOCATION | Correct |
| CustomerFeedback | CustomerName | PERSON | PERSON | Correct |
| CustomerFeedback | FeedbackText | EMAIL_ADDRESS | EMAIL_ADDRESS / PHONE_NUMBER / PERSON | Correct — the scanner returns the first PII type found in the column |

**Partially correct:**

| Table | Column | Detected | Expected | Notes |
|---|---|---|---|---|
| Patients | SSN | PHONE_NUMBER | US_SSN / CPF | Presidio recognizes SSN and CPF patterns but the confidence score for PHONE_NUMBER may be higher in some rows. The scanner reports the highest-scoring entity type. |

**Debatable / low-threshold findings:**

| Table | Column | Detected | Notes |
|---|---|---|---|
| Patients | DateOfBirth | DATE_TIME | ISO date strings (`1985-03-15`) trigger DATE_TIME. Whether this counts as PII depends on your compliance framework. |
| Patients | AdmissionDate | DATE_TIME | Same as above. |

**Expected negative (no findings):**

| Table | Column | Notes |
|---|---|---|
| Products | *(all columns)* | No PII detected — correct. |

**Known false positives outside the sample schema:**

The scanner also scans other user tables in the namespace (e.g., `dc_python.PersistentClass`). These are not part of the sample database. Use the `--namespace` flag or schema exclusions to control scope.

## Design Decisions

- **VARCHAR for date columns** — IRIS `DATE` type requires `$HOROLOG` internal format for inserts via `iris.sql.exec()`. Using `VARCHAR(20)` avoids format conversion issues and ensures date strings are preserved as-is for the scanner to analyze.
- **DROP TABLE IF EXISTS** — The `populate()` function drops and recreates every table on each call. This guarantees a clean state and makes the function safe to call repeatedly.
- **PIISample schema** — A dedicated schema clearly separates demo data from application tables. It does not match any of the scanner's default exclusion patterns (`%SYS`, `INFORMATION_SCHEMA`, `DOCBOOK`, `HSLIB`, `Ens*`).
- **Mixed US and Brazilian records** — Rows 1, 3, 5 use US formats (SSN `123-45-6789`, phone `555-123-4567`). Rows 2, 4, 6 use Brazilian formats (CPF `123.456.789-00`, phone `(11) 99999-1234`). This exercises both NLP models (`en_core_web_sm` and `pt_core_news_sm`).

## Resetting

To reset the sample database to its original state, simply call `populate()` again — it drops and recreates all tables:

```bash
docker compose exec iris irispython -c "from irisapp.pii_discovery.sample_data import populate; populate()"
```

To remove the sample tables entirely:

```bash
docker compose exec iris irispython -c "
import iris
iris.sql.exec('DROP TABLE IF EXISTS PIISample.Patients')
iris.sql.exec('DROP TABLE IF EXISTS PIISample.CustomerFeedback')
iris.sql.exec('DROP TABLE IF EXISTS PIISample.Products')
print('Sample tables removed.')
"
```
