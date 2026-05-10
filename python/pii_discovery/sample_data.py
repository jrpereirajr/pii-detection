"""Sample database for PII Discovery demonstration.

Creates three tables in the PIISample schema with realistic PII data
for testing and validation: Patients (structured single-field PII),
CustomerFeedback (free-text PII), and Products (no-PII control table).
Uses DROP TABLE IF EXISTS for idempotency.
"""

import iris

_PATIENTS_CREATE = """
CREATE TABLE PIISample.Patients (
PatientID INT,
FullName VARCHAR(100),
Email VARCHAR(150),
Phone VARCHAR(50),
SSN VARCHAR(50),
DateOfBirth VARCHAR(20),
Address VARCHAR(200),
Diagnosis VARCHAR(100),
AdmissionDate VARCHAR(20)
)
"""

_PATIENTS_INSERTS = [
    "INSERT INTO PIISample.Patients VALUES (1, 'John Smith', 'john.smith@email.com', '555-123-4567', '123-45-6789', '1985-03-15', '123 Main St, Springfield, IL 62701', 'Hypertension', '2024-01-10')",
    "INSERT INTO PIISample.Patients VALUES (2, 'Maria Silva', 'maria.silva@email.com', '(11) 99999-1234', '123.456.789-00', '1990-07-22', 'Rua Augusta 1200, São Paulo, SP', 'Diabetes Type 2', '2024-02-05')",
    "INSERT INTO PIISample.Patients VALUES (3, 'Robert Johnson', 'robert.johnson@company.org', '555-987-6543', '987-65-4321', '1978-11-30', '456 Oak Avenue, Portland, OR 97201', 'Asthma', '2024-03-12')",
    "INSERT INTO PIISample.Patients VALUES (4, 'Ana Carolina Santos', 'ana.santos@email.com.br', '(21) 98888-5678', '987.654.321-00', '1995-05-10', 'Av. Paulista 1500, São Paulo, SP', 'Migraine', '2024-04-01')",
    "INSERT INTO PIISample.Patients VALUES (5, 'Emily Davis', 'emily.davis@hospital.net', '555-456-7890', '456-78-9012', '1982-09-18', '789 Pine Road, Austin, TX 73301', 'Fracture', '2024-05-20')",
    "INSERT INTO PIISample.Patients VALUES (6, 'Carlos Eduardo Oliveira', 'carlos.oliveira@empresa.com', '(31) 97777-4321', '456.789.012-34', '1988-12-05', 'Rua da Assembleia 100, Rio de Janeiro, RJ', 'Pneumonia', '2024-06-15')",
]

_FEEDBACK_CREATE = """
CREATE TABLE PIISample.CustomerFeedback (
FeedbackID INT,
CustomerName VARCHAR(100),
FeedbackText VARCHAR(2000),
CreatedAt VARCHAR(20)
)
"""

_FEEDBACK_INSERTS = [
    "INSERT INTO PIISample.CustomerFeedback VALUES (1, 'James Wilson', 'My name is James Wilson and I had an excellent experience at the Springfield clinic. Please send follow-up information to james.wilson@email.com or call me at 555-222-3333. My address is 321 Elm Street, Springfield, IL 62704.', '2024-03-01')",
    "INSERT INTO PIISample.CustomerFeedback VALUES (2, 'Fernanda Costa', 'Olá, sou Fernanda Costa, CPF 234.567.890-11. Gostaria de reclamar sobre o atendimento. Meu telefone é (11) 96666-7890 e moro na Rua Consolação 500, São Paulo. Enviem resposta para fernanda.costa@bol.com.br.', '2024-03-05')",
    "INSERT INTO PIISample.CustomerFeedback VALUES (3, 'Sarah Thompson', 'The product quality is outstanding. I have been a loyal customer for 3 years and never had any issues. No complaints from me!', '2024-03-10')",
    "INSERT INTO PIISample.CustomerFeedback VALUES (4, 'Paulo Mendes', 'Preciso atualizar meus dados. Meu CPF é 345.678.901-22 e meu novo email é paulo.mendes@outlook.com. Telefone: (21) 95555-1234. Endereço atual: Av. Atlantica 2000, Copacabana, Rio de Janeiro.', '2024-03-15')",
    "INSERT INTO PIISample.CustomerFeedback VALUES (5, 'Michael Brown', 'I would like to schedule an appointment. You can reach me at michael.brown@email.com or at my cell 555-444-5555. My SSN is 111-22-3333 for insurance verification. I live at 567 Maple Drive, Denver, CO 80201.', '2024-03-20')",
    "INSERT INTO PIISample.CustomerFeedback VALUES (6, 'Juliana Rocha', 'Gostei muito do serviço. Recomendo a todos. Nada a reclamar.', '2024-03-25')",
]

_PRODUCTS_CREATE = """
CREATE TABLE PIISample.Products (
ProductID INT,
ProductName VARCHAR(100),
Category VARCHAR(50),
Price DECIMAL(10,2),
StockQuantity INT
)
"""

_PRODUCTS_INSERTS = [
    "INSERT INTO PIISample.Products VALUES (1, 'Wireless Mouse', 'Electronics', 29.99, 150)",
    "INSERT INTO PIISample.Products VALUES (2, 'Office Chair', 'Furniture', 249.00, 45)",
    "INSERT INTO PIISample.Products VALUES (3, 'Running Shoes', 'Sports', 89.50, 200)",
    "INSERT INTO PIISample.Products VALUES (4, 'Coffee Maker', 'Kitchen', 79.99, 80)",
    "INSERT INTO PIISample.Products VALUES (5, 'Notebook', 'Stationery', 4.50, 500)",
]

_TABLES = [
    ("PIISample.Patients", _PATIENTS_CREATE, _PATIENTS_INSERTS),
    ("PIISample.CustomerFeedback", _FEEDBACK_CREATE, _FEEDBACK_INSERTS),
    ("PIISample.Products", _PRODUCTS_CREATE, _PRODUCTS_INSERTS),
]


def populate():
    """Create and populate the PIISample schema with sample data.

    Drops existing tables (if any) and recreates them with sample rows.
    Safe to call repeatedly — uses DROP TABLE IF EXISTS for idempotency.

    Tables created:
        PIISample.Patients — Structured single-field PII (names, emails,
            phones, SSNs/CPFs, addresses, dates) mixed US and Brazilian.
        PIISample.CustomerFeedback — Free-text PII embedded in narrative
            paragraphs, with two no-PII rows as negative controls.
        PIISample.Products — No-PII control table with product names,
            categories, prices, and stock quantities.
    """
    for table_name, create_sql, insert_sqls in _TABLES:
        iris.sql.exec(f"DROP TABLE IF EXISTS {table_name}")
        iris.sql.exec(create_sql)
        for insert_sql in insert_sqls:
            iris.sql.exec(insert_sql)
        print(f"Created {table_name} with {len(insert_sqls)} rows")
    print("Sample data populated successfully.")
