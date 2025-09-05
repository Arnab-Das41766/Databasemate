# DatabaseMate

DatabaseMate is an AI-powered command-line database assistant that converts **natural language queries** into **SQL commands** and executes them across multiple database types.

Powered by **Qwen AI 7B**, DatabaseMate allows you to interact with your database without writing a single line of SQL.

---

## Features
- Convert **plain English queries** into SQL using Qwen AI 7B.
- Supports multiple databases: **SQLite, MySQL, PostgreSQL**.
- Perform **CRUD operations**: Create, Read, Update, Delete.
- CLI interface for quick query execution.
- Logs both **user input** and **generated SQL** for transparency.

---

## How It Works

```
User Input (English)
        |
        v
   Qwen AI 7B (LLM)
        |
        v
   SQL Query String
        |
        v
Database Adapter (SQLite/MySQL/Postgres)
        |
        v
     Query Result
        |
        v
  Display to User
```

1. User enters a natural language query.
2. DatabaseMate sends this input to **Qwen AI 7B**.
3. AI generates a SQL query string.
4. Query executes on the selected database.
5. Results are displayed in the CLI.

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DatabaseMate.git
cd DatabaseMate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have **Ollama** installed and Qwen AI 7B available:
```bash
ollama pull qwen2.5-coder:7b
```

---

## Configuration

Edit `config.json` to set up your databases:

```json
{
  "default_db": "sqlite",
  "databases": {
    "sqlite": {
      "path": "databases/main.db"
    },
    "mysql": {
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "mydb"
    },
    "postgres": {
      "host": "localhost",
      "port": 5432,
      "user": "postgres",
      "password": "password",
      "database": "mydb"
    }
  }
}
```

---

## Running DatabaseMate

```bash
python main.py
```

Then enter your queries in **plain English**.  
Examples:
```
> List all users who signed up in August
> Show all products with price > 500
> Add a new employee named John Doe with salary 60000
```

DatabaseMate will automatically:
- Generate the SQL query using **Qwen AI 7B**.
- Execute it on the selected database.
- Return the results in CLI.

---

## Notes
- Ensure **Qwen AI 7B** is installed locally.
- Double-check **database credentials** in `config.json`.
- Logs are saved in `logs/` for troubleshooting.
- Works best with well-defined table schemas.

---

## License
MIT License

