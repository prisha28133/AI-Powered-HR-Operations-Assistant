# AI-Powered HR Operations Assistant

## 1. Project Overview

The AI-Powered HR Operations Assistant is an AI-based HR automation system designed to process routine employee HR requests received through email.

The system uses Artificial Intelligence to understand employee requests, Retrieval-Augmented Generation (RAG) to retrieve relevant HR policies, MySQL to validate employee-specific information, and deterministic business rules to control the final decision.

The current system supports:

- Leave Management
- Attendance Correction
- Work From Home (WFH)
- Human Review for exceptional cases
- Audit Logging
- Automated Employee Email Responses

---

## 2. Core Workflow

Employee Email
↓
Gmail / IMAP
↓
AI Request Extraction
↓
RAG Policy Retrieval
↓
Database Validation
↓
Deterministic Business Rules
↓
Approved / Rejected / Needs Human Review
↓
Database Update
↓
Audit Log
↓
Automated Email Response

### Core Design Principle

**AI understands the request, RAG provides the policy, the database provides employee-specific facts, and deterministic business rules control the final action.**

---

## 3. Technologies Used

- Python
- Qwen 2.5:3B
- Ollama
- LangChain
- Nomic Embed Text
- Chroma Vector Database
- MySQL
- Gmail / IMAP
- PDF-based HR Policy Documents

---

## 4. Project Modules

### Email Processing

**imap_reader.py**  
Connects to the email server and retrieves employee emails.

**parser.py**  
Extracts information such as sender, subject, date, and email body.

**email_sender.py**  
Sends automated responses to employees.

### AI Processing

**prompt.py**  
Builds the prompt used for extracting structured information from employee emails.

**llm.py**  
Communicates with the local Qwen language model through Ollama.

### RAG

**rag.py**  
Loads HR policy documents, creates embeddings, stores them in Chroma, and retrieves relevant policy information for employee requests.

### Leave Management

**leave_procedure.py**  
Processes approved leave requests and applies the required leave transaction logic.

**leave_transaction.py**  
Handles insertion of leave transaction records.

**validation.py**  
Validates leave requests against employee data, leave balance, dates, duplicates, and applicable rules.

### Attendance Management

**attendance_procedure.py**  
Processes approved attendance correction requests.

**validation_attendance.py**  
Validates attendance correction requests including employee records, attendance dates, correction limits, and duplicate requests.

### Work From Home

**wfh_procedure.py**  
Processes approved WFH requests.

**wfh_transaction.py**  
Handles WFH transaction records.

**validation_wfh.py**  
Validates WFH requests against employee data, balance, dates, and duplicate conditions.

### Decision and Review

**recommendation.py**  
Generates the final recommendation using the extracted request, policy context, and validation result.

**human_review.py**  
Stores requests that require human intervention.

### Database

**database.py**  
Handles MySQL database connectivity and database operations.

**config.py**  
Contains project configuration settings.

### Main Application

**app.py**  
Acts as the main controller and connects email processing, AI extraction, RAG, validation, recommendation, database updates, and email responses.

---

## 5. Policy Documents

The `Policies` folder contains the HR policy documents used by the RAG system.

Current policy documents include:

- Attendance Management Policy
- Employee Information Policy
- Leave Management Policy
- WFH Policy

These documents provide company-specific policy context to the AI system.

---

## 6. AI Model

### Language Model

**Qwen 2.5:3B**

The model is used for:

- Intent classification
- Employee request understanding
- Structured information extraction
- Processing natural-language HR requests

The model runs locally using **Ollama**.

### Embedding Model

**Nomic Embed Text**

Used to generate embeddings for HR policy documents and policy queries.

### Vector Database

**Chroma**

Used to store and retrieve policy document embeddings for RAG.

---

## 7. Database

The system uses MySQL to store and validate employee-specific information.

The database is used for:

- Employee information
- Leave balances
- Leave transactions
- Attendance records
- WFH transactions
- Email transactions
- Audit logs
- Human review records

The database provides factual employee-specific information required for validation.

---

## 8. Decision Flow

After AI extraction and policy retrieval, the request is validated against database information and deterministic business rules.

The possible outcomes are:

### Approved

The request satisfies the required validation conditions and the corresponding transaction is processed.

### Rejected

The request does not satisfy one or more required conditions.

### Needs Human Review

The request contains an exceptional, ambiguous, or conflicting situation that should be verified by HR.

---

## 9. Environment Configuration

Sensitive credentials must not be uploaded to GitHub.

Create a `.env` file locally containing the required email and MySQL configuration.

Example:

```env
EMAIL=
EMAIL_PASSWORD=

MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=