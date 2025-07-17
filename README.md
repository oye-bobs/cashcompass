# CashCompass: Your AI-Powered Financial Companion

**Video Demo:** [https://youtu.be/gNMQEYg4LTY](https://youtu.be/gNMQEYg4LTY)

## Description

CashCompass is a personal financial management web application designed to help users track their income, expenses, savings, and debt, and gain insights into their financial health. It features an **AI Financial Advisor** powered by Google's Gemini API, providing personalized financial advice based on your aggregated data.

---

## Features

- **Financial Dashboard**: A comprehensive overview of your financial metrics, including Net Worth, Cash Flow, Savings, Liabilities, Income, and Expenses.
- **Income & Expense Tracking**: Easily record and categorize all your financial transactions.
- **Savings Goals**: Set and track progress towards your financial goals.
- **Debt Management**: Keep tabs on your liabilities and plan for repayment.
- **AI Financial Advisor**: Get personalized financial advice and actionable recommendations powered by cutting-edge AI (Google Gemini).
- **User Profiles**: Manage personal details and account settings.
- **Responsive Design**: Optimized for seamless use across various devices.

---

## Setup and Installation

Follow these steps to get **CashCompass** up and running on your local machine.

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd CashCompass
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

#### Activate the virtual environment:

- On **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

- On **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```

- On **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> You can generate `requirements.txt` by running:
```bash
pip freeze > requirements.txt
```

Include packages such as `Flask`, `requests`, `markdown`, `python-dotenv`, `cs50`, `Flask-Session`, and `Werkzeug`.

---

### 4. Set up Environment Variables (`.env` file)

CashCompass uses environment variables to securely store sensitive information.

#### Create `.env`:

In your project's root directory:

```env
GEMINI_API_KEY="YOUR_ACTUAL_GOOGLE_GEMINI_API_KEY"
DATABASE_URL="sqlite:///cashcompass.db"
MAIL_SERVER="your.smtp.server"
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME="your_smtp_username"
MAIL_PASSWORD="your_smtp_password"
MAIL_DEFAULT_SENDER="your_verified_sender@example.com"
SECRET_KEY="your_secret_key"
```

>  **Important:** Add `.env` to your `.gitignore` to keep it out of version control.

---

### 5. Initialize the Database

CashCompass uses SQLite. Create a `schema.sql` file with the following:

```sql
-- Users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Income
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL,
    category TEXT NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL,
    category TEXT NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Savings
CREATE TABLE IF NOT EXISTS savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal TEXT NOT NULL,
    amount NUMERIC NOT NULL DEFAULT 0,
    target_amount NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Debt
CREATE TABLE IF NOT EXISTS debt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    debt_name TEXT NOT NULL,
    original_balance NUMERIC NOT NULL,
    current_balance NUMERIC NOT NULL,
    interest_rate NUMERIC,
    minimum_payment NUMERIC,
    due_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Budget
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alert_hash TEXT NOT NULL UNIQUE,
    dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Run schema.sql:

```bash
sqlite3 database.db < schema.sql
```

Or using Python:

```bash
python -c "from app import db; db.execute(open('schema.sql').read())"
```

---

### 6. Run the Application

```bash
flask run
```

Visit: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## Usage

1. **Register/Login**: Access your personal dashboard.
2. **Record Data**: Add income, expenses, savings, and debts.
3. **View Dashboard**: Monitor your financial health.
4. **AI Advisor**: Navigate to "AI Financial Advisor" and click "Generate Advice".
5. **Manage Profile**: Update your settings and user info.

---


- "Forgot Password" is currently now functional .

---

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: PostGRE SQL
- **Frontend**: HTML, CSS, JavaScript (Bootstrap 5, Font Awesome)
- **AI Integration**: Google Gemini API
- **Environment Management**: python-dotenv
- **Markdown Rendering**: python-markdown

---

© 2025 **CashCompass**. All rights reserved.  
*Your path to financial freedom.*
